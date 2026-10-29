"""TwachaAI: FastAPI backend. Serves the static UI and proxies YouCam Skin Analysis server-side."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from .concerns import CONCERNS, actions_for, normalize_output, report_card, level_for
from .imaging import ImageError, prepare_image
from .mock import mock_output
from .routine import BUDGETS, CLIMATES, build_routine
from .youcam import YouCamClient, YouCamError

log = logging.getLogger("twacha")
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
API_NAME = "YouCam Skin Analysis API (V2)"

DISCLAIMER = {
    "en": "TwachaAI is a cosmetic skin check, not medical advice. For painful, cystic or scarring acne, sudden rashes, or a changing mole, please see a dermatologist.",
    "hi": "TwachaAI एक कॉस्मेटिक स्किन जांच है, चिकित्सा सलाह नहीं। दर्द वाले, गहरे या दाग़ छोड़ने वाले मुंहासे, अचानक चकत्ते, या बदलते तिल के लिए त्वचा विशेषज्ञ से मिलें।",
}


def default_client_factory() -> YouCamClient | None:
    key = os.getenv("YOUCAM_API_KEY", "").strip()
    return YouCamClient(api_key=key) if key else None


app = FastAPI(title="TwachaAI", version="1.0.0")
app.state.client_factory = default_client_factory  # overridable in tests
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _mode() -> str:
    return "live" if os.getenv("YOUCAM_API_KEY", "").strip() else "demo"


def _quality_pref() -> str:
    q = os.getenv("YOUCAM_QUALITY", "auto").strip().lower()
    return q if q in ("auto", "sd", "hd") else "auto"


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": _mode()}


@app.get("/api/config")
def config() -> dict[str, Any]:
    return {
        "mode": _mode(),
        "api": API_NAME,
        "quality": _quality_pref(),
        "actions": {"sd": actions_for("sd"), "hd": actions_for("hd")},
        "concerns": list(CONCERNS),
        "budgets": list(BUDGETS),
        "climates": list(CLIMATES),
        "disclaimer": DISCLAIMER,
    }


@app.post("/api/analyze")
async def analyze(photo: UploadFile = File(...), budget: int = Form(1500), climate: str = Form("humid")):
    if budget not in BUDGETS:
        return _err(422, "invalid_budget", f"Budget must be one of {list(BUDGETS)}.")
    if climate not in CLIMATES:
        return _err(422, "invalid_climate", f"Climate must be one of {list(CLIMATES)}.")
    raw = await photo.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        return _err(413, "file_too_large", "Please upload a photo under 15 MB.")
    if not raw:
        return _err(422, "empty_file", "No photo received.")

    try:
        img = prepare_image(raw, prefer=_quality_pref())
    except ImageError as exc:
        return _err(422, exc.code, exc.message)

    actions = actions_for(img.quality)
    client = app.state.client_factory()
    demo = client is None
    if demo:
        output = mock_output(img.data, img.quality)
        task_id = None
    else:
        try:
            # Sync HTTP client; run in a worker thread so the event loop stays free.
            result = await run_in_threadpool(client.analyze, img.data, actions, img.content_type)
        except YouCamError as exc:
            log.warning("YouCam error %s (%s): %s", exc.code, exc.http_status, exc.message)
            return _err(502, exc.code, exc.user_message)
        output, task_id = result.output, result.task_id

    normalized = normalize_output(output)
    if not normalized["scores"]:
        return _err(502, "no_scores", "The analysis returned no skin scores. Please try another photo.")

    return {
        "demo": demo,
        "source": API_NAME,
        "quality": img.quality,
        "actions": actions,
        "task_id": task_id,
        "image": {"width": img.width, "height": img.height},
        "overall": normalized["overall"],
        "skin_age": normalized["skin_age"],
        "scores": {k: {"ui_score": v["ui_score"], "raw_score": v["raw_score"], "level": v["level"]}
                   for k, v in normalized["scores"].items()},
        "report": report_card(normalized),
        "routine": build_routine(normalized["scores"], budget, climate),
        "disclaimer": DISCLAIMER,
    }


class RoutineRequest(BaseModel):
    scores: dict[str, dict[str, float | str]]
    budget: int = 1500
    climate: str = "humid"


@app.post("/api/routine")
def routine(req: RoutineRequest):
    """Re-plan a routine for a new budget/climate from existing scores (no new API call)."""
    if req.budget not in BUDGETS:
        return _err(422, "invalid_budget", f"Budget must be one of {list(BUDGETS)}.")
    if req.climate not in CLIMATES:
        return _err(422, "invalid_climate", f"Climate must be one of {list(CLIMATES)}.")
    scores: dict[str, dict[str, Any]] = {}
    for key, s in req.scores.items():
        if key not in CONCERNS or "raw_score" not in s:
            continue
        raw = float(s["raw_score"])
        scores[key] = {"raw_score": raw, "ui_score": s.get("ui_score", raw), "level": level_for(raw)}
    if not scores:
        return _err(422, "no_scores", "No valid scores supplied.")
    return build_routine(scores, req.budget, req.climate)
