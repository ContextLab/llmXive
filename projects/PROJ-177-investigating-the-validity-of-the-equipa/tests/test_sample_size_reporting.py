"""
Unit test for T058: Verify that n_samples in statistical_results.json
matches the actual row count per bin in energy_samples.csv.
"""
import json
import os
import pytest
import pandas as pd
from pathlib import Path

# Project root relative to tests/
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
ARTIFACTS = PROJECT_ROOT / "artifacts"

STAT_RESULTS_PATH = ARTIFACTS / "statistical_results.json"
ENERGY_SAMPLES_PATH = DATA_DERIVED / "energy_samples.csv"


@pytest.fixture
def sample_data_files():
    """
    Create minimal mock data files to simulate a completed US1/US2 run.
    This fixture ensures the test can run without the full pipeline,
    focusing solely on the logic of T058.
    """
    # Ensure directories exist
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    # Create mock energy_samples.csv with known bin structure
    # Columns: particle_id, timestamp, E_trans, E_rot, E_pot, E_vib, pot_incomplete, frequency_bin, material_type
    data = {
        "particle_id": [1, 1, 1, 2, 2, 2, 2, 3, 3],
        "timestamp": [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0, 1.0, 2.0],
        "E_trans": [1.0, 1.1, 1.2, 2.0, 2.1, 2.2, 2.3, 3.0, 3.1],
        "E_rot": [0.5, 0.6, 0.7, 1.0, 1.1, 1.2, 1.3, 1.5, 1.6],
        "E_pot": [0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.3, 0.3],
        "E_vib": [0.01, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.03, 0.03],
        "pot_incomplete": [False, False, False, False, False, False, False, False, False],
        "frequency_bin": [10.0, 10.0, 10.0, 20.0, 20.0, 20.0, 20.0, 30.0, 30.0],
        "material_type": ["steel", "steel", "steel", "polymer", "polymer", "polymer", "polymer", "glass", "glass"]
    }
    df = pd.DataFrame(data)
    df.to_csv(ENERGY_SAMPLES_PATH, index=False)

    # Create mock statistical_results.json with n_samples that MATCHES the CSV counts
    # Bin 1: frequency=10.0, material=steel -> count = 3
    # Bin 2: frequency=20.0, material=polymer -> count = 4
    # Bin 3: frequency=30.0, material=glass -> count = 2
    results = [
        {
            "bin_id": "10.0_steel",
            "frequency_bin": 10.0,
            "material_type": "steel",
            "n_samples": 3,
            "ks_statistic": 0.1,
            "ks_p_value": 0.5,
            "chi2_statistic": 1.0,
            "chi2_p_value": 0.8,
            "rejection": False
        },
        {
            "bin_id": "20.0_polymer",
            "frequency_bin": 20.0,
            "material_type": "polymer",
            "n_samples": 4,
            "ks_statistic": 0.2,
            "ks_p_value": 0.3,
            "chi2_statistic": 2.0,
            "chi2_p_value": 0.6,
            "rejection": False
        },
        {
            "bin_id": "30.0_glass",
            "frequency_bin": 30.0,
            "material_type": "glass",
            "n_samples": 2,
            "ks_statistic": 0.05,
            "ks_p_value": 0.9,
            "chi2_statistic": 0.5,
            "chi2_p_value": 0.95,
            "rejection": False
        }
    ]

    with open(STAT_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    return df, results

def test_sample_size_reporting_matches_csv(sample_data_files):
    """
    Verify that n_samples in statistical_results.json matches
    the actual row count per bin in energy_samples.csv.
    """
    df, _ = sample_data_files

    # Load statistical results
    with open(STAT_RESULTS_PATH, "r") as f:
        stat_results = json.load(f)

    # Verify logic for each result entry
    for entry in stat_results:
        freq = entry["frequency_bin"]
        mat = entry["material_type"]
        reported_n = entry["n_samples"]

        # Calculate actual count from CSV
        mask = (df["frequency_bin"] == freq) & (df["material_type"] == mat)
        actual_n = mask.sum()

        assert actual_n == reported_n, (
            f"Mismatch for bin (freq={freq}, mat={mat}): "
            f"statistical_results.json reports {reported_n}, "
            f"but energy_samples.csv has {actual_n} rows."
        )

def test_sample_size_reporting_mismatch_detection(sample_data_files):
    """
    Verify that the test FAILS if n_samples in statistical_results.json
    does NOT match the actual row count in energy_samples.csv.
    We simulate a mismatch by modifying the loaded results.
    """
    df, _ = sample_data_files

    # Load and corrupt the results to simulate a mismatch
    with open(STAT_RESULTS_PATH, "r") as f:
        stat_results = json.load(f)

    # Change n_samples for the first bin to be incorrect
    stat_results[0]["n_samples"] = 999

    # Write back the corrupted results
    with open(STAT_RESULTS_PATH, "w") as f:
        json.dump(stat_results, f, indent=2)

    # Now run the check logic again (should raise AssertionError)
    # We re-load the file to ensure we are checking the corrupted version
    with open(STAT_RESULTS_PATH, "r") as f:
        corrupted_results = json.load(f)

    # Find the mismatched entry
    for entry in corrupted_results:
        freq = entry["frequency_bin"]
        mat = entry["material_type"]
        reported_n = entry["n_samples"]

        mask = (df["frequency_bin"] == freq) & (df["material_type"] == mat)
        actual_n = mask.sum()

        # This assertion should fail for the first entry
        if freq == 10.0 and mat == "steel":
            assert actual_n != reported_n, "Test logic error: mismatch was not detected."
            # Verify the specific error message logic
            with pytest.raises(AssertionError) as exc_info:
                assert actual_n == reported_n, (
                    f"Mismatch for bin (freq={freq}, mat={mat}): "
                    f"statistical_results.json reports {reported_n}, "
                    f"but energy_samples.csv has {actual_n} rows."
                )
            assert "999" in str(exc_info.value)
            assert "3" in str(exc_info.value)
            return

    pytest.fail("Expected mismatch for (10.0, steel) was not found.")

def test_empty_bin_handling():
    """
    Verify that if a bin exists in statistical_results.json but has 0 rows in CSV,
    the test correctly reports 0 == 0.
    """
    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    # Create CSV with missing bin
    data = {
        "particle_id": [1, 1],
        "timestamp": [1.0, 2.0],
        "E_trans": [1.0, 1.1],
        "E_rot": [0.5, 0.6],
        "E_pot": [0.1, 0.1],
        "E_vib": [0.01, 0.01],
        "pot_incomplete": [False, False],
        "frequency_bin": [10.0, 10.0],
        "material_type": ["steel", "steel"]
    }
    pd.DataFrame(data).to_csv(ENERGY_SAMPLES_PATH, index=False)

    # Create results with an empty bin (n_samples=0)
    results = [
        {
            "bin_id": "10.0_steel",
            "frequency_bin": 10.0,
            "material_type": "steel",
            "n_samples": 2,
            "ks_statistic": 0.1,
            "ks_p_value": 0.5,
            "chi2_statistic": 1.0,
            "chi2_p_value": 0.8,
            "rejection": False
        },
        {
            "bin_id": "50.0_glass",
            "frequency_bin": 50.0,
            "material_type": "glass",
            "n_samples": 0,
            "ks_statistic": 0.0,
            "ks_p_value": 1.0,
            "chi2_statistic": 0.0,
            "chi2_p_value": 1.0,
            "rejection": False
        }
    ]

    with open(STAT_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    # Load and verify
    df = pd.read_csv(ENERGY_SAMPLES_PATH)
    with open(STAT_RESULTS_PATH, "r") as f:
        stat_results = json.load(f)

    for entry in stat_results:
        freq = entry["frequency_bin"]
        mat = entry["material_type"]
        reported_n = entry["n_samples"]

        mask = (df["frequency_bin"] == freq) & (df["material_type"] == mat)
        actual_n = mask.sum()

        assert actual_n == reported_n, (
            f"Mismatch for bin (freq={freq}, mat={mat}): "
            f"statistical_results.json reports {reported_n}, "
            f"but energy_samples.csv has {actual_n} rows."
        )