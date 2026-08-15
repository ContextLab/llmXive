"""
Tests for T017c: Create Test Data for Data Gap.
Verifies that the generated dataset has exactly 29 rows and all sample_count < 30.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.create_test_n_dataset import create_test_n_dataset

class TestCreateTestNDataSet:
    def test_row_count_is_exactly_29(self, tmp_path):
        """Verify the generated dataset has exactly 29 rows."""
        output_path = tmp_path / "test_n.csv"
        df = create_test_n_dataset(str(output_path), row_count=29)
        
        assert len(df) == 29, f"Expected 29 rows, got {len(df)}"
    
    def test_all_sample_counts_are_less_than_30(self, tmp_path):
        """Verify all sample_count values are strictly less than 30."""
        output_path = tmp_path / "test_n.csv"
        df = create_test_n_dataset(str(output_path), row_count=29)
        
        assert all(df['sample_count'] < 30), "All sample_count values must be < 30"
        assert df['sample_count'].max() < 30, f"Max sample_count {df['sample_count'].max()} is not < 30"
    
    def test_required_columns_exist(self, tmp_path):
        """Verify the dataset contains required columns for the pipeline."""
        output_path = tmp_path / "test_n.csv"
        df = create_test_n_dataset(str(output_path), row_count=29)
        
        required_cols = [
            'composition', 'weibull_modulus', 'sample_count', 
            'sintering_temp', 'primary_anion_cation_group'
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"
    
    def test_file_is_written_to_disk(self, tmp_path):
        """Verify the CSV file is actually written to disk."""
        output_path = tmp_path / "test_n.csv"
        create_test_n_dataset(str(output_path), row_count=29)
        
        assert output_path.exists(), "Output file was not written to disk"
        assert output_path.stat().st_size > 0, "Output file is empty"
    
    def test_data_integrity(self, tmp_path):
        """Verify data types and basic integrity."""
        output_path = tmp_path / "test_n.csv"
        df = create_test_n_dataset(str(output_path), row_count=29)
        
        # Check for NaN values in critical columns
        assert not df['sample_count'].isnull().any(), "sample_count has NaN values"
        assert not df['weibull_modulus'].isnull().any(), "weibull_modulus has NaN values"
        assert not df['composition'].isnull().any(), "composition has NaN values"