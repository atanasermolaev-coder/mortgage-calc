import pytest

from app.mortgage import (monthly_payment, overpayment, payment_schedule,
                          total_payment)


def test_monthly_payment_known_value():
    # 1 000 000 руб., 12 % годовых, 1 год -> 88 848.79 руб./мес.
    assert monthly_payment(1_000_000, 12, 1) == pytest.approx(88848.79, abs=0.01)


def test_zero_rate_is_simple_division():
    assert monthly_payment(120_000, 0, 1) == pytest.approx(10_000)


def test_total_equals_monthly_times_months():
    m = monthly_payment(2_000_000, 10, 15)
    assert total_payment(2_000_000, 10, 15) == pytest.approx(m * 180)


def test_overpayment_positive_with_rate():
    assert overpayment(1_000_000, 10, 10) > 0


def test_overpayment_zero_without_rate():
    assert overpayment(1_000_000, 0, 10) == pytest.approx(0, abs=1e-6)


def test_longer_term_means_bigger_overpayment():
    assert overpayment(1_000_000, 10, 20) > overpayment(1_000_000, 10, 10)


def test_schedule_length_and_final_balance():
    rows = payment_schedule(1_000_000, 12, 2)
    assert len(rows) == 24
    assert rows[-1]["balance"] == pytest.approx(0, abs=0.01)


def test_schedule_principal_sums_to_loan_amount():
    rows = payment_schedule(1_500_000, 9.5, 5)
    assert sum(r["principal"] for r in rows) == pytest.approx(1_500_000, abs=0.01)


@pytest.mark.parametrize("p,r,y", [
    (0, 10, 10),            # нулевая сумма
    (-5, 10, 10),           # отрицательная сумма
    (100, 10, 0),           # нулевой срок
    (100, -1, 5),           # отрицательная ставка
    (100, 101, 5),          # ставка выше допустимой
    (100, 10, 101),         # срок выше допустимого
    (float("nan"), 10, 5),  # не число
    (float("inf"), 10, 5),  # бесконечность
])
def test_invalid_input_raises(p, r, y):
    with pytest.raises(ValueError):
        monthly_payment(p, r, y)
