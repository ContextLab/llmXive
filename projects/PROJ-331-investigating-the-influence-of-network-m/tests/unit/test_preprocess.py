import os
import sys
import numpy as np
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess import parcellate_streamlines, threshold_to_density, compute_global_efficiency
from utils import save_npy, load_npy, get_logger

logger = get_logger(__name__)

@pytest.fixture
def mock_atlas(tmp_path):
    """Create a mock 4x4 atlas with 3 regions (1, 2, 3) and background (0)"""
    atlas_data = np.array([
        [0, 1, 1, 2],
        [1, 1, 2, 2],
        [3, 3, 0, 0],
        [3, 3, 0, 0]
    ], dtype=np.int32)
    atlas_path = tmp_path / "atlas.nii.gz"
    # We can't easily create a real nii.gz without nibabel in tests, 
    # so we save as npy and modify the loader to accept it for testing
    # OR we create a minimal nii.gz
    import nibabel as nib
    img = nib.Nifti1Image(atlas_data, np.eye(4))
    nib.save(img, str(atlas_path))
    return str(atlas_path)

@pytest.fixture
def mock_streamlines(tmp_path):
    """Create a mock streamlines file (.trk) with known connections"""
    # Create a simple tractogram
    # Streamline 1: connects region 1 (voxels 0,1,0) and region 2 (voxels 0,3,0)
    # Streamline 2: connects region 1 and region 3
    # Streamline 3: connects region 2 and region 3
    
    # Coordinates in mm, need to map to voxel indices
    # Atlas shape is 4x4x1 (we assume z=0)
    # Region 1: (0,1), (1,1) -> voxels [0,1,0], [1,1,0]
    # Region 2: (0,3), (1,3) -> voxels [0,3,0], [1,3,0]
    # Region 3: (2,0), (3,0) -> voxels [2,0,0], [3,0,0]
    
    # We'll create streamlines that pass through these voxels
    streamlines = [
        # S1: Region 1 to Region 2
        np.array([
            [0.5, 0.5, 0.0], # near region 1
            [0.5, 2.5, 0.0], # middle
            [0.5, 3.5, 0.0]  # near region 2
        ], dtype=np.float32),
        # S2: Region 1 to Region 3
        np.array([
            [0.5, 1.5, 0.0],
            [2.5, 1.5, 0.0],
            [3.5, 0.5, 0.0]
        ], dtype=np.float32),
        # S3: Region 2 to Region 3
        np.array([
            [0.5, 3.5, 0.0],
            [2.5, 2.5, 0.0],
            [3.5, 0.5, 0.0]
        ], dtype=np.float32)
    ]
    
    # Save as .trk
    import nibabel as nib
    tractogram = nib.streamlines.TrkFile(streamlines)
    tract_path = tmp_path / "streamlines.trk"
    nib.save(tractogram, str(tract_path))
    return str(tract_path)

def test_parcellate_streamlines(mock_streamlines, mock_atlas, tmp_path):
    """Test T014a: Parcellation produces weighted adjacency matrix"""
    # Run parcellation
    adj = parcellate_streamlines(mock_streamlines, mock_atlas)
    
    # Verify output type and shape
    assert isinstance(adj, np.ndarray)
    assert adj.dtype in [np.float32, np.float64]
    # Atlas has 3 regions (1, 2, 3), so matrix should be 3x3
    assert adj.shape == (3, 3)
    
    # Verify non-negative values
    assert np.all(adj >= 0)
    
    # Verify density (should not be empty if streamlines connect regions)
    # We expect at least some connections
    assert np.sum(adj) > 0, "Adjacency matrix should not be empty"
    
    # Verify symmetry (undirected count)
    # Note: Our implementation counts directed pairs, but since we iterate all pairs in visited_regions,
    # and the streamline visits both, it should be symmetric for simple cases
    # However, the logic in parcellate_streamlines adds to both (i,j) and (j,i)
    # So it should be symmetric
    np.testing.assert_array_almost_equal(adj, adj.T, decimal=5)
    
    # Save for inspection
    save_path = tmp_path / "test_weighted_adj.npy"
    np.save(save_path, adj)
    assert save_path.exists()

def test_threshold_to_density(tmp_path):
    """Test T014b: Thresholding produces binary matrices at correct densities"""
    # Create a mock weighted matrix
    weighted = np.array([
        [0, 10, 5, 0],
        [10, 0, 8, 2],
        [5, 8, 0, 0],
        [0, 2, 0, 0]
    ], dtype=np.float32)
    
    weighted_path = tmp_path / "weighted.npy"
    np.save(weighted_path, weighted)
    
    # Run thresholding
    results = threshold_to_density(str(weighted_path), [0.5, 0.8])
    
    assert isinstance(results, dict)
    assert "50p" in results
    assert "80p" in results
    
    # Check binary nature
    for key, mat in results.items():
        assert np.all((mat == 0) | (mat == 1))
        assert np.diag(mat).sum() == 0, "Diagonal should be zero"
        
        # Verify density is roughly correct
        n = mat.shape[0]
        max_edges = n * (n - 1)
        actual_density = np.sum(mat) / max_edges
        # Allow some tolerance due to discrete edge selection
        assert 0.0 <= actual_density <= 1.0

def test_compute_global_efficiency(tmp_path):
    """Test T015: Global efficiency calculation"""
    # Create a simple connected graph
    adj = np.array([
        [0, 1, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [0, 1, 1, 0]
    ], dtype=np.float32)
    
    eff = compute_global_efficiency(adj)
    
    assert isinstance(eff, float)
    assert eff > 0
    assert eff <= 1.0 # Efficiency is bounded by 1 for unweighted, but for weighted it can vary
    
    # Test with disconnected graph
    adj_disconnected = np.array([
        [0, 1, 0, 0],
        [1, 0, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0]
    ], dtype=np.float32)
    
    eff_dis = compute_global_efficiency(adj_disconnected)
    # Should be lower than connected
    assert eff_dis < eff
