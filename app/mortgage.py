"""Логика калькулятора ипотеки (аннуитетные платежи).

Модуль не зависит от интерфейса: его используют и веб-версия (app/web.py),
и tkinter-версия (app/gui.py), и тесты.
"""
import math

MAX_RATE = 100      # максимальная ставка, % годовых
MAX_YEARS = 100     # максимальный срок, лет


def _validate(principal: float, annual_rate: float, years: int) -> None:
    if not (math.isfinite(principal) and math.isfinite(annual_rate)):
        raise ValueError("Числа должны быть конечными")
    if principal <= 0:
        raise ValueError("Сумма кредита должна быть больше 0")
    if not 0 <= annual_rate <= MAX_RATE:
        raise ValueError(f"Ставка должна быть от 0 до {MAX_RATE} %")
    if not 1 <= years <= MAX_YEARS:
        raise ValueError(f"Срок должен быть от 1 до {MAX_YEARS} лет")


def monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """Ежемесячный аннуитетный платёж. annual_rate задаётся в процентах."""
    _validate(principal, annual_rate, years)
    n = years * 12
    r = annual_rate / 100 / 12
    if r == 0:
        return principal / n
    k = r * (1 + r) ** n / ((1 + r) ** n - 1)
    return principal * k


def total_payment(principal: float, annual_rate: float, years: int) -> float:
    """Общая сумма выплат за весь срок."""
    return monthly_payment(principal, annual_rate, years) * years * 12


def overpayment(principal: float, annual_rate: float, years: int) -> float:
    """Переплата: общая сумма выплат минус тело кредита."""
    return total_payment(principal, annual_rate, years) - principal


def payment_schedule(principal: float, annual_rate: float, years: int) -> list:
    """График платежей: список словарей по месяцам."""
    payment = monthly_payment(principal, annual_rate, years)
    r = annual_rate / 100 / 12
    balance = principal
    rows = []
    for month in range(1, years * 12 + 1):
        interest = balance * r
        body = payment - interest
        balance -= body
        rows.append({
            "month": month,
            "payment": payment,
            "interest": interest,
            "principal": body,
            "balance": max(balance, 0.0),
        })
    return rows
