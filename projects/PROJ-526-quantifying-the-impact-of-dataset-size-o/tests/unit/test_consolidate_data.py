"""
Unit tests for data consolidation logic.

Tests the consolidate_data module to ensure it correctly:
- Loads processed Parquet files
- Handles memory constraints
- Merges dataframes correctly
- Saves output in the correct format
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.consolidate_data import (
    load_processed_data,
    save_consolidated_data,
    _get_system_memory_gb,
    _estimate_dataframe_memory,
    _load_with_fallback
)


class TestConsolidateData:
    """Test cases for data consolidation functions."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.test_dir) / "input"
        self.output_dir = Path(self.test_dir) / "output"
        self.input_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_processed_data_empty_directory(self):
        """Test that loading from empty directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_processed_data(self.input_dir, self.output_dir)

    def test_load_processed_data_single_file(self):
        """Test loading a single Parquet file."""
        # Create test data
        df = pd.DataFrame({
            'material_id': ['m1', 'm2', 'm3'],
            'property': [1.0, 2.0, 3.0],
            'magpie_feature_1': [0.1, 0.2, 0.3]
        })
        test_file = self.input_dir / "test_data.parquet"
        df.to_parquet(test_file)

        # Load data
        dataframes = load_processed_data(self.input_dir, self.output_dir)

        # Verify
        assert len(dataframes) == 1
        assert len(dataframes[0]) == 3
        assert 'material_id' in dataframes[0].columns

    def test_load_processed_data_multiple_files(self):
        """Test loading multiple Parquet files."""
        # Create test data
        df1 = pd.DataFrame({
            'material_id': ['m1', 'm2'],
            'property': [1.0, 2.0]
        })
        df2 = pd.DataFrame({
            'material_id': ['m3', 'm4'],
            'property': [3.0, 4.0]
        })

        df1.to_parquet(self.input_dir / "data1.parquet")
        df2.to_parquet(self.input_dir / "data2.parquet")

        # Load data
        dataframes = load_processed_data(self.input_dir, self.output_dir)

        # Verify
        assert len(dataframes) == 2
        assert len(dataframes[0]) == 2
        assert len(dataframes[1]) == 2

    def test_save_consolidated_data_parquet(self):
        """Test saving consolidated data as Parquet."""
        # Create test data
        df1 = pd.DataFrame({
            'material_id': ['m1', 'm2'],
            'value': [1.0, 2.0]
        })
        df2 = pd.DataFrame({
            'material_id': ['m3', 'm4'],
            'value': [3.0, 4.0]
        })

        output_path = self.output_dir / "consolidated.parquet"

        # Save data
        save_consolidated_data([df1, df2], output_path, use_csv_fallback=False)

        # Verify
        assert output_path.exists()
        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == 4
        assert 'material_id' in loaded_df.columns

    def test_save_consolidated_data_csv_fallback(self):
        """Test saving consolidated data as CSV when fallback is enabled."""
        df = pd.DataFrame({
            'material_id': ['m1', 'm2'],
            'value': [1.0, 2.0]
        })

        output_path = self.output_dir / "consolidated.csv"

        # Save data
        save_consolidated_data([df], output_path, use_csv_fallback=True)

        # Verify
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2

    def test_save_consolidated_data_deduplication(self):
        """Test that duplicate material_ids are removed."""
        df1 = pd.DataFrame({
            'material_id': ['m1', 'm2', 'm1'],  # Duplicate m1
            'value': [1.0, 2.0, 3.0]
        })
        df2 = pd.DataFrame({
            'material_id': ['m2', 'm3'],  # Duplicate m2
            'value': [4.0, 5.0]
        })

        output_path = self.output_dir / "deduped.parquet"

        # Save data
        save_consolidated_data([df1, df2], output_path)

        # Verify
        loaded_df = pd.read_parquet(output_path)
        # Should have 3 unique IDs: m1, m2, m3
        assert len(loaded_df) == 3
        assert len(loaded_df['material_id'].unique()) == 3

    def test_save_consolidated_data_empty_list(self):
        """Test that saving empty list raises ValueError."""
        output_path = self.output_dir / "empty.parquet"

        with pytest.raises(ValueError):
            save_consolidated_data([], output_path)

    def test_load_with_fallback_creates_csv(self):
        """Test that fallback strategy creates intermediate CSV files."""
        # Create a test Parquet file
        df = pd.DataFrame({
            'material_id': [f'm{i}' for i in range(100)],
            'value': list(range(100))
        })
        test_file = self.input_dir / "large_data.parquet"
        df.to_parquet(test_file)

        # Run fallback loading
        result = _load_with_fallback([test_file], self.output_dir)

        # Verify
        assert len(result) == 1
        assert result[0].suffix == '.csv'
        assert result[0].exists()

        # Clean up
        result[0].unlink()

    def test_estimate_dataframe_memory(self):
        """Test memory estimation function."""
        df = pd.DataFrame({
            'col1': range(1000),
            'col2': ['test'] * 1000,
            'col3': np.random.rand(1000)
        })

        memory_gb = _estimate_dataframe_memory(df)
        
        # Should be a positive number
        assert memory_gb >= 0
        # Should be small (less than 1GB for this small dataframe)
        assert memory_gb < 1.0

    def test_get_system_memory_gb(self):
        """Test system memory estimation."""
        memory_gb = _get_system_memory_gb()
        
        # Should be a positive number
        assert memory_gb > 0
        # Should be reasonable (between 1GB and 256GB for most systems)
        assert 1.0 <= memory_gb <= 256.0