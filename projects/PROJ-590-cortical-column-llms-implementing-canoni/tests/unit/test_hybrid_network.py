import pytest
import torch
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.models.microcircuit import LayerConfig

class TestHybridNetworkForwardPassCPU:
    """
    Test T023: [US2] Create tests/unit/test_hybrid_network.py::test_forward_pass_cpu
    that instantiates the model and asserts no shape mismatches.
    """

    def test_forward_pass_cpu_small(self):
        """
        Instantiate a small HybridNetwork on CPU, run a forward pass,
        and assert that the output shape matches expectations.
        """
        # Configuration for a minimal test network
        config = {
            "d_model": 64,
            "n_heads": 4,
            "n_layers": 2,
            "d_ff": 128,
            "max_seq_len": 16,
            "vocab_size": 1000,
            "column_config": {
                "d_model": 64,
                "n_layers": 2,
                "layer_configs": [
                    LayerConfig(name="L4", n_units=32, is_excitatory=True),
                    LayerConfig(name="L23", n_units=32, is_excitatory=True),
                    LayerConfig(name="L5", n_units=32, is_excitatory=True),
                    LayerConfig(name="L6", n_units=32, is_excitatory=True)
                ]
            }
        }

        # Instantiate model
        model = create_hybrid_network(config)
        
        # Ensure model is on CPU
        model = model.cpu()
        model.eval()

        # Create dummy input: (batch_size, seq_len)
        batch_size = 2
        seq_len = 10
        input_ids = torch.randint(0, config["vocab_size"], (batch_size, seq_len))

        # Run forward pass
        with torch.no_grad():
            output = model(input_ids)

        # Assertions
        assert output is not None, "Output should not be None"
        assert isinstance(output, torch.Tensor), "Output must be a torch.Tensor"
        
        # Expected output shape: (batch_size, seq_len, vocab_size)
        expected_shape = (batch_size, seq_len, config["vocab_size"])
        assert output.shape == torch.Size(expected_shape), (
            f"Output shape mismatch: expected {expected_shape}, got {output.shape}"
        )

        # Verify no NaNs or Infs (basic sanity check for valid computation)
        assert not torch.isnan(output).any(), "Output contains NaN values"
        assert not torch.isinf(output).any(), "Output contains Inf values"

    def test_forward_pass_cpu_variable_seq(self):
        """
        Test forward pass with variable sequence lengths to ensure
        the model handles dynamic input shapes correctly without errors.
        """
        config = {
            "d_model": 32,
            "n_heads": 2,
            "n_layers": 1,
            "d_ff": 64,
            "max_seq_len": 32,
            "vocab_size": 500,
            "column_config": {
                "d_model": 32,
                "n_layers": 1,
                "layer_configs": [
                    LayerConfig(name="L4", n_units=16, is_excitatory=True),
                    LayerConfig(name="L23", n_units=16, is_excitatory=True)
                ]
            }
        }

        model = create_hybrid_network(config).cpu()
        model.eval()

        batch_size = 1
        
        # Test with different sequence lengths
        for seq_len in [4, 8, 16, 32]:
            input_ids = torch.randint(0, config["vocab_size"], (batch_size, seq_len))
            
            with torch.no_grad():
                output = model(input_ids)
            
            expected_shape = (batch_size, seq_len, config["vocab_size"])
            assert output.shape == torch.Size(expected_shape), (
                f"Shape mismatch for seq_len={seq_len}: expected {expected_shape}, got {output.shape}"
            )

    def test_parameter_count_parity(self):
        """
        Verify that the HybridNetwork has a reasonable parameter count
        (not zero or absurdly large) to ensure layers are initialized.
        """
        config = {
            "d_model": 64,
            "n_heads": 4,
            "n_layers": 2,
            "d_ff": 128,
            "max_seq_len": 16,
            "vocab_size": 1000,
            "column_config": {
                "d_model": 64,
                "n_layers": 2,
                "layer_configs": [
                    LayerConfig(name="L4", n_units=32, is_excitatory=True),
                    LayerConfig(name="L23", n_units=32, is_excitatory=True)
                ]
            }
        }

        model = create_hybrid_network(config)
        
        total_params = sum(p.numel() for p in model.parameters())
        
        assert total_params > 0, "Model must have at least one parameter"
        assert total_params < 10_000_000, "Parameter count seems unreasonably high for test config"