import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path if running standalone, though conftest handles this in project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.analysis.save_results import validate_result_structure, save_correlation_results
from code.src.utils.config import get_results_dir

class TestSaveResults:
    
    @pytest.fixture
    def valid_result(self):
        return {
            "correlation_coefficient": 0.45,
            "p_value": 0.03,
            "adjusted_p_value": 0.06,
            "confidence_interval": [0.12, 0.78]
        }

    @pytest.fixture
    def valid_results_list(self, valid_result):
        return [valid_result, {
            "correlation_coefficient": -0.12,
            "p_value": 0.45,
            "adjusted_p_value": 0.50,
            "confidence_interval": [-0.45, 0.21]
        }]

    def test_validate_result_structure_valid(self, valid_result):
        assert validate_result_structure(valid_result) is True

    def test_validate_result_structure_missing_key(self, valid_result):
        del valid_result["p_value"]
        assert validate_result_structure(valid_result) is False

    def test_validate_result_structure_wrong_type_coeff(self, valid_result):
        valid_result["correlation_coefficient"] = "not a number"
        assert validate_result_structure(valid_result) is False

    def test_validate_result_structure_wrong_ci_type(self, valid_result):
        valid_result["confidence_interval"] = [0.1] # Too short
        assert validate_result_structure(valid_result) is False

    def test_validate_result_structure_wrong_ci_tuple(self, valid_result):
        valid_result["confidence_interval"] = (0.1, 0.9) # Tuple is valid input but should convert
        assert validate_result_structure(valid_result) is True

    def test_save_correlation_results_creates_file(self, valid_results_list, tmp_path):
        # Mock get_results_dir to return a temporary directory
        with patch('code.src.analysis.save_results.get_results_dir', return_value=tmp_path):
            with patch('code.src.analysis.save_results.ensure_directories'):
                output_path = save_correlation_results(valid_results_list, "test_output.json")
                
                assert output_path.exists()
                assert output_path.name == "test_output.json"
                
                # Verify content
                with open(output_path, 'r') as f:
                    data = json.load(f)
                
                assert len(data) == 2
                assert data[0]["correlation_coefficient"] == 0.45
                assert isinstance(data[0]["confidence_interval"], list)

    def test_save_correlation_results_invalid_data_raises(self, valid_result, tmp_path):
        invalid_result = valid_result.copy()
        invalid_result["p_value"] = "invalid"
        
        with patch('code.src.analysis.save_results.get_results_dir', return_value=tmp_path):
            with patch('code.src.analysis.save_results.ensure_directories'):
                with pytest.raises(ValueError, match="failed schema validation"):
                    save_correlation_results([invalid_result], "test_fail.json")