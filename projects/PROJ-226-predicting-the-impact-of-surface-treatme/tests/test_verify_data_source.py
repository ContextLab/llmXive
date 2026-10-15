import json
from pathlib import Path

from llmxive_toolkit import paths

def test_availability_report_exists(tmp_path, monkeypatch):
    """
    Ensure that the verify_data_source script writes a non‑empty availability
    report containing at least one dataset.
    """
    # Run the script
    from code.verify_data_source import main as verify_main
    verify_main()

    report_path = paths.data("source", "availability_report.json")
    assert report_path.is_file(), "availability_report.json was not created"

    with report_path.open() as f:
        data = json.load(f)

    assert isinstance(data, dict), "Report should be a JSON object"
    datasets = data.get("datasets")
    assert isinstance(datasets, list) and len(datasets) > 0, "datasets list must be non‑empty"

    # Verify that each entry has a URL we can handle
    for ds in datasets:
        assert "url" in ds, "Each dataset entry must contain a 'url' field"
        assert ds["url"].startswith("file://") or ds["url"].startswith("http"), "URL scheme must be file or http"