"""
Integration tests for the p_values_saver module.

These tests verify that raw p-values are correctly saved to disk
and can be read back with the expected structure.
"""
import os
import csv
import tempfile
import shutil
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from p_values_saver import save_raw_p_values, ensure_p_values_dir
from config import RESULTS_DIR

class TestPValuesSaver:
    """Tests for the p_values_saver module."""

    def setup_method(self):
        """Set up a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        # Patch RESULTS_DIR for testing by creating a mock config
        # We will test the function directly with a specific path
        self.test_output_path = Path(self.temp_dir) / "test_p_values"
        self.test_output_path.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_single_p_value(self):
        """Test saving a single p-value entry."""
        p_values = [
            {"query_id": 1, "metric": "NDCG@10", "p_value": 0.045}
        ]
        
        output_file = self.test_output_path / "single.csv"
        result_path = save_raw_p_values(p_values, str(output_file))
        
        assert result_path.exists()
        assert result_path == output_file
        
        with open(result_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        assert rows[0]['query_id'] == '1'
        assert rows[0]['metric'] == 'NDCG@10'
        assert float(rows[0]['p_value']) == 0.045

    def test_save_multiple_p_values(self):
        """Test saving multiple p-value entries."""
        p_values = [
            {"query_id": 1, "metric": "NDCG@10", "p_value": 0.045},
            {"query_id": 1, "metric": "MAP", "p_value": 0.032},
            {"query_id": 2, "metric": "NDCG@10", "p_value": 0.890}
        ]
        
        output_file = self.test_output_path / "multiple.csv"
        result_path = save_raw_p_values(p_values, str(output_file))
        
        assert result_path.exists()
        
        with open(result_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 3
        assert rows[0]['query_id'] == '1'
        assert rows[1]['metric'] == 'MAP'
        assert float(rows[2]['p_value']) == 0.890

    def test_save_empty_list_creates_headers(self):
        """Test that saving an empty list creates a file with headers only."""
        p_values = []
        
        output_file = self.test_output_path / "empty.csv"
        result_path = save_raw_p_values(p_values, str(output_file))
        
        assert result_path.exists()
        
        with open(result_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        assert len(rows) == 1  # Header only
        assert rows[0] == ['query_id', 'metric', 'p_value']

    def test_invalid_data_raises_error(self):
        """Test that invalid data types raise ValueError."""
        p_values = [
            {"query_id": 1, "metric": "NDCG@10", "p_value": "invalid_string"}
        ]
        
        output_file = self.test_output_path / "invalid.csv"
        
        with pytest.raises(ValueError, match="invalid p_value type"):
            save_raw_p_values(p_values, str(output_file))

    def test_missing_keys_raises_error(self):
        """Test that missing required keys raise ValueError."""
        p_values = [
            {"query_id": 1, "metric": "NDCG@10"}  # Missing p_value
        ]
        
        output_file = self.test_output_path / "missing_keys.csv"
        
        with pytest.raises(ValueError, match="missing keys"):
            save_raw_p_values(p_values, str(output_file))

    def test_file_format_correct(self):
        """Verify the CSV format is correct with proper delimiters."""
        p_values = [
            {"query_id": 100, "metric": "MAP@20", "p_value": 0.001}
        ]
        
        output_file = self.test_output_path / "format_test.csv"
        save_raw_p_values(p_values, str(output_file))
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.strip().split('\n')
        assert lines[0] == "query_id,metric,p_value"
        assert lines[1] == "100,MAP@20,0.001"
