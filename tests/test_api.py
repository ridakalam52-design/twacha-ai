import pytest
from fastapi.testclient import TestClient

from app import main
from app.youcam import SkinAnalysisResult, YouCamError
from tests.conftest import make_image


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("YOUCAM_API_KEY", raising=False)
    monkeypatch.delenv("YOUCAM_QUALITY", raising=False)
    main.app.state.client_factory = main.default_client_factory
    yield TestClient(main.app)
    main.app.state.client_factory = main.default_client_factory


def post_photo(client, data, budget="1500", climate="humid"):
    return client.post("/api/analyze", files={"photo": ("selfie.jpg", data, "image/jpeg")},
                       data={"budget": budget, "climate": climate})


class FakeYouCam:
    def __init__(self, output=None, error=None):
        self.output, self.error, self.calls = output, error, []

    def analyze(self, image, actions, content_type="image/jpeg"):
        self.calls.append((len(image), actions, content_type))
        if self.error:
            raise self.error
        return SkinAnalysisResult(actions=actions, output=self.output, task_id="t1")


def test_index_and_static(client):
    r = client.get("/")
    assert r.status_code == 200 and "TwachaAI" in r.text
    assert "Powered by YouCam Skin Analysis API" in r.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200


def test_health_and_config_demo(client):
    assert client.get("/api/health").json() == {"status": "ok", "mode": "demo"}
    cfg = client.get("/api/config").json()
    assert cfg["mode"] == "demo"
    assert "moisture" in cfg["actions"]["sd"] and "hd_moisture" in cfg["actions"]["hd"]
    assert cfg["budgets"] == [500, 1500, 3000]
    assert "not medical advice" in cfg["disclaimer"]["en"]


def test_config_reports_live_mode_without_leaking_key(client, monkeypatch):
    monkeypatch.setenv("YOUCAM_API_KEY", "sk-super-secret")
    r = client.get("/api/config")
    assert r.json()["mode"] == "live"
    assert "sk-super-secret" not in r.text


def test_analyze_demo_mode(client):
    r = post_photo(client, make_image(900, 1200), "500", "polluted")
    assert r.status_code == 200
    d = r.json()
    assert d["demo"] is True
    assert d["quality"] == "sd"
    assert len(d["report"]) == 8 and len(d["actions"]) == 8
    assert d["routine"]["monthly_total"] <= 500
    assert d["routine"]["profile"]["climate"] == "polluted"
    assert 0 < d["overall"] <= 100
    # same photo -> same demo scores
    assert post_photo(client, make_image(900, 1200)).json()["scores"] == d["scores"]


def test_analyze_live_mode_uses_youcam_client(client):
    fake = FakeYouCam(output=[
        {"type": "hd_acne", "region": "whole", "raw_score": 35, "ui_score": 55, "mask_urls": ["https://m/a.jpg"]},
        {"type": "hd_oiliness", "raw_score": 50, "ui_score": 65, "mask_urls": []},
        {"type": "all", "score": 70},
    ])
    main.app.state.client_factory = lambda: fake
    r = post_photo(client, make_image(1200, 1600), "1500", "humid")
    assert r.status_code == 200
    d = r.json()
    assert d["demo"] is False and d["quality"] == "hd"
    assert fake.calls[0][1][0].startswith("hd_") and fake.calls[0][2] == "image/jpeg"
    assert d["report"][0]["key"] == "acne" and d["report"][0]["mask_url"] == "https://m/a.jpg"
    assert "see_dermatologist" in d["routine"]["flags"]
    assert d["task_id"] == "t1"


def test_analyze_live_error_maps_to_502_with_friendly_message(client):
    main.app.state.client_factory = lambda: FakeYouCam(error=YouCamError("error_lighting_dark", "dark"))
    r = post_photo(client, make_image())
    assert r.status_code == 502
    err = r.json()["error"]
    assert err["code"] == "error_lighting_dark"
    assert "too dark" in err["message"]


def test_analyze_rejects_bad_inputs(client):
    assert post_photo(client, make_image(), budget="999").status_code == 422
    assert post_photo(client, make_image(), climate="arctic").status_code == 422
    small = post_photo(client, make_image(300, 400))
    assert small.status_code == 422 and small.json()["error"]["code"] == "error_below_min_image_size"
    bad = post_photo(client, b"definitely not a jpeg")
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "error_decode_image"
    assert post_photo(client, b"").status_code == 422


def test_routine_replan_endpoint(client):
    scores = {"acne": {"raw_score": 45, "ui_score": 62}, "oiliness": {"raw_score": 50}, "bogus": {"raw_score": 1}}
    r = client.post("/api/routine", json={"scores": scores, "budget": 3000, "climate": "dry"})
    assert r.status_code == 200
    d = r.json()
    assert d["budget"] == 3000 and d["monthly_total"] <= 3000
    assert client.post("/api/routine", json={"scores": scores, "budget": 10, "climate": "dry"}).status_code == 422
    assert client.post("/api/routine", json={"scores": {}, "budget": 500, "climate": "dry"}).status_code == 422
