"""Веб-интерфейс калькулятора (этот файл запускается на продуктовом сервере)."""
from flask import Flask, render_template_string, request

from app.mortgage import monthly_payment, overpayment, total_payment

app = Flask(__name__)

PAGE = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Калькулятор ипотеки</title>
  <style>
    body { font-family: sans-serif; max-width: 420px; margin: 40px auto; }
    label { display: block; margin: 10px 0 4px; }
    input { width: 100%; padding: 6px; box-sizing: border-box; }
    button { margin-top: 14px; padding: 8px 16px; }
    .result { margin-top: 20px; font-weight: bold; }
    .error { color: #b00020; }
  </style>
</head>
<body>
  <h2>Калькулятор ипотеки</h2>
  <form method="post">
    <label>Сумма кредита, руб.</label>
    <input name="p" value="{{ p }}">
    <label>Ставка, % годовых</label>
    <input name="r" value="{{ r }}">
    <label>Срок, лет</label>
    <input name="y" value="{{ y }}">
    <button type="submit">Рассчитать</button>
  </form>
  {% if error %}<p class="result error">{{ error }}</p>{% endif %}
  {% if result %}
  <p class="result">
    Платёж: {{ result.monthly }} / мес.<br>
    Всего выплат: {{ result.total }}<br>
    Переплата: {{ result.over }}
  </p>
  {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    p, r, y = "3000000", "12", "20"
    result, error = None, None
    if request.method == "POST":
        p = request.form.get("p", "")
        r = request.form.get("r", "")
        y = request.form.get("y", "")
        try:
            args = (float(p), float(r), int(y))
            result = {
                "monthly": f"{monthly_payment(*args):,.2f}",
                "total": f"{total_payment(*args):,.2f}",
                "over": f"{overpayment(*args):,.2f}",
            }
        except ValueError as exc:
            error = f"Ошибка во входных данных: {exc}"
    return render_template_string(PAGE, p=p, r=r, y=y, result=result, error=error)


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
