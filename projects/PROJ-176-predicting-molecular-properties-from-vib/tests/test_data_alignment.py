"""
Contract test for data alignment in US1.

This test verifies that the inner join on InChIKey between QM9 and IR-spectra
datasets is performed correctly, ensuring that only molecules present in both
datasets are retained.

It acts as a contract test: it expects the aligned data to exist and validates
the integrity of the alignment process.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.preprocess import perform_inner_join


class TestDataAlignmentContract:
    """Contract tests for the data alignment process."""

    @pytest.fixture
    def sample_qm9_data(self, tmp_path):
        """Create a sample QM9 dataset with InChIKeys and properties."""
        data = {
            'InChIKey': ['ABCD123', 'EFGH456', 'IJKL789', 'MNOP012'],
            'dipole_moment': [1.5, 2.0, 1.8, 2.2],
            'polarizability': [10.0, 12.0, 11.5, 13.0],
            'homo_lumo_gap': [5.0, 6.0, 5.5, 6.5],
            'other_property': [100, 200, 300, 400]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "qm9_sample.csv"
        df.to_csv(file_path, index=False)
        return file_path

    @pytest.fixture
    def sample_ir_spectra_data(self, tmp_path):
        """Create a sample IR-spectra dataset with InChIKeys and spectra."""
        # Create some dummy spectral data (wavenumbers, intensity)
        data = {
            'InChIKey': ['EFGH456', 'IJKL789', 'QRST345', 'UVWX678'],
            'spectra': [
                np.array([0.1, 0.2, 0.3, 0.4]),
                np.array([0.2, 0.3, 0.4, 0.5]),
                np.array([0.3, 0.4, 0.5, 0.6]),
                np.array([0.4, 0.5, 0.6, 0.7])
            ]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "ir_spectra_sample.csv"
        df.to_csv(file_path, index=False)
        return file_path

    def test_inner_join_returns_only_common_keys(self, sample_qm9_data, sample_ir_spectra_data):
        """
        Contract test: Verify that perform_inner_join returns only molecules
        that exist in both datasets (InChIKey match).
        """
        # Expected common keys: EFGH456, IJKL789
        expected_common_keys = {'EFGH456', 'IJKL789'}
        
        qm9_df = pd.read_csv(sample_qm9_data)
        ir_df = pd.read_csv(sample_ir_spectra_data)
        
        # Perform the join
        aligned_df = perform_inner_join(qm9_df, ir_df, key_column='InChIKey')
        
        # Assert that the result contains only common keys
        result_keys = set(aligned_df['InChIKey'].unique())
        assert result_keys == expected_common_keys, (
            f"Inner join failed. Expected keys: {expected_common_keys}, "
            f"Got: {result_keys}"
        )

    def test_inner_join_preserves_all_columns(self, sample_qm9_data, sample_ir_spectra_data):
        """
        Contract test: Verify that perform_inner_join preserves columns from both datasets.
        """
        qm9_df = pd.read_csv(sample_qm9_data)
        ir_df = pd.read_csv(sample_ir_spectra_data)
        
        expected_qm9_cols = set(qm9_df.columns)
        expected_ir_cols = set(ir_df.columns)
        
        aligned_df = perform_inner_join(qm9_df, ir_df, key_column='InChIKey')
        
        # Check that all QM9 columns are present
        assert set(aligned_df.columns) >= expected_qm9_cols, (
            f"Missing QM9 columns in aligned data. Expected: {expected_qm9_cols}, "
            f"Got: {set(aligned_df.columns)}"
        )
        
        # Check that all IR columns are present
        assert set(aligned_df.columns) >= expected_ir_cols, (
            f"Missing IR columns in aligned data. Expected: {expected_ir_cols}, "
            f"Got: {set(aligned_df.columns)}"
        )

    def test_inner_join_row_count_matches_common_keys(self, sample_qm9_data, sample_ir_spectra_data):
        """
        Contract test: Verify that the number of rows in the aligned data
        matches the number of common InChIKeys.
        """
        qm9_df = pd.read_csv(sample_qm9_data)
        ir_df = pd.read_csv(sample_ir_spectra_data)
        
        aligned_df = perform_inner_join(qm9_df, ir_df, key_column='InChIKey')
        
        # Count unique common keys
        common_keys = set(qm9_df['InChIKey']).intersection(set(ir_df['InChIKey']))
        expected_row_count = len(common_keys)
        
        assert len(aligned_df) == expected_row_count, (
            f"Row count mismatch. Expected: {expected_row_count}, "
            f"Got: {len(aligned_df)}"
        )

    def test_inner_join_fails_gracefully_on_missing_key_column(self, sample_qm9_data, sample_ir_spectra_data):
        """
        Contract test: Verify that perform_inner_join raises an error
        if the key column is missing in either dataset.
        """
        qm9_df = pd.read_csv(sample_qm9_data)
        ir_df = pd.read_csv(sample_ir_spectra_data)
        
        # Remove InChIKey from one dataset
        ir_df_no_key = ir_df.drop(columns=['InChIKey'])
        
        with pytest.raises(KeyError):
            perform_inner_join(qm9_df, ir_df_no_key, key_column='InChIKey')

    def test_inner_join_handles_empty_intersection(self, tmp_path):
        """
        Contract test: Verify that perform_inner_join returns an empty DataFrame
        when there are no common InChIKeys between datasets.
        """
        # Create datasets with no common keys
        qm9_data = {
            'InChIKey': ['UNIQUE1', 'UNIQUE2'],
            'dipole_moment': [1.0, 2.0]
        }
        qm9_df = pd.DataFrame(qm9_data)
        qm9_file = tmp_path / "qm9_unique.csv"
        qm9_df.to_csv(qm9_file, index=False)
        
        ir_data = {
            'InChIKey': ['UNIQUE3', 'UNIQUE4'],
            'spectra': [np.array([0.1]), np.array([0.2])]
        }
        ir_df = pd.DataFrame(ir_data)
        ir_file = tmp_path / "ir_unique.csv"
        ir_df.to_csv(ir_file, index=False)
        
        qm9_df_loaded = pd.read_csv(qm9_file)
        ir_df_loaded = pd.read_csv(ir_file)
        
        aligned_df = perform_inner_join(qm9_df_loaded, ir_df_loaded, key_column='InChIKey')
        
        assert len(aligned_df) == 0, "Expected empty DataFrame for no common keys"
        assert 'InChIKey' in aligned_df.columns, "Expected InChIKey column even in empty result"