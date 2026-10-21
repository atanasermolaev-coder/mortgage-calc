from app.web import app


def test_page_opens():
    resp = app.test_client().get("/")
    assert resp.status_code == 200
    assert "Калькулятор ипотеки" in resp.get_data(as_text=True)


def test_health():
    resp = app.test_client().get("/health")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "ok"


def test_calculation_result_shown():
    resp = app.test_client().post("/", data={"p": "1000000", "r": "12", "y": "1"})
    assert "88,848.79" in resp.get_data(as_text=True)


def test_invalid_input_shows_error():
    resp = app.test_client().post("/", data={"p": "abc", "r": "12", "y": "1"})
    assert resp.status_code == 200
    assert "Ошибка" in resp.get_data(as_text=True)


def test_negative_amount_shows_error():
    resp = app.test_client().post("/", data={"p": "-1", "r": "12", "y": "1"})
    assert "Ошибка" in resp.get_data(as_text=True)


def test_user_input_is_escaped():
    payload = '"><script>alert(1)</script>'
    resp = app.test_client().post("/", data={"p": payload, "r": "12", "y": "1"})
    assert "<script>alert(1)</script>" not in resp.get_data(as_text=True)
