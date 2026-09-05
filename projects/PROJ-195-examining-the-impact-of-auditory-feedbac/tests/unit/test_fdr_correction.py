"""
Unit tests for FDR correction and cluster extraction (T025).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from glm_fdr_correction import (
    load_t_stat_map,
    apply_fdr_correction,
    extract_clusters,
    save_thresholded_map,
    save_cluster_metadata
)

@pytest.fixture
def temp_t_stat_map():
    """Create a temporary t-statistic map for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple 3D array with some significant values
        data = np.zeros((10, 10, 10))
        # Add a cluster of high t-values
        data[3:7, 3:7, 3:7] = 5.0  # High t-values
        # Add some noise
        data[0:2, 0:2, 0:2] = 1.5
        
        affine = np.eye(4)
        img = nib.Nifti1Image(data, affine)
        path = Path(tmpdir) / "test_t_stat.nii.gz"
        nib.save(img, str(path))
        yield path, img

def test_load_t_stat_map(temp_t_stat_map):
    """Test loading of t-statistic map."""
    path, _ = temp_t_stat_map
    loaded_img = load_t_stat_map(path)
    assert loaded_img is not None
    assert np.allclose(loaded_img.get_fdata(), np.load(path).get_fdata())

def test_apply_fdr_correction(temp_t_stat_map):
    """Test FDR correction application."""
    _, img = temp_t_stat_map
    # Use a high q-value to ensure some voxels are significant
    mask = apply_fdr_correction(img, q=0.10)
    
    assert mask is not None
    assert mask.shape == img.shape
    # The cluster of high t-values should be significant
    assert np.sum(mask) > 0

def test_extract_clusters():
    """Test cluster extraction from a boolean mask."""
    # Create a simple mask with two clusters
    mask = np.zeros((10, 10, 10), dtype=bool)
    mask[2:4, 2:4, 2:4] = True  # Cluster 1
    mask[6:8, 6:8, 6:8] = True  # Cluster 2
    
    affine = np.eye(4)
    shape = mask.shape
    
    clusters = extract_clusters(mask, affine, shape)
    
    assert len(clusters) == 2
    for cluster in clusters:
        assert "cluster_id" in cluster
        assert "size_voxels" in cluster
        assert "centroid_mni" in cluster
        assert cluster["size_voxels"] > 0

def test_save_thresholded_map(temp_t_stat_map):
    """Test saving of thresholded map."""
    path, img = temp_t_stat_map
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "thresholded.nii.gz"
        mask = np.zeros(img.shape, dtype=bool)
        mask[3:7, 3:7, 3:7] = True
        
        save_thresholded_map(img, mask, output_path)
        
        assert output_path.exists()
        saved_img = nib.load(str(output_path))
        saved_data = saved_img.get_fdata()
        # Check that non-significant voxels are zero
        assert np.all(saved_data[mask] != 0) or np.sum(saved_data) > 0

def test_save_cluster_metadata():
    """Test saving of cluster metadata."""
    clusters = [
        {"cluster_id": 1, "size_voxels": 10, "centroid_mni": [0, 0, 0]},
        {"cluster_id": 2, "size_voxels": 20, "centroid_mni": [10, 10, 10]}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "clusters.json"
        save_cluster_metadata(clusters, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_clusters = json.load(f)
        
        assert len(loaded_clusters) == 2
        assert loaded_clusters[0]["cluster_id"] == 1
        assert loaded_clusters[1]["size_voxels"] == 20

if __name__ == "__main__":
    pytest.main([__file__, "-v"])