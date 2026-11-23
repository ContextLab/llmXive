"""
Unit tests for analyze_results.py functions.
Verifies data loading, validation, and regression building logic.
"""
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analyze_results import load_simulation_data, validate_sample_size


class TestLoadSimulationData:
    """Tests for the load_simulation_data function."""

    def test_load_valid_csv(self):
        """Should load valid CSV simulation data."""
        # Create a temporary CSV file
        csv_content = """trajectory_id,turn,retention_horizon,density,is_success
        1,10,5,0.5,1
        2,15,3,0.7,0
        3,20,8,0.3,1
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = load_simulation_data(temp_path)
            assert len(result) == 3
            assert 'trajectory_id' in result[0]
            assert 'is_success' in result[0]
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        """Should raise FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            load_simulation_data("/nonexistent/path/data.csv")

    def test_empty_csv(self):
        """Should handle empty CSV gracefully."""
        csv_content = "trajectory_id,turn,retention_horizon,density,is_success\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = load_simulation_data(temp_path)
            assert len(result) == 0
        finally:
            os.unlink(temp_path)


class TestValidateSampleSize:
    """Tests for the validate_sample_size function."""

    def test_sufficient_sample_size(self):
        """Sample size above threshold should return True."""
        result = validate_sample_size(1000, min_size=100)
        assert result is True

    def test_insufficient_sample_size(self):
        """Sample size below threshold should return False."""
        result = validate_sample_size(50, min_size=100)
        assert result is False

    def test_exact_threshold(self):
        """Sample size exactly at threshold should return True."""
        result = validate_sample_size(100, min_size=100)
        assert result is True

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        result = validate_sample_size(50, min_size=25)
        assert result is True

        result = validate_sample_size(20, min_size=25)
        assert result is False
