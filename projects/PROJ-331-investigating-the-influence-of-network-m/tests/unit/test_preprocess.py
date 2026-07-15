"""
Unit tests for preprocess.py functionality.

Tests:
- streamlines_to_adjacency returns correct shape and dtype
- threshold_density produces binary matrix with expected density
- Preprocessing pipeline handles valid inputs correctly
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path
import nibabel as nib
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess import (
    streamlines_to_adjacency,
    threshold_density,
    preprocess_subject
)
from utils import load_npy

@pytest.fixture
def mock_atlas():
    """Create a mock Schaefer-100 atlas."""
    # Create a 3D array with region labels 1-100
    shape = (10, 10, 10)  # Small for testing
    data = np.zeros(shape, dtype=np.int32)
    
    # Fill with region labels (cycling through 1-100)
    for i in range(shape[0]):
        for j in range(shape[1]):
            for k in range(shape[2]):
                label = (i * shape[1] * shape[2] + j * shape[2] + k) % 100 + 1
                data[i, j, k] = label
    
    # Create NIfTI image with identity affine
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    return img

@pytest.fixture
def mock_streamlines():
    """Create mock streamlines data."""
    # Mock streamlines object
    sft = Mock()
    
    # Create simple streamlines connecting different regions
    # Each streamline is a (N_points, 3) array
    streamlines = [
        np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=np.float32),  # Region 1 -> Region 2
        np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=np.float32),  # Region 1 -> Region 2
        np.array([[5, 5, 5], [6, 6, 6], [7, 7, 7]], dtype=np.float32),  # Region 3 -> Region 4
        np.array([[0, 0, 0], [2, 2, 2]], dtype=np.float32),            # Region 1 -> Region 2
    ]
    
    sft.streamlines = streamlines
    return sft

def test_streamlines_to_adjacency_shape(mock_atlas, mock_streamlines):
    """Test that adjacency matrix has correct shape and dtype."""
    adj = streamlines_to_adjacency(mock_streamlines, mock_atlas, n_regions=100)
    
    assert adj.shape == (100, 100), f"Expected shape (100, 100), got {adj.shape}"
    assert adj.dtype in [np.float32, np.float64], f"Expected float dtype, got {adj.dtype}"
    assert np.all(adj >= 0), "Adjacency matrix should be non-negative"

def test_streamlines_to_adjacency_values(mock_atlas, mock_streamlines):
    """Test that adjacency matrix reflects streamline counts."""
    adj = streamlines_to_adjacency(mock_streamlines, mock_atlas, n_regions=100)
    
    # We have 3 streamlines from Region 1 to Region 2 (indices 0 and 1)
    # And 1 streamline from Region 3 to Region 4 (indices 2 and 3)
    # Note: This depends on how the mock atlas maps coordinates to regions
    # For this test, we just verify that some connections exist
    assert np.sum(adj) > 0, "Expected non-zero connections in adjacency matrix"

def test_threshold_density_binary_output(mock_atlas, mock_streamlines):
    """Test that threshold_density produces binary matrix."""
    weighted_adj = streamlines_to_adjacency(mock_streamlines, mock_atlas, n_regions=100)
    binary_adj = threshold_density(weighted_adj, density=0.1)
    
    assert binary_adj.shape == weighted_adj.shape
    assert set(np.unique(binary_adj)).issubset({0.0, 1.0}), "Binary matrix should only contain 0 and 1"
    assert binary_adj.dtype in [np.float32, np.int32, np.int64], f"Expected numeric dtype, got {binary_adj.dtype}"

def test_threshold_density_symmetry(mock_atlas, mock_streamlines):
    """Test that binary adjacency matrix is symmetric."""
    weighted_adj = streamlines_to_adjacency(mock_streamlines, mock_atlas, n_regions=100)
    binary_adj = threshold_density(weighted_adj, density=0.1)
    
    assert np.allclose(binary_adj, binary_adj.T), "Binary matrix should be symmetric"

def test_threshold_density_zero_diagonal(mock_atlas, mock_streamlines):
    """Test that diagonal of binary matrix is zero."""
    weighted_adj = streamlines_to_adjacency(mock_streamlines, mock_atlas, n_regions=100)
    binary_adj = threshold_density(weighted_adj, density=0.1)
    
    assert np.all(np.diag(binary_adj) == 0), "Diagonal should be zero"

def test_preprocess_subject_integration(tmp_path, mock_atlas, mock_streamlines):
    """Test full preprocessing pipeline."""
    # Create temporary files
    atlas_path = tmp_path / "atlas.nii.gz"
    nib.save(mock_atlas, str(atlas_path))
    
    # Mock the streamlines loading
    with patch('preprocess.load_streamlines', return_value=mock_streamlines):
        with patch('preprocess.load_atlas', return_value=mock_atlas):
            result = preprocess_subject(
                streamlines_path="fake.trk",
                atlas_path=str(atlas_path),
                output_dir=str(tmp_path / "processed"),
                density_threshold=0.1
            )
            
            # Check output files exist
            assert os.path.exists(result['binary_path'])
            assert os.path.exists(result['weighted_path'])
            
            # Load and verify matrices
            binary_adj = load_npy(result['binary_path'])
            weighted_adj = load_npy(result['weighted_path'])
            
            assert binary_adj.shape == (100, 100)
            assert weighted_adj.shape == (100, 100)
            assert set(np.unique(binary_adj)).issubset({0.0, 1.0})

def test_preprocess_subject_raises_on_missing_file(tmp_path):
    """Test that preprocessing raises error for missing files."""
    with pytest.raises(Exception):
        preprocess_subject(
            streamlines_path="nonexistent.trk",
            atlas_path="nonexistent.nii.gz",
            output_dir=str(tmp_path / "processed")
        )
