"""
Unit tests for the synthetic base data generation script (T040b).
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the functions to test
# Assuming the script is in code/scripts/generate_synthetic_base.py
# We need to adjust the import path if running from tests/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code" / "scripts"))

from generate_synthetic_base import generate_synthetic_base_data, save_to_csv

class TestGenerateSyntheticBase:
    def test_generate_synthetic_base_data_structure(self):
        """Verify that the generated data has the correct structure and columns."""
        data = generate_synthetic_base_data(n_studies=10, seed=42)
        
        assert len(data) == 10
        assert isinstance(data, list)
        
        # Check keys
        required_keys = {"study_id", "effect_size", "variance", "sample_size"}
        for item in data:
            assert set(item.keys()) == required_keys
            assert isinstance(item["study_id"], str)
            assert isinstance(item["effect_size"], float)
            assert isinstance(item["variance"], float)
            assert isinstance(item["sample_size"], int)

    def test_generate_synthetic_base_data_values(self):
        """Verify that the generated values are within expected ranges."""
        data = generate_synthetic_base_data(n_studies=10, mean_effect=0.5, seed=42)
        
        # Check mean effect is roughly 0.5
        effects = [item["effect_size"] for item in data]
        mean_effect = np.mean(effects)
        # Allow some tolerance for random variation with small N
        assert 0.0 < mean_effect < 1.0 
        
        # Check variance is positive
        for item in data:
            assert item["variance"] > 0
            assert item["sample_size"] >= 10  # Based on min clamp in generator
            assert item["sample_size"] <= 10000

    def test_generate_synthetic_base_data_reproducibility(self):
        """Verify that the same seed produces the same data."""
        data1 = generate_synthetic_base_data(n_studies=10, seed=123)
        data2 = generate_synthetic_base_data(n_studies=10, seed=123)
        
        assert data1 == data2

    def test_save_to_csv(self):
        """Verify that data is saved correctly to CSV."""
        data = generate_synthetic_base_data(n_studies=5, seed=42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            save_to_csv(data, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 5
            assert set(rows[0].keys()) == {"study_id", "effect_size", "variance", "sample_size"}

    def test_save_to_csv_empty_data(self):
        """Verify that saving empty data raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            with pytest.raises(ValueError, match="No data to save"):
                save_to_csv([], output_path)