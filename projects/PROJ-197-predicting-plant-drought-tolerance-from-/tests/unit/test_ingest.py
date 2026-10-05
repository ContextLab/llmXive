"""
Unit tests for data ingestion module (T014a).
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data.ingest import apply_mice_imputation, merge_datasets
from code.config import VALIDATION_MODE

class TestMergeDatasets:
    def test_merge_success(self):
        """Test successful merge of TRY and genomic data."""
        try_df = pd.DataFrame({
            'species_id': ['A', 'B', 'C'],
            'root_depth': [10.0, 20.0, 30.0]
        })
        genomic_df = pd.DataFrame({
            'species_id': ['A', 'B', 'C'],
            'NCED3': [1, 0, 1]
        })
        
        result = merge_datasets(try_df, genomic_df)
        
        assert len(result) == 3
        assert 'root_depth' in result.columns
        assert 'NCED3' in result.columns
        assert list(result['species_id']) == ['A', 'B', 'C']

    def test_merge_excludes_missing_genomic(self):
        """Test that species missing genomic data are excluded and logged."""
        try_df = pd.DataFrame({
            'species_id': ['A', 'B', 'C'],
            'root_depth': [10.0, 20.0, 30.0]
        })
        genomic_df = pd.DataFrame({
            'species_id': ['A', 'B'],
            'NCED3': [1, 0]
        })
        
        # Mock the metrics log path to use a temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "metrics.json"
            # Patch the constant
            with patch('code.data.ingest.METRICS_LOG_PATH', metrics_path):
                result = merge_datasets(try_df, genomic_df)
                
                # Check result
                assert len(result) == 2
                assert 'C' not in result['species_id'].values
                
                # Check metrics log
                assert metrics_path.exists()
                with open(metrics_path, 'r') as f:
                    metrics = json.load(f)
                
                assert 'excluded_species' in metrics
                assert 'C' in metrics['excluded_species']

class TestImputation:
    def test_median_imputation_validation_mode(self):
        """Test median imputation when tree is missing and VALIDATION_MODE is True."""
        # Create a dataframe with missing values
        df = pd.DataFrame({
            'species_id': ['A', 'B', 'C'],
            'root_depth': [10.0, np.nan, 30.0],
            'leaf_area': [100.0, 200.0, np.nan],
            'label': [0, 1, 0]
        })
        
        # Mock REAL_PHYLO_PATH to not exist
        with patch('code.data.ingest.REAL_PHYLO_PATH', Path("/nonexistent/path.npy")):
            with patch('code.config.VALIDATION_MODE', True):
                result = apply_mice_imputation(df)
                
                # Check that NaNs are filled
                assert not result['root_depth'].isna().any()
                assert not result['leaf_area'].isna().any()
                
                # Check values are median
                assert result.loc[result['species_id'] == 'B', 'root_depth'].values[0] == 20.0
                assert result.loc[result['species_id'] == 'C', 'leaf_area'].values[0] == 150.0

    def test_critical_error_production_mode(self):
        """Test that critical error is raised when tree is missing and VALIDATION_MODE is False."""
        df = pd.DataFrame({
            'species_id': ['A', 'B'],
            'root_depth': [10.0, np.nan]
        })
        
        with patch('code.data.ingest.REAL_PHYLO_PATH', Path("/nonexistent/path.npy")):
            with patch('code.config.VALIDATION_MODE', False):
                with pytest.raises(RuntimeError) as excinfo:
                    apply_mice_imputation(df)
                
                assert "CONSTITUTION VI VIOLATION" in str(excinfo.value)

    def test_no_imputation_needed(self):
        """Test that dataframe is returned unchanged if no missing values."""
        df = pd.DataFrame({
            'species_id': ['A', 'B'],
            'root_depth': [10.0, 20.0],
            'label': [0, 1]
        })
        
        with patch('code.data.ingest.REAL_PHYLO_PATH', Path("/nonexistent/path.npy")):
            with patch('code.config.VALIDATION_MODE', True):
                result = apply_mice_imputation(df)
                
                pd.testing.assert_frame_equal(result, df)