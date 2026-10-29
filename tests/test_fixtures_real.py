"""Tests against REAL YouCam responses captured on 29 Oct 2026 (see app/fixtures/README.md)."""
import json

import httpx

from app.concerns import actions_for, normalize_output, report_card
from app.mock import fixture_response, mock_output
from app.routine import build_routine
from app.youcam import DEFAULT_BASE_URL, TASK_PATH, YouCamClient


def output(q):
    return fixture_response(q)["data"]["results"]["output"]


def test_fixture_envelope_shape():
    for q in ("hd", "sd"):
        body = fixture_response(q)
        assert body["status"] == 200
        assert body["data"]["task_status"] == "success"
        assert body["data"]["error"] is None
        types = {o["type"] for o in body["data"]["results"]["output"]}
        assert set(actions_for(q)) <= types  # every requested action came back
        assert {"all", "skin_age", "resize_image"} <= types


def test_real_hd_regions_and_scores():
    n = normalize_output(output("hd"))
    assert set(n["scores"]) == {"moisture", "oiliness", "acne", "pores", "redness", "texture", "dark_circles", "spots"}
    assert set(n["scores"]["pores"]["regions"]) == {"forehead", "nose", "cheek"}
    assert n["scores"]["moisture"]["level"] == "focus"  # raw 31.1
    assert n["scores"]["redness"]["level"] == "good"    # raw 98.9
    assert n["overall"] == 76 and n["skin_age"] == 64
    for s in n["scores"].values():
        assert 1 <= s["ui_score"] <= 100 and s["mask_url"].endswith(".jpg")


def test_real_sd_has_no_regions():
    n = normalize_output(output("sd"))
    assert len(n["scores"]) == 8
    assert all("regions" not in s for s in n["scores"].values())
    assert n["scores"]["dark_circles"]["ui_score"] == 71  # SD action name is dark_circle_v2


def test_real_result_drives_routine():
    n = normalize_output(output("hd"))
    rows = report_card(n)
    assert rows[0]["key"] == "moisture"
    r = build_routine(n["scores"], 1500, "dry")
    assert r["profile"]["type"] in ("dry", "combination")
    assert r["monthly_total"] <= 1500


def test_client_parses_real_poll_body():
    body = fixture_response("sd")

    def handler(req):
        url = str(req.url)
        if url.endswith("/s2s/v2.0/file"):
            return httpx.Response(200, json={"status": 200, "data": {"files": [{"file_id": "f1", "requests": [
                {"method": "PUT", "url": "https://s3.example/up", "headers": {"Content-Type": "image/jpeg"}}]}]}})
        if req.method == "PUT":
            return httpx.Response(200)
        if url == DEFAULT_BASE_URL + TASK_PATH:
            return httpx.Response(200, json={"status": 200, "data": {"task_id": "t"}})
        return httpx.Response(200, json=body)

    c = YouCamClient("k", http=httpx.Client(transport=httpx.MockTransport(handler)), sleep=lambda s: None)
    res = c.analyze(b"img", actions_for("sd"))
    assert res.output == body["data"]["results"]["output"]


def test_running_state_from_live_api_shape_keeps_polling():
    states = [{"status": 200, "data": {"error": None, "results": None, "task_status": "running"}}, fixture_response("hd")]

    def handler(req):
        if req.method == "GET":
            return httpx.Response(200, json=states.pop(0))
        return httpx.Response(200, json={"status": 200, "data": {"task_id": "t"}})

    c = YouCamClient("k", http=httpx.Client(transport=httpx.MockTransport(handler)), sleep=lambda s: None)
    assert len(c.poll("t")) == 14


def test_mock_mode_uses_real_shape_without_masks_or_skin_age():
    a, b = mock_output(b"photo-a", "sd"), mock_output(b"photo-b", "sd")
    assert a == mock_output(b"photo-a", "sd")  # deterministic
    assert a != b
    assert {o["type"] for o in a} == {o["type"] for o in output("sd")} - {"skin_age"}
    assert all(o["mask_urls"] == [] for o in a if "mask_urls" in o)
    hd = mock_output(b"x", "hd")
    pores = [o for o in hd if o["type"] == "hd_pore"]
    assert len(pores) == 4
    json.dumps(hd)


def test_fixtures_hold_no_signed_urls():
    for q in ("hd", "sd"):
        text = json.dumps(fixture_response(q))
        assert "X-Amz" not in text and "Signature" not in text and "?" not in text
