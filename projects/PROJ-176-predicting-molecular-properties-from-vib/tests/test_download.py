import json
from pathlib import Path

def test_checksums_file_exists():
    """Verify that the checksums.json file is created and reports status ok."""
    checksums_path = Path("results/checksums.json")
    assert checksums_path.is_file(), "checksums.json was not created"
    with open(checksums_path, "r") as f:
        data = json.load(f)
    assert data.get("status") == "ok", "Checksum status is not ok"
    # Ensure both expected files are listed
    files = data.get("files", {})
    assert "qm9.parquet" in files, "qm9.parquet checksum missing"
    assert "ir_spectra.parquet" in files, "ir_spectra.parquet checksum missing"

def test_alignment_report():
    """Check that the alignment report contains matched >= 129000."""
    report_path = Path("data/processed/alignment_report.json")
    assert report_path.is_file(), "alignment_report.json was not created"
    with open(report_path, "r") as f:
        report = json.load(f)
    assert report["matched"] >= 129_000, f"Matched molecules {report['matched']} < 129000"
    assert "selection_bias_stats" in report, "selection_bias_stats missing in report"