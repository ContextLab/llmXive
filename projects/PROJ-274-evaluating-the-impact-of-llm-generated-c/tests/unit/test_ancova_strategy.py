"""
Unit tests for the ANCOVA Strategy Implementation (T021h).

These tests verify that the strategy configuration is generated correctly
and that the module handles missing/invalid data as expected.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.ancova_strategy import (
    validate_covariate_structure,
    define_ancova_model,
    generate_strategy_config,
    OUTPUT_CONFIG_PATH,
    COVARIATES_INPUT_PATH
)


class TestValidateCovariateStructure:
    def test_valid_structure(self):
        data = [
            {"repo_id": "r1", "loc": 100, "cc": 5, "doc_quality": 3},
            {"repo_id": "r2", "loc": 200, "cc": 10, "doc_quality": 2}
        ]
        assert validate_covariate_structure(data) is True

    def test_missing_keys(self):
        data = [
            {"repo_id": "r1", "loc": 100} # Missing cc and doc_quality
        ]
        assert validate_covariate_structure(data) is False

    def test_empty_list(self):
        assert validate_covariate_structure([]) is False

    def test_non_numeric_loc(self):
        data = [
            {"repo_id": "r1", "loc": "high", "cc": 5, "doc_quality": 3}
        ]
        assert validate_covariate_structure(data) is False

    def test_not_a_list(self):
        assert validate_covariate_structure({"repo_id": "r1"}) is False


class TestDefineAncovaModel:
    def test_model_structure(self):
        model = define_ancova_model()
        assert model["model_type"] == "ANCOVA"
        assert model["dependent_variable"] == "task_completion_time"
        assert model["independent_variable"] == "condition"
        assert len(model["covariates"]) == 3
        
        cov_names = [c["name"] for c in model["covariates"]]
        assert "loc" in cov_names
        assert "cc" in cov_names
        assert "doc_quality" in cov_names

        assert "loc + cc + doc_quality" in model["formula"]


class TestGenerateStrategyConfig:
    def test_config_generation(self, mocker, tmp_path):
        # Mock the COVARIATES_INPUT_PATH to point to a temp file
        mock_data = [
            {"repo_id": "test_repo", "loc": 500, "cc": 20, "doc_quality": 2}
        ]
        
        # Create a temporary file for input
        temp_input = tmp_path / "repo_covariates.json"
        with open(temp_input, 'w') as f:
            json.dump(mock_data, f)
        
        # Mock the global path
        import code.analysis.ancova_strategy as module
        original_path = module.COVARIATES_INPUT_PATH
        module.COVARIATES_INPUT_PATH = temp_input
        
        try:
            config = module.generate_strategy_config()
            
            assert "strategy_id" in config
            assert config["total_repos"] == 1
            assert config["covariate_summary"]["loc_stats"]["min"] == 500
            assert "model_definition" in config
            assert config["model_definition"]["formula"] is not None
        finally:
            module.COVARIATES_INPUT_PATH = original_path

    def test_missing_input_file(self, mocker):
        import code.analysis.ancova_strategy as module
        original_path = module.COVARIATES_INPUT_PATH
        
        # Point to a non-existent file
        module.COVARIATES_INPUT_PATH = Path("/nonexistent/path/file.json")
        
        try:
            with pytest.raises(FileNotFoundError):
                module.generate_strategy_config()
        finally:
            module.COVARIATES_INPUT_PATH = original_path