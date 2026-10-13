import json
from pathlib import Path
from llmxive_toolkit import paths

def test_data_gap_report_created():
    """Ensure the Data Gap Report is generated when no dataset is available."""
    report_path = paths.results("data_gap_report.md")
    assert report_path.is_file(), f"Data Gap Report not found at {report_path}"
    with open(report_path, "r") as f:
        content = json.load(f)
    # The report must contain the required statement
    assert "Data Gap" in content.get("message", ""), "Report does not contain required 'Data Gap' statement"
    assert content.get("status") == "DATA_GAP", "Report status should be DATA_GAP"