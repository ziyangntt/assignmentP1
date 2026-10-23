# loan-calc — Architecture (Assignment P1)

This document explains the *current* behavior of the legacy module under `loan_calc/calculator.py` in plain language: what each function does, key assumptions, and how functions relate to each other.

> Notes:
> - Rates are treated as **annual percentage rate** inputs (e.g. `9` means 9% p.a.).
> - Most computations convert to a **monthly decimal rate** (e.g. 9% p.a. → 0.0075 per month) via `_monthly_rate()`.
> - Monetary values are generally rounded to **2 decimals**.
> - The module is functional (no classes), with one internal helper (`_monthly_rate`) and multiple public functions.

---

## Files & entrypoints

- `loan_calc/calculator.py`: all business logic (EMI, schedules, prepayment, etc.)
- `cli.py`: command-line wrapper that prints:
  - a `summary()` for any loan input
  - optionally `amortisation_schedule()` rows (`--schedule`)
  - optionally `prepayment_savings()` output (`--prepay-month`, `--prepay-amount`)

---

## Constants

### `DEFAULT_CURRENCY = "INR"`
Used by `summary()` to label output currency.

---

## Function-by-function explanations

### `_monthly_rate(annual_rate)`
**Type:** internal helper (leading underscore)

**Purpose:** Convert an annual rate in percent p.a. to a monthly *decimal* rate.

**Implementation:**
- `annual_rate / 1200` (divide by 12 months and by 100 for percent)
- rounded to 4 decimals

**Used by:**
- `emi()`
- `amortisation_schedule()`
- `eligible_amount()`
- `remaining_tenure()` (after bug fix)

---

### `emi(principal, annual_rate, tenure_months)`
**Purpose:** Compute the fixed monthly EMI (Equated Monthly Instalment).

**Key logic:**
- Validates `tenure_months > 0` and `principal > 0`
- Uses monthly rate `r = _monthly_rate(annual_rate)`
- If `r == 0`, returns `principal / tenure_months`
- Else uses standard EMI formula:

`EMI = P * r * (1+r)^n / ((1+r)^n - 1)`

**Returns:** float rounded to 2 decimals.

---

### `total_payment(principal, annual_rate, tenure_months)`
**Purpose:** Total amount paid over the full tenure (EMI × months).

**Implementation:** `emi(...) * tenure_months`, rounded to 2 decimals.

---

### `total_interest(principal, annual_rate, tenure_months)`
**Purpose:** Total interest paid over the full tenure.

**Implementation:** `total_payment(...) - principal`, rounded to 2 decimals.

---

### `amortisation_schedule(principal, annual_rate, tenure_months)`
**Purpose:** Produce a month-by-month amortisation schedule.

**Output format:** list of dicts, each row like:
```py
{
  "month": int,
  "emi": float,
  "interest": float,
  "principal": float,
  "balance": float
}
```

**Algorithm:**
- Computes:
  - monthly rate `r`
  - monthly `instalment = emi(...)`
- Tracks a running `balance` starting from `principal`
- For each month from 1..`tenure_months`:
  - `interest = balance * r`
  - `principal_part = instalment - interest`
  - On the **last month**, forces principal_part to equal the remaining `balance`
    - and adjusts last EMI to `principal_part + interest`
  - Updates `balance = balance - principal_part`
  - clamps `balance` at minimum 0.0 in output

**Important:** This function is central; other functions treat it as the source of truth for balances over time.

---

### `outstanding_after(principal, annual_rate, tenure_months, months_paid)`
**Purpose:** Return outstanding principal after a certain number of EMIs have been paid.

**Behavior:**
- If `months_paid <= 0`: returns original principal
- Builds amortisation schedule
- If `months_paid > len(schedule)`: returns `0.0`
- Else returns `schedule[months_paid - 1]["balance"]`

---

### `remaining_tenure(balance, annual_rate, instalment)`
**Purpose:** Compute how many months are required to repay a given remaining balance with a fixed monthly payment (`instalment`), at a given interest rate.

**Interpretation of inputs:**
- `balance`: remaining principal (not the original principal)
- `instalment`: the monthly payment amount (EMI)

