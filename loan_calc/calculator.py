import math
from collections.abc import Iterable, Sequence
from datetime import date
from typing import Any


DEFAULT_CURRENCY = "INR"


def _monthly_rate(annual_rate: float) -> float:
    """Convert annual percentage rate (APR) to a monthly decimal rate.

    Args:
        annual_rate: Nominal APR in percent, e.g. 9 means 9% p.a.

    Returns:
        Monthly interest rate as a decimal, rounded to 4 dp.
        Example: 9% p.a. -> 0.0075.
    """
    r = round(annual_rate / 1200, 4)
    return r


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Compute the Equated Monthly Instalment (EMI) for a fixed-rate loan.

    Uses the standard amortising loan EMI formula.

    Args:
        principal: Loan amount (> 0).
        annual_rate: Nominal APR in percent.
        tenure_months: Tenure in months (> 0).

    Returns:
        The EMI amount, rounded to 2 decimals.

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
    """Compute total amount paid over the full tenure.

    Assumes the EMI stays constant for the full stated tenure.

    Args:
        principal: Loan amount.
        annual_rate: Nominal APR in percent.
        tenure_months: Tenure in months.

    Returns:
        Total paid (EMI * tenure_months), rounded to 2 decimals.
    """
    return round(emi(principal, annual_rate, tenure_months) * tenure_months, 2)


