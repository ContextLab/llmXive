"""
Unit tests for the data‑availability recording script (T002).
The test validates that the JSON report conforms to the expected schema
(the schema is exercised elsewhere) and that each entry reports a
``status`` of ``verified`` when the underlying file matches its checksum.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths

# Import the script under test
from code.src.data.record_availability import main as record_main


def test_data_availability_report():
    """
    Run the script and verify the produced JSON contains ``verified``
    status for all entries.
    """
    # Execute the CLI – it will raise SystemExit on failure
    record_main()

    report_path = paths.results("data_availability.json")
    assert report_path.is_file(), "Report file not created"

    with report_path.open("r", encoding="utf-8") as fh:
        report = json.load(fh)

    # Every entry must have a ``status`` field equal to "verified"
    for meta in report.values():
        assert meta.get("status") == "verified", "File not verified"