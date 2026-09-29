"""
Tests for the test dataset generation script (T017c).
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from code.scripts.create_test_n_dataset import generate_test_dataset

class TestCreateTestNDataset:
    """Test suite for T017c test dataset generation."""

    def test_row_count_is_29(self, tmp_path):
        """Verify the generated dataset has exactly 29 rows."""
        output_file = tmp_path / "test_n.csv"
        df = generate_test_dataset(output_file)
        
        assert len(df) == 29, f"Expected 29 rows, got {len(df)}"

    def test_columns_match_schema(self, tmp_path):
        """Verify the columns match the required schema."""
        output_file = tmp_path / "test_n.csv"
        df = generate_test_dataset(output_file)
        
        expected_columns = [
            'composition', 'weibull_modulus', 'sample_count',
            'sintering_temp', 'primary_anion_cation_group'
        ]
        
        assert list(df.columns) == expected_columns, \
            f"Column mismatch. Expected {expected_columns}, got {list(df.columns)}"

    def test_compositions_are_valid(self, tmp_path):
        """Verify all compositions are from the fixed list."""
        output_file = tmp_path / "test_n.csv"
        df = generate_test_dataset(output_file)
        
        valid_compositions = [
            'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO',
            'TiC', 'HfC', 'B4C', 'WC', 'AlN'
        ]
        
        for comp in df['composition']:
            assert comp in valid_compositions, \
                f"Invalid composition: {comp}"

    def test_data_types(self, tmp_path):
        """Verify data types are correct."""
        output_file = tmp_path / "test_n.csv"
        df = generate_test_dataset(output_file)
        
        assert df['composition'].dtype == 'object'
        assert pd.api.types.is_float_dtype(df['weibull_modulus'])
        assert pd.api.types.is_int_dtype(df['sample_count'])
        assert pd.api.types.is_float_dtype(df['sintering_temp'])
        assert df['primary_anion_cation_group'].dtype == 'object'

    def test_file_is_written(self, tmp_path):
        """Verify the file is actually written to disk."""
        output_file = tmp_path / "test_n.csv"
        generate_test_dataset(output_file)
        
        assert output_file.exists(), "Output file was not created"
        assert output_file.stat().st_size > 0, "Output file is empty"