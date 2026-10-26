# loan-calc — Architecture / Function Guide

This document explains what each public function in `loan_calc/` does, its inputs/outputs, and how the pieces fit together. It reflects the **current code as-is** (including known quirks/bugs), so it can be used as a baseline before fixing the seeded issues in later steps.

## Package layout

- `loan_calc/__init__.py` — package export surface (re-exports functions).
- `loan_calc/calculator.py` — implementation of all core calculations (EMI, schedule, prepayment, etc.).
- `cli.py` — thin CLI wrapper around the library functions.
- `tests/` — empty starter test folder.

---

## `loan_calc/calculator.py`

### `DEFAULT_CURRENCY = "INR"`
A constant used by `summary()` to label output currency.

---

### `_monthly_rate(annual_rate)`
**Purpose:** Convert an annual percentage rate (APR) into a monthly rate used for interest calculations.

**Signature:** `def _monthly_rate(annual_rate):`

**Inputs**
- `annual_rate`: nominal annual interest rate in percent (e.g. `9` means 9% p.a.)

**Output**
- Returns `r` as a decimal monthly rate (e.g. `9% / 12` → `0.0075`) rounded to 4 decimals.

**Notes / behavior**
- The function rounds the monthly rate to **4 decimal places**:
  ```py
  r = round(annual_rate / 1200, 4)
  ```
  This rounding affects downstream results (EMI, total interest, schedules).

**Used by**
- `emi()`, `amortisation_schedule()`, `eligible_amount()`

---

### `emi(principal, annual_rate, tenure_months)`
**Purpose:** Compute the Equated Monthly Instalment (EMI) for a fixed-rate amortising loan.

**Inputs**
- `principal`: loan amount (must be `> 0`)
- `annual_rate`: APR in percent (must be valid number; negative isn’t explicitly blocked)
- `tenure_months`: number of months (must be `> 0`)

**Output**
- Monthly EMI as a float rounded to 2 decimals.

**Logic**
- If `tenure_months <= 0`: raises `ValueError("tenure must be positive")`
- If `principal <= 0`: raises `ValueError("principal must be positive")`
- Monthly rate is derived via `_monthly_rate(annual_rate)`
- If monthly rate is zero, EMI is simple division: `principal / tenure_months`
- Else uses standard EMI formula:
  \[
  EMI = P \cdot r \cdot \frac{(1+r)^n}{(1+r)^n - 1}
  \]

**Used by**
- `total_payment()`, `total_interest()`, `amortisation_schedule()`, `prepayment_savings()`, `compare_offers()`, `summary()`

---

### `total_payment(principal, annual_rate, tenure_months)`
**Purpose:** Total amount paid over the full tenure, assuming constant EMI and full tenure payments.

**Output**
- `emi(...) * tenure_months`, rounded to 2 decimals.

**Notes**
- Uses `emi()` internally; so its rounding and `_monthly_rate()` rounding affect totals.

---

### `total_interest(principal, annual_rate, tenure_months)`
**Purpose:** Total interest paid over full tenure.

**Output**
- `total_payment(...) - principal`, rounded to 2 decimals.

---

### `amortisation_schedule(principal, annual_rate, tenure_months)`
**Purpose:** Build a month-by-month amortisation schedule: interest/principal split and remaining balance.

**Output**
- A list of dict rows:
  ```py
  {
    "month": int,
    "emi": float,
    "interest": float,
    "principal": float,
    "balance": float,
  }
  ```

**Logic (as currently implemented)**
- Computes:
  - `r = _monthly_rate(annual_rate)`
  - `instalment = emi(...)`
  - iterates:
    ```py
    for month in range(1, tenure_months):
    ```
  - For each `month`, calculates:
    - `interest = round(balance * r, 2)`
    - `principal_part = round(instalment - interest, 2)`
    - `balance = round(balance - principal_part, 2)`
    - stores row with `balance` clamped at minimum 0.

