"""
Tests for the synthetic data generator.
"""
import os
import sys
import csv
import tempfile
import pytest
import importlib

# Ensure we can import from code/
code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from data.generate_synthetic import generate_synthetic_data, write_csv

class TestGenerateSynthetic:
    def test_generation_size(self):
        """Test that the generator produces the requested number of rows."""
        size = 50
        rows = generate_synthetic_data(size, seed=42)
        assert len(rows) == size

    def test_generation_reproducibility(self):
        """Test that the same seed produces the same data."""
        rows1 = generate_synthetic_data(10, seed=123)
        rows2 = generate_synthetic_data(10, seed=123)
        assert rows1 == rows2

    def test_generation_columns(self):
        """Test that all required columns are present."""
        rows = generate_synthetic_data(5, seed=42)
        required_cols = {
            "step", "config", "coherence_score", 
            "diversity_score", "step_latency_sec", 
            "memory_mb", "is_power_limited"
        }
        assert required_cols.issubset(set(rows[0].keys()))

    def test_write_csv(self):
        """Test writing data to a temporary CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name

        try:
            rows = generate_synthetic_data(10, seed=42)
            write_csv(rows, tmp_path)
            
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                reader = csv.DictReader(f)
                read_rows = list(reader)
            
            assert len(read_rows) == 10
            assert read_rows[0]['step'] == '0'
            assert float(read_rows[0]['coherence_score']) > 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_empty_rows_raises(self):
        """Test that writing empty rows raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
        
        try:
            with pytest.raises(ValueError, match="No data to write"):
                write_csv([], tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)