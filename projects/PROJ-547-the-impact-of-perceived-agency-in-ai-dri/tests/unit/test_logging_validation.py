"""
Unit tests ensuring that validation modules emit log entries.
The tests run the modules on synthetic data and verify that a log file
has been created and contains expected keys.
"""
import json
import os
import pathlib
import tempfile

import pandas as pd
import pytest

from logging.pipeline_logger import get_logger, log_dict

# Helper to locate the most recent log file
def _latest_log_path() -> pathlib.Path:
    log_dir = pathlib.Path("logs")
    log_files = sorted(log_dir.glob("run_*.log"))
    assert log_files, "No log files found in logs/ directory."
    return log_files[-1]

def _read_log_entries(log_path: pathlib.Path):
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

@pytest.fixture(scope="module")
def synthetic_data(tmp_path_factory):
    """Create minimal synthetic CSV files for reliability and convergence."""
    # Reliability data – 4 marker items
    rel_path = tmp_path_factory.mktemp("data") / "reliability.csv"
    df_rel = pd.DataFrame(
        {
            "item1": [1, 0, 1, 1],
            "item2": [1, 1, 0, 1],
            "item3": [0, 0, 1, 1],
            "item4": [1, 0, 0, 1],
        }
    )
    df_rel.to_csv(rel_path, index=False)

    # Merged data for convergent validity
    conv_path = tmp_path_factory.mktemp("data") / "merged.csv"
    df_conv = pd.DataFrame(
        {
            "session_id": [1, 2, 3, 4],
            "agency_score": [0.2, 0.5, 0.7, 0.9],
            "external_scale_score": [0.1, 0.4, 0.6, 0.95],
        }
    )
    df_conv.to_csv(conv_path, index=False)

    return rel_path, conv_path

def test_reliability_logging(synthetic_data, caplog):
    rel_path, _ = synthetic_data
    from validation.compute_reliability import compute_split_half_reliability

    # Ensure a fresh logger instance writes to a new file
    logger = get_logger("test_reliability")
    logger.handlers.clear()  # Remove any existing handlers
    # Trigger computation
    reliability = compute_split_half_reliability(rel_path)

    # Verify a numeric reliability was returned
    assert isinstance(reliability, float)

    # Check that a log entry with the reliability value exists
    log_path = _latest_log_path()
    entries = _read_log_entries(log_path)
    assert any(
        entry.get("event") == "split_half_reliability_computed"
        and "reliability" in entry
        for entry in entries
    ), "Reliability computation not logged."

def test_convergent_logging(synthetic_data, caplog):
    _, conv_path = synthetic_data
    from validation.compute_convergent import compute_convergent_correlation

    r, p = compute_convergent_correlation(conv_path)
    assert isinstance(r, float) and isinstance(p, float)

    log_path = _latest_log_path()
    entries = _read_log_entries(log_path)
    assert any(
        entry.get("event") == "convergent_correlation_computed"
        and "pearson_r" in entry
        for entry in entries
    ), "Convergent correlation not logged."

def test_report_generation_logging(tmp_path):
    # Create a minimal subset CSV with required columns
    subset_path = tmp_path / "subset.csv"
    df = pd.DataFrame(
        {
            "reliability_score": [0.85, 0.90],
            "agency_score": [0.3, 0.6],
            "external_scale_score": [0.25, 0.65],
        }
    )
    df.to_csv(subset_path, index=False)

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    from validation.generate_report import main as generate_main

    # Run the report generator
    generate_main_args = [str(subset_path), str(output_dir)]
    # Simulate command‑line invocation
    import sys

    original_argv = sys.argv
    sys.argv = ["generate_report.py"] + generate_main_args
    try:
        generate_main()
    finally:
        sys.argv = original_argv

    # Verify that both files were created
    assert (output_dir / "validation_report.yaml").exists()
    assert (output_dir / "validation_report.pdf").exists()

    # Verify logging captured the generation step
    log_path = _latest_log_path()
    entries = _read_log_entries(log_path)
    assert any(
        entry.get("event") == "convergent_correlation_computed"
        for entry in entries
    ) or any(
        entry.get("event") == "split_half_reliability_computed"
        for entry in entries
    ), "Report generation did not produce expected log entries."
