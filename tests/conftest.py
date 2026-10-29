import io

import pytest
from PIL import Image

from app.concerns import level_for


def make_image(w=900, h=1200, fmt="JPEG", mode="RGB") -> bytes:
    img = Image.new(mode, (w, h), (205, 165, 135) if mode == "RGB" else (205, 165, 135, 255))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def scores_from(raw: dict) -> dict:
    return {k: {"raw_score": float(v), "ui_score": int(v), "level": level_for(v)} for k, v in raw.items()}


@pytest.fixture
def face_jpeg() -> bytes:
    return make_image()


@pytest.fixture
def oily_acne():
    return scores_from(dict(moisture=72, oiliness=45, acne=42, pores=52, redness=80, texture=66, dark_circles=70, spots=58))


@pytest.fixture
def dry_sensitive():
    return scores_from(dict(moisture=40, oiliness=85, acne=86, pores=82, redness=50, texture=55, dark_circles=62, spots=64))
