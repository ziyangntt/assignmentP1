import math

import pytest

from loan_calc.calculator import (
    amortisation_schedule,
    compare_offers,
    eligible_amount,
    emi,
    format_inr,
    outstanding_after,
    prepayment_savings,
    remaining_tenure,
    total_interest,
    total_payment,
)


def test_emi_reference_case_matches_acceptance_criteria():
    # Acceptance criteria: EMI for ₹10,00,000 at 9% p.a. over 240 months ~ ₹8,997 (±1)
    assert emi(1_000_000, 9.0, 240) == pytest.approx(8997.0, abs=1.0)


def test_emi_zero_interest_is_simple_division():
    assert emi(120_000, 0.0, 12) == 10_000.0
    assert emi(100_000, 0.0, 1) == 100_000.0


def test_emi_one_month_tenure_nonzero_interest():
    # For 1 month, EMI should be principal + one month's interest.
    # (EMI formula reduces to P*(1+r) when n=1)
    assert emi(100_000, 12.0, 1) == pytest.approx(101_000.0, abs=0.01)


def test_total_payment_and_total_interest_consistency():
    p, rate, n = 500_000, 8.5, 180
    tp = total_payment(p, rate, n)
    ti = total_interest(p, rate, n)
    assert tp == pytest.approx(emi(p, rate, n) * n, abs=0.01)
    assert ti == pytest.approx(tp - p, abs=0.01)


def test_amortisation_schedule_length_and_ends_at_zero_balance():
    p, rate, n = 100_000, 12.0, 12
    sched = amortisation_schedule(p, rate, n)
    assert len(sched) == n
    assert sched[-1]["month"] == n
    assert sched[-1]["balance"] == pytest.approx(0.0, abs=0.01)


def test_amortisation_schedule_interest_and_principal_components_sum_to_emi():
    p, rate, n = 250_000, 10.0, 24
    sched = amortisation_schedule(p, rate, n)
    for row in sched[:-1]:
        assert row["emi"] == pytest.approx(row["interest"] + row["principal"], abs=0.01)


def test_outstanding_after_edge_cases():
    p, rate, n = 100_000, 12.0, 12
    assert outstanding_after(p, rate, n, 0) == pytest.approx(p, abs=0.01)
    assert outstanding_after(p, rate, n, -5) == pytest.approx(p, abs=0.01)
    assert outstanding_after(p, rate, n, n) == pytest.approx(0.0, abs=0.01)
    assert outstanding_after(p, rate, n, n + 10) == pytest.approx(0.0, abs=0.01)


def test_remaining_tenure_zero_interest():
    # balance / instalment ceiling
    assert remaining_tenure(100_000, 0.0, 10_000) == 10
    assert remaining_tenure(100_001, 0.0, 10_000) == 11


def test_remaining_tenure_positive_interest_smoke():
    # With a valid EMI, remaining_tenure should return a finite positive integer.
    p, rate, n = 1_000_000, 9.0, 240
    instalment = emi(p, rate, n)
    assert remaining_tenure(p, rate, instalment) == n


def test_prepayment_larger_than_balance_results_in_full_closure():
    p, rate, n = 100_000, 12.0, 12
    prepay_month = 1
    # Pay more than the remaining principal right after first payment
    result = prepayment_savings(p, rate, n, prepay_month, prepay_amount=1_000_000)
    assert result["new_tenure"] == prepay_month
    assert result["months_saved"] == n - prepay_month
    assert result["interest_saved"] >= 0


def test_prepayment_savings_typical_case_saves_months_and_interest():
    result = prepayment_savings(
        principal=1_000_000,
        annual_rate=9.0,
        tenure_months=240,
        prepay_month=24,
        prepay_amount=200_000,
    )
    assert result["months_saved"] > 0
    assert result["interest_saved"] > 0
    assert result["new_tenure"] < 240


def test_eligible_amount_zero_interest_matches_available_times_months():
    # available = 100000 * 0.5 - 0 = 50000
    assert eligible_amount(100_000, 0, 0.0, 12, foir=0.5) == pytest.approx(
        600_000.0, abs=0.01
    )


def test_compare_offers_sorted_by_total_cost():
    offers = [
        {"bank": "A", "rate": 9.0, "tenure": 240, "processing_fee_pct": 1.0},
        {"bank": "B", "rate": 8.9, "tenure": 240, "processing_fee_pct": 1.5},
        {"bank": "C", "rate": 9.2, "tenure": 240, "processing_fee_pct": 0.0},
    ]
    out = compare_offers(1_000_000, offers)
    assert out == sorted(out, key=lambda x: x["total_cost"])


def test_format_inr_basic_grouping_and_sign():
    assert format_inr(1_000_000) == "₹10,00,000.00"
    assert format_inr(-1_000_000) == "-₹10,00,000.00"


def test_very_large_principal_does_not_overflow_and_returns_reasonable_value():
    e = emi(1_000_000_000, 7.5, 360)  # 100 crore, 30 years
    assert math.isfinite(e)
    assert e > 0
