"""
Tests for Task T016: Integration of GFM and Symbolic Solver.
"""
import os
import sys
import tempfile
import json
import pytest
import numpy as np
import torch

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.inference_integration import InferenceIntegration
from code.gfm_wrapper import GFMWrapper
from code.symbolic_solver import SymbolicSolver
from code.config import Config, SolverConfig, TopologyConfig, ExperimentConfig

class TestT016Integration:
    
    @pytest.fixture
    def dummy_gfm_path(self, tmp_path):
        """Create a dummy GFM model file for testing."""
        model_path = tmp_path / "gfm_baseline.pt"
        
        # Create a dummy model
        class DummyGFMModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = torch.nn.Linear(100, 64)
                self.decoder = torch.nn.Linear(64, 100)
                
            def forward(self, x):
                latent = self.encoder(x)
                action = self.decoder(latent)
                return latent, action
        
        model = DummyGFMModel()
        torch.save(model.state_dict(), model_path)
        return str(model_path)

    @pytest.fixture
    def dummy_config_path(self, tmp_path):
        """Create a dummy config.yaml for testing."""
        config_path = tmp_path / "config.yaml"
        
        config_data = {
            "topology": {
                "counts": [5, 10, 15],
                "stiffness_range": [0.1, 1.0]
            },
            "solver": {
                "timeout": 30.0,
                "max_iterations": 1000,
                "tolerance": 1e-6
            },
            "experiment": {
                "seed": 42,
                "trial_count": 10
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
            
        return str(config_path)

    def test_instantiation(self, dummy_config_path, dummy_gfm_path):
        """Test that InferenceIntegration can be instantiated."""
        integration = InferenceIntegration(dummy_config_path, dummy_gfm_path)
        assert integration is not None
        assert integration.gfm is not None
        assert integration.solver is not None

    def test_encode_observation(self, dummy_config_path, dummy_gfm_path):
        """Test encoding an observation."""
        integration = InferenceIntegration(dummy_config_path, dummy_gfm_path)
        obs = np.random.randn(100).astype(np.float32)
        latent = integration.encode_observation(obs)
        
        assert isinstance(latent, np.ndarray)
        assert latent.shape == (64,) # Dummy model latent size
        assert not np.isnan(latent).any()

    def test_decode_action(self, dummy_config_path, dummy_gfm_path):
        """Test decoding a latent vector."""
        integration = InferenceIntegration(dummy_config_path, dummy_gfm_path)
        latent = np.random.randn(64).astype(np.float32)
        action = integration.decode_action(latent)
        
        assert isinstance(action, np.ndarray)
        assert action.shape == (100,) # Dummy model action size
        assert not np.isnan(action).any()

    def test_solve_constraints(self, dummy_config_path, dummy_gfm_path):
        """Test solving constraints."""
        integration = InferenceIntegration(dummy_config_path, dummy_gfm_path)
        latent = np.random.randn(100).astype(np.float32)
        
        optimized = integration.solve_constraints(latent)
        
        assert isinstance(optimized, torch.Tensor)
        assert not torch.isnan(optimized).any()

    def test_run_step(self, dummy_config_path, dummy_gfm_path):
        """Test the full run_step pipeline."""
        integration = InferenceIntegration(dummy_config_path, dummy_gfm_path)
        obs = np.random.randn(100).astype(np.float32)
        
        action, latency = integration.run_step(obs)
        
        assert isinstance(action, np.ndarray)
        assert action.shape == (100,)
        assert isinstance(latency, float)
        assert latency >= 0
        assert not np.isnan(action).any()

    def test_gradient_flow_isolation(self, dummy_config_path, dummy_gfm_path):
        """
        Verify that gradients do not flow into the GFM wrapper parameters.
        This ensures the GFM remains frozen as per T014a requirements.
        """
        integration = InferenceIntegration(dummy_config_path, dummy_gfm_path)
        
        # Create a tensor that requires grad (simulating the solver input)
        latent = torch.randn(100, requires_grad=True)
        
        # Run solve (this involves the solver which computes gradients)
        optimized = integration.solve_constraints(latent)
        
        # Compute a dummy loss
        loss = optimized.sum()
        loss.backward()
        
        # Check that latent has gradients
        assert latent.grad is not None
        
        # Check that GFM parameters do NOT have gradients
        # The GFM wrapper should be in eval mode and require_grad=False
        for name, param in integration.gfm.model.named_parameters():
            assert not param.requires_grad, f"Parameter {name} should not require grad"
            # Since we didn't run the solver through the GFM, gradients shouldn't be there anyway,
            # but the critical check is requires_grad=False.
            # If the solver used the GFM in a way that backpropagated, we'd check param.grad is None.
            # Here we ensure the wrapper is set up correctly to prevent it.
        
        assert not integration.gfm.model.training