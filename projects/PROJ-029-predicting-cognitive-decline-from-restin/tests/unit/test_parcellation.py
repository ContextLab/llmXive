"""
Unit tests for AAL atlas parcellation logic.

Tests the loading of the AAL atlas mask and the creation of a dummy
parcellation workflow to ensure the utility functions in utils.graph
are correctly wired and handle expected inputs.
"""
import pytest
import numpy as np
import nibabel as nib
from pathlib import Path
import tempfile
import os

# Import the function under test from the project's utility module
# Note: We are testing the logic of load_aal_atlas_mask and its interaction
# with the graph utilities as per the API surface provided in T005.
from utils.graph import load_aal_atlas_mask, create_graph_from_adjacency

# Mock data helper to create a dummy AAL-style mask file
def create_dummy_atlas_file(filepath: Path, shape: tuple = (90, 90, 90)):
    """
    Creates a dummy NIfTI file with integer labels 1..90 to simulate AAL atlas.
    """
    # Create a 3D volume where each voxel has a label
    data = np.zeros(shape, dtype=np.int16)
    
    # Simulate 90 regions by filling distinct blocks or random sparse labels
    # For simplicity, we fill a few slices with specific IDs to ensure connectivity
    # and non-zero labels.
    for i in range(1, 91):
        # Assign label i to a specific region (simulated)
        # In a real AAL atlas, these are specific anatomical regions.
        # Here we just ensure the file has valid integer data > 0.
        if i <= 30:
            data[i, :, :] = i
        elif i <= 60:
            data[:, i-30, :] = i
        else:
            data[:, :, i-60] = i
    
    # Ensure at least some voxels have labels 1-90
    # We'll just fill a block for the first 90 to be safe
    data[:90, :1, :1] = np.arange(1, 91).reshape(-1, 1, 1)

    img = nib.Nifti1Image(data, affine=np.eye(4))
    nib.save(img, filepath)
    return filepath

class TestAALParcellation:
    """Test suite for AAL atlas loading and basic parcellation logic."""

    def test_load_aal_atlas_mask_file_exists(self, tmp_path):
        """Test that load_aal_atlas_mask correctly loads a valid file."""
        atlas_path = tmp_path / "aal_atlas.nii.gz"
        create_dummy_atlas_file(atlas_path)

        # The function expects a Path object
        mask_data = load_aal_atlas_mask(atlas_path)

        assert mask_data is not None
        assert isinstance(mask_data, np.ndarray)
        assert mask_data.shape == (90, 90, 90)
        # Check that labels 1-90 exist in the data
        unique_labels = np.unique(mask_data)
        # We expect labels 1 through 90 to be present
        for i in range(1, 91):
            assert i in unique_labels, f"Label {i} missing from atlas"

    def test_load_aal_atlas_mask_file_not_found(self, tmp_path):
        """Test that load_aal_atlas_mask raises FileNotFoundError for missing file."""
        missing_path = tmp_path / "non_existent_atlas.nii.gz"
        
        with pytest.raises(FileNotFoundError):
            load_aal_atlas_mask(missing_path)

    def test_load_aal_atlas_mask_invalid_extension(self, tmp_path):
        """Test that load_aal_atlas_mask handles invalid file extensions gracefully."""
        # Create a file with wrong extension
        invalid_path = tmp_path / "atlas.txt"
        invalid_path.write_text("dummy content")

        with pytest.raises(Exception):
            # nibabel should fail to load a text file as nifti
            load_aal_atlas_mask(invalid_path)

    def test_create_graph_from_adjacency_with_dummy_data(self, tmp_path):
        """
        Test the full flow: load atlas -> create adjacency (simulated) -> create graph.
        This verifies the integration of load_aal_atlas_mask with graph creation.
        """
        # 1. Create dummy atlas
        atlas_path = tmp_path / "test_atlas.nii.gz"
        create_dummy_atlas_file(atlas_path)
        
        # 2. Load the mask to get the number of regions (nodes)
        # The function returns the 3D array. We need to determine the number of unique labels.
        mask_data = load_aal_atlas_mask(atlas_path)
        unique_labels = np.unique(mask_data)
        # Filter out 0 (background)
        nodes = [int(l) for l in unique_labels if l != 0]
        n_nodes = len(nodes)
        
        assert n_nodes == 90, f"Expected 90 nodes, got {n_nodes}"

        # 3. Create a dummy adjacency matrix (90x90)
        # In a real scenario, this comes from fMRI correlation.
        # Here we create a random symmetric matrix.
        np.random.seed(42)
        adj_matrix = np.random.rand(n_nodes, n_nodes)
        adj_matrix = (adj_matrix + adj_matrix.T) / 2
        np.fill_diagonal(adj_matrix, 0) # No self-loops

        # 4. Create the graph
        G = create_graph_from_adjacency(adj_matrix)

        # 5. Verify graph properties
        assert G is not None
        assert len(G.nodes()) == n_nodes
        assert len(G.edges()) > 0 # Random matrix should have edges

        # Verify that the graph utilities work on this graph
        # e.g., calculate degree centrality
        from utils.graph import calculate_degree_centrality
        degree_centrality = calculate_degree_centrality(G)
        assert len(degree_centrality) == n_nodes

    def test_parcellation_label_range(self, tmp_path):
        """Verify that the loaded atlas contains the expected label range (1-90)."""
        atlas_path = tmp_path / "aal_atlas.nii.gz"
        create_dummy_atlas_file(atlas_path)
        
        mask_data = load_aal_atlas_mask(atlas_path)
        unique_labels = np.unique(mask_data)
        
        # Check min and max
        assert min(unique_labels) == 0  # Background
        assert max(unique_labels) == 90
        
        # Check count of non-zero labels
        non_zero_labels = unique_labels[unique_labels != 0]
        assert len(non_zero_labels) == 90
        assert set(non_zero_labels) == set(range(1, 91))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