**Behavior:**
- If `balance <= 0`: returns 0
- Uses monthly rate `r = _monthly_rate(annual_rate)`
- If `r == 0`: returns `ceil(balance / instalment)`
- If `instalment <= balance * r`: raises `ValueError` (payment doesn’t even cover monthly interest)
- Else computes `n` using the standard closed-form repayment formula:

`n = -log(1 - balance*r/instalment) / log(1+r)`

Returns `ceil(n)`.

---

### `prepayment_savings(principal, annual_rate, tenure_months, prepay_month, prepay_amount)`
**Purpose:** Model a lump-sum prepayment at a given month while keeping EMI constant, then compute tenure reduction and interest saved.

**Steps:**
1. Compute `instalment = emi(...)`
2. Build full schedule
3. Look up balance at `prepay_month`:
   - `balance = sched[prepay_month - 1]["balance"]`
4. Subtract `prepay_amount` to get `new_balance`
5. If `new_balance <= 0`: `months_left = 0`
   else `months_left = remaining_tenure(new_balance, annual_rate, instalment)`
6. Compute:
   - `original_left = tenure_months - prepay_month`
   - `interest_paid_so_far = sum(interest for rows up to prepay_month)`
   - `original_interest = total_interest(...)`
7. Estimate new totals:
   - `new_total = instalment * prepay_month + prepay_amount + instalment * months_left`
   - `new_interest = new_total - principal`
8. Return a dict including:
   - `months_saved`
   - `new_tenure`
   - `interest_saved`
   - `interest_paid_before_prepayment`
   - `emi` (instalment)

**Assumption:** After prepayment, EMI stays the same and tenure shortens.

---

### `compare_offers(principal, offers)`
**Purpose:** Compare multiple loan offers and sort by total cost.

**Input:** `offers` list of dicts like:
```py
{"bank": "...", "rate": 8.5, "tenure": 240, "processing_fee_pct": 0.5}
```

**Computes per offer:**
- `emi`
- `total_interest`
- `processing_fee = processing_fee_pct * principal / 100`
- `total_cost = total_interest + processing_fee`

Sorts ascending by `total_cost`.

---

### `eligible_amount(monthly_income, existing_emis, annual_rate, tenure_months, foir=0.5)`
**Purpose:** Calculate maximum eligible loan principal given an affordability constraint.

**Definitions:**
- FOIR = fraction of income allowed to go to EMIs
- `available = monthly_income * foir - existing_emis`

**Behavior:**
- If `available <= 0`: returns 0.0
- If rate is 0: eligible principal = `available * tenure_months`
- Else rearranges EMI formula to solve for principal given `available` EMI:
  - `P = available * (f - 1) / (r * f)` where `f = (1 + r)^n`

---

### `format_inr(amount)`
**Purpose:** Format a number into an INR-style currency string (₹ with Indian digit grouping).

**Examples:**
- `format_inr(1000000)` → `₹10,00,000.00`
- `format_inr(-1234.5)` → `-₹1,234.50`

---

### `schedule_to_csv(rows, path)`
**Purpose:** Write amortisation rows to a CSV file.

**Output columns:**
`month,emi,interest,principal,balance`

---

### `summary(principal, annual_rate, tenure_months, start=None)`
**Purpose:** Create a display-friendly summary dict (used by CLI).

**Includes:**
- formatted principal, EMI, totals (via `format_inr`)
- tenure string
- rate string
- `last_emi` as `YYYY-MM` computed by adding `tenure_months` to the start month
- `currency` set to `DEFAULT_CURRENCY`

---

## Call relationships (high-level)

- `_monthly_rate()` is used by several computations to ensure consistent monthly-rate handling.
- `emi()` is the core primitive:
  - used by `total_payment()`, `amortisation_schedule()`, `prepayment_savings()`, `compare_offers()`, `summary()`
- `amortisation_schedule()` is used by:
  - `outstanding_after()`
  - `prepayment_savings()`
- `remaining_tenure()` is used by:
  - `prepayment_savings()`

---
