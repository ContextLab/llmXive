"""
Integration test for the Sensitivity Analysis Transport Loop (T025c).

The test runs the ``code/sensitivity_analysis_transport_loop.py`` script,
then verifies that the output CSV exists and contains exactly one row per
cutoff value defined in the simulation configuration.
"""

import csv
from pathlib import Path

import pytest

from utils.io import load_simulation_config, get_config_value


@pytest.mark.integration
def test_sensitivity_transport_loop_produces_expected_rows(tmp_path, monkeypatch):
    """
    Run the transport loop script and assert the CSV contains a row for each
    cutoff defined in ``code/simulation_config.yaml``.
    """
    # Ensure the repository root is the current working directory for the
    # subprocess call.
    import os
    cwd = Path(__file__).resolve().parents[2]  # project root
    os.chdir(cwd)

    # Execute the script.
    result = pytest.run(["python", "code/sensitivity_analysis_transport_loop.py"])
    assert result.returncode == 0, f"Script exited with {result.returncode}"

    # Load the expected cutoffs from the config.
    config_path = Path("code/simulation_config.yaml")
    cfg = load_simulation_config(config_path)
    cutoffs = get_config_value(cfg, "cutoff_values")
    expected_rows = len(cutoffs)

    # Read the generated CSV.
    csv_path = Path("data/analysis/sensitivity_results.csv")
    assert csv_path.is_file(), f"{csv_path} was not created"

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == expected_rows, (
        f"Expected {expected_rows} rows (one per cutoff), got {len(rows)}"
    )

    # Basic sanity checks on column existence.
    for row in rows:
        assert "cutoff" in row
        assert "network_id" in row
        assert "kappa" in row
        assert "runtime_seconds" in row
        assert "status" in row

    # Clean up after test to keep the repo tidy.
    csv_path.unlink()
