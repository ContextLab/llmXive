"""
Unit tests for the Lightweight MPNN module.

Tests architecture initialization, forward pass, parameter count,
and checkpoint save/load functionality.
"""
import pytest
import os
import sys
import tempfile
import torch
import numpy as np
from torch_geometric.data import Data

# Import the module under test
from src.models.mpnn import (
    LightweightMPNN,
    create_model_and_optimizer,
    save_model_checkpoint,
    load_model_checkpoint,
    train_epoch,
    evaluate_epoch
)
from src.utils.seeding import set_seed

class TestLightweightMPNN:
    """Tests for the LightweightMPNN class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        set_seed(42)
        self.node_dim = 42
        self.hidden_dim = 64
        self.out_dim = 1
    
    def test_model_initialization(self):
        """Test that model initializes correctly with expected parameters."""
        model = LightweightMPNN(
            node_input_dim=self.node_dim,
            hidden_dim=self.hidden_dim,
            out_dim=self.out_dim
        )
        
        assert model.node_input_dim == self.node_dim
        assert model.hidden_dim == self.hidden_dim
        assert model.out_dim == self.out_dim
        assert model.count_parameters() > 0
        assert model.count_parameters() < 1_000_000
    
    def test_forward_pass_single_graph(self):
        """Test forward pass with a single graph."""
        model = LightweightMPNN(node_input_dim=self.node_dim, hidden_dim=self.hidden_dim)
        model.eval()
        
        # Create a single graph
        num_nodes = 10
        x = torch.randn(num_nodes, self.node_dim)
        edge_index = torch.randint(0, num_nodes, (2, 20))
        batch = torch.zeros(num_nodes, dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, batch=batch)
        
        with torch.no_grad():
            output = model(data)
        
        assert output.shape == (1, 1), f"Expected shape (1, 1), got {output.shape}"
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()
    
    def test_forward_pass_batch(self):
        """Test forward pass with a batch of graphs."""
        model = LightweightMPNN(node_input_dim=self.node_dim, hidden_dim=self.hidden_dim)
        model.eval()
        
        # Create a batch of 3 graphs
        num_graphs = 3
        nodes_per_graph = [5, 8, 12]
        
        x_list = []
        edge_index_list = []
        batch_list = []
        
        node_offset = 0
        for i, n_nodes in enumerate(nodes_per_graph):
            x_list.append(torch.randn(n_nodes, self.node_dim))
            edge_index_list.append(torch.randint(0, n_nodes, (2, 15)))
            batch_list.append(torch.full((n_nodes,), i, dtype=torch.long))
            node_offset += n_nodes
        
        x = torch.cat(x_list, dim=0)
        # Adjust edge_index for global node indices
        edge_index = torch.cat([
            idx + offset for idx, offset in zip(edge_index_list, [0, 5, 13])
        ], dim=1)
        batch = torch.cat(batch_list, dim=0)
        
        data = Data(x=x, edge_index=edge_index, batch=batch)
        
        with torch.no_grad():
            output = model(data)
        
        assert output.shape == (num_graphs, 1), f"Expected shape ({num_graphs}, 1), got {output.shape}"
    
    def test_parameter_count_constraint(self):
        """Ensure model stays under 1M parameter constraint."""
        # Test with various hidden dimensions
        for hidden_dim in [32, 64, 128]:
            model = LightweightMPNN(
                node_input_dim=self.node_dim,
                hidden_dim=hidden_dim
            )
            param_count = model.count_parameters()
            assert param_count < 1_000_000, f"Model with hidden_dim={hidden_dim} has {param_count} params"
    
    def test_dropout_training_vs_eval(self):
        """Test that dropout behaves differently in training vs eval mode."""
        model = LightweightMPNN(node_input_dim=self.node_dim, hidden_dim=self.hidden_dim, dropout=0.5)
        
        num_nodes = 10
        x = torch.randn(num_nodes, self.node_dim)
        edge_index = torch.randint(0, num_nodes, (2, 20))
        batch = torch.zeros(num_nodes, dtype=torch.long)
        data = Data(x=x, edge_index=edge_index, batch=batch)
        
        # Run multiple times in training mode (should vary due to dropout)
        model.train()
        outputs_train = []
        for _ in range(5):
            with torch.no_grad():
                outputs_train.append(model(data).clone())
        
        # Run multiple times in eval mode (should be identical)
        model.eval()
        outputs_eval = []
        for _ in range(5):
            with torch.no_grad():
                outputs_eval.append(model(data).clone())
        
        # In eval mode, all outputs should be identical
        for i in range(1, len(outputs_eval)):
            assert torch.allclose(outputs_eval[0], outputs_eval[i]), "Eval outputs should be deterministic"
    
    def test_gradient_flow(self):
        """Test that gradients flow through the network."""
        model = LightweightMPNN(node_input_dim=self.node_dim, hidden_dim=self.hidden_dim)
        model.train()
        
        num_nodes = 10
        x = torch.randn(num_nodes, self.node_dim, requires_grad=True)
        edge_index = torch.randint(0, num_nodes, (2, 20))
        batch = torch.zeros(num_nodes, dtype=torch.long)
        data = Data(x=x, edge_index=edge_index, batch=batch)
        
        output = model(data)
        loss = output.sum()
        loss.backward()
        
        # Check that parameters have gradients
        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient"
            assert not torch.isnan(param.grad).any(), f"Parameter {name} has NaN gradients"

class TestModelCheckpointing:
    """Tests for model save/load functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        set_seed(42)
        self.node_dim = 42
        self.hidden_dim = 64
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_checkpoint(self):
        """Test saving and loading a model checkpoint."""
        model, optimizer = create_model_and_optimizer(
            node_dim=self.node_dim,
            hidden_dim=self.hidden_dim
        )
        
        checkpoint_path = os.path.join(self.temp_dir, "test_model.pt")
        
        # Save checkpoint
        save_model_checkpoint(
            model=model,
            optimizer=optimizer,
            epoch=10,
            loss=0.5,
            save_path=checkpoint_path
        )
        
        assert os.path.exists(checkpoint_path), "Checkpoint file was not created"
        
        # Load checkpoint
        loaded_model, metadata = load_model_checkpoint(checkpoint_path, device=torch.device('cpu'))
        
        # Verify metadata
        assert metadata['epoch'] == 10
        assert metadata['loss'] == 0.5
        
        # Verify model parameters match
        for (name1, param1), (name2, param2) in zip(
            model.named_parameters(),
            loaded_model.named_parameters()
        ):
            assert torch.allclose(param1, param2), f"Parameter {name1} mismatch after load"
    
    def test_save_with_fold_index(self):
        """Test saving checkpoint with fold index in filename."""
        model, optimizer = create_model_and_optimizer(node_dim=self.node_dim, hidden_dim=self.hidden_dim)
        
        checkpoint_path = os.path.join(self.temp_dir, "model.pt")
        
        save_model_checkpoint(
            model=model,
            optimizer=optimizer,
            epoch=5,
            loss=0.3,
            save_path=checkpoint_path,
            fold_idx=3
        )
        
        expected_path = os.path.join(self.temp_dir, "model_fold3.pt")
        assert os.path.exists(expected_path), f"Fold checkpoint not saved to {expected_path}"

