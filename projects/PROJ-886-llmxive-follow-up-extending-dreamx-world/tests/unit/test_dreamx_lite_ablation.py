"""
Unit tests for DreamXLite model ablation.

This test suite verifies:
1. The fixed projection layer is non-trainable.
2. The parameter count is reduced compared to a hypothetical learned version.
3. The model accepts 4x4 camera extrinsic matrices without error.
4. Deterministic output on fixed input.
"""
import torch
import pytest
import os
import sys

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.models.dreamx_lite import DreamXLite, create_dreamx_lite_model
from code.utils.config import set_global_seed


class TestDreamXLiteAblation:
    """Tests for DreamXLite ablation properties."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        set_global_seed(42)
        self.embedding_dim = 768
        self.device = "cpu"

    def test_fixed_projection_is_non_trainable(self):
        """Verify that the fixed_projection layer has requires_grad=False."""
        model = create_dreamx_lite_model(
            pretrained_path=None,
            embedding_dim=self.embedding_dim,
            device=self.device
        )

        assert hasattr(model, 'fixed_projection'), "Model must have fixed_projection attribute"

        # Check that the layer itself is non-trainable
        assert not model.fixed_projection.requires_grad, "fixed_projection layer must be non-trainable"

        # Check that all parameters in the layer are non-trainable
        for param in model.fixed_projection.parameters():
            assert not param.requires_grad, f"Parameter {param} in fixed_projection must be non-trainable"

    def test_parameter_count_reduction(self):
        """Verify that the fixed projection reduces parameter count compared to a learned version."""
        model = create_dreamx_lite_model(
            pretrained_path=None,
            embedding_dim=self.embedding_dim,
            device=self.device
        )

        # Calculate total trainable parameters
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())

        # The fixed projection layer (16 * 768) should be frozen
        # In a learned version, this would be trainable
        expected_frozen_params = 16 * self.embedding_dim  # 12288

        # Verify that the frozen parameters count matches expectation
        frozen_params = total_params - trainable_params
        assert frozen_params >= expected_frozen_params, \
            f"Expected at least {expected_frozen_params} frozen params, got {frozen_params}"

        # Verify that the model is not entirely non-trainable (base model should have trainable params)
        assert trainable_params > 0, "Model must have some trainable parameters from the base model"

    def test_accepts_4x4_camera_extrinsics(self):
        """Verify that the model accepts 4x4 camera extrinsic matrices."""
        model = create_dreamx_lite_model(
            pretrained_path=None,
            embedding_dim=self.embedding_dim,
            device=self.device
        )

        # Create a dummy 4x4 camera extrinsic matrix
        camera_extrinsics = torch.eye(4, 4, dtype=torch.float32)

        # Create a dummy latent tensor (batch_size=1, seq_len=16, dim=embedding_dim)
        latent = torch.randn(1, 16, self.embedding_dim, dtype=torch.float32)

        # Forward pass should not raise an error
        try:
            output = model(
                latent=latent,
                camera_extrinsics=camera_extrinsics,
                timestep=torch.tensor([0.5], dtype=torch.float32)
            )
            assert isinstance(output, torch.Tensor), "Output must be a tensor"
            assert output.shape[0] == 1, "Batch size should be preserved"
        except Exception as e:
            pytest.fail(f"Model failed to accept 4x4 camera extrinsics: {e}")

    def test_deterministic_output_on_fixed_input(self):
        """Verify that the model produces deterministic output on fixed input."""
        # Set seed
        set_global_seed(12345)
        model1 = create_dreamx_lite_model(
            pretrained_path=None,
            embedding_dim=self.embedding_dim,
            seed=12345,
            device=self.device
        )

        set_global_seed(12345)
        model2 = create_dreamx_lite_model(
            pretrained_path=None,
            embedding_dim=self.embedding_dim,
            seed=12345,
            device=self.device
        )

        # Create identical inputs
        torch.manual_seed(12345)
        latent = torch.randn(1, 16, self.embedding_dim, dtype=torch.float32)
        camera_extrinsics = torch.randn(4, 4, dtype=torch.float32)
        timestep = torch.tensor([0.5], dtype=torch.float32)

        # Forward pass
        output1 = model1(latent=latent, camera_extrinsics=camera_extrinsics, timestep=timestep)
        output2 = model2(latent=latent, camera_extrinsics=camera_extrinsics, timestep=timestep)

        # Verify outputs are identical
        assert torch.allclose(output1, output2, atol=1e-6), \
            "Outputs should be identical for identical inputs and seeds"

    def test_projection_layer_dimensions(self):
        """Verify that the projection layer has correct input/output dimensions."""
        model = create_dreamx_lite_model(
            pretrained_path=None,
            embedding_dim=self.embedding_dim,
            device=self.device
        )

        # Input dimension should be 16 (flattened 4x4 matrix)
        assert model.fixed_projection.in_features == 16, \
            f"Expected in_features=16, got {model.fixed_projection.in_features}"

        # Output dimension should match embedding_dim
        assert model.fixed_projection.out_features == self.embedding_dim, \
            f"Expected out_features={self.embedding_dim}, got {model.fixed_projection.out_features}"

        # Bias should be False as per specification
        assert model.fixed_projection.bias is None, \
            "Projection layer should not have bias"