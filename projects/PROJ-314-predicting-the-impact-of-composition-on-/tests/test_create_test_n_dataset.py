"""
Tests for T017c: Create Test Data for Data Gap.

Verifies that the test dataset is generated correctly with the expected schema and row count.
"""
import os
import sys
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scripts.create_test_n_dataset import generate_test_dataset, COMPOSITIONS, TARGET_ROWS

class TestCreateTestNDataset:
    """Test suite for the test dataset generation."""

    @pytest.fixture
    def temp_output_path(self, tmp_path):
        """Create a temporary output path for testing."""
        return tmp_path / "test_n.csv"

    def test_row_count(self, temp_output_path):
        """Verify the dataset has exactly 29 rows."""
        generate_test_dataset(temp_output_path)
        df = pd.read_csv(temp_output_path)
        assert len(df) == TARGET_ROWS, f"Expected {TARGET_ROWS} rows, got {len(df)}"

    def test_required_columns(self, temp_output_path):
        """Verify the dataset has all required columns."""
        generate_test_dataset(temp_output_path)
        df = pd.read_csv(temp_output_path)
        
        expected_columns = [
            'composition', 'weibull_modulus', 'sample_count', 
            'sintering_temp', 'primary_anion_cation_group'
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_composition_values(self, temp_output_path):
        """Verify composition values are from the fixed list."""
        generate_test_dataset(temp_output_path)
        df = pd.read_csv(temp_output_path)
        
        for comp in df['composition']:
            assert comp in COMPOSITIONS, f"Invalid composition: {comp}"

    def test_data_types(self, temp_output_path):
        """Verify data types are correct."""
        generate_test_dataset(temp_output_path)
        df = pd.read_csv(temp_output_path)
        
        assert df['composition'].dtype == 'object', "composition should be string"
        assert pd.api.types.is_float_dtype(df['weibull_modulus']), "weibull_modulus should be float"
        assert pd.api.types.is_integer_dtype(df['sample_count']), "sample_count should be int"
        assert pd.api.types.is_float_dtype(df['sintering_temp']), "sintering_temp should be float"
        assert df['primary_anion_cation_group'].dtype == 'object', "primary_anion_cation_group should be string"

    def test_no_missing_values(self, temp_output_path):
        """Verify there are no missing values in the dataset."""
        generate_test_dataset(temp_output_path)
        df = pd.read_csv(temp_output_path)
        
        assert not df.isnull().any().any(), "Dataset contains missing values"

    def test_primary_anion_cation_group_format(self, temp_output_path):
        """Verify primary_anion_cation_group follows the 'Anion-Cation' format."""
        generate_test_dataset(temp_output_path)
        df = pd.read_csv(temp_output_path)
        
        for group in df['primary_anion_cation_group']:
            assert '-' in group, f"Invalid format for group: {group}"
            parts = group.split('-')
            assert len(parts) == 2, f"Invalid format for group: {group}"

    def test_sample_count_range(self, temp_output_path):
        """Verify sample_count values are within a reasonable range."""
        generate_test_dataset(temp_output_path)
        df = pd.read_csv(temp_output_path)
        
        assert df['sample_count'].min() >= 30, "sample_count should be >= 30"
        assert df['sample_count'].max() <= 100, "sample_count should be <= 100"