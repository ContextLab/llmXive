"""
Unit tests for the synthetic base data generator (T040b).
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest
import numpy as np

from generate_synthetic_base import generate_synthetic_base_data, save_to_csv, main

class TestSyntheticBaseGenerator:
    def test_generate_synthetic_base_data_structure(self):
        """Verify that the generated data has the correct structure."""
        data = generate_synthetic_base_data(n_studies=25, seed=42)
        
        assert len(data) == 25
        assert isinstance(data, list)
        assert all(isinstance(item, dict) for item in data)
        
        # Check required keys
        required_keys = {"study_id", "yi", "sei", "vi"}
        for item in data:
            assert required_keys.issubset(item.keys())

    def test_generate_synthetic_base_data_values(self):
        """Verify that the generated data values are within expected ranges."""
        data = generate_synthetic_base_data(n_studies=30, seed=42)
        
        for item in data:
            # yi should be a float
            assert isinstance(item["yi"], float)
            # sei should be positive
            assert item["sei"] > 0
            # vi should be sei^2
            assert abs(item["vi"] - item["sei"]**2) < 1e-6

    def test_save_to_csv(self):
        """Verify that data is correctly saved to CSV."""
        data = generate_synthetic_base_data(n_studies=10, seed=42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.csv")
            save_to_csv(data, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 10
                assert set(rows[0].keys()) == {"study_id", "yi", "sei", "vi"}

    def test_reproducibility(self):
        """Verify that the generator produces the same results with the same seed."""
        data1 = generate_synthetic_base_data(n_studies=20, seed=123)
        data2 = generate_synthetic_base_data(n_studies=20, seed=123)
        
        assert data1 == data2

    def test_reproducibility_different_seed(self):
        """Verify that different seeds produce different results."""
        data1 = generate_synthetic_base_data(n_studies=20, seed=123)
        data2 = generate_synthetic_base_data(n_studies=20, seed=456)
        
        assert data1 != data2

    def test_n_studies_range(self):
        """Verify that the number of studies is within the expected range."""
        for _ in range(10):
            data = generate_synthetic_base_data(seed=42)
            assert 20 <= len(data) <= 30

if __name__ == "__main__":
    pytest.main([__file__, "-v"])