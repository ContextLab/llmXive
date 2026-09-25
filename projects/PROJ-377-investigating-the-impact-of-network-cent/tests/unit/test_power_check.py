import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the functions to test
from code.data.power_check import load_retention_metrics, check_power, save_power_check_results

class TestPowerCheck:
    """Unit tests for the power calculation logic (T004a)."""

    @pytest.fixture
    def sample_retention_data(self):
        """Fixture providing sample retention data."""
        return {
            "total_subjects": 100,
            "retained_subjects": 65,
            "retention_rate": 0.65,
            "exclusion_reasons": {"motion": 10, "missing_data": 25}
        }

    @pytest.fixture
    def temp_retention_file(self, tmp_path, sample_retention_data):
        """Fixture creating a temporary retention metrics file."""
        file_path = tmp_path / "retention_metrics.json"
        with open(file_path, "w") as f:
            json.dump(sample_retention_data, f)
        return file_path

    def test_check_power_meets_threshold(self, sample_retention_data):
        """Test that check_power returns True when N >= 50."""
        result = check_power(sample_retention_data, threshold=50)
        assert result["n_subjects"] == 65
        assert result["threshold"] == 50
        assert result["meets_threshold"] is True

    def test_check_power_fails_threshold(self):
        """Test that check_power returns False when N < 50."""
        data = {"retained_subjects": 30}
        result = check_power(data, threshold=50)
        assert result["n_subjects"] == 30
        assert result["threshold"] == 50
        assert result["meets_threshold"] is False

    def test_check_power_exact_threshold(self):
        """Test that check_power returns True when N == 50."""
        data = {"retained_subjects": 50}
        result = check_power(data, threshold=50)
        assert result["meets_threshold"] is True

    def test_load_retention_metrics_file_not_found(self, tmp_path):
        """Test that load_retention_metrics raises FileNotFoundError if file missing."""
        fake_path = tmp_path / "nonexistent.json"
        with patch("code.data.power_check.RETENTION_INPUT", fake_path):
            with pytest.raises(FileNotFoundError):
                load_retention_metrics()

    def test_save_power_check_results(self, tmp_path, sample_retention_data):
        """Test that save_power_check_results writes valid JSON."""
        output_file = tmp_path / "power_metrics.json"
        power_data = check_power(sample_retention_data)
        
        with patch("code.data.power_check.OUTPUT_PATH", output_file):
            save_power_check_results(power_data)
        
        assert output_file.exists()
        with open(output_file, "r") as f:
            saved_data = json.load(f)
        
        assert saved_data["n_subjects"] == sample_retention_data["retained_subjects"]
        assert "meets_threshold" in saved_data