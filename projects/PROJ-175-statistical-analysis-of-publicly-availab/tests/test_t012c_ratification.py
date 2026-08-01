"""
Tests for T012c: Spec Amendment Ratification Log
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to simulate the project structure for testing
# Since the script uses relative paths from its location, we'll mock the environment
from unittest.mock import patch, mock_open

# Import the module functions
# Note: We need to import from the actual file path structure
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code', 'data'))

# We will test the logic by mocking file system operations
from spec_ratification import check_plan_for_amendment, create_ratification_log, REQUIRED_AMENDMENT_KEYWORD

class TestT012cRatification:
    
    def test_plan_contains_amendment(self):
        """Test that a plan containing 'Critical Reframe' passes."""
        plan_content = """
        # Project Plan
        ## Critical Reframe
        This project uses Recipe1M embeddings as a proxy.
        """
        with patch('spec_ratification.PLAN_PATH') as mock_path:
            mock_path.exists.return_value = True
            with patch('builtins.open', mock_open(read_data=plan_content)):
                result = check_plan_for_amendment()
                assert result is True

    def test_plan_missing_amendment_raises(self):
        """Test that a plan without 'Critical Reframe' raises ValueError."""
        plan_content = """
        # Project Plan
        ## Standard Approach
        This project uses FlavorDB.
        """
        with patch('spec_ratification.PLAN_PATH') as mock_path:
            mock_path.exists.return_value = True
            with patch('builtins.open', mock_open(read_data=plan_content)):
                with pytest.raises(ValueError) as excinfo:
                    check_plan_for_amendment()
                assert REQUIRED_AMENDMENT_KEYWORD in str(excinfo.value)

    def test_plan_file_missing_raises(self):
        """Test that a missing plan file raises FileNotFoundError."""
        with patch('spec_ratification.PLAN_PATH') as mock_path:
            mock_path.exists.return_value = False
            with pytest.raises(FileNotFoundError):
                check_plan_for_amendment()

    def test_create_log_when_missing(self, tmp_path):
        """Test creating a new ratification log."""
        # Mock the output path
        test_log_path = tmp_path / "amendment_ratification_log.json"
        
        with patch('spec_ratification.OUTPUT_PATH', test_log_path):
            with patch('spec_ratification.PLAN_PATH') as mock_plan:
                mock_plan.exists.return_value = True
                plan_content = f"Contains {REQUIRED_AMENDMENT_KEYWORD}"
                with patch('builtins.open', mock_open(read_data=plan_content)):
                    result = create_ratification_log()
                    
                    assert result is True
                    assert test_log_path.exists()
                    
                    with open(test_log_path, 'r') as f:
                        log_data = json.load(f)
                    
                    assert log_data["status"] == "BOOTSTRAPPED"
                    assert "FR-001" in log_data["amendment"]
                    assert "Plan Critical Reframe detected" in log_data["rationale"]

    def test_log_already_exists_valid(self, tmp_path):
        """Test that existing valid log is not overwritten."""
        existing_log = {
            "status": "RATIFIED",
            "amendment": "FR-001/FR-004",
            "rationale": "Previous run"
        }
        test_log_path = tmp_path / "amendment_ratification_log.json"
        
        with open(test_log_path, 'w') as f:
            json.dump(existing_log, f)
        
        with patch('spec_ratification.OUTPUT_PATH', test_log_path):
            # Should return True without modifying file
            result = create_ratification_log()
            assert result is True
            
            with open(test_log_path, 'r') as f:
                current_data = json.load(f)
            
            assert current_data["status"] == "RATIFIED"