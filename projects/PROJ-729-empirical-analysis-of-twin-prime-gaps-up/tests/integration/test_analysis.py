"""
Integration test for the analysis pipeline (User Story 2).

This test verifies the full execution of `code/analyze_gaps.py` to ensure:
1. The script runs without error on the generated twin prime data.
2. The output artifacts (`data/results/stats.json` and `data/figures/qq_plot.png`) are created.
3. The statistical results in `stats.json` contain valid KS statistics and p-values.
4. The rejection status is correctly computed based on the alpha threshold.
"""
import os
import sys
import json
import subprocess
import pytest
from pathlib import Path

# Project root is the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = DATA_DIR / "figures"

# Expected artifact paths
INPUT_CSV = DATA_DIR / "raw" / "twin_primes.csv"
STATS_JSON = RESULTS_DIR / "stats.json"
QQ_PNG = FIGURES_DIR / "qq_plot.png"

# Ensure paths are strings for subprocess
SCRIPT_PATH = CODE_DIR / "analyze_gaps.py"


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    """Ensure directories exist before running tests."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    # Note: We assume T012 has successfully generated INPUT_CSV.
    # If INPUT_CSV is missing, this test will fail loudly as expected.
    if not INPUT_CSV.exists():
        pytest.fail(
            f"Input data file {INPUT_CSV} not found. "
            "Please ensure User Story 1 (T012) has been completed successfully."
        )


def test_analyze_gaps_pipeline_execution():
    """
    Test that analyze_gaps.py executes successfully and produces expected artifacts.
    """
    # Clean up previous artifacts to ensure fresh generation
    if STATS_JSON.exists():
        STATS_JSON.unlink()
    if QQ_PNG.exists():
        QQ_PNG.unlink()

    # Run the analysis script
    # We use the project root as cwd so relative imports in the script work if needed,
    # though the script likely uses absolute paths or config.
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    # Assert script execution was successful
    assert result.returncode == 0, (
        f"Script execution failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Verify output artifacts exist
    assert STATS_JSON.exists(), f"Expected stats file {STATS_JSON} was not created."
    assert QQ_PNG.exists(), f"Expected QQ plot {QQ_PNG} was not created."

    # Verify content of stats.json
    with open(STATS_JSON, "r") as f:
        stats_data = json.load(f)

    # Check for required keys based on T021, T021b
    required_keys = ["ks_statistic", "p_value", "rejection_status"]
    for key in required_keys:
        assert key in stats_data, f"Missing required key '{key}' in stats.json"

    # Verify types and logical consistency
    assert isinstance(stats_data["ks_statistic"], (int, float)), "ks_statistic must be numeric"
    assert isinstance(stats_data["p_value"], (int, float)), "p_value must be numeric"
    assert isinstance(stats_data["rejection_status"], bool), "rejection_status must be boolean"

    # Verify the rejection status logic (p < 0.05 -> True)
    alpha = 0.05
    expected_rejection = stats_data["p_value"] < alpha
    assert stats_data["rejection_status"] == expected_rejection, (
        f"rejection_status mismatch: expected {expected_rejection} "
        f"based on p_value {stats_data['p_value']} and alpha {alpha}"
    )

    # Verify the plot is not empty (basic size check)
    file_size = QQ_PNG.stat().st_size
    assert file_size > 1000, "QQ plot file seems too small to be a valid image."


def test_parametric_bootstrap_reproducibility():
    """
    Optional: Verify that running the script again produces identical results (seed=42).
    This ensures the Parametric Bootstrap KS test is reproducible.
    """
    # Read current stats
    with open(STATS_JSON, "r") as f:
        original_stats = json.load(f)

    # Run script again
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "Second run failed."

    # Read new stats
    with open(STATS_JSON, "r") as f:
        new_stats = json.load(f)

    # Compare key metrics
    assert original_stats["ks_statistic"] == new_stats["ks_statistic"], "KS statistic changed between runs."
    assert original_stats["p_value"] == new_stats["p_value"], "P-value changed between runs."
    assert original_stats["rejection_status"] == new_stats["rejection_status"], "Rejection status changed between runs."