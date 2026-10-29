"""YouCam client tests with mocked HTTP (httpx.MockTransport): no network, no real key."""
import json

import httpx
import pytest

from app.youcam import DEFAULT_BASE_URL, TASK_PATH, YouCamClient, YouCamError

KEY = "test-key-123"
UPLOAD_URL = "https://yce-us.s3-accelerate.amazonaws.com/demo/ttl30/abc?sig=1"
FILE_ID = "SaGaqpDgKwFrVBgMpQMA3HY0LeqdT9/13W5TOD8/u/FfjK3xgCQ+hRt9MJXBFaud"
TASK_ID = "task_123"


def file_response(size=1234):
    return {"status": 200, "data": {"files": [{
        "content_type": "image/jpeg", "file_name": "twacha_selfie.jpg", "file_id": FILE_ID,
        "requests": [{"method": "PUT", "url": UPLOAD_URL, "headers": {"Content-Type": "image/jpeg", "Content-Length": str(size)}}],
    }]}}


SUCCESS_OUTPUT = [
    {"type": "acne", "ui_score": 80, "raw_score": 70.5, "mask_urls": ["https://m/acne.jpg"]},
    {"type": "moisture", "ui_score": 60, "raw_score": 48.7, "mask_urls": ["https://m/moisture.jpg"]},
    {"type": "all", "score": 75.7},
    {"type": "skin_age", "score": 27},
]


class Recorder:
    def __init__(self, task_states):
        self.calls = []
        self.task_states = list(task_states)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        url = str(request.url)
        if request.method == "POST" and url == DEFAULT_BASE_URL + "/s2s/v2.0/file":
            body = json.loads(request.content)
            return httpx.Response(200, json=file_response(body["files"][0]["file_size"]))
        if request.method == "PUT" and url == UPLOAD_URL:
            return httpx.Response(200)
        if request.method == "POST" and url == DEFAULT_BASE_URL + TASK_PATH:
            return httpx.Response(200, json={"status": 200, "data": {"task_id": TASK_ID}})
        if request.method == "GET" and url == f"{DEFAULT_BASE_URL}{TASK_PATH}/{TASK_ID}":
            return httpx.Response(200, json={"status": 200, "data": self.task_states.pop(0)})
        return httpx.Response(404, json={"status": 404, "error": "not found"})


def make_client(handler, **kw):
    sleeps = []
    c = YouCamClient(KEY, base_url=DEFAULT_BASE_URL, http=httpx.Client(transport=httpx.MockTransport(handler)),
                     sleep=sleeps.append, **kw)
    return c, sleeps


def test_full_flow_success():
    rec = Recorder([{"task_status": "running"}, {"task_status": "running"},
                    {"task_status": "success", "results": {"output": SUCCESS_OUTPUT}}])
    client, sleeps = make_client(rec)
    image = b"\xff\xd8" + b"x" * 1232
    res = client.analyze(image, ["acne", "moisture"])

    assert res.output == SUCCESS_OUTPUT
    assert res.task_id == TASK_ID
    assert len(sleeps) == 2  # polled until success

    file_req, put_req, task_req, *polls = rec.calls
    # 1. File API: bearer auth + file metadata
    assert file_req.headers["authorization"] == f"Bearer {KEY}"
    meta = json.loads(file_req.content)["files"][0]
    assert meta == {"content_type": "image/jpeg", "file_name": "twacha_selfie.jpg", "file_size": len(image)}
    # 2. Upload: raw bytes to the presigned URL with the given headers, and NO api key
    assert put_req.method == "PUT"
    assert put_req.content == image
    assert put_req.headers["content-type"] == "image/jpeg"
    assert "authorization" not in put_req.headers
    # 3. Task: src_file_id, dst_actions, miniserver_args, format=json
    body = json.loads(task_req.content)
    assert body["src_file_id"] == FILE_ID
    assert body["dst_actions"] == ["acne", "moisture"]
    assert body["format"] == "json"
    assert body["miniserver_args"] == {"enable_mask_overlay": True}
    assert task_req.headers["authorization"] == f"Bearer {KEY}"
    # 4. Polls hit GET /task/skin-analysis/{task_id}
    assert len(polls) == 3 and all(p.method == "GET" for p in polls)


