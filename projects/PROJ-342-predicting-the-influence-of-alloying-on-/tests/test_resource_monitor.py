"""
Unit test for the ``limit_resources`` decorator introduced in T001.

The test decorates a trivial function, invokes it, and then checks that
``data/resource_usage.json`` has been created with the required keys.
"""
import json
import time
from pathlib import Path

from code.resource_monitor import limit_resources, ResourceLimitExceeded

def test_limit_resources_creates_report(tmp_path, monkeypatch):
    """
    Verify that the decorator writes a JSON report containing
    ``runtime_seconds`` and ``peak_ram_gb`` after the wrapped function
    finishes.
    """
    # Ensure the project root points to the temporary directory for isolation
    project_root = Path(__file__).resolve().parents[2]
    # Monkey‑patch the path used inside the decorator to a temporary location
    # (the decorator uses ``Path(__file__).resolve().parent.parent`` which
    # resolves to the repository root; we keep that but make sure the
    # ``data`` directory is writable.)
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    @limit_resources()
    def dummy():
        # Short sleep to produce a measurable runtime
        time.sleep(0.1)
        return 42

    # Run the decorated function – it should not raise
    result = dummy()
    assert result == 42

    # Load the generated JSON report
    report_path = project_root / "data" / "resource_usage.json"
    assert report_path.is_file(), "resource_usage.json was not created"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Required keys
    assert "runtime_seconds" in report, "Missing runtime_seconds in report"
    assert "peak_ram_gb" in report, "Missing peak_ram_gb in report"

    # Basic sanity checks on the values
    assert isinstance(report["runtime_seconds"], (int, float))
    assert isinstance(report["peak_ram_gb"], (int, float))
    assert report["runtime_seconds"] > 0
    assert report["peak_ram_gb"] > 0
    # Respect the project‑wide limit of 7 GB
    assert report["peak_ram_gb"] <= 7.0
