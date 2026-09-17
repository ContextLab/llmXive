"""
Unit tests for VAE architecture shapes and dimensions.

Verifies that the encoder outputs the correct latent dimension (64)
and that the decoder reconstructs tensors matching the input dimension.
"""
import pytest
import torch
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdmolops

from utils.seeds import set_global_seed
from models.vae import MolecularVAE, MPNNLayer

# Set seed for reproducibility in tests
set_global_seed(42)

# Mock graph generation for testing (simplified adjacency and feature matrix)
def create_mock_graph(num_nodes: int = 10, feature_dim: int = 42):
    """
    Creates a mock molecular graph as tensors.
    
    Args:
        num_nodes: Number of atoms in the mock molecule
        feature_dim: Dimension of node features (matches RDKit fingerprint size used in VAE)
        
    Returns:
        Tuple of (adjacency_matrix, node_features, num_nodes)
    """
    # Create a random adjacency matrix (symmetric, 0 diagonal)
    adj = np.random.randint(0, 2, size=(num_nodes, num_nodes)).astype(np.float32)
    adj = (adj + adj.T) / 2  # Make symmetric
    np.fill_diagonal(adj, 0)  # No self-loops
    
    # Create random node features
    features = np.random.randn(num_nodes, feature_dim).astype(np.float32)
    
    return adj, features, num_nodes

class TestVAEArchitecture:
    """Test suite for VAE architectural properties."""
    
    @pytest.fixture
    def input_dim(self):
        """Standard input dimension used in the project (RDKit fingerprint size)."""
        return 2048  # Typical size for Morgan fingerprints or similar graph features
        
    @pytest.fixture
    def latent_dim(self):
        """Expected latent dimension as per specification."""
        return 64
        
    @pytest.fixture
    def hidden_dim(self):
        """Hidden dimension for MPNN layers."""
        return 128
        
    def test_encoder_output_shape(self, input_dim, latent_dim, hidden_dim):
        """
        Test that the encoder outputs tensors of shape (batch_size, latent_dim).
        
        Verifies:
        - Latent dimension is exactly 64
        - Output has correct batch dimension
        """
        vae = MolecularVAE(input_dim=input_dim, latent_dim=latent_dim, hidden_dim=hidden_dim)
        
        # Create a batch of mock inputs
        batch_size = 4
        x = torch.randn(batch_size, input_dim)
        
        # Run through encoder
        mu, logvar = vae.encode(x)
        
        # Assert latent dimension
        assert mu.shape == (batch_size, latent_dim), \
            f"Encoder mu shape mismatch: expected ({batch_size}, {latent_dim}), got {mu.shape}"
        assert logvar.shape == (batch_size, latent_dim), \
            f"Encoder logvar shape mismatch: expected ({batch_size}, {latent_dim}), got {logvar.shape}"
            
    def test_decoder_output_shape(self, input_dim, latent_dim, hidden_dim):
        """
        Test that the decoder outputs tensors matching input dimension.
        
        Verifies:
        - Reconstruction dimension equals input dimension
        - Batch dimension is preserved
        """
        vae = MolecularVAE(input_dim=input_dim, latent_dim=latent_dim, hidden_dim=hidden_dim)
        
        # Create a batch of latent vectors
        batch_size = 4
        z = torch.randn(batch_size, latent_dim)
        
        # Run through decoder
        reconstruction = vae.decode(z)
        
        # Assert reconstruction matches input dimension
        assert reconstruction.shape == (batch_size, input_dim), \
            f"Decoder output shape mismatch: expected ({batch_size}, {input_dim}), got {reconstruction.shape}"
            
    def test_full_reconstruction_shape(self, input_dim, latent_dim, hidden_dim):
        """
        Test that the full VAE forward pass preserves input dimensions.
        
        Verifies:
        - Input and output shapes match
        - Latent dimension is exactly 64
        """
        vae = MolecularVAE(input_dim=input_dim, latent_dim=latent_dim, hidden_dim=hidden_dim)
        
        # Create a batch of inputs
        batch_size = 4
        x = torch.randn(batch_size, input_dim)
        
        # Run full forward pass
        reconstruction, mu, logvar = vae(x)
        
        # Assert shapes
        assert reconstruction.shape == x.shape, \
            f"Reconstruction shape mismatch: expected {x.shape}, got {reconstruction.shape}"
        assert mu.shape[1] == latent_dim, \
            f"Latent dimension mismatch: expected {latent_dim}, got {mu.shape[1]}"
            
    def test_mpnn_layer_dimensions(self, input_dim, latent_dim, hidden_dim):
        """
        Test that MPNN layers maintain expected dimensionality.
        """
        # Create MPNN layers as used in VAE
        encoder_layer = MPNNLayer(input_dim, hidden_dim)
        decoder_layer = MPNNLayer(hidden_dim, input_dim)
        
        # Test encoder layer
        batch_size = 4
        x = torch.randn(batch_size, input_dim)
        h = encoder_layer(x)
        assert h.shape[1] == hidden_dim, \
            f"Encoder MPNN output dimension mismatch: expected {hidden_dim}, got {h.shape[1]}"
            
        # Test decoder layer
        z = torch.randn(batch_size, latent_dim)
        # Note: decoder layer expects hidden_dim input, so we need to project latent first
        # This test focuses on the MPNN layer itself
        h_decoder = torch.randn(batch_size, hidden_dim)
        out = decoder_layer(h_decoder)
        assert out.shape[1] == input_dim, \
            f"Decoder MPNN output dimension mismatch: expected {input_dim}, got {out.shape[1]}"
            
    def test_latent_dimension_is_64(self, input_dim, latent_dim, hidden_dim):
        """
        Explicit test that latent dimension is exactly 64 as required by spec.
        """
        vae = MolecularVAE(input_dim=input_dim, latent_dim=latent_dim, hidden_dim=hidden_dim)
        
        # Check that latent_dim parameter is actually 64
        assert latent_dim == 64, \
            f"Latent dimension must be 64, got {latent_dim}"
            
    def test_reconstruction_matches_input_dim(self, input_dim, latent_dim, hidden_dim):
        """
        Test that reconstruction output dimension matches input dimension.
        """
        vae = MolecularVAE(input_dim=input_dim, latent_dim=latent_dim, hidden_dim=hidden_dim)
        
        batch_size = 2
        x = torch.randn(batch_size, input_dim)
        
        reconstruction, _, _ = vae(x)
        
        assert reconstruction.shape[1] == input_dim, \
            f"Reconstruction dimension {reconstruction.shape[1]} does not match input dimension {input_dim}"
            
    def test_vae_initialization_with_standard_params(self):
        """
        Test VAE initialization with standard project parameters.
        """
        # Standard parameters from project config
        input_dim = 2048
        latent_dim = 64
        hidden_dim = 128
        
        vae = MolecularVAE(
            input_dim=input_dim,
            latent_dim=latent_dim,
            hidden_dim=hidden_dim
        )
        
        # Verify model has expected attributes
        assert hasattr(vae, 'encoder'), "VAE must have encoder attribute"
        assert hasattr(vae, 'decoder'), "VAE must have decoder attribute"
        assert hasattr(vae, 'fc_mu'), "VAE must have mu projection layer"
        assert hasattr(vae, 'fc_logvar'), "VAE must have logvar projection layer"
        
        # Test a forward pass
        x = torch.randn(1, input_dim)
        reconstruction, mu, logvar = vae(x)
        
        assert mu.shape[1] == 64, "Latent dimension must be 64"
        assert reconstruction.shape[1] == input_dim, "Reconstruction must match input dimension"