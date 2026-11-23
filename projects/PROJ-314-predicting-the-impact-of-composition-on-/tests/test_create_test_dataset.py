"""
Unit tests for create_test_n_dataset.py (T017c).
"""
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.create_test_n_dataset import generate_test_dataset

class TestCreateTestDataset:
    """Tests for the test dataset generation script."""
    
    def test_generates_correct_number_of_rows(self):
        """Verify the script generates the specified number of rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            generate_test_dataset(output_path, num_rows=29)
            
            df = pd.read_csv(output_path)
            assert len(df) == 29, f"Expected 29 rows, got {len(df)}"
    
    def test_generates_correct_columns(self):
        """Verify the script generates the required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            generate_test_dataset(output_path, num_rows=5)
            
            df = pd.read_csv(output_path)
            required_columns = [
                'composition', 'weibull_modulus', 'sample_count', 
                'sintering_temp', 'primary_anion_cation_group'
            ]
            for col in required_columns:
                assert col in df.columns, f"Missing required column: {col}"
    
    def test_uses_correct_compositions(self):
        """Verify the script uses the specified list of compositions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            generate_test_dataset(output_path, num_rows=10)
            
            df = pd.read_csv(output_path)
            expected_compositions = [
                'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 
                'TiC', 'HfC', 'B4C', 'WC', 'AlN'
            ]
            
            for comp in df['composition']:
                assert comp in expected_compositions, f"Unexpected composition: {comp}"
    
    def test_sample_count_is_valid(self):
        """Verify sample_count values are >= 30 (valid per T018f-1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            generate_test_dataset(output_path, num_rows=10)
            
            df = pd.read_csv(output_path)
            assert (df['sample_count'] >= 30).all(), "Some sample_count values are < 30"
    
    def test_data_types_correct(self):
        """Verify data types are correct for each column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            generate_test_dataset(output_path, num_rows=5)
            
            df = pd.read_csv(output_path)
            
            # composition: string
            assert df['composition'].dtype == 'object'
            
            # weibull_modulus: float
            assert df['weibull_modulus'].dtype == 'float64'
            
            # sample_count: int
            assert df['sample_count'].dtype == 'int64'
            
            # sintering_temp: float
            assert df['sintering_temp'].dtype == 'float64'
            
            # primary_anion_cation_group: string
            assert df['primary_anion_cation_group'].dtype == 'object'
    
    def test_cyclic_repetition(self):
        """Verify compositions repeat cyclically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            generate_test_dataset(output_path, num_rows=15)
            
            df = pd.read_csv(output_path)
            expected = ['Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 
                        'TiC', 'HfC', 'B4C', 'WC', 'AlN', 
                        'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO']
            
            assert list(df['composition']) == expected, "Compositions did not repeat cyclically"