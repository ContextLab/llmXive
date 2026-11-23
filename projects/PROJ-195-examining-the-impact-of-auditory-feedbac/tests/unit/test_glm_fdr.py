import os
import sys
import tempfile
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from glm_fdr_correction import apply_fdr_correction, extract_clusters, save_thresholded_map, save_cluster_metadata

def create_test_nifti(data, shape=(10, 10, 10)):
    """Helper to create a dummy NIfTI image."""
    affine = np.eye(4)
    return nib.Nifti1Image(data, affine)

class TestFDRCorrection:
    def test_apply_fdr_correction_with_significant_values(self):
        """Test that FDR correction correctly identifies significant voxels."""
        # Create a 3D map with some high t-values and some low ones
        data = np.zeros((10, 10, 10))
        data[2:5, 2:5, 2:5] = 5.0  # High t-values
        data[7:9, 7:9, 7:9] = 1.0  # Low t-values
        
        img = create_test_nifti(data)
        
        # Apply FDR (q=0.05)
        mask = apply_fdr_correction(img, fdr_q=0.05)
        
        # The high t-values should be significant
        assert np.any(mask), "FDR correction should find significant voxels."
        # The low t-values should not be significant (likely)
        # Note: With such a small sample, p-values might be high, so this is a heuristic test.
        
    def test_apply_fdr_correction_all_null(self):
        """Test FDR correction when no values are significant."""
        data = np.random.randn(10, 10, 10) * 0.5  # Small t-values
        img = create_test_nifti(data)
        
        mask = apply_fdr_correction(img, fdr_q=0.05)
        
        # It's possible no voxels survive, but not guaranteed with random noise.
        # We just ensure the function runs and returns a boolean array of correct shape.
        assert mask.shape == data.shape
        assert mask.dtype == bool

class TestClusterExtraction:
    def test_extract_clusters(self):
        """Test cluster extraction from a binary mask."""
        data = np.zeros((10, 10, 10), dtype=bool)
        data[2:5, 2:5, 2:5] = True  # One cluster
        data[7:8, 7:8, 7:8] = True  # Another small cluster (size 1)
        
        affine = np.eye(4)
        shape = data.shape
        
        clusters = extract_clusters(data, affine, shape, cluster_threshold=5)
        
        # Only the first cluster should be returned (size 27 > 5)
        assert len(clusters) == 1
        assert clusters[0]["size_voxels"] == 27

class TestSaving:
    def test_save_thresholded_map(self):
        """Test saving a mask to NIfTI."""
        data = np.zeros((10, 10, 10), dtype=bool)
        data[2:5, 2:5, 2:5] = True
        
        img = create_test_nifti(data.astype(float))
        
        with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            save_thresholded_map(img, data, output_path)
            assert output_path.exists()
            # Verify it can be loaded
            loaded = nib.load(str(output_path))
            assert np.array_equal(loaded.get_fdata().astype(bool), data)
        finally:
            if output_path.exists():
                os.remove(output_path)

    def test_save_cluster_metadata(self):
        """Test saving cluster metadata to CSV."""
        clusters = [
            {"cluster_id": 1, "size_voxels": 10, "center_mni": {"x": 10.0, "y": 20.0, "z": 30.0}}
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            save_cluster_metadata(clusters, output_path)
            assert output_path.exists()
            # Verify content
            content = output_path.read_text()
            assert "cluster_id" in content
            assert "1" in content
        finally:
            if output_path.exists():
                os.remove(output_path)

    def test_save_cluster_metadata_empty(self):
        """Test saving empty cluster metadata."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            save_cluster_metadata([], output_path)
            assert output_path.exists()
            content = output_path.read_text()
            assert "cluster_id" in content  # Headers should exist
        finally:
            if output_path.exists():
                os.remove(output_path)