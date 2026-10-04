"""
Unit tests for the connectivity module (Task T018).

These tests verify:
1. Pearson correlation matrix computation
2. Positive edge retention
3. Integration with preprocessed data loading
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.graph.connectivity import (
    compute_correlation_matrix,
    retain_positive_edges,
    load_time_series_from_processed,
    compute_connectivity_for_subject,
    compute_all_connectivity
)

class TestComputeCorrelationMatrix:
    """Tests for compute_correlation_matrix function."""
    
    def test_pearson_correlation_basic(self):
        """Test basic Pearson correlation computation."""
        # Create a simple time series with known correlation
        np.random.seed(42)
        n_timepoints = 100
        n_regions = 5
        
        # Create two perfectly correlated regions
        region1 = np.random.randn(n_timepoints)
        region2 = region1 * 2 + 1  # Perfectly correlated
        
        time_series = np.column_stack([region1, region2])
        
        corr_matrix = compute_correlation_matrix(time_series, method='pearson')
        
        # Check that the correlation between region1 and region2 is ~1.0
        assert abs(corr_matrix[0, 1] - 1.0) < 0.01
        # Check that the matrix is symmetric
        assert np.allclose(corr_matrix, corr_matrix.T)
        # Check that diagonal is 1.0
        assert np.allclose(np.diag(corr_matrix), 1.0)
    
    def test_pearson_correlation_independent(self):
        """Test correlation of independent time series."""
        np.random.seed(42)
        n_timepoints = 1000  # Large sample for better estimation
        n_regions = 3
        
        time_series = np.random.randn(n_timepoints, n_regions)
        
        corr_matrix = compute_correlation_matrix(time_series, method='pearson')
        
        # Correlations should be close to 0 for independent series
        off_diag = corr_matrix[~np.eye(corr_matrix.shape[0], dtype=bool)]
        assert np.all(np.abs(off_diag) < 0.1)  # Allow some small correlation due to finite sample
    
    def test_spearman_correlation(self):
        """Test Spearman correlation computation."""
        np.random.seed(42)
        n_timepoints = 100
        n_regions = 3
        
        time_series = np.random.randn(n_timepoints, n_regions)
        
        corr_matrix = compute_correlation_matrix(time_series, method='spearman')
        
        # Check basic properties
        assert corr_matrix.shape == (n_regions, n_regions)
        assert np.allclose(np.diag(corr_matrix), 1.0)
        assert np.allclose(corr_matrix, corr_matrix.T)
    
    def test_invalid_input_shape(self):
        """Test error handling for invalid input shape."""
        with pytest.raises(ValueError):
            compute_correlation_matrix(np.random.randn(10))  # 1D array
    
    def test_nan_handling(self):
        """Test handling of NaN values in time series."""
        time_series = np.random.randn(100, 5)
        time_series[0, 0] = np.nan  # Introduce a NaN
        
        corr_matrix = compute_correlation_matrix(time_series)
        
        # Should not raise an error
        assert not np.any(np.isnan(corr_matrix))

class TestRetainPositiveEdges:
    """Tests for retain_positive_edges function."""
    
    def test_retain_positive_basic(self):
        """Test basic positive edge retention."""
        corr_matrix = np.array([
            [1.0, 0.5, -0.3],
            [0.5, 1.0, -0.8],
            [-0.3, -0.8, 1.0]
        ])
        
        positive_matrix = retain_positive_edges(corr_matrix)
        
        expected = np.array([
            [1.0, 0.5, 0.0],
            [0.5, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])
        
        assert np.allclose(positive_matrix, expected)
    
    def test_custom_threshold(self):
        """Test with custom threshold."""
        corr_matrix = np.array([
            [1.0, 0.6, 0.4],
            [0.6, 1.0, 0.3],
            [0.4, 0.3, 1.0]
        ])
        
        positive_matrix = retain_positive_edges(corr_matrix, threshold=0.5)
        
        expected = np.array([
            [1.0, 0.6, 0.0],
            [0.6, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])
        
        assert np.allclose(positive_matrix, expected)
    
    def test_all_negative(self):
        """Test with all negative correlations."""
        corr_matrix = np.array([
            [1.0, -0.5, -0.3],
            [-0.5, 1.0, -0.8],
            [-0.3, -0.8, 1.0]
        ])
        
        positive_matrix = retain_positive_edges(corr_matrix)
        
        # Only diagonal should remain
        assert np.allclose(positive_matrix, np.eye(3))

class TestLoadTimeSeries:
    """Tests for load_time_series_from_processed function."""
    
    def test_load_existing_file(self):
        """Test loading an existing time series file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a dummy time series file
            subject_id = "100104"
            ts_data = np.random.randn(100, 5)
            df = pd.DataFrame(ts_data, columns=[f"region_{i}" for i in range(5)])
            df.insert(0, "subject_id", subject_id)
            df.to_csv(tmpdir / f"{subject_id}_preprocessed_ts.csv", index=False)
            
            loaded = load_time_series_from_processed(subject_id, tmpdir)
            
            assert loaded is not None
            assert loaded.shape == (100, 5)
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loaded = load_time_series_from_processed("999999", Path(tmpdir))
            assert loaded is None

class TestComputeConnectivityForSubject:
    """Tests for compute_connectivity_for_subject function."""
    
    def test_full_pipeline(self):
        """Test the full connectivity computation pipeline for a subject."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processed_dir = Path(tmpdir) / "processed"
            output_dir = Path(tmpdir) / "output"
            processed_dir.mkdir()
            output_dir.mkdir()
            
            # Create a dummy time series file
            subject_id = "100104"
            ts_data = np.random.randn(100, 5)
            df = pd.DataFrame(ts_data, columns=[f"region_{i}" for i in range(5)])
            df.insert(0, "subject_id", subject_id)
            df.to_csv(processed_dir / f"{subject_id}_preprocessed_ts.csv", index=False)
            
            result = compute_connectivity_for_subject(
                subject_id, processed_dir, output_dir
            )
            
            assert result is not None
            corr_matrix, output_path = result
            
            assert corr_matrix.shape == (5, 5)
            assert output_path.exists()
            
            # Check that negative edges are removed
            assert np.all(corr_matrix >= 0)

class TestComputeAllConnectivity:
    """Tests for compute_all_connectivity function."""
    
    def test_multiple_subjects(self):
        """Test connectivity computation for multiple subjects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processed_dir = Path(tmpdir) / "processed"
            output_dir = Path(tmpdir) / "output"
            processed_dir.mkdir()
            output_dir.mkdir()
            
            # Create dummy time series files for multiple subjects
            subject_ids = ["100104", "100206", "100308"]
            for subject_id in subject_ids:
                ts_data = np.random.randn(100, 5)
                df = pd.DataFrame(ts_data, columns=[f"region_{i}" for i in range(5)])
                df.insert(0, "subject_id", subject_id)
                df.to_csv(processed_dir / f"{subject_id}_preprocessed_ts.csv", index=False)
            
            results = compute_all_connectivity(
                subject_ids, processed_dir, output_dir
            )
            
            assert len(results) == 3
            for subject_id in subject_ids:
                assert subject_id in results
                assert results[subject_id]['status'] == 'success'
                assert results[subject_id]['shape'] == [5, 5]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])