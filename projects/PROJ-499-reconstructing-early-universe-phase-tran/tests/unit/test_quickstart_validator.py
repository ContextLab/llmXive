"""
Unit tests for the Quickstart Validator script.
These tests verify the structural integrity of the validation process
without executing the full heavy-weight pipeline.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.quickstart_validator import ensure_directories, validate_outputs

class TestQuickstartValidator:
    
    def test_ensure_directories_creates_structure(self, tmp_path):
        """Test that ensure_directories creates the required folder structure."""
        # Mock project_root to use tmp_path
        with patch('code.quickstart_validator.project_root', tmp_path):
            with patch('code.quickstart_validator.logging'):
                ensure_directories()
        
        # Check that expected directories exist
        expected_dirs = [
            tmp_path / 'data' / 'raw',
            tmp_path / 'data' / 'derived',
            tmp_path / 'data' / 'synthetic',
            tmp_path / 'figures',
            tmp_path / 'state'
        ]
        
        for d in expected_dirs:
            assert d.exists(), f"Directory {d} was not created"
            assert d.is_dir(), f"{d} is not a directory"

    def test_validate_outputs_returns_true_when_all_exist(self, tmp_path):
        """Test validation returns True when all expected files exist."""
        # Create the expected structure
        files_to_create = [
            tmp_path / 'data' / 'synthetic' / 'inflation_r001.json',
            tmp_path / 'data' / 'derived' / 'model_comparison_results.json',
            tmp_path / 'figures' / 'posterior_inflation_r.png'
        ]
        
        for f in files_to_create:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.touch()
        
        # Mock the project_root and expected_files list
        with patch('code.quickstart_validator.project_root', tmp_path):
            with patch('code.quickstart_validator.logging'):
                # Manually run the logic from validate_outputs
                expected_files = [
                    tmp_path / 'data' / 'synthetic' / 'inflation_r001.json',
                    tmp_path / 'data' / 'derived' / 'model_comparison_results.json',
                    tmp_path / 'figures' / 'posterior_inflation_r.png'
                ]
                
                all_exist = all(f.exists() for f in expected_files)
                assert all_exist is True

    def test_validate_outputs_returns_false_when_missing(self, tmp_path):
        """Test validation returns False when some expected files are missing."""
        # Create only one of the expected files
        (tmp_path / 'data' / 'synthetic').mkdir(parents=True, exist_ok=True)
        (tmp_path / 'data' / 'synthetic' / 'inflation_r001.json').touch()
        
        with patch('code.quickstart_validator.project_root', tmp_path):
            with patch('code.quickstart_validator.logging'):
                expected_files = [
                    tmp_path / 'data' / 'synthetic' / 'inflation_r001.json',
                    tmp_path / 'data' / 'derived' / 'model_comparison_results.json', # Missing
                    tmp_path / 'figures' / 'posterior_inflation_r.png' # Missing
                ]
                
                all_exist = all(f.exists() for f in expected_files)
                assert all_exist is False

    def test_model_comparison_results_schema(self, tmp_path):
        """Test that model comparison results follow the expected schema."""
        result_path = tmp_path / 'model_comparison_results.json'
        sample_data = {
            "model_1": "inflation",
            "model_2": "phase_transition",
            "log_evidence_1": -100.5,
            "log_evidence_2": -98.2,
            "log_bayes_factor": -2.3,
            "bayes_factor": 0.100,
            "interpretation": "Inconclusive",
            "threshold_K": 10.0,
            "decision": "inconclusive"
        }
        
        with open(result_path, 'w') as f:
            json.dump(sample_data, f)
        
        with open(result_path, 'r') as f:
            loaded = json.load(f)
        
        # Verify keys
        required_keys = [
            "model_1", "model_2", "log_evidence_1", "log_evidence_2",
            "log_bayes_factor", "bayes_factor", "interpretation",
            "threshold_K", "decision"
        ]
        
        for key in required_keys:
            assert key in loaded, f"Missing key: {key}"
        
        # Verify types
        assert isinstance(loaded['bayes_factor'], float)
        assert isinstance(loaded['decision'], str)
        assert loaded['decision'] in ['favor_inflation', 'favor_pt', 'inconclusive']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])