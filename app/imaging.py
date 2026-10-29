"""Server-side image preparation to the YouCam Skin Analysis file spec.

Spec (docs, File Specs & Errors):
  SD: short side >= 480 px;  HD: short side >= 1080 px;  long side > 2560 is auto-resized
  by YouCam, but we downscale to <= 2560 ourselves; file < 10 MB; jpg/jpeg/png.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_LONG_SIDE = 2560
SD_MIN_SHORT = 480
HD_MIN_SHORT = 1080
MAX_BYTES = 10 * 1024 * 1024


class ImageError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class PreparedImage:
    data: bytes
    width: int
    height: int
    quality: str  # "hd" | "sd"
    content_type: str = "image/jpeg"


def prepare_image(raw: bytes, prefer: str = "auto") -> PreparedImage:
    """Decode, fix EXIF rotation, downscale to <= 2560 long side, pick HD or SD, encode JPEG < 10 MB.

    prefer: "auto" (HD when short side >= 1080, else SD), "sd" or "hd".
    """
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageError("error_decode_image", "Please upload a JPG or PNG photo.") from exc

    w, h = img.size
    long_side = max(w, h)
    if long_side > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / long_side
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        w, h = img.size

    short_side = min(w, h)
    if short_side < SD_MIN_SHORT:
        raise ImageError(
            "error_below_min_image_size",
            f"Photo is too small ({w}x{h}). The short side needs at least {SD_MIN_SHORT} px.",
        )
    if prefer == "hd" and short_side < HD_MIN_SHORT:
        raise ImageError(
            "error_below_min_image_size",
            f"HD analysis needs at least {HD_MIN_SHORT} px on the short side (got {short_side}).",
        )
    quality = "hd" if (prefer == "hd" or (prefer == "auto" and short_side >= HD_MIN_SHORT)) else "sd"

    for q in (92, 85, 75, 65):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        data = buf.getvalue()
        if len(data) < MAX_BYTES:
            return PreparedImage(data=data, width=w, height=h, quality=quality)
    raise ImageError("exceed_max_filesize", "Photo is too large even after compression.")
