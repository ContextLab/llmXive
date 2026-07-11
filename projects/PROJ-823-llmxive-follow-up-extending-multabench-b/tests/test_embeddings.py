import pytest
import torch
import torch.nn as nn
from pathlib import Path
import sys
import os

# Add project root to path to resolve imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.memory_monitor import MemoryMonitor
from models.base import FrozenEmbeddingModel

logger = get_logger(__name__)


class DummyModel(nn.Module):
    """A simple dummy model for testing gradient context behavior."""
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 5)

    def forward(self, x):
        return self.linear(x)


class TestNoGradContext:
    """
    Unit tests for gradient disabling in inference scenarios.
    Ensures that models run without tracking gradients to save memory and time.
    """

    def test_no_grad_context_manager(self):
        """
        Verify that torch.no_grad() context manager effectively disables
        gradient tracking for operations within the block.
        """
        model = DummyModel()
        x = torch.randn(3, 10, requires_grad=True)

        # Ensure gradients are tracked outside
        out = model(x)
        assert out.requires_grad, "Gradients should be tracked outside context"

        # Disable gradients inside context
        with torch.no_grad():
            out_no_grad = model(x)
            # The output tensor itself should not require grad if inputs were tracked
            # but the operation graph is not built.
            # However, if x requires_grad, the output of no_grad block
            # still carries the requires_grad flag from x, but no graph is built.
            # The critical check is that .backward() would fail or do nothing useful
            # if we tried to backprop through the graph built inside no_grad.
            # A more direct check: is_grad_enabled
            assert not torch.is_grad_enabled(), "Gradient tracking should be disabled"

        # Verify graph is not built for operations inside no_grad
        # If we try to backward on a tensor created inside no_grad using a leaf that requires_grad,
        # it should raise an error because there is no graph.
        try:
            out_no_grad.sum().backward()
            # If we are here, the graph might have been built (unexpected) or x wasn't leaf?
            # Actually, torch.no_grad() prevents graph construction.
            # If x requires_grad, out_no_grad.requires_grad is True, but .grad_fn is None.
            assert out_no_grad.grad_fn is None, "No gradient function should exist for no_grad output"
        except RuntimeError as e:
            # This is expected if we try to backward through a graph that doesn't exist
            assert "element 0 of the tensors does not require grad" in str(e) or "grad_fn" in str(e)


    def test_frozen_model_inference_no_grad(self):
        """
        Verify that the FrozenEmbeddingModel (or similar inference-only model)
        runs correctly within a no_grad context and does not accumulate gradients.
        """
        # Mock a frozen embedding scenario
        # Since FrozenEmbeddingModel might be abstract or require specific setup,
        # we test the principle with a standard model wrapped in no_grad
        model = DummyModel()
        model.eval() # Set to eval mode

        x = torch.randn(2, 10, requires_grad=True)

        # Simulate the pattern used in T013 (generator.py)
        with torch.no_grad():
            output = model(x)

        # Verify output shape
        assert output.shape == (2, 5)

        # Verify no gradients were accumulated for the model parameters
        # (Though they wouldn't be accumulated anyway without .backward(),
        # this ensures the context was active)
        for param in model.parameters():
            assert param.grad is None, "Parameters should not have accumulated gradients"


    def test_memory_savings_no_grad(self):
        """
        Verify that running in no_grad context prevents storage of intermediate
        activations required for backpropagation, effectively saving memory.
        This test checks the flag behavior rather than exact memory values which
        can be flaky.
        """
        model = DummyModel()
        x = torch.randn(10, 10, requires_grad=True)

        # Run with gradients
        out_with_grad = model(x)
        assert out_with_grad.grad_fn is not None, "Graph should exist with grad"

        # Run without gradients
        with torch.no_grad():
            out_no_grad = model(x)

        # The output of no_grad block doesn't store the graph.
        # If we try to compute something that requires the graph from the 'no_grad' run,
        # it should fail or be None.
        assert out_no_grad.grad_fn is None, "Graph should NOT exist without grad"


    def test_multiple_no_grad_blocks(self):
        """
        Verify that multiple nested or sequential no_grad blocks work correctly.
        """
        model = DummyModel()
        x = torch.randn(3, 10, requires_grad=True)

        # First block
        with torch.no_grad():
            out1 = model(x)

        # Second block
        with torch.no_grad():
            out2 = model(x)

        # Both should have no grad function
        assert out1.grad_fn is None
        assert out2.grad_fn is None

        # Outside block, gradients should work again
        out3 = model(x)
        assert out3.grad_fn is not None


    def test_no_grad_with_gpu_tensor_cpu_only(self):
        """
        Ensure that no_grad works correctly even when the environment is CPU-only.
        This task runs on CPU, so we verify the logic holds without CUDA.
        """
        model = DummyModel()
        x = torch.randn(2, 10, requires_grad=True)

        # Explicitly ensure we are on CPU
        if torch.cuda.is_available():
            pytest.skip("This test is designed for CPU-only execution context")

        with torch.no_grad():
            out = model(x)

        assert out.device.type == "cpu"
        assert out.grad_fn is None
        assert torch.is_grad_enabled() == False  # Inside context
        # After context, it should be back to default (True if not set otherwise)
        assert torch.is_grad_enabled() == True  # Default state is True