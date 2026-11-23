import pytest
import torch
import yaml
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.adapters.text_cross_attention import TextCrossAttentionAdapter, load_adapter_from_config

class TestTextCrossAttentionAdapter:
    """Unit tests for T017: TextCrossAttentionAdapter implementation."""

    @pytest.fixture
    def temp_config(self):
        """Creates a temporary config file for testing."""
        config_data = {
            "adapter": {
                "text_dim": 512,
                "hidden_dim": 512,
                "num_heads": 4,
                "num_layers": 2
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            yield f.name
        os.unlink(f.name)

    def test_cpu_initialization_enforced(self):
        """Test that initialization on non-CPU devices raises RuntimeError."""
        with pytest.raises(RuntimeError, match="must be initialized on CPU"):
            # Attempt to initialize on CUDA (even if available, should fail check)
            # We simulate the check by passing 'cuda' string
            TextCrossAttentionAdapter(
                config={},
                device='cuda',
                text_dim=768,
                hidden_dim=768
            )

    def test_cpu_initialization_success(self):
        """Test that initialization on CPU succeeds."""
        adapter = TextCrossAttentionAdapter(
            config={},
            device='cpu',
            text_dim=768,
            hidden_dim=768
        )
        assert adapter.device == 'cpu'
        assert next(adapter.parameters()).device.type == 'cpu'

    def test_forward_pass_shapes(self, temp_config):
        """Test that forward pass produces correct output shapes."""
        config = {
            "adapter": {
                "text_dim": 512,
                "hidden_dim": 512,
                "num_heads": 4,
                "num_layers": 2
            }
        }
        adapter = TextCrossAttentionAdapter(
            config=config["adapter"],
            device='cpu'
        )

        batch_size = 2
        text_seq = 77
        query_seq = 64

        text_emb = torch.zeros(batch_size, text_seq, 512)
        query_feat = torch.zeros(batch_size, query_seq, 512)

        output = adapter(text_emb, query_feat)

        assert output.shape == (batch_size, query_seq, 512)

    def test_load_from_config(self, temp_config):
        """Test loading adapter from a config file path."""
        adapter = load_adapter_from_config(temp_config, device='cpu')
        assert adapter is not None
        assert adapter.device == 'cpu'
        # Check dimensions from config
        assert adapter.text_dim == 512
        assert adapter.hidden_dim == 512
        assert adapter.num_heads == 4
        assert len(adapter.cross_attention_layers) == 2

    def test_no_cuda_calls_in_forward(self, temp_config):
        """Ensure forward pass does not attempt to move tensors to CUDA."""
        adapter = load_adapter_from_config(temp_config, device='cpu')
        
        # Create inputs explicitly on CPU
        text_emb = torch.zeros(1, 10, 512, device='cpu')
        query_feat = torch.zeros(1, 10, 512, device='cpu')

        # This should not raise a CUDA error
        try:
            output = adapter(text_emb, query_feat)
            assert output.device.type == 'cpu'
        except RuntimeError as e:
            if "CUDA" in str(e) or "cuda" in str(e):
                pytest.fail(f"Forward pass attempted CUDA call: {e}")
            raise