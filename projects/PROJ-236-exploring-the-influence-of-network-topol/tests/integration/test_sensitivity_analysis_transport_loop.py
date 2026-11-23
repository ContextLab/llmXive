"""
Integration test for the sensitivity analysis transport loop (T025c).

The test verifies that:
* The script creates ``data/analysis/sensitivity_results.csv``.
* The CSV contains one row per cutoff value defined in the simulation config.
* Each row includes the ``cutoff`` column and the expected transport fields.
"""

import csv
from pathlib import Path

import pytest
import yaml
from unittest import mock

# The module under test
from sensitivity_analysis_transport_loop import main as sensitivity_main


@pytest.fixture
def temp_simulation_config(tmp_path):
    """
    Write a minimal ``simulation_config.yaml`` containing a short list of
    cutoff values.  The file is placed at the canonical location
    ``code/simulation_config.yaml`` so that ``load_simulation_config`` picks it up.
    """
    config_dir = Path("code")
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "simulation_config.yaml"
    config_data = {"cutoff_values": [0.8, 1.0, 1.2]}
    with config_path.open("w") as f:
        yaml.safe_dump(config_data, f)
    yield config_path
    # Cleanup after the test
    if config_path.is_file():
        config_path.unlink()


def _fake_transport_run(cutoff: float):
    """
    Create a dummy ``transport_results.csv`` that mimics the output of the
    transport solver for a given cutoff.  This function is used to replace
    ``subprocess.run`` during the test.
    """
    transport_path = Path("data/transport/transport_results.csv")
    transport_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "network_id",
        "kappa",
        "error_estimate",
        "convergence_status",
        "runtime",
        "regime_flag",
    ]
    with transport_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "network_id": f"net_{cutoff}",
                "kappa": f"{1.0 + cutoff:.3f}",
                "error_estimate": "0.01",
                "convergence_status": "converged",
                "runtime": "5",
                "regime_flag": "none",
            }
        )


def test_sensitivity_analysis_transport_loop_creates_csv(
    tmp_path, temp_simulation_config, monkeypatch
):
    """
    Run the sensitivity analysis loop with a mocked transport solver.
    Verify that the output CSV exists and contains exactly three rows,
    one for each cutoff value.
    """
    # ------------------------------------------------------------------
    # Mock ``subprocess.run`` so that the real transport solver is not
    # invoked.  The mock writes a deterministic transport CSV for the
    # supplied cutoff.
    # ------------------------------------------------------------------
    def mock_run(cmd, check):
        # The cutoff argument is the last element in the command list.
        cutoff_str = cmd[-1]
        _fake_transport_run(float(cutoff_str))

    monkeypatch.setattr("subprocess.run", mock_run)

    # Execute the sensitivity analysis loop.
    sensitivity_main()

    # ------------------------------------------------------------------
    # Validate the generated CSV.
    # ------------------------------------------------------------------
    output_path = Path("data/analysis/sensitivity_results.csv")
    assert output_path.is_file(), "sensitivity_results.csv was not created"

    with output_path.open() as f:
        rows = list(csv.DictReader(f))

    # Expect one row per cutoff defined in the config.
    expected_cutoffs = [0.8, 1.0, 1.2]
    assert len(rows) == len(expected_cutoffs), (
        f"Expected {len(expected_cutoffs)} rows, found {len(rows)}"
    )

    # Verify that each row contains the correct cutoff value and the
    # transport fields.
    for row in rows:
        assert "cutoff" in row
        assert float(row["cutoff"]) in expected_cutoffs
        for field in [
            "network_id",
            "kappa",
            "error_estimate",
            "convergence_status",
            "runtime",
            "regime_flag",
        ]:
            assert field in row, f"Missing field '{field}' in sensitivity CSV"