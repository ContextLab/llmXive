import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.connectivity import fisher_z_transform, compute_pearson_correlation_chunked, process_subject_connectivity
from utils.memory_monitor import MemoryLimitExceeded

class TestFisherZTransform:
    def test_fisher_z_basic(self):
        """Test Fisher Z-transform logic with known values."""
        # r = 0.5 -> z = 0.5 * ln((1.5)/(0.5)) = 0.5 * ln(3) ≈ 0.5493
        r_val = 0.5
        expected_z = 0.5 * np.log(3)
        
        # Create a small matrix
        r_matrix = np.array([[1.0, r_val], [r_val, 1.0]])
        z_matrix = fisher_z_transform(r_matrix)
        
        assert np.abs(z_matrix[0, 1] - expected_z) < 1e-6, f"Expected {expected_z}, got {z_matrix[0, 1]}"
        # Diagonal should remain 0 (since z(1) is infinite, but we clip)
        # Our implementation clips 1.0 to 0.9999, so z(0.9999) is large but finite.
        # We just check it's not NaN.
        assert not np.isnan(z_matrix[0, 0])
        
    def test_fisher_z_negative(self):
        """Test Fisher Z-transform with negative correlation."""
        r_val = -0.5
        expected_z = -0.5 * np.log(3)
        
        r_matrix = np.array([[1.0, r_val], [r_val, 1.0]])
        z_matrix = fisher_z_transform(r_matrix)
        
        assert np.abs(z_matrix[0, 1] - expected_z) < 1e-6

    def test_fisher_z_clipping(self):
        """Test that values of 1.0 and -1.0 are handled without inf."""
        r_matrix = np.array([[1.0, 1.0, -1.0], [1.0, 1.0, -1.0], [-1.0, -1.0, 1.0]])
        z_matrix = fisher_z_transform(r_matrix)
        
        # Should not contain inf or nan
        assert not np.any(np.isinf(z_matrix))
        assert not np.any(np.isnan(z_matrix))

class TestPearsonCorrelationChunked:
    def test_compute_pearson_correlation_chunked_identity(self):
        """Test correlation of a signal with itself is 1."""
        # Create data where columns are identical
        n_timepoints = 100
        n_rois = 10
        data = np.random.randn(n_timepoints, n_rois)
        # Make column 0 and 1 identical
        data[:, 1] = data[:, 0]
        
        corr_matrix = compute_pearson_correlation_chunked(data, chunk_size=5)
        
        assert np.abs(corr_matrix[0, 1] - 1.0) < 1e-5
        assert np.abs(corr_matrix[1, 0] - 1.0) < 1e-5
        assert np.abs(corr_matrix[0, 0] - 1.0) < 1e-5

    def test_compute_pearson_correlation_chunked_symmetry(self):
        """Test that the resulting matrix is symmetric."""
        n_timepoints = 200
        n_rois = 20
        data = np.random.randn(n_timepoints, n_rois)
        
        corr_matrix = compute_pearson_correlation_chunked(data, chunk_size=7)
        
        # Check symmetry
        diff = np.max(np.abs(corr_matrix - corr_matrix.T))
        assert diff < 1e-6, f"Matrix not symmetric: max diff {diff}"

class TestProcessSubjectConnectivity:
    def test_process_subject_connectivity_integration(self, tmp_path):
        """Integration test: create mock fMRI data and process it."""
        # Setup
        subject_id = "sub_test_001"
        fmri_dir = tmp_path / "fmri"
        fmri_dir.mkdir()
        
        # Create mock fMRI data (100 timepoints, 400 ROIs)
        n_timepoints = 100
        n_rois = 400
        mock_data = np.random.randn(n_timepoints, n_rois)
        fmri_file = fmri_dir / f"{subject_id}_timeseries.npy"
        np.save(str(fmri_file), mock_data)
        
        atlas_path = str(tmp_path / "dummy_atlas.parquet")
        Path(atlas_path).touch()
        
        # Run
        result = process_subject_connectivity(subject_id, str(fmri_file), atlas_path)
        
        # Assert
        assert result is not None
        assert result.shape == (n_rois, n_rois)
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
        # Diagonal should be approx 0 (z-transform of 1 is large, but we clipped)
        # Actually, z-transform of 1 is infinity, but we clip to 0.9999.
        # The diagonal of correlation matrix is 1.0, so z-transform of 1.0 (clipped) is large.
        # We just check it's not NaN.
        assert not np.any(np.isnan(np.diag(result)))
    
    def test_process_subject_connectivity_missing_file(self, tmp_path):
        """Test handling of missing fMRI file."""
        subject_id = "sub_missing"
        fmri_path = str(tmp_path / "missing.npy")
        atlas_path = str(tmp_path / "dummy.parquet")
        
        result = process_subject_connectivity(subject_id, fmri_path, atlas_path)
        assert result is None