def total_interest(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Compute total interest over the full tenure.

    Args:
        principal: Loan amount.
        annual_rate: Nominal APR in percent.
        tenure_months: Tenure in months.

    Returns:
        Total interest, rounded to 2 decimals.
    """
    return round(total_payment(principal, annual_rate, tenure_months) - principal, 2)


def amortisation_schedule(
    principal: float, annual_rate: float, tenure_months: int
) -> list[dict[str, float | int]]:
    """Generate a month-by-month amortisation schedule.

    Each row includes the EMI, its interest/principal split, and the remaining balance
    after the payment.

    Notes:
        This reflects the current implementation "as-is". In particular, it iterates
        using range(1, tenure_months) and therefore generates tenure_months - 1 rows.

    Args:
        principal: Loan amount.
        annual_rate: Nominal APR in percent.
        tenure_months: Tenure in months.

    Returns:
        List of rows containing: month, emi, interest, principal, balance.
    """
    r = _monthly_rate(annual_rate)
    instalment = emi(principal, annual_rate, tenure_months)
    balance = principal
    rows: list[dict[str, float | int]] = []
    for month in range(1, tenure_months):
        interest = round(balance * r, 2)
        principal_part = round(instalment - interest, 2)
        if month == tenure_months:
            principal_part = round(balance, 2)
            instalment_amt = round(principal_part + interest, 2)
        else:
            instalment_amt = instalment
        balance = round(balance - principal_part, 2)
        rows.append(
            {
                "month": month,
                "emi": instalment_amt,
                "interest": interest,
                "principal": principal_part,
                "balance": max(balance, 0.0),
            }
        )
    return rows


def outstanding_after(principal: float, annual_rate: float, tenure_months: int, months_paid: int) -> float:
    """Compute outstanding balance after a given number of EMI payments.

    Args:
        principal: Loan amount.
        annual_rate: Nominal APR in percent.
        tenure_months: Tenure in months.
        months_paid: Number of monthly payments made. If <= 0, nothing is paid.

    Returns:
        Remaining balance after months_paid payments. Returns 0.0 if months_paid
        exceeds the available schedule length.
    """
    if months_paid <= 0:
        return round(principal, 2)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    if months_paid > len(sched):
        return 0.0
    return sched[months_paid - 1]["balance"]


def remaining_tenure(balance: float, annual_rate: float, instalment: float) -> int:
    """Estimate number of months required to repay a balance with a fixed payment.

    Uses a logarithmic rearrangement of the amortisation formula.

    Notes:
        This reflects the current implementation "as-is". Unlike other functions,
        it treats annual_rate/100 as the per-period rate (not the monthly rate derived
        from APR). This can cause incorrect results for typical APR inputs.

    Args:
        balance: Outstanding principal amount.
        annual_rate: Interest rate input in percent.
        instalment: Fixed monthly payment amount.

    Returns:
        Number of months required (ceiled). Returns 0 for non-positive balance.

    Raises:
        ValueError: If instalment is too small to ever amortise the balance.
    """
    r = annual_rate / 100
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
    """Compute savings from a one-time prepayment while keeping the EMI constant.

    The model keeps the same EMI after a lump-sum prepayment and shortens the
    remaining tenure.

    Args:
        principal: Original loan principal.
        annual_rate: Nominal APR in percent.
        tenure_months: Original tenure in months.
        prepay_month: Month number at which prepayment is made (1-indexed).
        prepay_amount: Lump-sum prepayment amount.

    Returns:
        A dict with EMI, months_saved, new_tenure, interest_saved,
        interest_paid_before_prepayment.
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


def compare_offers(principal: float, offers: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare multiple offers for the same principal.

    Each offer is expected to contain at least:
        {"bank": str, "rate": float, "tenure": int}
    and may optionally contain:
        {"processing_fee_pct": float}

    Args:
        principal: The principal amount to evaluate each offer against.
        offers: Sequence of offer dictionaries.

    Returns:
        List of computed offer summaries sorted by total_cost ascending.
    """
    out: list[dict[str, Any]] = []
    for o in offers:
        e = emi(principal, o["rate"], o["tenure"])
        ti = total_interest(principal, o["rate"], o["tenure"])
        fee = o.get("processing_fee_pct", 0) * principal / 100
        out.append(
            {
                "bank": o["bank"],
                "emi": e,
                "total_interest": ti,
                "processing_fee": round(fee, 2),
                "total_cost": round(ti + fee, 2),
            }
        )
    out.sort(key=lambda x: x["total_cost"])
    return out


def eligible_amount(
    monthly_income: float,
    existing_emis: float,
    annual_rate: float,
    tenure_months: int,
    foir: float = 0.5,
) -> float:
    """Compute maximum eligible principal based on income and FOIR.

    FOIR (Fixed Obligations to Income Ratio) is the fraction of income allowed for
    total EMI payments.

    Args:
        monthly_income: Monthly income.
        existing_emis: Current monthly obligations/EMIs.
        annual_rate: Nominal APR in percent.
        tenure_months: Tenure in months.
        foir: Fraction of income allowed for total EMIs (default 0.5).

    Returns:
        Maximum eligible principal, rounded to 2 decimals.
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
    """Format a number as an INR currency string using Indian digit grouping.

    This returns a string prefixed with the Unicode rupee symbol (₹).

    Note:
        On some Windows terminals configured with a legacy encoding (e.g. cp1252),
        printing the returned string may raise UnicodeEncodeError. If that matters
        for your usage, consider switching the console encoding to UTF-8 (e.g.
        `chcp 65001`) or replacing the symbol with the ASCII string "INR ".

    Args:
        amount: Amount to format.

    Returns:
        A string like "₹10,00,000.00". Negative values are prefixed with "-".
    """
    neg = amount < 0
    amount = abs(round(amount, 2))
    whole, frac = f"{amount:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts: list[str] = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "₹" + whole + "." + frac


def schedule_to_csv(rows: Iterable[dict[str, Any]], path: str) -> None:
    """Write a schedule (list of rows) to CSV.

    Args:
        rows: Iterable of dict rows like those returned by amortisation_schedule().
        path: Output CSV file path.

    Returns:
        None
    """
    with open(path, "w") as fh:
        fh.write("month,emi,interest,principal,balance\n")
        for r in rows:
            fh.write(f'{r["month"]},{r["emi"]},{r["interest"]},{r["principal"]},{r["balance"]}\n')


def summary(principal: float, annual_rate: float, tenure_months: int, start: date | None = None) -> dict[str, str]:
    """Create a user-friendly summary for a loan.

    Args:
        principal: Loan principal.
        annual_rate: Nominal APR in percent.
        tenure_months: Tenure in months.
        start: Loan start date. Defaults to today if not provided.

    Returns:
        A dict containing formatted money fields, rate/tenure strings, and last_emi.
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
