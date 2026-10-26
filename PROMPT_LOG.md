# Prompt Log Records (AI Review & Corrections)

## Record 1 — Incorrect data type introduced during type-hinting (schedule month became float)

**AI suggestion / change**
- While adding type hints/docstrings, the assistant changed the amortisation schedule row shape:
  - from: `\"month\": month` (int)
  - to: `\"month\": float(month)` (float)

**Why it was wrong**
- The month number is a discrete index and is expected to be an integer.
- Changing it to float silently alters the API contract and can break consumers relying on integer month labels.

**Correction applied**
- Reverted the schedule row field to an integer:
  - `\"month\": month`
- Updated the return type annotation to reflect a mixed-type row value set:
  - `list[dict[str, float | int]]`

**Result**
- Schedule rows preserve the expected structure and types.

---

## Record 2 — Test failure diagnosed as a real defect: 0% APR showed non-zero interest

**AI test proposal**
- Added a test asserting:
  - `total_interest(250_000, 0.0, 24) == 0.0`

**What happened**
- The test failed; output was `0.08` instead of `0.0`.

**Why the AI expectation was incomplete**
- The existing implementation rounded EMI to 2 decimals first, then computed totals as:
  - `rounded_emi * months`
- Multiplying a rounded monthly value can introduce small remainders even when APR is 0%, creating “phantom interest”.

**Correction applied**
- Fixed the code (not the test) to ensure correct behavior at 0% APR:
  - `total_payment()` now special-cases 0% APR to return `principal` exactly.
  - For non-zero APR, totals are computed using an unrounded EMI and rounded only at the end.
  - `total_interest()` now returns `0.0` when `annual_rate == 0`.

**Result**
- The test passed and totals are consistent with expected math at 0% APR.

---

## Record 3 — Prepayment calculation raised ValueError due to incorrect periodic rate in remaining_tenure

**AI observation**
- A test expected this call not to raise:
  - `prepayment_savings(1_000_000, 9.0, 240, 24, 200_000)`
- It raised:
  - `ValueError: instalment too small to repay the loan`

**Why it was wrong**
- `remaining_tenure()` used:
  - `r = annual_rate / 100`
- That treats APR as if it were a per-month rate, drastically overstating interest and making repayment conditions fail.

**Correction applied**
- Aligned `remaining_tenure()` with the rest of the module’s monthly-rate convention:
  - `r = _monthly_rate(annual_rate)`

**Result**
- `prepayment_savings()` no longer throws for normal inputs and the full pytest suite passes.
