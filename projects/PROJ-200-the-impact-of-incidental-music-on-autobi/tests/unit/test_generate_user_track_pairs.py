"""
Unit tests for generate_user_track_pairs.py (T029).

Tests the artifact generation logic, checksum calculation, and state update.
"""
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock dependencies that might require external data
import pyarrow as pa
import pyarrow.parquet as pq

from generate_user_track_pairs import calculate_file_checksum, load_aggregated_data, save_final_dataset


class TestCalculateFileChecksum:
    def test_calculate_checksum_valid_file(self):
        """Test checksum calculation on a valid file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = calculate_file_checksum(tmp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(tmp_path)

    def test_calculate_checksum_empty_file(self):
        """Test checksum calculation on an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            checksum = calculate_file_checksum(tmp_path)
            assert len(checksum) == 64
        finally:
            os.unlink(tmp_path)


class TestLoadAggregatedData:
    @patch('generate_user_track_pairs.aggregate_to_user_track')
    @patch('generate_user_track_pairs.filter_zero_variance')
    @patch('generate_user_track_pairs.pd.read_parquet')
    def test_load_aggregated_data_success(self, mock_read_parquet, mock_filter, mock_aggregate):
        """Test successful loading and aggregation of data."""
        # Mock ingested cohort
        mock_cohort = pd.DataFrame({'user_id': [1, 2], 'track_id': [10, 20]})
        mock_read_parquet.return_value = mock_cohort
        
        # Mock aggregated result
        mock_aggregated = pd.DataFrame({
            'user_id': [1, 2],
            'track_id': [10, 20],
            'mean_vividness': [3.5, 4.0]
        })
        mock_aggregate.return_value = mock_aggregated
        
        # Mock filtered result
        mock_filtered = mock_aggregated.copy()
        mock_filter.return_value = mock_filtered
        
        with patch('generate_user_track_pairs.get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)
                
                # Create required directory structure
                processed_dir = Path(tmpdir) / "data" / "processed"
                processed_dir.mkdir(parents=True)
                
                # Create dummy ingested cohort file
                cohort_path = processed_dir / "ingested_cohort.parquet"
                mock_cohort.to_parquet(cohort_path)
                
                result = load_aggregated_data()
                
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 2
                assert 'mean_vividness' in result.columns
                mock_aggregate.assert_called_once_with(mock_cohort)
                mock_filter.assert_called_once_with(mock_aggregated)

    @patch('generate_user_track_pairs.pd.read_parquet')
    def test_load_aggregated_data_missing_file(self, mock_read_parquet):
        """Test that FileNotFoundError is raised when ingested cohort is missing."""
        mock_read_parquet.side_effect = FileNotFoundError("File not found")
        
        with patch('generate_user_track_pairs.get_project_root') as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_root.return_value = Path(tmpdir)
                
                with pytest.raises(FileNotFoundError):
                    load_aggregated_data()

    @patch('generate_user_track_pairs.aggregate_to_user_track')
    @patch('generate_user_track_pairs.get_project_root')
    def test_load_aggregated_data_empty_result(self, mock_root, mock_aggregate):
        """Test handling of empty aggregation result."""
        mock_aggregate.return_value = pd.DataFrame()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_root.return_value = Path(tmpdir)
            
            processed_dir = Path(tmpdir) / "data" / "processed"
            processed_dir.mkdir(parents=True)
            
            # Create dummy ingested cohort
            cohort_path = processed_dir / "ingested_cohort.parquet"
            pd.DataFrame({'user_id': [1]}).to_parquet(cohort_path)
            
            result = load_aggregated_data()
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0


class TestSaveFinalDataset:
    def test_save_final_dataset_creates_file(self):
        """Test that save_final_dataset creates the Parquet file."""
        df = pd.DataFrame({
            'user_id': [1, 2],
            'track_id': [10, 20],
            'mean_vividness': [3.5, 4.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.parquet"
            
            save_final_dataset(df, output_path)
            
            assert output_path.exists()
            
            # Verify content
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == 2
            assert list(loaded_df.columns) == ['user_id', 'track_id', 'mean_vividness']

    def test_save_final_dataset_creates_directories(self):
        """Test that save_final_dataset creates parent directories."""
        df = pd.DataFrame({'a': [1]})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "deep" / "output.parquet"
            
            save_final_dataset(df, output_path)
            
            assert output_path.exists()
            assert output_path.parent.exists()
