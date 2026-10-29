"""Repo hygiene: secrets stay out of git."""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    return [line for line in out.splitlines() if line]


def test_dotenv_not_tracked():
    files = tracked_files()
    assert ".env" not in files
    assert not [f for f in files if Path(f).name.startswith(".env") and f != ".env.example"]


def test_gitignore_covers_dotenv():
    lines = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in lines
    assert "!.env.example" in lines


def test_env_example_has_no_real_key():
    text = (ROOT / ".env.example").read_text()
    m = re.search(r"^YOUCAM_API_KEY=(.*)$", text, re.M)
    assert m and m.group(1).strip() == ""


def test_render_yaml_does_not_sync_key():
    text = (ROOT / "render.yaml").read_text()
    assert "YOUCAM_API_KEY" in text and "sync: false" in text


def test_no_bearer_tokens_committed():
    pattern = re.compile(r"Bearer\s+[A-Za-z0-9_\-]{24,}")
    for f in tracked_files():
        p = ROOT / f
        if p.suffix in {".py", ".js", ".html", ".md", ".yaml", ".yml", ".txt", ".example"} and p.is_file():
            assert not pattern.search(p.read_text(errors="ignore")), f
