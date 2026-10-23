import math
from datetime import date
from typing import Any


DEFAULT_CURRENCY = "INR"


def _monthly_rate(annual_rate: float) -> float:
    r = round(annual_rate / 1200, 4)
    return r


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate the Equated Monthly Instalment (EMI).

    Args:
        principal: Loan principal amount. Must be positive.
        annual_rate: Nominal annual interest rate in percent (e.g. 9 for 9% p.a.).
        tenure_months: Loan tenure in months. Must be positive.

    Returns:
        Monthly EMI amount, rounded to 2 decimals.

    Raises:
        ValueError: If principal <= 0 or tenure_months <= 0.
    """
    if tenure_months <= 0:
        raise ValueError("tenure must be positive")
    if principal <= 0:
        raise ValueError("principal must be positive")
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(principal / tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(principal * r * f / (f - 1), 2)


def total_payment(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Return the total amount paid over the full tenure (EMI × months)."""
    return round(emi(principal, annual_rate, tenure_months) * tenure_months, 2)


def total_interest(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Return total interest payable over the full tenure."""
    return round(total_payment(principal, annual_rate, tenure_months) - principal, 2)


def amortisation_schedule(
    principal: float, annual_rate: float, tenure_months: int
) -> list[dict[str, float]]:
    """Generate a month-by-month amortisation schedule.

    Each row includes the EMI, interest component, principal component and the
    remaining balance after the payment for that month.

    Args:
        principal: Original principal amount.
        annual_rate: Nominal annual interest rate in percent.
        tenure_months: Tenure in months.

    Returns:
        List of rows. Each row is a dict with keys: month, emi, interest,
        principal, balance.
    """
    r = _monthly_rate(annual_rate)
    instalment = emi(principal, annual_rate, tenure_months)
    balance = principal
    rows = []
    for month in range(1, tenure_months + 1):
        interest = round(balance * r, 2)
        principal_part = round(instalment - interest, 2)
        if month == tenure_months:
            principal_part = round(balance, 2)
            instalment_amt = round(principal_part + interest, 2)
        else:
            instalment_amt = instalment
        balance = round(balance - principal_part, 2)
        rows.append({
            "month": month,
            "emi": instalment_amt,
            "interest": interest,
            "principal": principal_part,
            "balance": max(balance, 0.0),
        })
    return rows


def outstanding_after(
    principal: float, annual_rate: float, tenure_months: int, months_paid: int
) -> float:
    """Return outstanding principal after `months_paid` payments."""
    if months_paid <= 0:
        return round(principal, 2)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    if months_paid > len(sched):
        return 0.0
    return sched[months_paid - 1]["balance"]


def remaining_tenure(balance: float, annual_rate: float, instalment: float) -> int:
    """Compute remaining number of months needed to repay a balance.

    Args:
        balance: Remaining principal outstanding.
        annual_rate: Nominal annual interest rate in percent.
        instalment: Fixed monthly payment amount (EMI).

    Returns:
        Number of months (rounded up) to repay the balance.

    Raises:
        ValueError: If the instalment is not large enough to cover monthly
            interest (repayment would never complete).
    """
    r = _monthly_rate(annual_rate)
    if balance <= 0:
        return 0
    if r == 0:
        return math.ceil(balance / instalment)
    if instalment <= balance * r:
        raise ValueError("instalment too small to repay the loan")
    n = -math.log(1 - balance * r / instalment) / math.log(1 + r)
    return math.ceil(n)


def prepayment_savings(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    prepay_month: int,
    prepay_amount: float,
) -> dict[str, float]:
    """Estimate savings from a lump-sum prepayment while keeping EMI constant.

    The model keeps EMI the same after the prepayment and reduces the remaining
    tenure accordingly.

    Args:
        principal: Original loan principal.
        annual_rate: Nominal annual interest rate in percent.
        tenure_months: Original tenure in months.
        prepay_month: Month number (1-indexed) at which prepayment is made.
        prepay_amount: Lump-sum amount paid towards principal.

    Returns:
        A dict containing EMI, months saved, new tenure, interest saved, and
        interest paid before prepayment.
    """
    instalment = emi(principal, annual_rate, tenure_months)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    balance = sched[prepay_month - 1]["balance"]
    new_balance = balance - prepay_amount
    if new_balance <= 0:
        months_left = 0
    else:
        months_left = remaining_tenure(new_balance, annual_rate, instalment)
    original_left = tenure_months - prepay_month
    interest_paid_so_far = sum(row["interest"] for row in sched[:prepay_month])
    original_interest = total_interest(principal, annual_rate, tenure_months)
    new_total = instalment * prepay_month + prepay_amount + instalment * months_left
    new_interest = new_total - principal
    return {
        "emi": instalment,
        "months_saved": original_left - months_left,
        "new_tenure": prepay_month + months_left,
        "interest_saved": round(original_interest - new_interest, 2),
        "interest_paid_before_prepayment": round(interest_paid_so_far, 2),
    }


def compare_offers(principal: float, offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare multiple loan offers and sort them by total cost.

    Each offer dict should have: bank, rate, tenure, and optional processing_fee_pct.
    """
    out = []
    for o in offers:
        e = emi(principal, o["rate"], o["tenure"])
        ti = total_interest(principal, o["rate"], o["tenure"])
        fee = o.get("processing_fee_pct", 0) * principal / 100
        out.append({
            "bank": o["bank"],
            "emi": e,
            "total_interest": ti,
            "processing_fee": round(fee, 2),
            "total_cost": round(ti + fee, 2),
        })
    out.sort(key=lambda x: x["total_cost"])
    return out


def eligible_amount(
    monthly_income: float,
    existing_emis: float,
    annual_rate: float,
    tenure_months: int,
    foir: float = 0.5,
) -> float:
    """Compute the maximum eligible principal based on income and FOIR.

    Args:
        monthly_income: Gross monthly income.
        existing_emis: Sum of existing monthly EMI obligations.
        annual_rate: Nominal annual interest rate in percent.
        tenure_months: Tenure in months.
        foir: Fraction of income allowed to be used for EMIs.

    Returns:
        Maximum eligible principal amount (rounded to 2 decimals).
    """
    available = monthly_income * foir - existing_emis
    if available <= 0:
        return 0.0
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(available * tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(available * (f - 1) / (r * f), 2)


def format_inr(amount: float) -> str:
    """Format a numeric amount as an INR currency string (₹) with Indian grouping."""
    neg = amount < 0
    amount = abs(round(amount, 2))
    whole, frac = f"{amount:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "₹" + whole + "." + frac


def schedule_to_csv(rows: list[dict[str, float]], path: str) -> None:
    """Write an amortisation schedule (rows) to a CSV file at `path`."""
    with open(path, "w") as fh:
        fh.write("month,emi,interest,principal,balance\n")
        for r in rows:
            fh.write(f'{r["month"]},{r["emi"]},{r["interest"]},{r["principal"]},{r["balance"]}\n')


def summary(
    principal: float, annual_rate: float, tenure_months: int, start: date | None = None
) -> dict[str, str]:
    """Return a display-friendly summary for the loan.

    Args:
        principal: Loan principal.
        annual_rate: Nominal annual rate in percent.
        tenure_months: Tenure in months.
        start: Start date (defaults to today).

    Returns:
        A dict of formatted strings for display/CLI output.
    """
    start = start or date.today()
    e = emi(principal, annual_rate, tenure_months)
    end_year = start.year + (start.month - 1 + tenure_months) // 12
    end_month = (start.month - 1 + tenure_months) % 12 + 1
    return {
        "principal": format_inr(principal),
        "rate": f"{annual_rate}% p.a.",
        "tenure": f"{tenure_months} months",
        "emi": format_inr(e),
        "total_interest": format_inr(total_interest(principal, annual_rate, tenure_months)),
        "total_payment": format_inr(total_payment(principal, annual_rate, tenure_months)),
        "last_emi": f"{end_year}-{end_month:02d}",
        "currency": DEFAULT_CURRENCY,
    }