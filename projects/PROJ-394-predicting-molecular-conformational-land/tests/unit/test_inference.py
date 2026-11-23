"""
Unit tests for the inference script functionality.
"""
import pytest
import torch
import numpy as np
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.seeds import set_global_seed
from models.vae import MolecularVAE, create_vae_model
from inference import encode_smiles_batch, load_checkpoint


class TestInference:
    """Test suite for inference logic."""

    @pytest.fixture
    def mock_vae_model(self):
        """Create a mock VAE model with deterministic outputs."""
        set_global_seed(42)
        model = create_vae_model(latent_dim=64)
        model.eval()
        
        # Mock the encode method to return deterministic values
        original_encode = model.encode if hasattr(model, 'encode') else None
        
        def mock_encode(node_features, edge_index, num_nodes, edge_features=None):
            batch_size = node_features.shape[0]
            latent_dim = 64
            # Return deterministic mu and logvar
            mu = torch.zeros(batch_size, latent_dim)
            logvar = torch.ones(batch_size, latent_dim) * -2.0
            return mu, logvar
        
        model.encode = mock_encode
        return model

    @pytest.fixture
    def mock_graph_data(self):
        """Generate mock graph data for a single molecule."""
        batch_size = 4
        num_nodes = 10
        node_dim = 64 # Assuming node feature dim based on typical MPNN
        
        mock_graphs = []
        for _ in range(batch_size):
            mock_graphs.append({
                'node_features': torch.randn(num_nodes, node_dim),
                'edge_index': torch.randint(0, num_nodes, (2, 20)),
                'num_nodes': num_nodes,
                'edge_features': torch.randn(20, 16) # Assuming edge feature dim
            })
        return mock_graphs

    @pytest.fixture
    def valid_smiles_file(self, tmp_path):
        """Create a temporary file with valid SMILES strings."""
        file_path = tmp_path / "test_smiles.txt"
        smiles = [
            "CCO",
            "c1ccccc1",
            "CC(=O)O",
            "C[C@H](O)C(=O)O"
        ]
        with open(file_path, 'w') as f:
            f.write("\n".join(smiles))
        return str(file_path)

    def test_encode_smiles_batch_success(self, mock_vae_model, mock_graph_data):
        """Test that encode_smiles_batch correctly processes a batch of graphs."""
        # Mock smiles_to_graph to return our mock data
        with patch('inference.smiles_to_graph') as mock_convert:
            # We need to map each call to a specific graph in our list
            # Since the function is called sequentially, we can use an iterator
            graph_iter = iter(mock_graph_data)
            def side_effect(smi):
                return next(graph_iter)
            
            mock_convert.side_effect = side_effect
            
            smiles_list = ["SMILES1", "SMILES2", "SMILES3", "SMILES4"]
            device = torch.device("cpu")
            
            results = encode_smiles_batch(mock_vae_model, smiles_list, device, batch_size=4)
            
            assert len(results) == 4
            assert all(r['success'] for r in results)
            assert all(r['latent_vector'] is not None for r in results)
            assert len(results[0]['latent_vector']) == 64

    def test_encode_smiles_batch_invalid_smiles(self, mock_vae_model):
        """Test handling of invalid SMILES strings."""
        with patch('inference.smiles_to_graph') as mock_convert:
            mock_convert.return_value = None # Simulate conversion failure
            
            smiles_list = ["INVALID_SMILES"]
            device = torch.device("cpu")
            
            results = encode_smiles_batch(mock_vae_model, smiles_list, device, batch_size=1)
            
            assert len(results) == 1
            assert results[0]['success'] is False
            assert results[0]['latent_vector'] is None
            assert "error" in results[0]

    def test_load_checkpoint_missing_file(self):
        """Test that load_checkpoint raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            load_checkpoint("nonexistent_path.pt", torch.device("cpu"))

    def test_load_checkpoint_success(self, tmp_path):
        """Test successful loading of a valid checkpoint."""
        checkpoint_path = tmp_path / "test_checkpoint.pt"
        dummy_state = {
            'epoch': 10,
            'loss': 0.5,
            'model_state_dict': {},
            'optimizer_state_dict': {}
        }
        torch.save(dummy_state, checkpoint_path)
        
        result = load_checkpoint(str(checkpoint_path), torch.device("cpu"))
        
        assert result['epoch'] == 10
        assert result['loss'] == 0.5
        assert 'model_state_dict' in result
        assert 'optimizer_state_dict' in result

    def test_encode_smiles_batch_mixed_results(self, mock_vae_model, mock_graph_data):
        """Test a batch with mixed success and failure."""
        graph_iter = iter(mock_graph_data)
        
        def side_effect(smi):
            if smi == "FAIL":
                return None
            return next(graph_iter)
        
        with patch('inference.smiles_to_graph', side_effect=side_effect):
            smiles_list = ["OK1", "FAIL", "OK2"]
            device = torch.device("cpu")
            
            results = encode_smiles_batch(mock_vae_model, smiles_list, device, batch_size=3)
            
            assert len(results) == 3
            assert results[0]['success'] is True
            assert results[1]['success'] is False
            assert results[2]['success'] is True
            assert results[0]['latent_vector'] is not None
            assert results[1]['latent_vector'] is None
            assert results[2]['latent_vector'] is not None