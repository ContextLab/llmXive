"""
Integration tests for trajectory aggregation (T016).

Tests the full aggregation pipeline by creating mock seed logs,
running the aggregation, and verifying the output.
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from aggregate_trajectories import aggregate_seed_logs
from config import get_project_root
from utils.io_utils import read_csv


class TestAggregationIntegration:
    """Integration tests for seed log aggregation."""
    
    @pytest.fixture
    def mock_seed_logs(self, tmp_path):
        """Create mock seed log files for testing."""
        input_dir = tmp_path / "raw"
        input_dir.mkdir()
        
        # Create mock data for 3 seeds
        seeds_data = []
        for seed_id in ["001", "002", "003"]:
            # Generate mock trajectory data
            n_timesteps = 100
            data = {
                't': list(range(n_timesteps)),
                'G(t)': np.random.rand(n_timesteps) * 10,
                'dG(t)': np.random.rand(n_timesteps) * 2 - 1,
                'z_score': np.random.randn(n_timesteps),
                'bias_type': ['biased' if seed_id == "001" else 'unbiased' for _ in range(n_timesteps)]
            }
            df = pd.DataFrame(data)
            
            # Write to file
            file_path = input_dir / f"seed_{seed_id}.csv"
            df.to_csv(file_path, index=False)
            seeds_data.append(df)
        
        return input_dir, seeds_data
    
    def test_aggregation_creates_output_file(self, mock_seed_logs):
        """Test that aggregation creates the output CSV file."""
        input_dir, _ = mock_seed_logs
        output_path = mock_seed_logs[0].parent / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        # Run aggregation
        result_df = aggregate_seed_logs(input_dir, output_path)
        
        # Verify file exists
        assert output_path.exists(), "Output CSV file was not created"
        
        # Verify it can be read back
        loaded_df = read_csv(output_path)
        assert len(loaded_df) > 0, "Output file is empty"
    
    def test_aggregation_preserves_seed_id(self, mock_seed_logs):
        """Test that seed_id is preserved in the aggregated output."""
        input_dir, _ = mock_seed_logs
        output_path = mock_seed_logs[0].parent / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        result_df = aggregate_seed_logs(input_dir, output_path)
        
        # Check that all original seed IDs are present
        expected_seeds = {"001", "002", "003"}
        actual_seeds = set(result_df['seed_id'].unique())
        
        assert expected_seeds == actual_seeds, (
            f"Seed IDs mismatch: expected {expected_seeds}, got {actual_seeds}"
        )
    
    def test_aggregation_preserves_bias_type(self, mock_seed_logs):
        """Test that bias_type is preserved correctly."""
        input_dir, _ = mock_seed_logs
        output_path = mock_seed_logs[0].parent / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        result_df = aggregate_seed_logs(input_dir, output_path)
        
        # Check that bias_type column exists and has expected values
        assert 'bias_type' in result_df.columns, "bias_type column is missing"
        
        # Verify seed 001 is biased, others are unbiased
        seed_001_bias = result_df[result_df['seed_id'] == '001']['bias_type'].iloc[0]
        assert seed_001_bias == 'biased', f"Expected seed 001 to be 'biased', got {seed_001_bias}"
    
    def test_aggregation_maintains_required_columns(self, mock_seed_logs):
        """Test that all required columns are present in output."""
        input_dir, _ = mock_seed_logs
        output_path = mock_seed_logs[0].parent / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        result_df = aggregate_seed_logs(input_dir, output_path)
        
        required_cols = ['t', 'G(t)', 'dG(t)', 'z_score', 'seed_id', 'bias_type']
        missing_cols = [col for col in required_cols if col not in result_df.columns]
        
        assert not missing_cols, f"Missing required columns: {missing_cols}"
    
    def test_aggregation_row_count(self, mock_seed_logs):
        """Test that the total row count matches expected value."""
        input_dir, seed_dfs = mock_seed_logs
        output_path = mock_seed_logs[0].parent / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        result_df = aggregate_seed_logs(input_dir, output_path)
        
        expected_rows = sum(len(df) for df in seed_dfs)
        actual_rows = len(result_df)
        
        assert actual_rows == expected_rows, (
            f"Row count mismatch: expected {expected_rows}, got {actual_rows}"
        )
    
    def test_aggregation_sorting(self, mock_seed_logs):
        """Test that output is sorted by seed_id then timestep."""
        input_dir, _ = mock_seed_logs
        output_path = mock_seed_logs[0].parent / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        result_df = aggregate_seed_logs(input_dir, output_path)
        
        # Check sorting
        sorted_df = result_df.sort_values(['seed_id', 't']).reset_index(drop=True)
        
        assert result_df.equals(sorted_df), "Output is not properly sorted by seed_id and t"
    
    def test_aggregation_with_missing_files(self, tmp_path):
        """Test that aggregation handles missing files gracefully."""
        input_dir = tmp_path / "raw"
        input_dir.mkdir()
        
        # Create only one seed file instead of three
        data = pd.DataFrame({
            't': list(range(50)),
            'G(t)': np.random.rand(50),
            'dG(t)': np.random.rand(50),
            'z_score': np.random.randn(50),
            'bias_type': ['biased'] * 50
        })
        (input_dir / "seed_001.csv").to_csv(data, index=False)
        
        output_path = tmp_path / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        # Should succeed with just one file
        result_df = aggregate_seed_logs(input_dir, output_path)
        
        assert len(result_df) == 50, "Expected 50 rows from single seed"
        assert result_df['seed_id'].iloc[0] == '001'
    
    def test_aggregation_no_files_raises_error(self, tmp_path):
        """Test that aggregation raises error when no seed files exist."""
        input_dir = tmp_path / "raw"
        input_dir.mkdir()
        
        output_path = tmp_path / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        with pytest.raises(FileNotFoundError):
            aggregate_seed_logs(input_dir, output_path)
    
    def test_aggregation_missing_columns_raises_error(self, tmp_path):
        """Test that aggregation raises error when required columns are missing."""
        input_dir = tmp_path / "raw"
        input_dir.mkdir()
        
        # Create file with missing columns
        data = pd.DataFrame({
            't': list(range(10)),
            'G(t)': np.random.rand(10)
            # Missing dG(t), z_score, bias_type
        })
        (input_dir / "seed_001.csv").to_csv(data, index=False)
        
        output_path = tmp_path / "processed" / "trajectories_divergence.csv"
        output_path.parent.mkdir()
        
        with pytest.raises(ValueError) as exc_info:
            aggregate_seed_logs(input_dir, output_path)
        
        assert "missing required columns" in str(exc_info.value).lower()


# Import numpy at module level for fixture
import numpy as np