**Important quirk / likely bug**
- The loop is `range(1, tenure_months)`, which yields months `1..tenure_months-1`.  
  That means the schedule returns **tenure_months - 1 rows**, not `tenure_months` rows.
- There is also an `if month == tenure_months:` block intended to adjust the final instalment, but it is currently **unreachable** because the loop never reaches `tenure_months`.

**Used by**
- `outstanding_after()`, `prepayment_savings()`, and the CLI `--schedule` output.

---

### `outstanding_after(principal, annual_rate, tenure_months, months_paid)`
**Purpose:** Compute remaining outstanding balance after paying `months_paid` EMIs.

**Inputs**
- `months_paid`: if `<= 0`, treated as none paid.

**Output**
- Remaining balance as float.

**Logic**
- If `months_paid <= 0`: returns principal
- Else it generates the amortisation schedule and returns the balance at index `months_paid - 1`
- If `months_paid > len(schedule)`: returns `0.0`

**Notes**
- Because `amortisation_schedule()` currently returns `tenure_months - 1` rows, the behavior near the end of the tenure can be off.

---

### `remaining_tenure(balance, annual_rate, instalment)`
**Purpose:** Compute how many months are needed to pay off a given `balance` at a fixed periodic payment.

**Output**
- An integer number of months (ceiled).

**Logic (as currently implemented)**
- Uses:
  ```py
  r = annual_rate / 100
  ```
  and then applies:
  ```py
  if instalment <= balance * r:
      raise ValueError("instalment too small to repay the loan")
  n = -log(1 - balance*r/instalment) / log(1+r)
  ```
- If `balance <= 0`: returns 0
- If `r == 0`: returns `ceil(balance / instalment)`

**Important quirk / likely bug**
- Unlike the rest of the module, this function treats `annual_rate/100` as the **per-period rate**.  
  Elsewhere, interest is calculated with `_monthly_rate(annual_rate)` (APR percent → monthly decimal).
- As a result, when `annual_rate` is an APR percent like `9`, this function effectively uses `0.09` **per month** rather than `0.0075` per month, which can cause:
  - spurious `ValueError("instalment too small...")`
  - incorrect tenure estimates

**Used by**
- `prepayment_savings()`

---

### `prepayment_savings(principal, annual_rate, tenure_months, prepay_month, prepay_amount)`
**Purpose:** Model a lump-sum prepayment at a given month while keeping EMI constant, and compute savings.

**Docstring**
- “Keep the same EMI after a lump-sum prepayment and shorten the tenure.”

**Output**
A dict:
```py
{
  "emi": float,
  "months_saved": int,
  "new_tenure": int,
  "interest_saved": float,
  "interest_paid_before_prepayment": float,
}
```

**Logic**
1. Compute original EMI (`instalment = emi(...)`).
2. Generate schedule.
3. Take `balance = schedule[prepay_month - 1]["balance"]` (outstanding after that month).
4. Compute `new_balance = balance - prepay_amount`.
5. If `new_balance <= 0`: `months_left = 0` else `months_left = remaining_tenure(new_balance, annual_rate, instalment)`.
6. Compute:
   - `original_left = tenure_months - prepay_month`
   - `interest_paid_so_far` = sum of interest rows up to `prepay_month`
   - `original_interest = total_interest(...)`
   - `new_total = instalment * prepay_month + prepay_amount + instalment * months_left`
   - `new_interest = new_total - principal`
7. Return the savings summary.

**Notes / quirks**
- Depends on both `amortisation_schedule()` row count and `remaining_tenure()` interest rate handling.
- The CLI example `--prepay-month 24 --prepay-amount 200000` currently throws `ValueError: instalment too small to repay the loan` due to the `remaining_tenure()` rate mismatch described above.

---

### `compare_offers(principal, offers)`
**Purpose:** Compare multiple loan offers for the same principal and sort by total cost.

**Inputs**
- `principal`: base principal amount
- `offers`: list of dicts like:
  ```py
  {"bank": str, "rate": float, "tenure": int, "processing_fee_pct": float?}
  ```

