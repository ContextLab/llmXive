"""
Integration test for the data download step (T003).

The test invokes the ``code/data/download.py`` entry point and checks that:
  * The expected raw Parquet files are created.
  * The alignment report JSON exists and records at least 129 000 matches.
  * The checksums JSON reports a status of "ok".
"""

import json
from pathlib import Path

import pytest

# Import the main function from the module under test
from data.download import main as download_main

@pytest.mark.timeout(300)
def test_download_and_verification(tmp_path, monkeypatch):
    """
    Run the download routine in a temporary directory and verify outputs.
    """

    # Redirect all project‑relative paths to a temporary location so the test
    # does not interfere with any existing data on the runner.
    project_root = Path(__file__).resolve().parents[2]  # <project>/code/tests/../..
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    results_dir = tmp_path / "results"

    # Monkey‑patch the paths used inside the module:
    # - ``download_qm9`` and ``download_ir_spectra`` use a default of "data/raw".
    # - ``paths.results`` is used for the checksums file.
    monkeypatch.setattr("data.download.Path", lambda *args, **kwargs: Path(*args, **kwargs))
    monkeypatch.setattr("data.download._ensure_dir", lambda p: p.parent.mkdir(parents=True, exist_ok=True) or p)
    monkeypatch.setattr("data.download.paths.results", lambda *args, **kwargs: results_dir / Path(*args, **kwargs))

    # Ensure the temporary directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Run the download routine (this will download the real datasets)
    download_main()

    # Expected file locations
    qm9_file = raw_dir / "qm9.parquet"
    ir_file = raw_dir / "ir_spectra.parquet"
    alignment_report = processed_dir / "alignment_report.json"
    checksums_file = results_dir / "checksums.json"

    # Verify that the files were created
    assert qm9_file.is_file(), "QM9 parquet file was not created"
    assert ir_file.is_file(), "IR spectra parquet file was not created"
    assert alignment_report.is_file(), "Alignment report JSON was not created"
    assert checksums_file.is_file(), "Checksums JSON was not created"

    # Verify alignment report contains sufficient matches
    with alignment_report.open() as f:
        report = json.load(f)
    assert report["matched"] >= 129_000, f"Matched molecules {report['matched']} < 129,000"

    # Verify checksums JSON status
    with checksums_file.open() as f:
        checks = json.load(f)
    assert checks.get("status") == "ok", "Checksums status is not 'ok'"