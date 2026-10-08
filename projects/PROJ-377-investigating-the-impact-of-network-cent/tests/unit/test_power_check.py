import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.power_check import load_retention_metrics, check_power, save_power_check_results

class TestPowerCheck:
    
    @pytest.fixture
    def temp_retention_file(self, tmp_path):
        """Create a temporary retention metrics file for testing."""
        retention_data = {
            "retention_rate": 0.85,
            "total_subjects": 100,
            "retained_subjects": 85
        }
        file_path = tmp_path / "retention_metrics.json"
        with open(file_path, 'w') as f:
            json.dump(retention_data, f)
        return str(file_path)

    @pytest.fixture
    def temp_missing_file(self, tmp_path):
        """Create a temporary file path that does not exist."""
        return str(tmp_path / "nonexistent.json")

    def test_load_retention_metrics_success(self, temp_retention_file):
        """Test successful loading of valid retention metrics."""
        data = load_retention_metrics(temp_retention_file)
        assert data['retained_subjects'] == 85
        assert data['total_subjects'] == 100
        assert data['retention_rate'] == 0.85

    def test_load_retention_metrics_missing_file(self, temp_missing_file):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_retention_metrics(temp_missing_file)

    def test_load_retention_metrics_missing_keys(self, tmp_path):
        """Test that ValueError is raised if required keys are missing."""
        bad_data = {"retention_rate": 0.8}  # Missing total_subjects and retained_subjects
        file_path = tmp_path / "bad_retention.json"
        with open(file_path, 'w') as f:
            json.dump(bad_data, f)
        
        with pytest.raises(ValueError):
            load_retention_metrics(str(file_path))

    def test_check_power_meets_threshold(self):
        """Test power check when N >= threshold."""
        retention_data = {'retained_subjects': 85}
        result = check_power(retention_data, threshold=50)
        assert result['n_subjects'] == 85
        assert result['threshold'] == 50
        assert result['meets_threshold'] is True

    def test_check_power_below_threshold(self):
        """Test power check when N < threshold."""
        retention_data = {'retained_subjects': 40}
        result = check_power(retention_data, threshold=50)
        assert result['n_subjects'] == 40
        assert result['meets_threshold'] is False

    def test_check_power_custom_threshold(self):
        """Test power check with a custom threshold."""
        retention_data = {'retained_subjects': 60}
        result = check_power(retention_data, threshold=80)
        assert result['meets_threshold'] is False

    def test_save_power_check_results(self, tmp_path):
        """Test saving power metrics to JSON."""
        power_data = {
            'n_subjects': 85,
            'threshold': 50,
            'meets_threshold': True
        }
        output_path = tmp_path / "power_metrics.json"
        
        save_power_check_results(power_data, str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == power_data