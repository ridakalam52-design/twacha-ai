"""Server-side client for the YouCam (Perfect Corp) AI Skin Analysis API, V2.

Flow (per https://docs.perfectcorp.com/reference/ai_skin_analysis):
  1. POST {base}/s2s/v2.0/file                  -> data.files[0].file_id + requests[0] (presigned PUT)
  2. PUT  requests[0].url  (with requests[0].headers) -> raw image bytes
  3. POST {base}/s2s/v2.0/task/skin-analysis     -> data.task_id
       body: {src_file_id, dst_actions, miniserver_args, format: "json"}
  4. GET  {base}/s2s/v2.0/task/skin-analysis/{task_id} until data.task_status is success | error
       success -> data.results.output = [{type, region?, ui_score, raw_score, score?, mask_urls}]

The API key is only ever read from the environment on the server and sent in the
Authorization header to the YouCam host. It is never returned to the browser.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

DEFAULT_BASE_URL = "https://yce-api-01.makeupar.com"
# The docs list the generic File API endpoint for V2. The feature-specific
# /s2s/v2.0/file/skin-analysis also answered 200 with the same shape in a live check
# (Oct 2026); either works. Overridable via YOUCAM_FILE_PATH.
DEFAULT_FILE_PATH = "/s2s/v2.0/file"
TASK_PATH = "/s2s/v2.0/task/skin-analysis"

# Engine error codes from the docs -> plain-language guidance for the user.
FRIENDLY_ERRORS = {
    "error_below_min_image_size": "The photo resolution is too small. Use a sharper photo (at least 480 px on the short side).",
    "error_exceed_max_image_size": "The photo resolution is too large. Please try a smaller photo.",
    "exceed_max_filesize": "The photo file is too large (limit is 10 MB).",
    "error_src_face_too_small": "Your face looks too small in the frame. Move closer so your face fills most of the photo width.",
    "error_src_face_out_of_bound": "Part of your face is outside the frame. Centre your whole face, forehead to chin.",
    "error_lighting_dark": "The photo is too dark. Face a window or a bright, even light and try again.",
    "error_no_face": "We couldn't find a face. Use a clear, front-facing selfie.",
    "error_large_face_angle": "Your face is turned too far. Look straight into the camera.",
    "error_multiple_people": "More than one person is in the photo. Use a selfie with only you.",
    "error_pose": "We couldn't read the pose. Look straight at the camera with a neutral expression.",
    "error_face_parsing": "We couldn't read the face clearly. Remove glasses, push hair off the forehead and retry.",
    "error_decode_image": "The photo couldn't be read. Please upload a JPG or PNG.",
    "error_nsfw_content_detected": "This photo can't be analysed. Please use a plain selfie.",
    "InvalidAccessToken": "The YouCam API key was rejected. Check YOUCAM_API_KEY on the server.",
    # Seen live (Oct 2026) on a 401: {"error_code": "InvalidApiKey", "error": "This API key isn't recognized."}
    "InvalidApiKey": "The YouCam API key was rejected. Check YOUCAM_API_KEY on the server.",
    "CreditInsufficiency": "The YouCam account is out of units for now. Try the demo mode instead.",
}


class YouCamError(Exception):
    """A failure talking to YouCam, with a code and a user-safe message."""

    def __init__(self, code: str, message: str, http_status: int | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.http_status = http_status

    @property
    def user_message(self) -> str:
        return FRIENDLY_ERRORS.get(self.code, "The skin analysis service had a problem. Please try again in a moment.")


@dataclass
class SkinAnalysisResult:
    actions: list[str]
    output: list[dict[str, Any]] = field(default_factory=list)
    task_id: str | None = None


class YouCamClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        file_path: str | None = None,
        http: httpx.Client | None = None,
        poll_interval: float = 2.0,
        timeout_s: float = 120.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = (base_url or os.getenv("YOUCAM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.file_path = file_path or os.getenv("YOUCAM_FILE_PATH") or DEFAULT_FILE_PATH
        self.http = http or httpx.Client(timeout=30.0)
        self.poll_interval = poll_interval
        self.timeout_s = timeout_s
        self.sleep = sleep

    # -- helpers ---------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _raise_for(resp: httpx.Response, step: str) -> dict[str, Any]:
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if resp.status_code >= 400:
            code = body.get("error_code") or (body.get("data") or {}).get("error") or f"http_{resp.status_code}"
            msg = body.get("error") or body.get("message") or resp.text[:200] or step
            raise YouCamError(str(code), f"{step}: {msg}", resp.status_code)
        if not isinstance(body, dict):
            raise YouCamError("bad_response", f"{step}: unexpected response", resp.status_code)
        return body

    # -- steps -----------------------------------------------------------
    def create_file(self, size: int, content_type: str = "image/jpeg", file_name: str = "selfie.jpg") -> tuple[str, dict]:
        payload = {"files": [{"content_type": content_type, "file_name": file_name, "file_size": size}]}
        resp = self.http.post(self.base_url + self.file_path, json=payload, headers=self._headers())
        body = self._raise_for(resp, "file")
        try:
            f = body["data"]["files"][0]
            return f["file_id"], f["requests"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise YouCamError("bad_response", "file: missing file_id or upload request") from exc

    def upload(self, request: dict, data: bytes) -> None:
        method = (request.get("method") or "PUT").upper()
        headers = {str(k): str(v) for k, v in (request.get("headers") or {}).items()}
        resp = self.http.request(method, request["url"], content=data, headers=headers)
        if resp.status_code >= 300:
            raise YouCamError("upload_failed", f"upload: HTTP {resp.status_code}", resp.status_code)

    def create_task(self, file_id: str, actions: list[str], mask_overlay: bool = True) -> str:
        payload = {
            "src_file_id": file_id,
            "dst_actions": actions,
            "miniserver_args": {"enable_mask_overlay": mask_overlay},
            "format": "json",
        }
        resp = self.http.post(self.base_url + TASK_PATH, json=payload, headers=self._headers())
        body = self._raise_for(resp, "task")
        task_id = (body.get("data") or {}).get("task_id")
        if not task_id:
            raise YouCamError("bad_response", "task: missing task_id")
        return task_id

    def poll(self, task_id: str) -> list[dict[str, Any]]:
        deadline = time.monotonic() + self.timeout_s
        while True:
            resp = self.http.get(f"{self.base_url}{TASK_PATH}/{task_id}", headers=self._headers())
            body = self._raise_for(resp, "poll")
            data = body.get("data") or {}
            status = data.get("task_status")
            if status == "success":
                results = data.get("results")
                if not isinstance(results, dict) or not isinstance(results.get("output"), list):
                    raise YouCamError("bad_response", "poll: results.output missing (format=json expected)")
                return results["output"]
            if status == "error":
                code = data.get("error") or "unknown_internal_error"
                raise YouCamError(str(code), data.get("error_message") or str(code))
            if time.monotonic() >= deadline:
                raise YouCamError("timeout", "poll: the analysis took too long")
            self.sleep(self.poll_interval)

    # -- full flow -------------------------------------------------------
    def analyze(self, image: bytes, actions: list[str], content_type: str = "image/jpeg") -> SkinAnalysisResult:
        ext = "png" if content_type == "image/png" else "jpg"
        file_id, request = self.create_file(len(image), content_type, f"twacha_selfie.{ext}")
        self.upload(request, image)
        task_id = self.create_task(file_id, actions)
        return SkinAnalysisResult(actions=actions, output=self.poll(task_id), task_id=task_id)
