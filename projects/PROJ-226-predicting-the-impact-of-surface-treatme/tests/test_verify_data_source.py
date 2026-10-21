import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

def test_availability_report_exists():
    """The script must produce a JSON file at the expected location."""
    report_path = paths.data("source", "availability_report.json")
    assert report_path.is_file(), f"Report not found at {report_path}"
    with report_path.open() as f:
        data = json.load(f)
    # The file must contain a top‑level 'datasets' key (list may be empty)
    assert isinstance(data, dict), "Report JSON should be an object"
    assert "datasets" in data, "'datasets' key missing in availability report"
    assert isinstance(data["datasets"], list), "'datasets' should be a list"