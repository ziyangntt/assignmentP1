import math

import pytest

from loan_calc import calculator as c


def test_emi_zero_interest_simple_division():
    # 0% interest should fall back to principal / tenure
    assert c.emi(120_000, 0.0, 12) == 10_000.0


def test_emi_one_month_tenure_nonzero_interest():
    # For a 1-month loan, EMI should be principal + one month's interest.
    # Interest uses monthly rate = round(APR/1200, 4) to match implementation.
    p = 100_000.0
    r = c._monthly_rate(12.0)  # 1% per month -> 0.01
    assert r == 0.01
    assert c.emi(p, 12.0, 1) == round(p * (1 + r), 2)


def test_total_interest_zero_interest_is_zero():
    assert c.total_interest(250_000, 0.0, 24) == 0.0


def test_amortisation_schedule_row_count_is_full_tenure():
    sched = c.amortisation_schedule(100_000, 9.0, 12)
    assert len(sched) == 12


def test_amortisation_schedule_first_row_fields_and_types():
    sched = c.amortisation_schedule(100_000, 9.0, 12)
    row = sched[0]
    assert row["month"] == 1
    assert isinstance(row["month"], int)
    assert set(row.keys()) == {"month", "emi", "interest", "principal", "balance"}
    assert row["emi"] == c.emi(100_000, 9.0, 12)
    # Interest should be balance * r (rounded to 2 dp)
    assert row["interest"] == round(100_000 * c._monthly_rate(9.0), 2)


def test_outstanding_after_zero_or_negative_months_is_principal():
    assert c.outstanding_after(123_456.78, 9.0, 36, 0) == round(123_456.78, 2)
    assert c.outstanding_after(123_456.78, 9.0, 36, -5) == round(123_456.78, 2)


def test_outstanding_after_months_paid_beyond_schedule_returns_zero():
    # Because schedule has tenure-1 rows, paying tenure months exceeds schedule length.
    assert c.outstanding_after(100_000, 9.0, 12, 999) == 0.0


def test_eligible_amount_when_available_capacity_non_positive_is_zero():
    assert c.eligible_amount(monthly_income=10_000, existing_emis=10_000, annual_rate=9.0, tenure_months=120) == 0.0
    assert c.eligible_amount(monthly_income=10_000, existing_emis=20_000, annual_rate=9.0, tenure_months=120) == 0.0


def test_format_inr_basic_and_negative():
    assert c.format_inr(1_000_000) == "₹10,00,000.00"
    assert c.format_inr(-1_000_000) == "-₹10,00,000.00"


def test_compare_offers_sorted_by_total_cost_and_defaults_processing_fee():
    offers = [
        # omit processing_fee_pct to cover default path in compare_offers()
        {"bank": "B", "rate": 9.0, "tenure": 12},
        {"bank": "A", "rate": 10.0, "tenure": 12, "processing_fee_pct": 1.0},
    ]
    out = c.compare_offers(100_000, offers)
    assert len(out) == 2
    assert out[0]["total_cost"] <= out[1]["total_cost"]
    # Ensure missing processing_fee_pct is treated as 0
    b = next(x for x in out if x["bank"] == "B")
    assert b["processing_fee"] == 0.0


def test_large_principal_does_not_overflow_and_returns_finite_results():
    p = 10**12  # very large principal
    e = c.emi(p, 9.0, 360)
    assert math.isfinite(e)
    assert e > 0
    ti = c.total_interest(p, 9.0, 360)
    assert math.isfinite(ti)
    assert ti > 0


def test_prepayment_savings_typical_case_should_not_raise():
    # Typical scenario should not raise, but currently does due to remaining_tenure bug.
    c.prepayment_savings(1_000_000, 9.0, 240, 24, 200_000)


def test_prepayment_larger_than_balance_returns_months_left_zero():
    # Choose prepay_month=1 so balance is close to principal after first payment,
    # then overpay to force new_balance <= 0 and months_left=0 path.
    p = 100_000
    savings = c.prepayment_savings(p, 0.0, 12, prepay_month=1, prepay_amount=1_000_000)
    assert savings["new_tenure"] == 1  # prepay_month + 0
    assert savings["months_saved"] == 11


def test_emi_rejects_non_positive_inputs():
    with pytest.raises(ValueError, match="tenure must be positive"):
        c.emi(100_000, 9.0, 0)
    with pytest.raises(ValueError, match="principal must be positive"):
        c.emi(0, 9.0, 12)


def test_total_payment_rejects_non_positive_inputs():
    with pytest.raises(ValueError, match="tenure must be positive"):
        c.total_payment(100_000, 9.0, 0)
    with pytest.raises(ValueError, match="principal must be positive"):
        c.total_payment(0, 9.0, 12)


def test_total_interest_non_zero_rate_path():
    # Covers the non-zero APR branch in total_interest()
    assert c.total_interest(100_000, 9.0, 12) > 0


def test_remaining_tenure_zero_rate_and_negative_balance_cases():
    # balance <= 0 path
    assert c.remaining_tenure(0.0, 9.0, 1000.0) == 0
    assert c.remaining_tenure(-1.0, 9.0, 1000.0) == 0
    # r == 0 path
    assert c.remaining_tenure(10_000.0, 0.0, 1000.0) == 10


def test_remaining_tenure_raises_if_instalment_too_small():
    # instalment <= balance * r should raise
    with pytest.raises(ValueError, match="instalment too small"):
        c.remaining_tenure(100_000.0, 12.0, instalment=1.0)