def test_task_error_is_raised_with_engine_code():
    rec = Recorder([{"task_status": "error", "error": "error_src_face_too_small", "error_message": "face too small"}])
    client, _ = make_client(rec)
    with pytest.raises(YouCamError) as e:
        client.analyze(b"img", ["acne"])
    assert e.value.code == "error_src_face_too_small"
    assert "closer" in e.value.user_message


def test_invalid_api_key():
    def handler(request):
        return httpx.Response(401, json={"status": 401, "error": "Unauthorized", "error_code": "InvalidAccessToken"})
    client, _ = make_client(handler)
    with pytest.raises(YouCamError) as e:
        client.analyze(b"img", ["acne"])
    assert e.value.code == "InvalidAccessToken"
    assert e.value.http_status == 401
    assert KEY not in e.value.user_message


def test_invalid_parameters_on_task_create():
    def handler(request):
        if str(request.url).endswith("/s2s/v2.0/file"):
            return httpx.Response(200, json=file_response())
        if request.method == "PUT":
            return httpx.Response(200)
        return httpx.Response(400, json={"status": 400, "error": "cannot mix HD and SD dst_actions", "error_code": "InvalidParameters"})
    client, _ = make_client(handler)
    with pytest.raises(YouCamError) as e:
        client.analyze(b"img", ["acne", "hd_pore"])
    assert e.value.code == "InvalidParameters"
    assert "cannot mix" in e.value.message


def test_upload_failure():
    def handler(request):
        if request.method == "PUT":
            return httpx.Response(403, text="SignatureDoesNotMatch")
        return httpx.Response(200, json=file_response())
    client, _ = make_client(handler)
    with pytest.raises(YouCamError) as e:
        client.analyze(b"img", ["acne"])
    assert e.value.code == "upload_failed"


def test_poll_timeout():
    rec = Recorder([{"task_status": "running"}] * 50)
    client, _ = make_client(rec, timeout_s=0)
    with pytest.raises(YouCamError) as e:
        client.analyze(b"img", ["acne"])
    assert e.value.code == "timeout"


def test_zip_shaped_result_rejected():
    rec = Recorder([{"task_status": "success", "results": {"url": "https://zip"}}])
    client, _ = make_client(rec)
    with pytest.raises(YouCamError) as e:
        client.analyze(b"img", ["acne"])
    assert e.value.code == "bad_response"


def test_missing_file_id():
    client, _ = make_client(lambda r: httpx.Response(200, json={"status": 200, "data": {"files": []}}))
    with pytest.raises(YouCamError):
        client.create_file(10)


def test_requires_key():
    with pytest.raises(ValueError):
        YouCamClient("")


def test_file_path_overridable(monkeypatch):
    monkeypatch.setenv("YOUCAM_FILE_PATH", "/s2s/v2.0/file/skin-analysis")
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json=file_response())
    c = YouCamClient(KEY, http=httpx.Client(transport=httpx.MockTransport(handler)))
    c.create_file(10)
    assert seen == [DEFAULT_BASE_URL + "/s2s/v2.0/file/skin-analysis"]


def test_live_invalid_api_key_code():
    # Exact 401 body seen from the live API in Oct 2026.
    def handler(request):
        return httpx.Response(401, json={"status": 401, "error": "This API key isn't recognized.", "error_code": "InvalidApiKey"})
    client, _ = make_client(handler)
    with pytest.raises(YouCamError) as e:
        client.create_file(10)
    assert e.value.code == "InvalidApiKey"
    assert "rejected" in e.value.user_message
