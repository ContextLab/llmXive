"""Tests for T001: project skeleton, logging, and resource monitoring."""

import json
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"

for p in (str(PROJECT_ROOT), str(CODE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


def test_required_directories_exist():
    required = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "artifacts" / "models",
        PROJECT_ROOT / "artifacts" / "metrics",
        PROJECT_ROOT / "artifacts" / "reports",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "specs" / "001-predicting-the-influence-of-alloying-on" / "contracts",
        PROJECT_ROOT / "logs",
    ]
    for d in required:
        assert d.is_dir(), f"missing directory: {d}"


def test_importing_code_produces_logger():
    import code as code_pkg
    assert isinstance(getattr(code_pkg, "logger", None), logging.Logger)


def test_limit_resources_writes_usage_report(tmp_path):
    from resource_monitor import limit_resources

    @limit_resources()
    def dummy():
        return sum(i * i for i in range(10000))

    dummy()

    report_path = PROJECT_ROOT / "data" / "resource_usage.json"
    assert report_path.is_file()
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert "runtime_seconds" in report
    assert "peak_ram_gb" in report
    assert isinstance(report["runtime_seconds"], float)
    assert isinstance(report["peak_ram_gb"], float)