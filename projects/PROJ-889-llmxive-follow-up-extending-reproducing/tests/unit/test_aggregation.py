"""
Unit tests for trajectory aggregation logic (T016).

Tests the aggregate_seed_logs function to ensure:
- Multiple seed logs are correctly merged
- seed_id and bias_type are preserved
- Output contains all required columns
- Data types are correct
"""

import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from code.aggregate_trajectories import aggregate_seed_logs
from code.utils.io_utils import write_csv, read_csv


class TestAggregation:
    """Test cases for trajectory aggregation."""

    @pytest.fixture
    def temp_input_dir(self, tmp_path):
        """Create a temporary directory with sample seed logs."""
        input_dir = tmp_path / "raw" / "cherrl_logs"
        input_dir.mkdir(parents=True)
        
        # Create sample seed 1 log
        seed1_data = {
            'seed_id': ['seed_001'] * 5,
            'bias_type': ['lexical'] * 5,
            'timestep': [1, 2, 3, 4, 5],
            'J_biased': [0.1, 0.2, 0.3, 0.4, 0.5],
            'J_unbiased': [0.05, 0.15, 0.25, 0.35, 0.45],
            'J_gold': [0.0, 0.0, 0.0, 0.0, 0.0],
            'G_t': [0.05, 0.05, 0.05, 0.05, 0.05],
            'dG_t': [0.0, 0.0, 0.0, 0.0, 0.0]
        }
        df1 = pd.DataFrame(seed1_data)
        write_csv(df1, input_dir / "seed_001_lexical.csv")
        
        # Create sample seed 2 log
        seed2_data = {
            'seed_id': ['seed_002'] * 4,
            'bias_type': ['format'] * 4,
            'timestep': [1, 2, 3, 4],
            'J_biased': [0.2, 0.3, 0.4, 0.5],
            'J_unbiased': [0.1, 0.2, 0.3, 0.4],
            'J_gold': [0.0, 0.0, 0.0, 0.0],
            'G_t': [0.1, 0.1, 0.1, 0.1],
            'dG_t': [0.0, 0.0, 0.0, 0.0]
        }
        df2 = pd.DataFrame(seed2_data)
        write_csv(df2, input_dir / "seed_002_format.csv")
        
        return input_dir

    def test_aggregates_multiple_seeds(self, temp_input_dir, tmp_path):
        """Test that multiple seed logs are correctly merged."""
        output_file = tmp_path / "processed" / "trajectories_divergence.csv"
        
        result_df = aggregate_seed_logs(temp_input_dir, output_file)
        
        # Should have 5 + 4 = 9 rows
        assert len(result_df) == 9
        
        # Should have 2 unique seeds
        assert result_df['seed_id'].nunique() == 2
        assert set(result_df['seed_id'].unique()) == {'seed_001', 'seed_002'}

    def test_preserves_seed_id(self, temp_input_dir, tmp_path):
        """Test that seed_id is preserved correctly."""
        output_file = tmp_path / "processed" / "trajectories_divergence.csv"
        
        result_df = aggregate_seed_logs(temp_input_dir, output_file)
        
        # Check seed_id values
        seed_counts = result_df['seed_id'].value_counts()
        assert seed_counts['seed_001'] == 5
        assert seed_counts['seed_002'] == 4

    def test_preserves_bias_type(self, temp_input_dir, tmp_path):
        """Test that bias_type is preserved correctly."""
        output_file = tmp_path / "processed" / "trajectories_divergence.csv"
        
        result_df = aggregate_seed_logs(temp_input_dir, output_file)
        
        # Check bias_type values
        assert set(result_df['bias_type'].unique()) == {'lexical', 'format'}
        assert (result_df[result_df['seed_id'] == 'seed_001']['bias_type'] == 'lexical').all()
        assert (result_df[result_df['seed_id'] == 'seed_002']['bias_type'] == 'format').all()

    def test_output_schema(self, temp_input_dir, tmp_path):
        """Test that output contains all required columns."""
        output_file = tmp_path / "processed" / "trajectories_divergence.csv"
        
        result_df = aggregate_seed_logs(temp_input_dir, output_file)
        
        required_columns = {
            'seed_id', 'bias_type', 'timestep', 
            'J_biased', 'J_unbiased', 'J_gold',
            'G_t', 'dG_t'
        }
        
        assert set(result_df.columns) == required_columns

    def test_numeric_columns_are_numeric(self, temp_input_dir, tmp_path):
        """Test that numeric columns are correctly typed."""
        output_file = tmp_path / "processed" / "trajectories_divergence.csv"
        
        result_df = aggregate_seed_logs(temp_input_dir, output_file)
        
        numeric_cols = ['timestep', 'J_biased', 'J_unbiased', 'J_gold', 'G_t', 'dG_t']
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(result_df[col])

    def test_sorted_output(self, temp_input_dir, tmp_path):
        """Test that output is sorted by seed_id, bias_type, timestep."""
        output_file = tmp_path / "processed" / "trajectories_divergence.csv"
        
        result_df = aggregate_seed_logs(temp_input_dir, output_file)
        
        # Check sorting
        expected_order = result_df.sort_values(
            by=['seed_id', 'bias_type', 'timestep']
        )
        assert result_df.equals(expected_order)

    def test_empty_input_directory(self, tmp_path):
        """Test that empty input directory raises error."""
        input_dir = tmp_path / "empty"
        input_dir.mkdir()
        output_file = tmp_path / "output.csv"
        
        with pytest.raises(FileNotFoundError, match="No CSV files found"):
            aggregate_seed_logs(input_dir, output_file)

    def test_missing_required_columns(self, tmp_path):
        """Test that missing columns raise error."""
        input_dir = tmp_path / "raw" / "cherrl_logs"
        input_dir.mkdir(parents=True)
        
        # Create file with missing columns
        bad_data = {
            'seed_id': ['seed_001'],
            'timestep': [1]
            # Missing J_biased, J_unbiased, etc.
        }
        df = pd.DataFrame(bad_data)
        write_csv(df, input_dir / "bad_seed.csv")
        
        output_file = tmp_path / "output.csv"
        
        with pytest.raises(ValueError, match="missing required columns"):
            aggregate_seed_logs(input_dir, output_file)

    def test_output_file_created(self, temp_input_dir, tmp_path):
        """Test that output file is actually created on disk."""
        output_file = tmp_path / "processed" / "trajectories_divergence.csv"
        
        aggregate_seed_logs(temp_input_dir, output_file)
        
        assert output_file.exists()
        
        # Verify we can read it back
        loaded_df = read_csv(output_file)
        assert len(loaded_df) == 9