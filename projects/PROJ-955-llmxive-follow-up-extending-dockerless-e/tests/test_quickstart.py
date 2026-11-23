"""
Test that the quick‑run command creates the expected directory layout
and sample result file.
"""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_dry_run_creates_artifacts(tmp_path, monkeypatch):
    # Run the CLI dry‑run using the module entry point.
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.run_pipeline", "--dry-run"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=True,
    )
    # Verify that the expected success message appears.
    assert "Dry-run completed. Sample result at:" in result.stdout

    # Verify that the required top‑level directories now exist.
    expected_dirs = [
        paths.data(),
        paths.data("results"),
        Path.cwd() / "interim",
        Path.cwd() / "features",
        Path.cwd() / "models",
        Path.cwd() / "reports",
        Path.cwd() / "src" / "pipeline",
        Path.cwd() / "src" / "cli",
    ]
    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} to exist"

    # Verify that the sample CSV exists and contains ≤ 10 rows.
    sample_csv = paths.data("results", "sample_run.csv")
    assert sample_csv.is_file(), "Sample result CSV not found"
    with sample_csv.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    # Header + data rows ≤ 11 lines total.
    assert len(lines) <= 11, "Sample CSV has more than 10 data rows"