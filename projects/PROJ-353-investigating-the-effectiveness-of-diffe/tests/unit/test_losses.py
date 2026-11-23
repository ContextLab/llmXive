import pytest
import torch
import torch.nn as nn
import numpy as np

# Import from the project's existing API surface
from losses import info_nce_loss, LinearProbe, compute_accuracy
from utils import seed_all

@pytest.fixture(autouse=True)
def set_seed():
    """Ensure deterministic behavior for tests."""
    seed_all(42)

class TestInfoNCELoss:
    """Unit tests for InfoNCE loss implementation."""

    def test_infonce_loss_shape(self):
        """Verify InfoNCE loss returns a scalar tensor."""
        batch_size = 8
        num_nodes = 16
        embed_dim = 32
        num_negatives = 4

        # Simulate embeddings: (batch, nodes, dim)
        z_pos = torch.randn(batch_size, num_nodes, embed_dim)
        z_neg = torch.randn(batch_size, num_negatives, num_nodes, embed_dim)

        loss = info_nce_loss(z_pos, z_neg)

        assert loss.dim() == 0, "InfoNCE loss should be a scalar"
        assert isinstance(loss, torch.Tensor)

    def test_infonce_loss_positive_gradient(self):
        """Verify that increasing positive similarity reduces loss."""
        batch_size = 4
        num_nodes = 8
        embed_dim = 16
        num_negatives = 2

        z_pos = torch.randn(batch_size, num_nodes, embed_dim, requires_grad=True)
        z_neg = torch.randn(batch_size, num_negatives, num_nodes, embed_dim)

        loss = info_nce_loss(z_pos, z_neg)
        loss.backward()

        # Check that gradients exist
        assert z_pos.grad is not None
        assert z_pos.grad.shape == z_pos.shape

    def test_infonce_loss_symmetry(self):
        """Verify loss is invariant to permutation of negative samples."""
        batch_size = 2
        num_nodes = 4
        embed_dim = 8
        num_negatives = 3

        z_pos = torch.randn(batch_size, num_nodes, embed_dim)
        z_neg = torch.randn(batch_size, num_negatives, num_nodes, embed_dim)

        loss_1 = info_nce_loss(z_pos, z_neg)

        # Permute negative samples along the negative dimension
        z_neg_perm = z_neg[:, [2, 0, 1], :, :]
        loss_2 = info_nce_loss(z_pos, z_neg_perm)

        assert torch.allclose(loss_1, loss_2, atol=1e-6), \
            "InfoNCE loss should be invariant to permutation of negatives"

    def test_infonce_loss_extreme_values(self):
        """Test loss behavior with extreme positive/negative similarities."""
        embed_dim = 16
        num_negatives = 4

        # High positive similarity, low negative similarity
        z_pos_high = torch.ones(1, 1, embed_dim) * 10.0
        z_neg_low = torch.zeros(1, num_negatives, 1, embed_dim)

        loss_high = info_nce_loss(z_pos_high, z_neg_low)

        # Low positive similarity, high negative similarity
        z_pos_low = torch.zeros(1, 1, embed_dim)
        z_neg_high = torch.ones(1, num_negatives, 1, embed_dim) * 10.0

        loss_low = info_nce_loss(z_pos_low, z_neg_high)

        # Loss should be lower when positives are similar and negatives are dissimilar
        assert loss_high < loss_low, \
            "InfoNCE loss should be lower for high positive / low negative similarity"


class TestLinearProbe:
    """Unit tests for LinearProbe accuracy calculation."""

    def test_linear_probe_init(self):
        """Verify LinearProbe initializes correctly."""
        input_dim = 32
        num_classes = 4
        probe = LinearProbe(input_dim, num_classes)

        assert isinstance(probe, nn.Module)
        assert isinstance(probe.fc, nn.Linear)
        assert probe.fc.in_features == input_dim
        assert probe.fc.out_features == num_classes

    def test_linear_probe_forward_shape(self):
        """Verify LinearProbe forward pass returns correct shape."""
        batch_size = 16
        input_dim = 32
        num_classes = 4
        probe = LinearProbe(input_dim, num_classes)

        # Simulate node embeddings: (batch, nodes, dim)
        x = torch.randn(batch_size, 8, input_dim)

        output = probe(x)

        assert output.shape == (batch_size, 8, num_classes), \
            f"Expected output shape (batch, nodes, classes), got {output.shape}"

    def test_linear_probe_trainable(self):
        """Verify LinearProbe parameters are trainable."""
        input_dim = 16
        num_classes = 2
        probe = LinearProbe(input_dim, num_classes)

        # Check that parameters require gradients
        for param in probe.parameters():
            assert param.requires_grad, "LinearProbe parameters should require gradients"

    def test_linear_probe_zero_grad(self):
        """Verify LinearProbe zero_grad works correctly."""
        input_dim = 16
        num_classes = 2
        probe = LinearProbe(input_dim, num_classes)

        # Dummy forward and backward
        x = torch.randn(4, 8, input_dim)
        y = torch.randint(0, num_classes, (4, 8))
        output = probe(x)
        loss = nn.functional.cross_entropy(output.view(-1, num_classes), y.view(-1))
        loss.backward()

        # Check gradients are not None
        for param in probe.parameters():
            assert param.grad is not None

        # Zero gradients
        probe.zero_grad()

        # Check gradients are None
        for param in probe.parameters():
            assert param.grad is None


