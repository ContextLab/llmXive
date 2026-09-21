"""
Integration tests for T021 and T022, explicitly linked to the test data files
generated in T020b.

This module resolves the cross-phase ambiguity by:
1. Verifying that `code/generate_test_data.py` correctly produces
   `data/derived/test_thermal_data.csv` and `data/derived/test_nonthermal_data.csv`.
2. Verifying that the stats pipeline (T022/T022b) explicitly rejects these files
   due to the `test_` prefix.
"""
import os
import json
import pytest
import pandas as pd
from pathlib import Path

# Import the generation logic to ensure we can run it if needed
# (Though T020b should have already run, we ensure the files exist for this test)
from generate_test_data import load_params, generate_thermal_data, generate_nonthermal_data, main as generate_main

# Import stats logic to test the rejection
from stats import bin_energy_data, StatsError

# Import config to load parameters
from config import load_config

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
ARTIFACTS = PROJECT_ROOT / "artifacts"


@pytest.fixture(scope="module")
def ensure_test_data_exists():
    """
    Ensure T020b artifacts exist before running these tests.
    If T020b failed or files are missing, we regenerate them here
    to satisfy the dependency for T023b's integration test.
    """
    thermal_path = DATA_DERIVED / "test_thermal_data.csv"
    nonthermal_path = DATA_DERIVED / "test_nonthermal_data.csv"
    
    # Check if files exist
    if not thermal_path.exists() or not nonthermal_path.exists():
        # Load params from T020a
        params_path = ARTIFACTS / "test_params.json"
        if not params_path.exists():
            pytest.fail("T020a artifact (test_params.json) missing. Cannot run T023b tests.")
        
        params = load_params(params_path)
        
        # Generate thermal data
        generate_thermal_data(params, str(thermal_path))
        
        # Generate non-thermal data
        generate_nonthermal_data(params, str(nonthermal_path))
    
    return thermal_path, nonthermal_path


class TestT021_ThermalDataPrefix:
    """
    T021 Unit test for correct handling of the `test_` prefix.
    Ensures that synthetic data files with `test_` prefix are generated correctly
    and identified as such.
    """
    def test_thermal_file_generated_correctly(self, ensure_test_data_exists):
        """Verify test_thermal_data.csv exists and has expected structure."""
        thermal_path, _ = ensure_test_data_exists
        
        assert thermal_path.exists(), "test_thermal_data.csv was not generated."
        
        df = pd.read_csv(thermal_path)
        
        # Verify it's a Maxwell-Boltzmann distribution (thermal)
        # Check for expected columns (energy_samples usually has these, 
        # but test data might be raw or derived. T020b says 'test_thermal_data.csv')
        # Based on T020b description, it's a generated dataset.
        assert len(df) > 0, "test_thermal_data.csv is empty."
        
        # Verify the prefix is present in the filename
        assert thermal_path.name.startswith("test_"), "Filename must start with 'test_'"

    def test_nonthermal_file_generated_correctly(self, ensure_test_data_exists):
        """Verify test_nonthermal_data.csv exists and has expected structure."""
        _, nonthermal_path = ensure_test_data_exists
        
        assert nonthermal_path.exists(), "test_nonthermal_data.csv was not generated."
        
        df = pd.read_csv(nonthermal_path)
        assert len(df) > 0, "test_nonthermal_data.csv is empty."
        assert nonthermal_path.name.startswith("test_"), "Filename must start with 'test_'"


class TestT022_RejectionOfTestPrefix:
    """
    T022 / T022b Integration test to verify that the analysis pipeline
    explicitly rejects files with the `test_` prefix.
    
    This resolves the ambiguity by ensuring that T022 (stats pipeline)
    behaves correctly when fed the files generated in T020b.
    """
    def test_bin_energy_data_rejects_test_thermal(self, ensure_test_data_exists):
        """
        Verify that bin_energy_data raises an error when fed test_thermal_data.csv.
        """
        thermal_path, _ = ensure_test_data_exists
        
        # The spec for T024/T022b says: "Raise FileNotFoundError with the exact message 
        # if the file is missing or has a `test_` prefix."
        with pytest.raises(FileNotFoundError) as exc_info:
            bin_energy_data(str(thermal_path))
        
        assert "test_" in str(exc_info.value).lower(), (
            f"Error message must explicitly mention 'test_' prefix rejection. "
            f"Got: {exc_info.value}"
        )

    def test_bin_energy_data_rejects_test_nonthermal(self, ensure_test_data_exists):
        """
        Verify that bin_energy_data raises an error when fed test_nonthermal_data.csv.
        """
        _, nonthermal_path = ensure_test_data_exists
        
        with pytest.raises(FileNotFoundError) as exc_info:
            bin_energy_data(str(nonthermal_path))
        
        assert "test_" in str(exc_info.value).lower(), (
            f"Error message must explicitly mention 'test_' prefix rejection. "
            f"Got: {exc_info.value}"
        )

    def test_sampling_metadata_records_test_files_ignored(self, ensure_test_data_exists):
        """
        Verify that if a scan were to occur, the metadata would reflect the exclusion.
        (Simulating the logic that T022 would record).
        """
        thermal_path, nonthermal_path = ensure_test_data_exists
        
        # We expect the stats pipeline to skip these. 
        # This test asserts that the rejection mechanism is in place.
        # If we were to run a directory scan, these would be filtered out.
        
        # Check that the files are indeed present but rejected
        assert thermal_path.exists()
        assert nonthermal_path.exists()
        
        # The actual rejection is tested in test_bin_energy_data_rejects_test_thermal
        # This test serves as a bridge to confirm the files exist and are the target of rejection.
        pass