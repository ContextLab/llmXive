"""Tests for code/data.py (T002)."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

import pytest

import data as data_mod


def test_loader_names_exist():
    assert callable(data_mod.load_gsm8k)
    assert callable(data_mod.load_bigbench_lite)


def test_manifest_lists_datasets_and_within_budget():
    manifest = PROJECT_ROOT / "data" / "raw" / "manifest.txt"
    if not manifest.exists():
        pytest.skip("data/raw/manifest.txt not generated yet; run code/data.py --download")
    text = manifest.read_text(encoding="utf-8")
    assert data_mod.GSM8K_ID in text
    assert data_mod.BIGBENCH_ID in text
    total = int(
        [ln for ln in text.splitlines() if ln.startswith("total_size_bytes:")][0].split(":")[1]
    )
    assert total <= 7 * 1024 ** 3