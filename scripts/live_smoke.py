"""One real end-to-end call to YouCam Skin Analysis (costs ~12 SD / ~16 HD units).

Usage:  YOUCAM_API_KEY=... python scripts/live_smoke.py path/to/selfie.jpg
Prints the normalised scores; never prints the key.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.concerns import actions_for, normalize_output  # noqa: E402
from app.imaging import prepare_image  # noqa: E402
from app.youcam import YouCamClient, YouCamError  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2 or not os.getenv("YOUCAM_API_KEY"):
        print(__doc__)
        return 2
    img = prepare_image(open(sys.argv[1], "rb").read(), prefer=os.getenv("YOUCAM_QUALITY", "auto"))
    actions = actions_for(img.quality)
    print(f"{img.width}x{img.height} -> {img.quality.upper()} actions: {', '.join(actions)}")
    try:
        res = YouCamClient(os.environ["YOUCAM_API_KEY"]).analyze(img.data, actions)
    except YouCamError as exc:
        print("YouCam error:", exc.code, "-", exc.message)
        return 1
    n = normalize_output(res.output)
    for s in n["scores"].values():
        s.pop("mask_url", None)
    print(json.dumps(n, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
