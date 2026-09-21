import pytest
import torch
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.gating_head import GatingHead, create_gating_head, count_parameters
from utils.seed import set_seed

class TestGatingHead:
    """Unit tests for the GatingHead component."""

    def setup_method(self):
        """Set up test fixtures."""
        set_seed(42)
        self.batch_size = 4
        self.channels = 64
        self.height = 32
        self.width = 32

    def test_create_gating_head_initialization(self):
        """Test that create_gating_head returns a valid GatingHead instance."""
        head = create_gating_head(input_channels=64)
        assert isinstance(head, GatingHead)
        assert head.output_dim == 1

    def test_gating_head_parameter_count(self):
        """Test that GatingHead parameter count is within the ≤5M limit."""
        head = create_gating_head(input_channels=64)
        params = count_parameters(head)
        # The head is designed to be lightweight (≤5M params)
        assert params <= 5_000_000, f"Parameter count {params} exceeds 5M limit"
        assert params > 0, "Parameter count must be positive"

    def test_gating_head_output_range(self):
        """Test that gating head output scalar is in expected range (1-5) after sigmoid scaling."""
        head = create_gating_head(input_channels=64)
        dummy_input = torch.randn(self.batch_size, self.channels, self.height, self.width)
        
        with torch.no_grad():
            output = head(dummy_input)
        
        assert output.shape == (self.batch_size, 1), f"Output shape mismatch: {output.shape}"
        
        # The head uses Sigmoid (0-1) * 4 + 1 to map to [1, 5]
        # Check if values are within the expected [1, 5] range
        min_val = output.min().item()
        max_val = output.max().item()
        
        assert min_val >= 1.0 - 1e-6, f"Output min {min_val} below lower bound 1.0"
        assert max_val <= 5.0 + 1e-6, f"Output max {max_val} above upper bound 5.0"

    def test_gating_head_gradient_flow(self):
        """Test that gradients flow correctly through the gating head."""
        head = create_gating_head(input_channels=64)
        dummy_input = torch.randn(self.batch_size, self.channels, self.height, self.width, requires_grad=True)
        
        output = head(dummy_input)
        loss = output.sum()
        loss.backward()
        
        assert dummy_input.grad is not None, "Input gradient is None"
        assert not torch.isnan(dummy_input.grad).any(), "Input gradient contains NaN"
        assert not torch.isinf(dummy_input.grad).any(), "Input gradient contains Inf"

    def test_gating_head_determinism(self):
        """Test that the gating head produces deterministic results with fixed seed."""
        head1 = create_gating_head(input_channels=64)
        head2 = create_gating_head(input_channels=64)
        
        # Copy weights from head1 to head2 to ensure identical initialization
        for param1, param2 in zip(head1.parameters(), head2.parameters()):
            param2.data.copy_(param1.data)
        
        set_seed(123)
        dummy_input = torch.randn(2, 64, 16, 16)
        
        with torch.no_grad():
            out1 = head1(dummy_input)
        
        set_seed(123)
        with torch.no_grad():
            out2 = head2(dummy_input)
        
        assert torch.allclose(out1, out2), "Deterministic run produced different results"

    def test_gating_head_batch_consistency(self):
        """Test that batch processing yields consistent shapes."""
        head = create_gating_head(input_channels=64)
        
        for batch_size in [1, 2, 8, 16]:
            dummy_input = torch.randn(batch_size, 64, 16, 16)
            with torch.no_grad():
                output = head(dummy_input)
            assert output.shape == (batch_size, 1), f"Shape mismatch for batch_size={batch_size}"
