"""
Unit tests for the power analysis verification module (T048).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.analysis.verify_power_analysis import verify_power_analysis_json, verify_report_reference
from code.config import Config

class TestVerifyPowerAnalysisJSON:
    def test_valid_json_with_required_keys(self, tmp_path):
        """Test verification of a valid power analysis JSON file."""
        # Create a temporary file with valid data
        power_file = tmp_path / "power_analysis.json"
        data = {
            "min_N_required": 20,
            "effect_size": 0.15,
            "alpha": 0.05,
            "power": 0.8,
            "method": "FTestPower"
        }
        with open(power_file, 'w') as f:
            json.dump(data, f)
            
        # Mock config to point to temp file
        class MockConfig:
            POWER_ANALYSIS_PATH = str(power_file)
            
        result = verify_power_analysis_json(MockConfig())
        assert result["min_N_required"] == 20
        
    def test_missing_required_key(self, tmp_path):
        """Test that verification fails if a required key is missing."""
        power_file = tmp_path / "power_analysis.json"
        data = {
            "min_N_required": 20,
            "effect_size": 0.15
            # Missing alpha, power, method
        }
        with open(power_file, 'w') as f:
            json.dump(data, f)
            
        class MockConfig:
            POWER_ANALYSIS_PATH = str(power_file)
            
        with pytest.raises(KeyError):
            verify_power_analysis_json(MockConfig())
            
    def test_file_not_found(self, tmp_path):
        """Test that verification fails if the file does not exist."""
        class MockConfig:
            POWER_ANALYSIS_PATH = str(tmp_path / "nonexistent.json")
            
        with pytest.raises(FileNotFoundError):
            verify_power_analysis_json(MockConfig())
            
    def test_invalid_json(self, tmp_path):
        """Test that verification fails for invalid JSON."""
        power_file = tmp_path / "power_analysis.json"
        with open(power_file, 'w') as f:
            f.write("not valid json")
            
        class MockConfig:
            POWER_ANALYSIS_PATH = str(power_file)
            
        with pytest.raises(json.JSONDecodeError):
            verify_power_analysis_json(MockConfig())
            
class TestVerifyReportReference:
    def test_report_contains_value(self, tmp_path):
        """Test that report verification succeeds when value is present."""
        # Create temp report
        report_file = tmp_path / "results.md"
        content = "# Results\n\nThe minimum N required is 20.\n"
        with open(report_file, 'w') as f:
            f.write(content)
            
        power_data = {"min_N_required": 20}
        
        class MockConfig:
            RESULTS_REPORT_PATH = str(report_file)
            
        assert verify_report_reference(MockConfig(), power_data) is True
        
    def test_report_missing_value(self, tmp_path):
        """Test that report verification fails when value is missing."""
        report_file = tmp_path / "results.md"
        content = "# Results\n\nNo sample size calculation performed.\n"
        with open(report_file, 'w') as f:
            f.write(content)
            
        power_data = {"min_N_required": 20}
        
        class MockConfig:
            RESULTS_REPORT_PATH = str(report_file)
            
        assert verify_report_reference(MockConfig(), power_data) is False
        
    def test_file_not_found(self, tmp_path):
        """Test that verification fails if report file does not exist."""
        class MockConfig:
            RESULTS_REPORT_PATH = str(tmp_path / "nonexistent.md")
            
        with pytest.raises(FileNotFoundError):
            verify_report_reference(MockConfig(), {"min_N_required": 20})
