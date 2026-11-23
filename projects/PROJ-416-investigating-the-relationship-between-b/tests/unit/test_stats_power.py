"""
Unit tests for T031 Power Analysis implementation.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.stats import run_power_analysis
from code.config import Config

class TestPowerAnalysis:
    
    @pytest.fixture
    def config(self):
        return Config()
    
    @pytest.fixture
    def temp_output_path(self, tmp_path):
        """Create a temporary path for output files."""
        return tmp_path / "power_analysis.json"

    def test_run_power_analysis_basic(self, temp_output_path):
        """Test basic execution of run_power_analysis."""
        with patch('code.analysis.stats.Config') as MockConfig:
            mock_config_instance = MagicMock()
            mock_config_instance.POWER_ANALYSIS_PATH = temp_output_path
            MockConfig.return_value = mock_config_instance
            
            result = run_power_analysis(n_obs=20, effect_size=0.15, alpha=0.05, power=0.8)
            
            assert result is not None
            assert "min_N_required" in result
            assert "status" in result
            assert result["method"] == "FTestPower"
            assert result["observed_n"] == 20
            
            # Check file was written
            assert temp_output_path.exists()
            
            with open(temp_output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["min_N_required"] == result["min_N_required"]
            assert saved_data["status"] == result["status"]

    def test_status_halt_low_n(self, temp_output_path):
        """Test that status is HALT when N < 5."""
        with patch('code.analysis.stats.Config') as MockConfig:
            mock_config_instance = MagicMock()
            mock_config_instance.POWER_ANALYSIS_PATH = temp_output_path
            MockConfig.return_value = mock_config_instance
            
            result = run_power_analysis(n_obs=3, effect_size=0.15, alpha=0.05, power=0.8)
            
            assert result["status"] == "HALT"
            assert "Insufficient Power" in result["warning_message"]

    def test_status_warning_underpowered(self, temp_output_path):
        """Test that status is WARNING when N is between 5 and min_N."""
        with patch('code.analysis.stats.Config') as MockConfig:
            mock_config_instance = MagicMock()
            mock_config_instance.POWER_ANALYSIS_PATH = temp_output_path
            MockConfig.return_value = mock_config_instance
            
            # Assuming min_N is around 30-40 for these params, 10 should be WARNING
            result = run_power_analysis(n_obs=10, effect_size=0.15, alpha=0.05, power=0.8)
            
            assert result["status"] == "WARNING"
            assert "Underpowered" in result["warning_message"]

    def test_status_ok_powered(self, temp_output_path):
        """Test that status is OK when N >= min_N."""
        with patch('code.analysis.stats.Config') as MockConfig:
            mock_config_instance = MagicMock()
            mock_config_instance.POWER_ANALYSIS_PATH = temp_output_path
            MockConfig.return_value = mock_config_instance
            
            # Use a very large N to ensure OK status
            result = run_power_analysis(n_obs=1000, effect_size=0.15, alpha=0.05, power=0.8)
            
            assert result["status"] == "OK"
            assert result["warning_message"] == ""
            
    def test_schema_compliance(self, temp_output_path):
        """Test that the output JSON strictly matches the required schema."""
        with patch('code.analysis.stats.Config') as MockConfig:
            mock_config_instance = MagicMock()
            mock_config_instance.POWER_ANALYSIS_PATH = temp_output_path
            MockConfig.return_value = mock_config_instance
            
            run_power_analysis(n_obs=20, effect_size=0.15, alpha=0.05, power=0.8)
            
            with open(temp_output_path, 'r') as f:
                data = json.load(f)
            
            required_keys = [
                "min_N_required", "effect_size", "alpha", "power", 
                "method", "status", "warning_message", "observed_n"
            ]
            
            for key in required_keys:
                assert key in data, f"Missing key: {key}"
            
            assert isinstance(data["min_N_required"], int)
            assert isinstance(data["effect_size"], float)
            assert isinstance(data["method"], str)
            assert data["method"] == "FTestPower"