"""
Unit tests for the download module (T019).

Tests synthetic data generation and parameter handling.
"""
import json
import os
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from code.download import (
    generate_synthetic_meta_analyses,
    save_simulation_parameters,
    save_synthetic_data,
    run_fallback_simulation,
    IOANNIDIS_PARAMS,
    DataAcquisitionError
)

class TestSyntheticDataGeneration:
    """Tests for synthetic data generation logic."""

    def test_generate_correct_number_of_meta_analyses(self):
        """Test that the correct number of meta-analyses are generated."""
        num_meta = 10
        meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=num_meta, seed=42)
        
        assert len(meta_analyses) == num_meta

    def test_generate_studies_within_range(self):
        """Test that study counts are within specified range."""
        meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=5, seed=42)
        
        for meta in meta_analyses:
            k = meta["num_studies"]
            assert 3 <= k <= 50, f"Study count {k} out of range [3, 50]"

    def test_effect_sizes_have_reasonable_variance(self):
        """Test that generated effect sizes have reasonable variance."""
        meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=10, seed=42)
        
        all_effects = []
        for meta in meta_analyses:
            effects = [s["effect_size"] for s in meta["studies"]]
            all_effects.extend(effects)
        
        assert len(all_effects) > 0
        mean_effect = np.mean(all_effects)
        std_effect = np.std(all_effects)
        
        # Mean should be around 0.4 (0.3 + 0.1 bias)
        assert 0.3 < mean_effect < 0.5, f"Mean effect {mean_effect} outside expected range"
        # Std should be > 0 due to tau^2 + sampling error
        assert std_effect > 0.1, f"Std effect {std_effect} too small"

    def test_se_values_are_positive(self):
        """Test that all standard errors are positive."""
        meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=5, seed=42)
        
        for meta in meta_analyses:
            for study in meta["studies"]:
                assert study["se"] > 0, f"SE {study['se']} is not positive"

    def test_sample_sizes_are_reasonable(self):
        """Test that sample sizes are within expected range."""
        meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=5, seed=42)
        
        for meta in meta_analyses:
            for study in meta["studies"]:
                assert 50 <= study["sample_size"] <= 1000, \
                    f"Sample size {study['sample_size']} out of range [50, 1000]"

    def test_events_less_than_or_equal_to_total(self):
        """Test that event counts do not exceed total sample size."""
        meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=5, seed=42)
        
        for meta in meta_analyses:
            for study in meta["studies"]:
                assert study["n_events"] <= study["n_total"], \
                    f"Events {study['n_events']} exceeds total {study['n_total']}"

class TestParameterSaving:
    """Tests for parameter saving functionality."""

    def test_save_parameters_creates_valid_json(self):
        """Test that parameters are saved as valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            params_path = os.path.join(tmpdir, "params.json")
            save_simulation_parameters(IOANNIDIS_PARAMS, params_path)
            
            assert os.path.exists(params_path)
            
            with open(params_path, 'r') as f:
                loaded_params = json.load(f)
            
            assert loaded_params == IOANNIDIS_PARAMS

    def test_save_parameters_creates_directory(self):
        """Test that missing directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "nested", "dir", "params.json")
            save_simulation_parameters(IOANNIDIS_PARAMS, nested_path)
            
            assert os.path.exists(nested_path)

class TestSyntheticDataSaving:
    """Tests for synthetic data saving functionality."""

    def test_save_creates_individual_files(self):
        """Test that each meta-analysis is saved to a separate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=3, seed=42)
            save_synthetic_data(meta_analyses, tmpdir)
            
            files = os.listdir(tmpdir)
            assert len(files) == 3
            assert all(f.endswith('.json') for f in files)

    def test_save_files_contain_valid_data(self):
        """Test that saved files contain valid meta-analysis data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_analyses = generate_synthetic_meta_analyses(num_meta_analyses=2, seed=42)
            save_synthetic_data(meta_analyses, tmpdir)
            
            for meta in meta_analyses:
                filepath = os.path.join(tmpdir, f"{meta['meta_id']}.json")
                assert os.path.exists(filepath)
                
                with open(filepath, 'r') as f:
                    loaded = json.load(f)
                
                assert loaded["meta_id"] == meta["meta_id"]
                assert loaded["num_studies"] == meta["num_studies"]
                assert len(loaded["studies"]) == meta["num_studies"]

class TestFallbackSimulation:
    """Tests for the fallback simulation process."""

    def test_run_fallback_creates_all_outputs(self):
        """Test that fallback simulation creates all required outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            params_path = run_fallback_simulation(
                num_meta_analyses=5,
                params=IOANNIDIS_PARAMS,
                output_dir=tmpdir
            )
            
            # Check params file
            assert os.path.exists(params_path)
            assert params_path.endswith("simulation_params.json")
            
            # Check data files
            files = os.listdir(tmpdir)
            json_files = [f for f in files if f.endswith('.json') and f != 'simulation_params.json']
            assert len(json_files) == 5

    def test_run_fallback_uses_correct_parameters(self):
        """Test that fallback simulation uses the provided parameters."""
        custom_params = IOANNIDIS_PARAMS.copy()
        custom_params["mean_effect"] = 0.5
        custom_params["tau_sq"] = 0.1
        
        with tempfile.TemporaryDirectory() as tmpdir:
            params_path = run_fallback_simulation(
                num_meta_analyses=3,
                params=custom_params,
                output_dir=tmpdir
            )
            
            with open(params_path, 'r') as f:
                saved_params = json.load(f)
            
            assert saved_params["mean_effect"] == 0.5
            assert saved_params["tau_sq"] == 0.1

class TestDataAcquisitionErrorHandling:
    """Tests for error handling in data acquisition."""

    def test_data_acquisition_error_is_raised(self):
        """Test that DataAcquisitionError is raised for failed fetches."""
        with pytest.raises(DataAcquisitionError):
            raise DataAcquisitionError("Test error message")

    def test_error_message_is_preserved(self):
        """Test that error messages are preserved."""
        error_msg = "Cochrane API unavailable"
        with pytest.raises(DataAcquisitionError) as exc_info:
            raise DataAcquisitionError(error_msg)
        
        assert str(exc_info.value) == error_msg
