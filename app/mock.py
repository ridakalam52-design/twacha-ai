"""Demo mode: built on a REAL YouCam response (app/fixtures), so the shape is exactly
what the live API returns (format=json `results.output`).

Used when YOUCAM_API_KEY is not set. Scores are nudged by a small amount seeded from the
image bytes, so the same photo always gives the same demo result and a different photo
gives a slightly different one (handy for showing the 4-week progress comparison).
Mask links are dropped because the captured ones were presigned and have expired, and the
`skin_age` item is dropped because it belongs to the fixture's subject, not the user.
The UI labels every demo result "Demo data".
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from functools import lru_cache
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@lru_cache(maxsize=2)
def fixture_response(quality: str) -> dict:
    q = "hd" if quality == "hd" else "sd"
    return json.loads((FIXTURES / f"youcam_skin_analysis_{q}.json").read_text())


def mock_output(image: bytes, quality: str = "sd") -> list[dict]:
    output = [i for i in copy.deepcopy(fixture_response(quality)["data"]["results"]["output"])
              if i.get("type") != "skin_age"]
    rng = random.Random(int.from_bytes(hashlib.sha256(image).digest()[:8], "big"))
    deltas: dict[str, float] = {}
    for item in output:
        item["mask_urls"] = []
        if "raw_score" not in item:
            continue
        # One nudge per action, shared by its regions so they stay consistent.
        d = deltas.setdefault(item["type"], rng.uniform(-8, 8))
        item["raw_score"] = round(min(99.0, max(1.0, item["raw_score"] + d)), 2)
        item["ui_score"] = int(min(99, max(1, round(item["ui_score"] + d / 2))))
    scored = [i["ui_score"] for i in output if "ui_score" in i and i.get("region", "whole") == "whole"]
    for item in output:
        if item.get("type") == "all" and scored:
            item["score"] = round(sum(scored) / len(scored), 2)
    return output
