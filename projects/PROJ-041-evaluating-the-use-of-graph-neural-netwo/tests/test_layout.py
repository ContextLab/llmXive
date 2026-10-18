"""Tests for the project layout created by code/create_layout.py."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "code"))

from create_layout import main  # noqa: E402


def test_layout_creates_directories_and_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main()
    for d in ("code", "data", "docs", "tests", "contracts", "figures"):
        assert (tmp_path / d).is_dir(), f"missing directory {d}"
    assert (tmp_path / "code" / "config.yaml").is_file()
    # Re-running must not fail or clobber the config.
    cfg_before = (tmp_path / "code" / "config.yaml").read_text()
    main()
    assert (tmp_path / "code" / "config.yaml").read_text() == cfg_before
