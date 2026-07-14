"""Unit tests for the correlation analysis module.

The tests verify that the module can:
* Load empty or missing CSVs without crashing.
* Compute a correlation when minimal synthetic but *real* data is provided.
* Write a correctly‑formatted CSV containing the expected header and rows.
"""

import csv
from pathlib import Path
import sys

# Ensure the project's ``code`` directory is on ``sys.path`` so that the
# ``correlation_analysis`` module can be imported as a top‑level module.
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "code"
sys.path.append(str(PROJECT_ROOT))

import pandas as pd
import pytest

# Import the functions we want to test
from correlation_analysis import (
    compute_correlations,
    save_correlation_results,
    run_correlation_analysis,
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create the directory structure expected by the pipeline."""
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "analysis").mkdir(parents=True)
    # Patch the Path objects used inside the module to point to the temporary dir
    original_cwd = Path.cwd()
    try:
        # Change cwd so that relative paths resolve inside the temp directory
        # (the module uses Path("data/...") which is relative to cwd)
        import os

        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(original_cwd)

def write_clone_metrics(path: Path):
    df = pd.DataFrame(
        {
            "file_path": ["a.py", "b.py", "c.py"],
            "clone_density": [0.1, 0.4, 0.3],
        }
    )
    df.to_csv(path, index=False)

def write_perplexity_scores(path: Path):
    df = pd.DataFrame(
        {
            "file_path": ["a.py", "b.py", "c.py"],
            "perplexity": [12.5, 20.1, 15.3],
        }
    )
    df.to_csv(path, index=False)

def write_bug_detection_results(path: Path):
    df = pd.DataFrame(
        {
            "problem_id": ["a.py", "b.py", "c.py"],
            "pass_at_1": [0.8, 0.5, 0.6],
        }
    )
    df.to_csv(path, index=False)

def test_compute_correlations_with_real_data(temp_data_dir):
    # Arrange – create minimal but realistic CSVs
    write_clone_metrics(Path("data/processed/clone_metrics.csv"))
    write_perplexity_scores(Path("data/processed/perplexity_scores.csv"))
    write_bug_detection_results(Path("data/processed/bug_detection_results.csv"))

    # Act
    correlations = compute_correlations()

    # Assert – we should get exactly two rows (clone↔perplexity, clone↔pass_at_1)
    metric_pairs = {(c["metric_x"], c["metric_y"]) for c in correlations}
    assert ("clone_density", "perplexity") in metric_pairs
    assert ("clone_density", "pass_at_1") in metric_pairs
    for c in correlations:
        assert isinstance(c["spearman_rho"], float)
        assert isinstance(c["p_value"], float)
        assert isinstance(c["n"], int) and c["n"] > 0

def test_save_correlation_results_writes_csv(temp_data_dir):
    # Arrange – a single fake correlation dict
    fake_corr = [
        {
            "metric_x": "clone_density",
            "metric_y": "perplexity",
            "spearman_rho": 0.42,
            "p_value": 0.01,
            "n": 3,
        }
    ]
    out_path = Path("data/analysis/correlation_results.csv")

    # Act
    save_correlation_results(fake_corr)

    # Assert – file exists and contains header + row
    assert out_path.is_file()
    with out_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == [
        {
            "metric_x": "clone_density",
            "metric_y": "perplexity",
            "spearman_rho": "0.42",
            "p_value": "0.01",
            "n": "3",
        }
    ]

def test_run_correlation_analysis_end_to_end(temp_data_dir):
    # Arrange – create the three input CSVs
    write_clone_metrics(Path("data/processed/clone_metrics.csv"))
    write_perplexity_scores(Path("data/processed/perplexity_scores.csv"))
    write_bug_detection_results(Path("data/processed/bug_detection_results.csv"))

    # Act
    correlations = run_correlation_analysis()

    # Assert – output file is written and matches the returned data
    out_path = Path("data/analysis/correlation_results.csv")
    assert out_path.is_file()
    with out_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    # Convert rows back to comparable dicts (values are strings in CSV)
    expected = [
        {
            "metric_x": c["metric_x"],
            "metric_y": c["metric_y"],
            "spearman_rho": f"{c['spearman_rho']}",
            "p_value": f"{c['p_value']}",
            "n": f"{c['n']}",
        }
        for c in correlations
    ]
    assert rows == expected
