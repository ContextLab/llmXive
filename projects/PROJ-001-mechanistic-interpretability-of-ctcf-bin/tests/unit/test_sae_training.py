"""
Unit tests for Sparse Autoencoder (SAE) training.
Verifies sparsity constraints, reconstruction loss, and feature activation.
"""

import unittest
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import sys
import os

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.interpret.sae import SparseAutoencoder, train_sae, load_sae_activations


class TestSAETraining(unittest.TestCase):
    """Test suite for SAE training and sparsity constraints."""

    def setUp(self):
        """Set up test fixtures."""
        self.input_dim = 64  # Small dimension for unit testing
        self.latent_dim = 256
        self.sparsity_target = 0.05
        self.sparsity_weight = 0.1
        self.batch_size = 8
        
        # Create a deterministic random seed for reproducibility
        torch.manual_seed(42)
        np.random.seed(42)
        
        # Create dummy input data
        self.dummy_inputs = torch.randn(self.batch_size, self.input_dim)
        
        # Initialize SAE
        self.sae = SparseAutoencoder(
            input_dim=self.input_dim,
            latent_dim=self.latent_dim,
            sparsity_target=self.sparsity_target,
            sparsity_weight=self.sparsity_weight
        )

    def test_sae_initialization(self):
        """Test that SAE initializes with correct dimensions."""
        self.assertEqual(self.sae.input_dim, self.input_dim)
        self.assertEqual(self.sae.latent_dim, self.latent_dim)
        
        # Check encoder and decoder dimensions
        self.assertEqual(self.sae.encoder.weight.shape[0], self.latent_dim)
        self.assertEqual(self.sae.encoder.weight.shape[1], self.input_dim)
        self.assertEqual(self.sae.decoder.weight.shape[0], self.input_dim)
        self.assertEqual(self.sae.decoder.weight.shape[1], self.latent_dim)

    def test_forward_pass_shape(self):
        """Test that forward pass returns correct shapes."""
        latent, reconstruction = self.sae(self.dummy_inputs)
        
        self.assertEqual(latent.shape, (self.batch_size, self.latent_dim))
        self.assertEqual(reconstruction.shape, (self.batch_size, self.input_dim))

    def test_sparsity_constraint_calculation(self):
        """Test that sparsity constraint is calculated correctly."""
        latent, _ = self.sae(self.dummy_inputs)
        
        # Calculate actual sparsity (mean activation across batch and features)
        actual_sparsity = torch.mean(latent).item()
        
        # The sparsity should be a positive value
        self.assertGreaterEqual(actual_sparsity, 0.0)
        self.assertLessEqual(actual_sparsity, 1.0)
        
        # With ReLU activation, latent should be non-negative
        self.assertTrue(torch.all(latent >= 0).item())

    def test_reconstruction_loss(self):
        """Test that reconstruction loss is computed."""
        latent, reconstruction = self.sae(self.dummy_inputs)
        
        # Compute MSE loss
        mse_loss = nn.functional.mse_loss(reconstruction, self.dummy_inputs)
        
        # Loss should be positive
        self.assertGreater(mse_loss.item(), 0.0)
        
        # Loss should be finite
        self.assertTrue(torch.isfinite(mse_loss))

    def test_sparsity_loss(self):
        """Test that sparsity loss is computed."""
        latent, _ = self.sae(self.dummy_inputs)
        
        # Calculate KL divergence-like sparsity loss
        actual_sparsity = torch.mean(latent, dim=0)
        
        # Avoid division by zero
        actual_sparsity = torch.clamp(actual_sparsity, min=1e-7)
        
        # KL divergence term
        kl_loss = self.sparsity_target * torch.log(self.sparsity_target / actual_sparsity) + \
                  (1 - self.sparsity_target) * torch.log((1 - self.sparsity_target) / (1 - actual_sparsity))
        
        # Total sparsity loss
        sparsity_loss = torch.mean(kl_loss)
        
        # Sparsity loss should be non-negative
        self.assertGreaterEqual(sparsity_loss.item(), 0.0)

    def test_total_loss_composition(self):
        """Test that total loss is a combination of reconstruction and sparsity loss."""
        latent, reconstruction = self.sae(self.dummy_inputs)
        
        mse_loss = nn.functional.mse_loss(reconstruction, self.dummy_inputs)
        
        # Calculate sparsity loss
        actual_sparsity = torch.mean(latent, dim=0)
        actual_sparsity = torch.clamp(actual_sparsity, min=1e-7)
        
        kl_loss = self.sparsity_target * torch.log(self.sparsity_target / actual_sparsity) + \
                  (1 - self.sparsity_target) * torch.log((1 - self.sparsity_target) / (1 - actual_sparsity))
        sparsity_loss = torch.mean(kl_loss)
        
        total_loss = mse_loss + self.sparsity_weight * sparsity_loss
        
        # Total loss should be greater than or equal to MSE loss
        self.assertGreaterEqual(total_loss.item(), mse_loss.item())

    def test_training_step_updates_weights(self):
        """Test that a training step updates model weights."""
        optimizer = optim.Adam(self.sae.parameters(), lr=0.001)
        
        # Get initial weights
        initial_encoder_weight = self.sae.encoder.weight.data.clone()
        initial_decoder_weight = self.sae.decoder.weight.data.clone()
        
        # Perform one training step
        optimizer.zero_grad()
        latent, reconstruction = self.sae(self.dummy_inputs)
        
        mse_loss = nn.functional.mse_loss(reconstruction, self.dummy_inputs)
        
        # Calculate sparsity loss
        actual_sparsity = torch.mean(latent, dim=0)
        actual_sparsity = torch.clamp(actual_sparsity, min=1e-7)
        
        kl_loss = self.sparsity_target * torch.log(self.sparsity_target / actual_sparsity) + \
                  (1 - self.sparsity_target) * torch.log((1 - self.sparsity_target) / (1 - actual_sparsity))
        sparsity_loss = torch.mean(kl_loss)
        
        total_loss = mse_loss + self.sparsity_weight * sparsity_loss
        
        total_loss.backward()
        optimizer.step()
        
        # Check that weights have changed
        weight_changed_encoder = not torch.equal(
            self.sae.encoder.weight.data, initial_encoder_weight
        )
        weight_changed_decoder = not torch.equal(
            self.sae.decoder.weight.data, initial_decoder_weight
        )
        
        self.assertTrue(weight_changed_encoder, "Encoder weights should be updated")
        self.assertTrue(weight_changed_decoder, "Decoder weights should be updated")

    def test_training_loop_convergence(self):
        """Test that training loop shows loss decrease over iterations."""
        optimizer = optim.Adam(self.sae.parameters(), lr=0.01)
        
        # Generate more data for training
        train_data = torch.randn(100, self.input_dim)
        
        losses = []
        for epoch in range(5):
            epoch_loss = 0.0
            for i in range(0, len(train_data), self.batch_size):
                batch = train_data[i:i+self.batch_size]
                optimizer.zero_grad()
                
                latent, reconstruction = self.sae(batch)
                mse_loss = nn.functional.mse_loss(reconstruction, batch)
                
                # Calculate sparsity loss
                actual_sparsity = torch.mean(latent, dim=0)
                actual_sparsity = torch.clamp(actual_sparsity, min=1e-7)
                
                kl_loss = self.sparsity_target * torch.log(self.sparsity_target / actual_sparsity) + \
                          (1 - self.sparsity_target) * torch.log((1 - self.sparsity_target) / (1 - actual_sparsity))
                sparsity_loss = torch.mean(kl_loss)
                
                total_loss = mse_loss + self.sparsity_weight * sparsity_loss
                
                total_loss.backward()
                optimizer.step()
                
                epoch_loss += total_loss.item()
            
            losses.append(epoch_loss)
        
        # Check that loss generally decreases (allowing for some variance)
        # We check if the last loss is significantly lower than the first
        self.assertLess(losses[-1], losses[0], "Training loss should decrease over epochs")

    def test_feature_activation_sparsity(self):
        """Test that latent features exhibit sparsity as expected."""
        # Generate a larger batch to check feature-wise sparsity
        large_batch = torch.randn(1000, self.input_dim)
        latent, _ = self.sae(large_batch)
        
        # Calculate mean activation per feature across the batch
        feature_sparsity = torch.mean(latent, dim=0)
        
        # Most features should have low activation (sparsity)
        # We expect the mean sparsity to be close to the target
        mean_sparsity = torch.mean(feature_sparsity).item()
        
        # Allow some tolerance around the target sparsity
        self.assertGreaterEqual(mean_sparsity, 0.0)
        self.assertLessEqual(mean_sparsity, 0.2)  # Should be relatively sparse

    def test_gradient_flow(self):
        """Test that gradients flow correctly through the SAE."""
        optimizer = optim.Adam(self.sae.parameters(), lr=0.001)
        
        latent, reconstruction = self.sae(self.dummy_inputs)
        mse_loss = nn.functional.mse_loss(reconstruction, self.dummy_inputs)
        
        # Calculate sparsity loss
        actual_sparsity = torch.mean(latent, dim=0)
        actual_sparsity = torch.clamp(actual_sparsity, min=1e-7)
        
        kl_loss = self.sparsity_target * torch.log(self.sparsity_target / actual_sparsity) + \
                  (1 - self.sparsity_target) * torch.log((1 - self.sparsity_target) / (1 - actual_sparsity))
        sparsity_loss = torch.mean(kl_loss)
        
        total_loss = mse_loss + self.sparsity_weight * sparsity_loss
        
        total_loss.backward()
        
        # Check that all parameters have gradients
        for name, param in self.sae.named_parameters():
            self.assertIsNotNone(param.grad, f"Gradient missing for {name}")
            self.assertFalse(torch.isnan(param.grad).any(), f"NaN gradient in {name}")
            self.assertFalse(torch.isinf(param.grad).any(), f"Inf gradient in {name}")


if __name__ == '__main__':
    unittest.main()