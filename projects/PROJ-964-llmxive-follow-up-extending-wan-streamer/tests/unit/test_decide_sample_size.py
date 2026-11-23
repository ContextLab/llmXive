"""
tests/unit/test_decide_sample_size.py (Task T014g)

Unit tests for code/data/decide_sample_size.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from data.decide_sample_size import decide_sample_size, load_power_analysis_initial, write_selected_sample_size
from config import DEFAULT_SAMPLE_SIZE

class TestDecideSampleSize:
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.metrics_dir = Path(self.temp_dir) / "data" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the PROJECT_ROOT path in the module temporarily if needed, 
        # but since we are testing logic, we focus on the functions.
        # For path-based tests, we might need to adjust how the module resolves paths.
        # However, the task is simple enough to test logic directly.

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_uses_recommended_size(self):
        """Test that the function uses the recommended size from JSON."""
        # Create a mock power analysis file
        power_data = {
            "recommended_sample_size": 12345,
            "expected_variance": 0.05
        }
        json_path = self.metrics_dir / "power_analysis_initial.json"
        with open(json_path, 'w') as f:
            json.dump(power_data, f)
        
        # We need to mock the path resolution inside the function or pass the path.
        # Since the function hardcodes the path relative to PROJECT_ROOT,
        # we will test the logic by mocking the file reading behavior.
        
        with patch('data.decide_sample_size.PROJECT_ROOT', Path(self.temp_dir)):
            result = decide_sample_size()
            assert result == 12345

    def test_uses_default_when_missing_key(self):
        """Test that the function falls back to default when key is missing."""
        power_data = {
            "expected_variance": 0.05
            # No recommended_sample_size
        }
        json_path = self.metrics_dir / "power_analysis_initial.json"
        with open(json_path, 'w') as f:
            json.dump(power_data, f)
        
        with patch('data.decide_sample_size.PROJECT_ROOT', Path(self.temp_dir)):
            result = decide_sample_size()
            assert result == DEFAULT_SAMPLE_SIZE

    def test_uses_default_when_file_missing(self):
        """Test that the function falls back to default when file is missing."""
        # Ensure the file does not exist
        json_path = self.metrics_dir / "power_analysis_initial.json"
        if json_path.exists():
            json_path.unlink()
        
        with patch('data.decide_sample_size.PROJECT_ROOT', Path(self.temp_dir)):
            result = decide_sample_size()
            assert result == DEFAULT_SAMPLE_SIZE

    def test_uses_default_when_invalid_value(self):
        """Test that the function falls back to default when value is invalid."""
        power_data = {
            "recommended_sample_size": -100
        }
        json_path = self.metrics_dir / "power_analysis_initial.json"
        with open(json_path, 'w') as f:
            json.dump(power_data, f)
        
        with patch('data.decide_sample_size.PROJECT_ROOT', Path(self.temp_dir)):
            result = decide_sample_size()
            assert result == DEFAULT_SAMPLE_SIZE

    def test_write_selected_sample_size(self):
        """Test that the function writes the size to the correct file."""
        size = 5000
        output_path = self.metrics_dir / "selected_sample_size.txt"
        
        # Mock PROJECT_ROOT to point to temp dir
        # Note: The function writes to PROJECT_ROOT/data/metrics/...
        # We need to ensure the path logic in the function aligns with our temp dir structure.
        # The function uses: PROJECT_ROOT / "data" / "metrics" / ...
        # Our temp dir is just a folder, so we need to structure it as:
        # temp_dir/data/metrics
        
        temp_root = Path(self.temp_dir)
        (temp_root / "data" / "metrics").mkdir(parents=True, exist_ok=True)
        
        with patch('data.decide_sample_size.PROJECT_ROOT', temp_root):
            write_selected_sample_size(size)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read().strip()
            assert content == str(size)