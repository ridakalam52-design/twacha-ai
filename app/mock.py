"""Demo mode: realistic sample output shaped exactly like YouCam's format=json result.

Used when YOUCAM_API_KEY is not set. Scores are seeded from the image bytes, so the
same photo always gives the same demo result and a different photo gives a different
one (handy for showing the 4-week progress comparison). Always labelled "Demo data".
"""
from __future__ import annotations

import hashlib
import random

from .concerns import CONCERNS

# Base raw scores around a typical oily-combination profile in a humid Indian city.
BASE_RAW = {
    "moisture": 63, "oiliness": 58, "acne": 68, "pores": 64,
    "redness": 80, "texture": 74, "dark_circles": 70, "spots": 70,
}


def _ui_from_raw(raw: float) -> int:
    # ui_score is a friendlier calibration of raw_score (docs); mimic a gentle lift.
    return max(1, min(100, round(40 + raw * 0.55)))


def mock_output(image: bytes, quality: str = "sd") -> list[dict]:
    seed = int.from_bytes(hashlib.sha256(image).digest()[:8], "big")
    rng = random.Random(seed)
    out: list[dict] = []
    for key, (sd, hd) in CONCERNS.items():
        raw = max(5.0, min(98.0, BASE_RAW[key] + rng.uniform(-10, 10)))
        out.append({
            "type": hd if quality == "hd" else sd,
            "region": "whole",
            "raw_score": round(raw, 2),
            "ui_score": _ui_from_raw(raw),
            "mask_urls": [],
        })
    avg = sum(o["ui_score"] for o in out) / len(out)
    out.append({"type": "all", "score": round(avg, 2)})
    out.append({"type": "skin_age", "score": 24 + rng.randint(0, 8)})
    return out
