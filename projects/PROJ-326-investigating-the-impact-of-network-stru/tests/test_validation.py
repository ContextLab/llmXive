"""
Tests for the validation module, specifically focusing on runtime validation (SC-002).
"""
import json
import pytest
from pathlib import Path
import tempfile
import os

from code.src.validation.validate_batch import (
    validate_runtime_duration,
    validate_provenance,
    validate_sensitivity_cutoffs,
    validate_batch
)

class TestRuntimeValidation:
    """Tests for SC-002 runtime validation logic."""

    def test_runtime_within_limit(self):
        """Test that a runtime under 60 mins passes."""
        result = {"runtime_duration_seconds": 3000.0}  # 50 mins
        assert validate_runtime_duration(result) is True

    def test_runtime_exceeds_limit(self):
        """Test that a runtime over 60 mins fails."""
        result = {"runtime_duration_seconds": 3601.0}  # 60m 1s
        assert validate_runtime_duration(result) is False

    def test_runtime_missing(self):
        """Test that missing runtime field fails."""
        result = {"status": "SUCCESS"}
        assert validate_runtime_duration(result) is False

    def test_runtime_zero(self):
        """Test that zero runtime passes."""
        result = {"runtime_duration_seconds": 0.0}
        assert validate_runtime_duration(result) is True

class TestProvenanceValidation:
    """Tests for Constitution Principle VI validation."""

    def test_provenance_complete(self):
        """Test that complete provenance passes."""
        result = {
            "generation_algorithm": "watts_strogatz",
            "parameter_values": {"k": 4, "p": 0.1}
        }
        assert validate_provenance(result) is True

    def test_provenance_missing_algorithm(self):
        """Test that missing algorithm fails."""
        result = {"parameter_values": {"k": 4}}
        assert validate_provenance(result) is False

    def test_provenance_missing_params(self):
        """Test that missing parameter_values fails."""
        result = {"generation_algorithm": "watts_strogatz"}
        assert validate_provenance(result) is False

class TestSensitivityValidation:
    """Tests for SC-005 sensitivity cutoffs validation."""

    @pytest.fixture
    def temp_sensitivity_file(self, tmp_path):
        file_path = tmp_path / "sensitivity_sweep.json"
        return file_path

    def test_sufficient_cutoffs(self, temp_sensitivity_file):
        """Test validation with >= 5 distinct cutoffs."""
        data = {"cutoffs": [0.1, 0.2, 0.3, 0.4, 0.5]}
        with open(temp_sensitivity_file, 'w') as f:
            json.dump(data, f)
        
        assert validate_sensitivity_cutoffs(temp_sensitivity_file) is True

    def test_insufficient_cutoffs(self, temp_sensitivity_file):
        """Test validation with < 5 distinct cutoffs."""
        data = {"cutoffs": [0.1, 0.2, 0.3, 0.4]}
        with open(temp_sensitivity_file, 'w') as f:
            json.dump(data, f)
        
        assert validate_sensitivity_cutoffs(temp_sensitivity_file) is False

    def test_duplicate_cutoffs_count_as_one(self, temp_sensitivity_file):
        """Test that duplicates reduce distinct count."""
        data = {"cutoffs": [0.1, 0.1, 0.2, 0.2, 0.3]}  # Only 3 distinct
        with open(temp_sensitivity_file, 'w') as f:
            json.dump(data, f)
        
        assert validate_sensitivity_cutoffs(temp_sensitivity_file) is False

    def test_file_not_found(self):
        """Test validation when file does not exist."""
        assert validate_sensitivity_cutoffs(Path("/nonexistent/path.json")) is False

class TestBatchValidation:
    """Integration tests for the full batch validation."""

    @pytest.fixture
    def temp_files(self, tmp_path):
        sim_path = tmp_path / "simulation_results.json"
        sens_path = tmp_path / "sensitivity_sweep.json"
        manifest_path = tmp_path / "global_batch_manifest.json"
        return sim_path, sens_path, manifest_path

    def test_full_validation_pass(self, temp_files):
        """Test a scenario where all validations pass."""
        sim_path, sens_path, manifest_path = temp_files
        
        # Setup valid simulation results
        sim_data = [
            {"runtime_duration_seconds": 100, "generation_algorithm": "er", "parameter_values": {}}
        ]
        with open(sim_path, 'w') as f:
            json.dump(sim_data, f)
        
        # Setup valid sensitivity
        sens_data = {"cutoffs": [0.1, 0.2, 0.3, 0.4, 0.5]}
        with open(sens_path, 'w') as f:
            json.dump(sens_data, f)
        
        # Setup valid manifest
        manifest_data = {"total_generated": 10}
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)

        report = validate_batch(sim_path, sens_path, manifest_path)

        assert report["sc_001_status"] == "PASS"
        assert report["sc_002_status"] == "PASS"
        assert report["sc_005_status"] == "PASS"

    def test_full_validation_fail_runtime(self, temp_files):
        """Test a scenario where runtime validation fails."""
        sim_path, sens_path, manifest_path = temp_files
        
        # Setup invalid simulation result (too slow)
        sim_data = [
            {"runtime_duration_seconds": 7200, "generation_algorithm": "er", "parameter_values": {}}
        ]
        with open(sim_path, 'w') as f:
            json.dump(sim_data, f)
        
        # Valid sensitivity and manifest
        with open(sens_path, 'w') as f:
            json.dump({"cutoffs": [0.1, 0.2, 0.3, 0.4, 0.5]}, f)
        with open(manifest_path, 'w') as f:
            json.dump({"total_generated": 10}, f)

        report = validate_batch(sim_path, sens_path, manifest_path)

        assert report["sc_002_status"] == "FAIL"
        assert "sc_002_error" in report["details"]