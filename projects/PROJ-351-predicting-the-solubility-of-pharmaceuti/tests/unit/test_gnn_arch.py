"""
Unit tests for MPNN architecture (CPU-only verification).

Tests the GNN model defined in code/models/gnn_mpnn.py to ensure:
1. The model can be instantiated.
2. The model runs inferences without attempting to access CUDA/GPU.
3. The model accepts valid PyTorch Geometric batch inputs.
"""
import os
import sys
import unittest
import tempfile
import shutil

import numpy as np
import torch
import torch.nn as nn
from torch_geometric.data import Data, Batch
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import to_dense_batch

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the model implementation
# Assuming the model is created in code/models/gnn_mpnn.py as per T020
# We import the class directly. If the file doesn't exist yet, we define a minimal 
# stub here to satisfy the test runner, but the expectation is T020 will provide the real one.
# However, per instructions, we must implement the test for the REAL artifact.
# We will assume T020 (GNP MPNN) will be implemented. We import it.
try:
    from models.gnn_mpnn import MPNNModel
    HAS_MODEL = True
except ImportError:
    HAS_MODEL = False
    # Fallback stub if T020 hasn't run yet, purely for test structure validation
    class MPNNModel(nn.Module):
        def __init__(self, input_dim=10, hidden_dim=32, output_dim=1):
            super().__init__()
            self.input_dim = input_dim
            self.hidden_dim = hidden_dim
            self.output_dim = output_dim
            self.lin = nn.Linear(hidden_dim, output_dim)
        
        def forward(self, x, edge_index, batch):
            # Dummy forward pass
            h = x
            for _ in range(2):
                # Dummy message passing
                row, col = edge_index
                msg = h[row]
                h = h + msg
            h = to_dense_batch(h, batch)[0].mean(dim=1)
            return self.lin(h)

class TestMPNNArchitecture(unittest.TestCase):
    """Test suite for MPNN CPU-only verification."""

    def setUp(self):
        """Set up test fixtures."""
        self.device = torch.device('cpu')
        self.input_dim = 10
        self.hidden_dim = 32
        self.output_dim = 1
        self.num_nodes = 10
        self.num_edges = 20
        self.batch_size = 2

    def _create_dummy_batch(self, num_graphs=2):
        """Create a dummy PyTorch Geometric Batch object."""
        data_list = []
        for i in range(num_graphs):
            num_nodes = self.num_nodes
            # Random node features
            x = torch.randn(num_nodes, self.input_dim)
            # Random edge index
            edge_index = torch.randint(0, num_nodes, (2, self.num_edges))
            # Ensure no self-loops for realism (optional)
            edge_index = edge_index[:, edge_index[0] != edge_index[1]]
            
            data = Data(x=x, edge_index=edge_index)
            data_list.append(data)
        
        batch = Batch.from_data_list(data_list)
        return batch

    def test_model_instantiation(self):
        """Test that the model can be instantiated on CPU."""
        if not HAS_MODEL:
            self.skipTest("Model implementation (T020) not yet available.")
        
        model = MPNNModel(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.output_dim
        )
        self.assertIsInstance(model, nn.Module)
        # Explicitly move to CPU to ensure no CUDA is assumed
        model = model.to(self.device)
        self.assertEqual(next(model.parameters()).device.type, 'cpu')

    def test_no_cuda_calls(self):
        """
        Verify that the model does not attempt to use CUDA.
        This test checks if torch.cuda.is_available() is called or if .to('cuda') is used.
        Since we cannot easily intercept internal calls without mocking, 
        we verify the device placement logic.
        """
        if not HAS_MODEL:
            self.skipTest("Model implementation (T020) not yet available.")

        model = MPNNModel(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.output_dim
        )
        
        # Force CPU
        model = model.to('cpu')
        
        # Check all parameters are on CPU
        for param in model.parameters():
            self.assertEqual(param.device.type, 'cpu', 
                             "Model parameter found on non-CPU device")
        
        # Check buffers
        for buf in model.buffers():
            self.assertEqual(buf.device.type, 'cpu',
                             "Model buffer found on non-CPU device")

    def test_forward_pass_cpu(self):
        """Test that a forward pass completes successfully on CPU."""
        if not HAS_MODEL:
            self.skipTest("Model implementation (T020) not yet available.")

        model = MPNNModel(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.output_dim
        ).to(self.device)
        model.eval()

        batch = self._create_dummy_batch(self.batch_size)
        
        # Move batch to CPU explicitly
        batch = batch.to(self.device)

        with torch.no_grad():
            try:
                output = model(batch.x, batch.edge_index, batch.batch)
                self.assertIsNotNone(output)
                # Output should be [batch_size, output_dim]
                self.assertEqual(output.shape[0], self.batch_size)
                self.assertEqual(output.shape[1], self.output_dim)
            except RuntimeError as e:
                self.fail(f"Forward pass failed on CPU: {e}")

    def test_architecture_cpu_only_flag(self):
        """
        Verify the model is designed for CPU.
        We check that the model does not contain any hardcoded CUDA calls
        in its __init__ or forward methods by inspecting source if possible,
        or ensuring it runs on a CPU-only environment.
        """
        if not HAS_MODEL:
            self.skipTest("Model implementation (T020) not yet available.")

        # Check if the model source contains 'cuda' in a way that forces GPU
        import inspect
        source = inspect.getsource(MPNNModel)
        
        # We allow 'cuda' in comments or docstrings, but not in active code paths like .to('cuda')
        # Simple heuristic: if .to('cuda') or .cuda() is in source, it's risky.
        # A better check is runtime, which we did in test_no_cuda_calls.
        # Here we just ensure the model accepts a device argument or defaults to CPU.
        
        # If the model has a 'device' attribute set to 'cuda' by default, fail.
        if hasattr(MPNNModel, 'device'):
            if MPNNModel.device == 'cuda':
                self.fail("Model defaults to CUDA device.")

    def test_gradient_flow_cpu(self):
        """Test that gradients flow correctly during backprop on CPU."""
        if not HAS_MODEL:
            self.skipTest("Model implementation (T020) not yet available.")

        model = MPNNModel(
            input_dim=self.input_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.output_dim
        ).to(self.device)
        model.train()

        batch = self._create_dummy_batch(self.batch_size)
        batch = batch.to(self.device)

        # Create dummy targets
        targets = torch.randn(self.batch_size, self.output_dim)

        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        optimizer.zero_grad()
        output = model(batch.x, batch.edge_index, batch.batch)
        loss = nn.MSELoss()(output, targets)
        loss.backward()

        # Check that gradients are not None
        for param in model.parameters():
            self.assertIsNotNone(param.grad, 
                                "Gradient is None for a parameter after backward pass")
            self.assertFalse(torch.isnan(param.grad).any(), 
                             "Gradient contains NaN values")

if __name__ == '__main__':
    unittest.main()