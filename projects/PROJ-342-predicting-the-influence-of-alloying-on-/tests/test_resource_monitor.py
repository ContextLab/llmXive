import os
import json
import time
from pathlib import Path

# Import the decorator from the project
from code.resource_monitor import limit_resources, ResourceLimitExceeded

def dummy_heavy_work():
    # Simple CPU work to ensure some measurable time
    total = 0
    for i in range(100000):
        total += i ** 2
    return total

@limit_resources()
def dummy_function():
    dummy_heavy_work()
    time.sleep(0.1)  # ensure a tiny wall‑clock delay

def test_resource_monitor_writes_report(tmp_path: Path):
    """
    Verify that the @limit_resources decorator creates the JSON usage report
    with the required keys.
    """
    # Run the decorated function
    result = dummy_function()
    assert result is not None

    # The report should be written under the project root / data/
    report_path = Path(__file__).resolve().parents[2] / "data" / "resource_usage.json"
    assert report_path.is_file(), f"Report file not found: {report_path}"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Required keys
    assert "runtime_seconds" in report, "Missing runtime_seconds in report"
    assert "peak_ram_gb" in report, "Missing peak_ram_gb in report"
    # Values should be non‑negative numbers
    assert isinstance(report["runtime_seconds"], (int, float))
    assert isinstance(report["peak_ram_gb"], (int, float))
    assert report["runtime_seconds"] >= 0
    assert report["peak_ram_gb"] >= 0

if __name__ == "__main__":
    # Simple manual run
    test_resource_monitor_writes_report(Path.cwd())
    print("Resource monitor test passed.")