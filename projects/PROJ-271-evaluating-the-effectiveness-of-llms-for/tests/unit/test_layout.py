"""Unit tests for T005: package initializer and directory layout."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_required_directories_exist():
    for rel in ["data/raw", "data/processed", "results"]:
        assert (PROJECT_ROOT / rel).is_dir(), f"missing directory: {rel}"


def test_code_package_has_init():
    assert (PROJECT_ROOT / "code" / "__init__.py").is_file()


def test_layout_verification_report_valid():
    report_path = PROJECT_ROOT / "results" / "layout_verification.json"
    assert report_path.is_file(), "layout verification report missing"
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    assert report["all_present"] is True
    for rel in ["data/raw", "data/processed", "results"]:
        assert report["directories"][rel]["exists"] is True