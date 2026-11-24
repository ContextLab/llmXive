import json
from pathlib import Path

from llmxive_toolkit import paths
from verify_data_source import main as verify_main

def test_verify_data_source_creates_outputs(tmp_path, monkeypatch):
    """
    Run the verification script and ensure that:
    - Three raw CSV files are created (nist.csv, zenodo.csv, materials_project.csv)
    - The availability report exists and reports columns_ok == True for each source
    """
    # Ensure a clean environment
    raw_dir = paths.data("raw")
    source_dir = paths.data("source")
    for p in raw_dir.iterdir():
        p.unlink()
    for p in source_dir.iterdir():
        p.unlink()

    # Execute the script (it will exit via sys.exit; capture SystemExit)
    try:
        verify_main()
    except SystemExit as e:
        assert e.code == 0, f"Script exited with non‑zero code {e.code}"

    # Check raw CSV files
    expected_raw_files = ["nist.csv", "zenodo.csv", "materials_project.csv"]
    for fname in expected_raw_files:
        assert (raw_dir / fname).is_file(), f"Missing raw file {fname}"

    # Check availability report
    report_path = source_dir / "availability_report.json"
    assert report_path.is_file(), "Missing availability_report.json"
    with report_path.open() as f:
        report = json.load(f)

    assert "datasets" in report, "Report missing 'datasets' key"
    assert len(report["datasets"]) == 3, "Report should contain three entries"
    for entry in report["datasets"]:
        assert entry["columns_ok"], f"Source {entry['source_name']} failed column check"