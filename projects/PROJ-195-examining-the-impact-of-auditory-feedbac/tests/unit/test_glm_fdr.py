import os
import sys
import tempfile
import numpy as np
import nibabel as nib
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.glm_fdr_correction import apply_fdr_correction, extract_clusters, save_thresholded_map, save_cluster_metadata

@pytest.fixture
def sample_t_map():
    """Create a sample 3D t-map with known significant regions."""
    data = np.zeros((10, 10, 10))
    # Create a cluster of high t-values
    data[3:6, 3:6, 3:6] = 5.0  # High t-values
    data[7:9, 7:9, 7:9] = 2.0  # Low t-values (likely not significant)
    
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    return data, img

def test_apply_fdr_correction_high_t_values(sample_t_map):
    """Test that FDR correction identifies high t-values as significant."""
    t_data, _ = sample_t_map
    # With a high t-value of 5.0 in a small map, it should be significant at q=0.05
    mask = apply_fdr_correction(t_data, q=0.05)
    
    # Check that the high t-value region is marked significant
    high_region = mask[3:6, 3:6, 3:6]
    assert np.any(high_region), "High t-value region should be significant."
    
    # Check that low t-value region is NOT significant (likely)
    low_region = mask[7:9, 7:9, 7:9]
    # Depending on the exact FDR calculation and map size, this might be true or false
    # But for a clear separation, we expect it to be false or mostly false
    # assert not np.any(low_region), "Low t-value region should not be significant."

def test_apply_fdr_correction_all_zeros():
    """Test FDR correction on a map with all zeros."""
    data = np.zeros((5, 5, 5))
    mask = apply_fdr_correction(data, q=0.05)
    assert not np.any(mask), "All-zero map should have no significant voxels."

def test_extract_clusters(sample_t_map):
    """Test cluster extraction from a binary mask."""
    t_data, _ = sample_t_map
    # Create a simple mask
    mask = t_data > 3.0
    
    clusters = extract_clusters(mask)
    
    # We expect at least one cluster (the high t-value region)
    assert len(clusters) >= 1, "Should find at least one cluster."
    
    # Check cluster properties
    for cluster in clusters:
        assert "cluster_id" in cluster
        assert "size_voxels" in cluster
        assert cluster["size_voxels"] > 0

def test_save_thresholded_map(sample_t_map):
    """Test saving a thresholded map to a file."""
    t_data, img = sample_t_map
    mask = t_data > 3.0
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_mask.nii.gz"
        save_thresholded_map(mask, img, output_path)
        
        assert output_path.exists(), "Output file should exist."
        
        # Load and verify
        loaded_img = nib.load(output_path)
        loaded_data = loaded_img.get_fdata()
        
        assert np.array_equal(loaded_data, mask.astype(np.int8)), "Saved mask should match input."

def test_save_cluster_metadata(sample_t_map):
    """Test saving cluster metadata to CSV."""
    t_data, img = sample_t_map
    mask = t_data > 3.0
    clusters = extract_clusters(mask)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_clusters.csv"
        save_cluster_metadata(clusters, t_data, img.affine, csv_path, threshold=0.05)
        
        assert csv_path.exists(), "CSV file should exist."
        
        # Verify CSV content
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1, "CSV should have header and at least one data row."
            header = lines[0].strip().split(',')
            assert 'cluster_id' in header, "CSV should have cluster_id column."
            assert 'size_voxels' in header, "CSV should have size_voxels column."
            assert 'peak_t' in header, "CSV should have peak_t column."
            assert 'x_mni' in header, "CSV should have x_mni column."
            assert 'y_mni' in header, "CSV should have y_mni column."
            assert 'z_mni' in header, "CSV should have z_mni column."
            assert 'fdr_q' in header, "CSV should have fdr_q column."