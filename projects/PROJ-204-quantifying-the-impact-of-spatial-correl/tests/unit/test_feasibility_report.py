"""
Simple sanity test that the feasibility report is valid JSON and contains
the expected top‑level keys.  The test does **not** assert that any source
is reachable – that would depend on external network availability.
"""
import json
from pathlib import Path

def test_feasibility_report_schema():
    report_path = Path("data/results/feasibility_report.json")
    assert report_path.is_file(), "Feasibility report file missing"
    with report_path.open() as fp:
        data = json.load(fp)

    # Basic schema checks
    assert isinstance(data, dict), "Report must be a JSON object"
    assert "sources" in data and isinstance(data["sources"], list), "'sources' list missing"
    assert "verdict" in data and data["verdict"] in {"continue", "halt"}, "Invalid verdict"
    # Each source entry should contain the required fields
    required_fields = {"source", "url", "reachable", "http_status", "n_records", "linked_sample_count", "has_linked_eds"}
    for src in data["sources"]:
        assert required_fields.issubset(src.keys()), f"Source entry missing fields: {src}"