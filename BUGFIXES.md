# loan-calc — Bug Fix Notes (Seeded Issues)

This document summarizes the three seeded defects discovered in the starter codebase, their impact, how to reproduce them, and how they were fixed. Wording and explanations here are intentionally independent of any “answer sheet” phrasing, but the technical substance matches the fixes applied.

---

## Bug 1 — APR-to-monthly conversion rounded too early

### Where
`loan_calc/calculator.py` → `_monthly_rate(annual_rate)`

### What went wrong
The module converted annual APR (%) to a monthly decimal rate and **rounded the rate to 4 decimal places** immediately. That seems small, but it systematically distorts the interest rate used in every downstream formula. For common APR values that don’t convert cleanly (e.g., 8.5%), the rounding error is large enough to noticeably shift EMI and totals.

### Symptoms / user impact
- EMI can be consistently too high or too low for some “non-round” rates.
- Any calculation that depends on EMI or per-period interest (schedule, totals, eligibility) inherits the drift.

### Minimal reproduction idea
Compute EMI for a principal/tenure with an APR like **8.5%** and compare against the EMI calculated using an unrounded monthly rate.

### Fix
- Removed the premature rounding.
- `_monthly_rate()` now returns:
  - `annual_rate / 1200`

This keeps full floating precision for rate math; rounding is left to monetary outputs (where it belongs).

### Suggested commit message
`fix: avoid rounding monthly rate to prevent EMI drift`

---

## Bug 2 — Amortisation schedule skipped the final month

### Where
`loan_calc/calculator.py` → `amortisation_schedule(...)`

### What went wrong
The schedule loop iterated using a range that stopped before the final month. As a result:
- The schedule contained **tenure_months - 1** rows.
- For a 1-month loan, the schedule could be empty.
- Code intended to “adjust the last EMI” never executed because the last month was never reached.

### Symptoms / user impact
- Schedules were shorter than requested (e.g., 239 rows for a 240‑month loan).
- Ending balance might not reach 0 in the schedule output.
- Any feature relying on the schedule length or the final balance (e.g., outstanding computations and prepayment calculations) could behave incorrectly.

### Fix
- Loop now runs through the full tenure:
  - `for month in range(1, tenure_months + 1):`
- For the last month, the code now explicitly sets principal repayment to the remaining balance (after rounding effects), and recomputes the last instalment amount accordingly.

### Suggested commit message
`fix: include final instalment in amortisation schedule`

---

## Bug 3 — remaining_tenure() used the wrong periodic interest rate

### Where
`loan_calc/calculator.py` → `remaining_tenure(balance, annual_rate, instalment)`

### What went wrong
This function treated `annual_rate / 100` as the per-payment interest rate. That is effectively applying an annual percentage rate as if it were a *monthly* rate, which makes the implied interest charge far too large.

### Symptoms / user impact
- `prepayment_savings()` could throw:
  - `ValueError: instalment too small to repay the loan`
  for normal loan parameters.
- Tenure estimates after prepayment were unreliable.

### Fix
- `remaining_tenure()` now uses the same monthly rate derivation as the rest of the module:
  - `r = _monthly_rate(annual_rate)`

### Suggested commit message
`fix: use monthly rate in remaining_tenure to prevent prepayment errors`

---

## Verification
After applying all three fixes, the test suite passes:

- `python -m pytest -q` → **13 passed**