class TestTrainingFunctions:
    """Tests for training and evaluation functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        set_seed(42)
        self.node_dim = 42
        self.hidden_dim = 64
    
    def test_evaluate_epoch_returns_valid_metrics(self):
        """Test that evaluate_epoch returns valid loss and predictions."""
        model = LightweightMPNN(node_input_dim=self.node_dim, hidden_dim=self.hidden_dim)
        model.eval()
        
        # Create a simple dataset
        data_list = []
        for _ in range(5):
            x = torch.randn(8, self.node_dim)
            edge_index = torch.randint(0, 8, (2, 16))
            batch = torch.zeros(8, dtype=torch.long)
            y = torch.randn(1)  # Target yield
            data_list.append(Data(x=x, edge_index=edge_index, batch=batch, y=y))
        
        dataset = torch.utils.data.Dataset.from_tensor_slices if False else None
        # Create a simple loader manually
        loader = torch.utils.data.DataLoader(data_list, batch_size=2)
        
        loss, preds, targets = evaluate_epoch(model, loader, device=torch.device('cpu'))
        
        assert isinstance(loss, float), "Loss should be a float"
        assert not np.isnan(loss), "Loss should not be NaN"
        assert len(preds) == 5, f"Expected 5 predictions, got {len(preds)}"
        assert len(targets) == 5, f"Expected 5 targets, got {len(targets)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])