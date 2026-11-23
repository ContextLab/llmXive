"""
Unit tests for T017: Metadata extraction functionality.
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.extract_metadata import (
    load_filtered_dataset,
    compute_global_stats,
    identify_continuous_columns,
    extract_metadata_for_dataset
)

class TestComputeGlobalStats:
    def test_skewness_calculation(self):
        """Test that skewness is correctly calculated."""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        stats = compute_global_stats(df, ['col1'])
        assert 'col1' in stats
        assert stats['col1']['skewness'] is not None
        # For a uniform distribution, skewness should be close to 0
        assert abs(stats['col1']['skewness']) < 1.0

    def test_kurtosis_calculation(self):
        """Test that kurtosis is correctly calculated."""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        stats = compute_global_stats(df, ['col1'])
        assert 'col1' in stats
        assert stats['col1']['kurtosis'] is not None

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame()
        stats = compute_global_stats(df, [])
        assert stats == {}

    def test_non_numeric_column(self):
        """Test that non-numeric columns are handled gracefully."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        stats = compute_global_stats(df, ['col2'])
        assert stats['col2']['skewness'] is None
        assert stats['col2']['kurtosis'] is None

class TestIdentifyContinuousColumns:
    def test_identify_numeric_columns(self):
        """Test identification of numeric columns."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'float_col': [1.1, 2.2, 3.3],
            'str_col': ['a', 'b', 'c']
        })
        continuous_cols = identify_continuous_columns(df)
        assert 'int_col' in continuous_cols
        assert 'float_col' in continuous_cols
        assert 'str_col' not in continuous_cols

    def test_no_numeric_columns(self):
        """Test when no numeric columns exist."""
        df = pd.DataFrame({
            'str_col1': ['a', 'b', 'c'],
            'str_col2': ['d', 'e', 'f']
        })
        continuous_cols = identify_continuous_columns(df)
        assert len(continuous_cols) == 0

class TestLoadFilteredDataset:
    def test_load_csv(self, tmp_path):
        """Test loading a CSV file."""
        csv_file = tmp_path / "test.csv"
        df_test = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        df_test.to_csv(csv_file, index=False)
        
        loaded_df = load_filtered_dataset(csv_file)
        pd.testing.assert_frame_equal(loaded_df, df_test)

    def test_file_not_found(self, tmp_path):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_filtered_dataset(tmp_path / "nonexistent.csv")

class TestExtractMetadataForDataset:
    def test_extract_metadata_structure(self, tmp_path):
        """Test that metadata extraction produces correct structure."""
        # Create a mock filtered dataset
        dataset_dir = tmp_path / "filtered"
        dataset_dir.mkdir()
        dataset_file = dataset_dir / "test_dataset.csv"
        df_test = pd.DataFrame({
            'var1': np.random.normal(0, 1, 100),
            'var2': np.random.normal(0, 1, 100)
        })
        df_test.to_csv(dataset_file, index=False)

        # Create mock checksums file
        checksums_file = tmp_path / "checksums.csv"
        checksums_file.write_text("dataset_id,checksum\ntest_dataset,abc123\n")

        # Create mock filter results file
        filter_results_file = tmp_path / "filter_results.csv"
        filter_results_file.write_text("dataset_id,source_url,sample_size,shapiro_p,included\n"
                                     "test_dataset,http://example.com,100,0.01,true\n")

        # Mock the global paths
        import code.extract_metadata as module
        original_checksums = module.CHECKSUMS_CSV
        original_filter_results = module.FILTER_RESULTS_CSV
        
        module.CHECKSUMS_CSV = checksums_file
        module.FILTER_RESULTS_CSV = filter_results_file

        try:
            metadata = extract_metadata_for_dataset("test_dataset", dataset_file)
            
            assert metadata is not None
            assert metadata['dataset_id'] == 'test_dataset'
            assert 'sample_size' in metadata
            assert metadata['sample_size'] == 100
            assert 'continuous_variables' in metadata
            assert 'var1' in metadata['continuous_variables']
            assert 'var2' in metadata['continuous_variables']
            assert 'skewness_stats' in metadata
            assert 'kurtosis_stats' in metadata
            assert metadata['checksum'] == 'abc123'
            assert metadata['included'] == 'true'
            
            # Verify stats are valid JSON
            skew_stats = json.loads(metadata['skewness_stats'])
            kurt_stats = json.loads(metadata['kurtosis_stats'])
            assert 'var1' in skew_stats
            assert 'var2' in skew_stats
            assert skew_stats['var1']['skewness'] is not None
            assert kurt_stats['var1']['kurtosis'] is not None
        finally:
            module.CHECKSUMS_CSV = original_checksums
            module.FILTER_RESULTS_CSV = original_filter_results

    def test_excluded_dataset_skipped(self, tmp_path):
        """Test that excluded datasets are skipped."""
        dataset_dir = tmp_path / "filtered"
        dataset_dir.mkdir()
        dataset_file = dataset_dir / "excluded_dataset.csv"
        df_test = pd.DataFrame({'var1': [1, 2, 3]})
        df_test.to_csv(dataset_file, index=False)

        checksums_file = tmp_path / "checksums.csv"
        checksums_file.write_text("dataset_id,checksum\nexcluded_dataset,abc123\n")

        filter_results_file = tmp_path / "filter_results.csv"
        filter_results_file.write_text("dataset_id,source_url,sample_size,shapiro_p,included\n"
                                     "excluded_dataset,http://example.com,3,0.5,false\n")

        import code.extract_metadata as module
        original_checksums = module.CHECKSUMS_CSV
        original_filter_results = module.FILTER_RESULTS_CSV
        
        module.CHECKSUMS_CSV = checksums_file
        module.FILTER_RESULTS_CSV = filter_results_file

        try:
            metadata = extract_metadata_for_dataset("excluded_dataset", dataset_file)
            assert metadata is None
        finally:
            module.CHECKSUMS_CSV = original_checksums
            module.FILTER_RESULTS_CSV = original_filter_results