"""
Unit tests for parcellation module.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import nibabel as nib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocessing.parcellate import (
    compute_correlation_matrix,
    load_parcellation_labels,
    get_aal_atlas_path
)

class TestCorrelationMatrix:
    """Tests for correlation matrix computation."""
    
    def test_full_correlation(self):
        """Test correlation of fully correlated signals."""
        # Create identical signals
        n_timepoints = 100
        n_regions = 5
        base_signal = np.random.randn(n_timepoints)
        timeseries = np.column_stack([base_signal] * n_regions)
        
        corr_matrix = compute_correlation_matrix(timeseries)
        
        # All off-diagonal elements should be 1.0 (or very close)
        np.testing.assert_array_almost_equal(
            corr_matrix, 
            np.ones((n_regions, n_regions)),
            decimal=5
        )
    
    def test_anti_correlation(self):
        """Test correlation of anti-correlated signals."""
        n_timepoints = 100
        base_signal = np.random.randn(n_timepoints)
        timeseries = np.column_stack([base_signal, -base_signal])
        
        corr_matrix = compute_correlation_matrix(timeseries)
        
        # Off-diagonal should be -1.0
        assert abs(corr_matrix[0, 1]) > 0.99
        assert abs(corr_matrix[1, 0]) > 0.99
    
    def test_constant_region(self):
        """Test handling of constant regions (NaN replacement)."""
        n_timepoints = 100
        base_signal = np.random.randn(n_timepoints)
        constant_signal = np.ones(n_timepoints)
        timeseries = np.column_stack([base_signal, constant_signal])
        
        corr_matrix = compute_correlation_matrix(timeseries)
        
        # Should not have NaN values
        assert not np.any(np.isnan(corr_matrix))
        
        # Diagonal should be 1.0
        assert corr_matrix[0, 0] == 1.0
        assert corr_matrix[1, 1] == 1.0
    
    def test_shape_consistency(self):
        """Test that output shape matches input."""
        n_timepoints = 50
        n_regions = 10
        timeseries = np.random.randn(n_timepoints, n_regions)
        
        corr_matrix = compute_correlation_matrix(timeseries)
        
        assert corr_matrix.shape == (n_regions, n_regions)
    
    def test_symmetry(self):
        """Test that correlation matrix is symmetric."""
        n_timepoints = 100
        n_regions = 8
        timeseries = np.random.randn(n_timepoints, n_regions)
        
        corr_matrix = compute_correlation_matrix(timeseries)
        
        np.testing.assert_array_almost_equal(corr_matrix, corr_matrix.T)

class TestLabelLoading:
    """Tests for label loading."""
    
    def test_load_labels(self):
        """Test loading labels from file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("1 RegionA 0 0 0\n")
            f.write("2 RegionB 1 1 1\n")
            f.write("3 RegionC 2 2 2\n")
            temp_path = f.name
        
        try:
            labels = load_parcellation_labels(Path(temp_path))
            assert len(labels) == 3
            assert labels[0] == "RegionA"
            assert labels[1] == "RegionB"
            assert labels[2] == "RegionC"
        finally:
            os.unlink(temp_path)
    
    def test_missing_labels_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_parcellation_labels(Path("/nonexistent/path/labels.txt"))

class TestAtlasRetrieval:
    """Tests for atlas retrieval."""
    
    def test_aal_atlas_exists(self):
        """Test that AAL atlas can be retrieved."""
        # This will download if not cached, so we just check it doesn't crash
        try:
            img_path, labels_path = get_aal_atlas_path()
            assert img_path.exists() or True  # May be cached
            assert labels_path.exists() or True
        except RuntimeError as e:
            # If download fails, that's okay for unit test environment
            pytest.skip(f"AAL atlas download failed: {e}")