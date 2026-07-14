"""
Basic sanity test for the final report generation script.
It checks that the script runs without raising exceptions and that the
expected output file is created.
"""
import os
import pathlib

import pytest

from t041_generate_final_report import main as generate_report


@pytest.fixture(scope="module", autouse=True)
def clean_artifacts(tmp_path_factory):
    """Remove any pre‑existing report files before the test suite runs."""
    base = pathlib.Path("data/processed")
    for f in ["final_report.txt", "baseline_metrics.json", "cleaned_metrics.json"]:
        p = base / f
        if p.is_file():
            p.unlink()
    yield
    # Cleanup after tests
    for f in ["final_report.txt", "baseline_metrics.json", "cleaned_metrics.json"]:
        p = base / f
        if p.is_file():
            p.unlink()


def test_final_report_creates_output(tmp_path):
    """
    Run the final report generation and assert that the summary file
    exists and is non‑empty.
    """
    # Ensure the working directory is the project root
    cwd = os.getcwd()
    assert pathlib.Path(cwd).joinpath("code", "t041_generate_final_report.py").exists()

    # Execute the script
    generate_report()

    summary_path = pathlib.Path("data/processed/final_report.txt")
    assert summary_path.is_file(), "Summary report was not created"
    assert summary_path.stat().st_size > 0, "Summary report is empty"


def test_baseline_and_cleaned_metrics_created():
    """
    Verify that the helper functions inside the script created the
    required metric JSON files when they were missing.
    """
    baseline_path = pathlib.Path("data/processed/baseline_metrics.json")
    cleaned_path = pathlib.Path("data/processed/cleaned_metrics.json")

    assert baseline_path.is_file(), "Baseline metrics JSON missing"
    assert cleaned_path.is_file(), "Cleaned metrics JSON missing"


# The test suite can be executed with ``pytest -q`` from the repository root.