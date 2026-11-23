"""
Integration test for saliency mapping pipeline.
Verifies that the saliency mapping module produces valid gradients for the GNN model.
"""
import pytest
import torch
import numpy as np
from pathlib import Path

# Add project root to path if running standalone
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from attribution.saliency_mapping import compute_saliency
from models.schnet_gnn import SchNetGNN


class TestSaliencyMappingPipeline:
    """Integration tests for the saliency mapping functionality."""

    def test_saliency_mapping_produces_valid_gradients(self):
        """
        Assert gradient validity:
        1. Gradients exist and are not None
        2. Gradients have the same shape as the input node features
        3. Gradients are not all zeros (model is sensitive to input)
        4. Gradients are finite (no NaN or Inf)
        """
        # Setup: Create a minimal mock dataset and model
        # We simulate a single molecule with 5 atoms
        batch_size = 1
        num_atoms = 5
        num_features = 10  # Feature dimension for node embeddings

        # Create random node features (simulating embeddings)
        # Shape: [batch_size, num_atoms, num_features]
        node_features = torch.randn(batch_size, num_atoms, num_features, requires_grad=True)
        
        # Create edge index for a simple fully connected graph (or sparse)
        # Shape: [2, num_edges]
        num_edges = num_atoms * num_atoms
        edge_index = torch.zeros(2, num_edges, dtype=torch.long)
        for i in range(num_atoms):
            for j in range(num_atoms):
                idx = i * num_atoms + j
                edge_index[0, idx] = i
                edge_index[1, idx] = j

        # Initialize a small SchNet model for testing
        # hidden_channels=16, num_filters=8, num_interactions=2, num_gaussians=16
        model = SchNetGNN(
            hidden_channels=16,
            num_filters=8,
            num_interactions=2,
            num_gaussians=16,
            num_targets=1
        )
        model.eval()

        # Execute: Compute saliency map
        # The saliency map should compute gradients of the output w.r.t. input features
        saliency_map = compute_saliency(model, node_features, edge_index)

        # Assert: Check 1 - Saliency map exists and is not None
        assert saliency_map is not None, "Saliency map should not be None"

        # Assert: Check 2 - Shape matches input features
        assert saliency_map.shape == node_features.shape, (
            f"Saliency map shape {saliency_map.shape} should match input shape {node_features.shape}"
        )

        # Assert: Check 3 - Gradients are not all zeros (model must be sensitive)
        # We use a small threshold to account for floating point precision
        non_zero_count = torch.count_nonzero(torch.abs(saliency_map))
        assert non_zero_count > 0, "Saliency map should not be all zeros; model should be sensitive to input"

        # Assert: Check 4 - Gradients are finite (no NaN or Inf)
        assert torch.all(torch.isfinite(saliency_map)), (
            "Saliency map contains NaN or Inf values. Check for numerical instability."
        )

        # Optional: Verify that the sum of absolute gradients is reasonable
        # This ensures the gradients are not vanishingly small
        total_magnitude = torch.sum(torch.abs(saliency_map))
        assert total_magnitude > 1e-6, "Total gradient magnitude is too small; potential vanishing gradient issue"

        print(f"✓ Saliency mapping test passed. Gradient shape: {saliency_map.shape}, "
              f"Non-zero elements: {non_zero_count}, Total magnitude: {total_magnitude:.6f}")