**Output**
- List of dicts:
  ```py
  {
    "bank": str,
    "emi": float,
    "total_interest": float,
    "processing_fee": float,
    "total_cost": float,
  }
  ```
  sorted by `total_cost` ascending.

**Notes**
- `total_cost` is computed as `total_interest + processing_fee`, which excludes principal (i.e., it is “cost over principal”), not “total payment including principal”.

---

### `eligible_amount(monthly_income, existing_emis, annual_rate, tenure_months, foir=0.5)`
**Purpose:** Compute the maximum principal eligible based on income and FOIR (fixed obligations to income ratio).

**Inputs**
- `monthly_income`: monthly income amount
- `existing_emis`: monthly obligations/EMIs
- `foir`: fraction of income allowed for total EMIs (default 0.5)

**Output**
- Maximum eligible principal as float rounded to 2 decimals.

**Logic**
1. Compute available monthly payment capacity:
   ```py
   available = monthly_income * foir - existing_emis
   ```
   If `available <= 0`: return `0.0`
2. Convert APR to monthly rate `r = _monthly_rate(annual_rate)`.
3. If `r == 0`: `available * tenure_months`
4. Else rearranges EMI formula to solve for principal:
   \[
   P = EMI \cdot \frac{(1+r)^n - 1}{r(1+r)^n}
   \]

---

### `format_inr(amount)`
**Purpose:** Format a numeric amount into an INR string with Indian digit grouping and 2 decimals.

**Output examples**
- `format_inr(1000000)` → `₹10,00,000.00`
- negative values get prefixed with `-`

**Notes**
- Always returns with rupee sign and 2 decimal places.
- Uses manual grouping (lakhs/crores style) rather than locale.

---

### `schedule_to_csv(rows, path)`
**Purpose:** Write schedule rows (as returned by `amortisation_schedule`) to a CSV file.

**CSV columns**
`month,emi,interest,principal,balance`

**Notes**
- Opens file with `open(path, "w")` (default encoding is platform dependent).

---

### `summary(principal, annual_rate, tenure_months, start=None)`
**Purpose:** Produce a user-friendly summary dict for the loan.

**Output**
```py
{
  "principal": "₹...",
  "rate": "9% p.a.",
  "tenure": "240 months",
  "emi": "₹...",
  "total_interest": "₹...",
  "total_payment": "₹...",
  "last_emi": "YYYY-MM",
  "currency": "INR"
}
```

**Logic**
- `start` defaults to today.
- Computes EMI, then computes an “end month” by adding `tenure_months` to `start`.
- Uses `format_inr()` for money fields.

---

## `cli.py`

### Purpose
Provides a minimal command-line interface to:
- print `summary()`
- optionally print `amortisation_schedule()` rows (`--schedule`)
- optionally print `prepayment_savings()` (`--prepay-month`, `--prepay-amount`)

### Arguments
- positional:
  - `principal` (float)
  - `rate` (float, APR percent)
  - `tenure` (int, months)
- options:
  - `--schedule`
  - `--prepay-month` (int)
  - `--prepay-amount` (float)

### Output
- Always prints the loan summary as JSON (with INR symbol preserved due to `ensure_ascii=False`).
- If `--schedule`, prints each schedule row as a Python dict (not JSON).
- If prepay args set, prints prepayment savings as JSON.

### Known issue: `--help` crash
Running `python cli.py --help` crashes with:
`ValueError: incomplete format`

Reason: `argparse` expands `%` sequences in help strings. This CLI defines:
```py
ap.add_argument("rate", type=float, help="annual interest rate in %")
```
The `%` is treated like a format specifier during help rendering. Escaping as `%%` would fix it, but the code is unchanged in this step.

---

## Exports (`loan_calc/__init__.py`)
`__init__.py` re-exports functions so callers can do:

```py
from loan_calc import emi, summary, amortisation_schedule
```

(See the file itself for the exact export list.)
