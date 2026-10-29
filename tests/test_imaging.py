import io

import pytest
from PIL import Image

from app.imaging import MAX_LONG_SIDE, ImageError, prepare_image
from tests.conftest import make_image


def dims(data: bytes):
    return Image.open(io.BytesIO(data)).size


def test_sd_photo_kept_and_reencoded_as_jpeg():
    out = prepare_image(make_image(600, 800, "PNG"))
    assert out.quality == "sd"
    assert (out.width, out.height) == (600, 800)
    assert out.content_type == "image/jpeg" and out.data[:2] == b"\xff\xd8"


def test_hd_selected_when_short_side_at_least_1080():
    out = prepare_image(make_image(1200, 1600))
    assert out.quality == "hd"


def test_long_side_downscaled_to_2560():
    out = prepare_image(make_image(3000, 4000))
    assert max(dims(out.data)) == MAX_LONG_SIDE
    assert dims(out.data) == (1920, 2560)
    assert out.quality == "hd"
    assert len(out.data) < 10 * 1024 * 1024


def test_force_sd_on_large_photo():
    assert prepare_image(make_image(1200, 1600), prefer="sd").quality == "sd"


def test_force_hd_rejects_small_photo():
    with pytest.raises(ImageError) as e:
        prepare_image(make_image(600, 800), prefer="hd")
    assert e.value.code == "error_below_min_image_size"


def test_too_small_rejected():
    with pytest.raises(ImageError) as e:
        prepare_image(make_image(300, 400))
    assert e.value.code == "error_below_min_image_size"


def test_rgba_png_converted():
    out = prepare_image(make_image(600, 800, "PNG", mode="RGBA"))
    assert Image.open(io.BytesIO(out.data)).mode == "RGB"


def test_garbage_bytes_rejected():
    with pytest.raises(ImageError) as e:
        prepare_image(b"not an image")
    assert e.value.code == "error_decode_image"


def test_exif_rotation_applied():
    img = Image.new("RGB", (800, 600), (200, 160, 130))
    exif = img.getexif()
    exif[0x0112] = 6  # rotate 90 CW on display
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    out = prepare_image(buf.getvalue())
    assert (out.width, out.height) == (600, 800)