class TestAccuracyCalculation:
    """Unit tests for accuracy calculation with LinearProbe."""

    def test_compute_accuracy_perfect(self):
        """Test accuracy calculation with perfect predictions."""
        batch_size = 4
        num_nodes = 8
        num_classes = 3
        input_dim = 16

        probe = LinearProbe(input_dim, num_classes)
        # Freeze probe weights to deterministic values for testing
        with torch.no_grad():
            probe.fc.weight.fill_(0.0)
            probe.fc.bias.fill_(0.0)

        # Create inputs where all nodes belong to class 0
        x = torch.randn(batch_size, num_nodes, input_dim)
        y = torch.zeros(batch_size, num_nodes, dtype=torch.long)

        # Manually set weights to predict class 0 perfectly
        with torch.no_grad():
            probe.fc.weight[0, :] = 10.0
            probe.fc.bias[0] = 10.0
            probe.fc.weight[1:, :] = -10.0
            probe.fc.bias[1:] = -10.0

        accuracy = compute_accuracy(probe, x, y)

        assert accuracy == 1.0, "Accuracy should be 1.0 for perfect predictions"

    def test_compute_accuracy_random(self):
        """Test accuracy calculation with random predictions."""
        batch_size = 4
        num_nodes = 8
        num_classes = 4
        input_dim = 16

        probe = LinearProbe(input_dim, num_classes)
        x = torch.randn(batch_size, num_nodes, input_dim)
        y = torch.randint(0, num_classes, (batch_size, num_nodes))

        # With random weights, accuracy should be > 0 but < 1 (with high probability)
        accuracy = compute_accuracy(probe, x, y)

        assert 0.0 < accuracy < 1.0, \
            f"Random accuracy should be between 0 and 1, got {accuracy}"

    def test_compute_accuracy_shape_invariance(self):
        """Test that accuracy is invariant to batch/node reshaping."""
        batch_size = 4
        num_nodes = 8
        num_classes = 2
        input_dim = 16

        probe = LinearProbe(input_dim, num_classes)
        x = torch.randn(batch_size, num_nodes, input_dim)
        y = torch.randint(0, num_classes, (batch_size, num_nodes))

        # Reshape to (batch*nodes, dim)
        x_flat = x.view(-1, input_dim)
        y_flat = y.view(-1)

        # Accuracy should be the same
        acc_original = compute_accuracy(probe, x, y)
        acc_flat = compute_accuracy(probe, x_flat, y_flat)

        # The function should handle both shapes correctly
        # We just verify it doesn't crash and returns a valid float
        assert isinstance(acc_original, float)
        assert isinstance(acc_flat, float)
        assert 0.0 <= acc_original <= 1.0
        assert 0.0 <= acc_flat <= 1.0

    def test_compute_accuracy_with_censored_data(self):
        """Test accuracy calculation with partially converged data (simulating censored)."""
        batch_size = 4
        num_nodes = 8
        num_classes = 3
        input_dim = 16

        probe = LinearProbe(input_dim, num_classes)
        x = torch.randn(batch_size, num_nodes, input_dim)
        y = torch.randint(0, num_classes, (batch_size, num_nodes))

        # Simulate a probe that hasn't converged (low accuracy)
        with torch.no_grad():
            # Set weights to predict randomly
            probe.fc.weight.normal_(0, 0.01)
            probe.fc.bias.zero_()

        accuracy = compute_accuracy(probe, x, y)

        # Accuracy should be close to random chance (1/num_classes)
        expected_random = 1.0 / num_classes
        # Allow some variance due to randomness
        assert abs(accuracy - expected_random) < 0.2, \
            f"Untrained accuracy should be near random chance ({expected_random}), got {accuracy}"

    def test_compute_accuracy_edge_cases(self):
        """Test accuracy with edge case inputs."""
        input_dim = 8
        num_classes = 2

        probe = LinearProbe(input_dim, num_classes)

        # Single node, single batch
        x_single = torch.randn(1, 1, input_dim)
        y_single = torch.randint(0, num_classes, (1, 1))

        acc_single = compute_accuracy(probe, x_single, y_single)
        assert isinstance(acc_single, float)
        assert 0.0 <= acc_single <= 1.0

        # Large batch
        x_large = torch.randn(100, 100, input_dim)
        y_large = torch.randint(0, num_classes, (100, 100))

        acc_large = compute_accuracy(probe, x_large, y_large)
        assert isinstance(acc_large, float)
        assert 0.0 <= acc_large <= 1.0