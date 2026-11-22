import app as app_module


def _client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_index_serves_dashboard():
    r = _client().get("/")
    assert r.status_code == 200 and b"Trading System" in r.data


def test_api_routes_with_synthetic_data(monkeypatch, ohlcv):
    monkeypatch.setattr(app_module, "get_historical_data", lambda *a, **k: ohlcv)
    c = _client()
    m = c.get("/api/market/EURUSD").get_json()
    s = c.get("/api/smc/EURUSD").get_json()
    assert m["success"] and m["analysis"]["symbol"] == "EURUSD"
    assert s["success"] and "direction" in s["analysis"]


def test_api_reports_missing_data(monkeypatch):
    monkeypatch.setattr(app_module, "get_historical_data", lambda *a, **k: None)
    r = _client().get("/api/smc/NOPE").get_json()
    assert r["success"] is False and "NOPE" in r["message"]
