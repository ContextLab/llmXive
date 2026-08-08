import os
import sys
import pytest
import numpy as np
from pathlib import Path
import tempfile
import nibabel as nib

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocess import (
    load_streamlines,
    load_atlas,
    parcellate_streamlines,
    threshold_to_density,
    compute_global_efficiency
)
from utils import ProcessingError

class TestParcellateStreamlines:
    @pytest.fixture
    def mock_atlas(self, tmp_path):
        """Create a simple 3x3x3 atlas with 2 regions + background."""
        data = np.zeros((3, 3, 3), dtype=np.int16)
        data[0, :, :] = 1  # Region 1
        data[1, :, :] = 2  # Region 2
        # Region 3 would be at index 2, but let's keep it simple
        
        atlas_path = tmp_path / "atlas.nii.gz"
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, atlas_path)
        return str(atlas_path)

    @pytest.fixture
    def mock_streamlines(self, tmp_path, mock_atlas):
        """Create a simple .trk file with known streamlines."""
        # We need to create a tractogram object.
        # Since Dipy might not be installed in all test envs, we mock the logic
        # or create a minimal valid file if possible.
        # For this test, we will test the logic by creating a minimal streamlines list
        # and mocking the load function if necessary, but ideally we test the function.
        
        # Let's create a dummy .trk file using dipy if available
        try:
            from dipy.io.streamline import save_tractogram
            from dipy.tracking.streamline import Streamlines
            
            # Create streamlines that connect Region 1 (0,0,0) to Region 2 (1,1,1)
            # Coordinates are in voxel space for this simple test
            s1 = np.array([[0.5, 0.5, 0.5], [1.5, 1.5, 1.5]])
            s2 = np.array([[0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]) # Another one
            s3 = np.array([[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]) # Self loop (should be 0 or 1)
            
            streamlines = Streamlines([s1, s2, s3])
            
            # Save to tmp_path
            tractogram_path = tmp_path / "streamlines.trk"
            # Create a dummy header
            header = {'voxel_sizes': [1, 1, 1], 'voxel_order': 'RAS'}
            save_tractogram(streamlines, tractogram_path, affine=np.eye(4))
            return str(tractogram_path)
        except ImportError:
            pytest.skip("Dipy not available for streamline creation")

    def test_parcellate_streamlines_returns_weighted_adjacency(self, mock_streamlines, mock_atlas):
        """Verify parcellate_streamlines returns a numpy array of shape (N, N)."""
        if not mock_streamlines:
            pytest.skip("Streamlines not created")
        
        result = parcellate_streamlines(mock_streamlines, mock_atlas)
        
        assert isinstance(result, np.ndarray)
        assert result.dtype in [np.float32, np.float64]
        assert result.ndim == 2
        assert result.shape[0] == result.shape[1] # Square matrix
        
        # Check for non-negative values
        assert np.all(result >= 0)
        
        # Check density (should be non-zero if streamlines connect regions)
        # We have 2 streamlines connecting 1->2 and 1 self-loop
        # So we expect some non-zero entries
        density = np.count_nonzero(result) / (result.size)
        assert density > 0, "Matrix should not be empty if streamlines connect regions"

    def test_parcellate_streamlines_unthresholded(self, mock_streamlines, mock_atlas):
        """Verify the output is unthresholded (counts, not binary)."""
        if not mock_streamlines:
            pytest.skip("Streamlines not created")
        
        result = parcellate_streamlines(mock_streamlines, mock_atlas)
        
        # Check that values are > 1 for connected regions (since we added 2 streamlines)
        # The exact indices depend on the label mapping, but we check max value
        assert np.max(result) >= 2, "Expected unthresholded counts (at least 2 for one pair)"

class TestThresholdToDensity:
    @pytest.fixture
    def mock_weighted_adj(self, tmp_path):
        """Create a dummy weighted adjacency matrix."""
        data = np.array([
            [0, 10, 5, 2],
            [10, 0, 8, 1],
            [5, 8, 0, 3],
            [2, 1, 3, 0]
        ], dtype=np.float64)
        path = tmp_path / "weighted.npy"
        np.save(path, data)
        return str(path)

    def test_threshold_to_density_generates_binary_matrices(self, mock_weighted_adj):
        """Verify threshold_to_density creates binary matrices at specified densities."""
        result = threshold_to_density(mock_weighted_adj, thresholds=[0.1, 0.2, 0.3])
        
        assert "10p" in result
        assert "20p" in result
        assert "30p" in result
        
        for label, path in result.items():
            assert os.path.exists(path)
            mat = np.load(path)
            assert mat.dtype in [np.int32, np.int64, np.float32, np.float64]
            # Check binary nature (0 or 1)
            unique_vals = np.unique(mat)
            assert set(unique_vals).issubset({0, 1})

    def test_threshold_to_density_preserves_symmetry(self, mock_weighted_adj):
        """Verify binary matrices are symmetric."""
        result = threshold_to_density(mock_weighted_adj, thresholds=[0.1])
        path = result["10p"]
        mat = np.load(path)
        
        assert np.allclose(mat, mat.T)

class TestGlobalEfficiency:
    def test_compute_global_efficiency(self):
        """Verify global efficiency calculation."""
        # Simple 3-node fully connected graph
        adj = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ], dtype=np.float64)
        
        eff = compute_global_efficiency(adj)
        
        # For a fully connected graph with weight 1, distance is 1.
        # Efficiency = sum(1/1) / (3*2) = 6 / 6 = 1.0
        assert np.isclose(eff, 1.0)

    def test_compute_global_efficiency_disconnected(self):
        """Verify global efficiency handles disconnected components."""
        # 3 nodes, 1-2 connected, 3 isolated
        adj = np.array([
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 0]
        ], dtype=np.float64)
        
        eff = compute_global_efficiency(adj)
        # Distance 1-2 is 1, others are inf (0 in inverse)
        # Sum = 1 (1->2) + 1 (2->1) = 2
        # Denom = 3*2 = 6
        # Eff = 2/6 = 0.333
        assert eff < 1.0
        assert eff > 0
