import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_validation import check_visual_indistinguishability, DataValidationError

class TestVisualIndistinguishability:
    
    def test_valid_pretest_results_pass(self):
        """Test that a valid pretest file with p > 0.05 passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pretest_file = Path(tmpdir) / "results.json"
            data = {
                "p_value": 0.85,
                "description": "Test data"
            }
            with open(pretest_file, 'w') as f:
                json.dump(data, f)
                
            passed, p_val = check_visual_indistinguishability(str(pretest_file))
            assert passed is True
            assert p_val == 0.85

    def test_significant_difference_raises_error(self):
        """Test that p <= 0.05 raises DataValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pretest_file = Path(tmpdir) / "results.json"
            data = {
                "p_value": 0.03,
                "description": "Significant difference"
            }
            with open(pretest_file, 'w') as f:
                json.dump(data, f)
                
            with pytest.raises(DataValidationError) as exc_info:
                check_visual_indistinguishability(str(pretest_file))
                
            assert "FAILED" in str(exc_info.value)
            assert "p-value" in str(exc_info.value)

    def test_missing_file_raises_error(self):
        """Test that a missing file raises DataValidationError."""
        with pytest.raises(DataValidationError) as exc_info:
            check_visual_indistinguishability("/nonexistent/path/results.json")
            
        assert "not found" in str(exc_info.value)

    def test_missing_p_value_raises_error(self):
        """Test that missing p_value key raises DataValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pretest_file = Path(tmpdir) / "results.json"
            data = {
                "description": "No p-value here"
            }
            with open(pretest_file, 'w') as f:
                json.dump(data, f)
                
            with pytest.raises(DataValidationError) as exc_info:
                check_visual_indistinguishability(str(pretest_file))
                
            assert "missing 'p_value'" in str(exc_info.value)

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises DataValidationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pretest_file = Path(tmpdir) / "results.json"
            with open(pretest_file, 'w') as f:
                f.write("not valid json")
                
            with pytest.raises(DataValidationError) as exc_info:
                check_visual_indistinguishability(str(pretest_file))
                
            assert "Invalid JSON" in str(exc_info.value)

    def test_boundary_p_value_exactly_0_05(self):
        """Test that p = 0.05 exactly raises error (must be > 0.05)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pretest_file = Path(tmpdir) / "results.json"
            data = {
                "p_value": 0.05,
                "description": "Boundary test"
            }
            with open(pretest_file, 'w') as f:
                json.dump(data, f)
                
            with pytest.raises(DataValidationError) as exc_info:
                check_visual_indistinguishability(str(pretest_file))
                
            assert "FAILED" in str(exc_info.value)

    def test_p_value_just_above_threshold(self):
        """Test that p = 0.0501 passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pretest_file = Path(tmpdir) / "results.json"
            data = {
                "p_value": 0.0501,
                "description": "Just above threshold"
            }
            with open(pretest_file, 'w') as f:
                json.dump(data, f)
                
            passed, p_val = check_visual_indistinguishability(str(pretest_file))
            assert passed is True