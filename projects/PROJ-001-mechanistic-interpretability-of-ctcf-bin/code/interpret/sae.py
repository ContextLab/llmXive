"""
Sparse Autoencoder (SAE) for CTCF Binding Interpretability.

This module trains a Sparse Autoencoder on hidden layer activations from the
CTCF predictor model to decompose them into latent features.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from models.predictor import CTCFPredictor, load_model
from models.train import load_dataset, prepare_features_targets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SparseAutoencoder(nn.Module):
    """
    A Sparse Autoencoder for decomposing hidden activations.
    
    Architecture:
    - Input: Hidden layer activations from the predictor
    - Encoder: Linear -> ReLU -> Linear (to latent space)
    - Decoder: Linear -> ReLU -> Linear (to reconstruction)
    - Loss: MSE Reconstruction + L1 Sparsity penalty
    """

    def __init__(
        self,
        input_dim: int,
        latent_dim: int,
        hidden_dim: Optional[int] = None,
        sparsity_weight: float = 1e-4,
        target_sparsity: float = 0.05
    ):
        super(SparseAutoencoder, self).__init__()
        
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim if hidden_dim else latent_dim * 2
        self.sparsity_weight = sparsity_weight
        self.target_sparsity = target_sparsity

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, latent_dim),
            nn.ReLU()
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, input_dim)
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode input to latent representation."""
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent representation to reconstruction."""
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Input activations (batch_size, input_dim)
            
        Returns:
            reconstruction: Reconstructed input
            latent: Latent representation
        """
        latent = self.encode(x)
        reconstruction = self.decode(latent)
        return reconstruction, latent

    def calculate_loss(
        self,
        x: torch.Tensor,
        reconstruction: torch.Tensor,
        latent: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate total loss: MSE + L1 Sparsity penalty.
        
        Args:
            x: Original input
            reconstruction: Reconstructed input
            latent: Latent representation
            
        Returns:
            total_loss: Combined loss
        """
        # Reconstruction loss (MSE)
        recon_loss = nn.functional.mse_loss(reconstruction, x)

        # Sparsity loss (L1 penalty on latent activations)
        # We want the mean activation of each latent feature to be close to target_sparsity
        mean_activation = torch.mean(latent, dim=0)
        sparsity_loss = torch.sum(torch.abs(mean_activation - self.target_sparsity))

        total_loss = recon_loss + self.sparsity_weight * sparsity_loss

        return total_loss

def extract_hidden_activations(
    model: CTCFPredictor,
    data_loader: torch.utils.data.DataLoader,
    device: torch.device,
    num_samples: Optional[int] = None
) -> np.ndarray:
    """
    Extract hidden layer activations from the predictor model.
    
    Args:
        model: Trained CTCF predictor model
        data_loader: DataLoader for the dataset
        device: Device to run inference on
        num_samples: Maximum number of samples to extract (None for all)
        
    Returns:
        activations: Numpy array of shape (num_samples, hidden_dim)
    """
    model.eval()
    activations = []
    samples_count = 0

    with torch.no_grad():
        for batch in data_loader:
            if num_samples and samples_count >= num_samples:
                break
            
            # Extract sequence and chromatin features
            sequence = batch['sequence'].to(device)
            chromatin = batch['chromatin'].to(device)
            
            # Get hidden activations from the predictor
            # The predictor returns logits, but we need intermediate hidden states
            # We'll extract from the final layer before the output
            hidden = model.get_hidden_activations(sequence, chromatin)
            
            activations.append(hidden.cpu().numpy())
            samples_count += hidden.shape[0]

    return np.concatenate(activations, axis=0)

def train_sae(
    sae: SparseAutoencoder,
    activations: np.ndarray,
    epochs: int = 100,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    device: torch.device = torch.device('cpu')
) -> Dict[str, Any]:
    """
    Train the Sparse Autoencoder.
    
    Args:
        sae: The SparseAutoencoder model
        activations: Numpy array of hidden activations
        epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate
        device: Device to train on
        
    Returns:
        metrics: Dictionary containing training metrics
    """
    sae.to(device)
    optimizer = optim.Adam(sae.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)

    # Convert activations to tensor
    activations_tensor = torch.tensor(activations, dtype=torch.float32)
    dataset = torch.utils.data.TensorDataset(activations_tensor)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True
    )

    history = {
        'train_loss': [],
        'recon_loss': [],
        'sparsity_loss': []
    }

    logger.info(f"Starting SAE training for {epochs} epochs...")
    start_time = time.time()

    for epoch in range(epochs):
        epoch_loss = 0.0
        epoch_recon_loss = 0.0
        epoch_sparsity_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            x = batch[0].to(device)
            
            optimizer.zero_grad()
            reconstruction, latent = sae(x)
            loss = sae.calculate_loss(x, reconstruction, latent)
            
            # Decompose loss for logging
            recon_loss = nn.functional.mse_loss(reconstruction, x)
            mean_activation = torch.mean(latent, dim=0)
            sparsity_loss = torch.sum(torch.abs(mean_activation - sae.target_sparsity))
            
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            epoch_recon_loss += recon_loss.item()
            epoch_sparsity_loss += sparsity_loss.item()
            num_batches += 1

        avg_loss = epoch_loss / num_batches
        avg_recon_loss = epoch_recon_loss / num_batches
        avg_sparsity_loss = epoch_sparsity_loss / num_batches

        history['train_loss'].append(avg_loss)
        history['recon_loss'].append(avg_recon_loss)
        history['sparsity_loss'].append(avg_sparsity_loss)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(
                f"Epoch [{epoch+1}/{epochs}] "
                f"Loss: {avg_loss:.4f}, "
                f"Recon: {avg_recon_loss:.4f}, "
                f"Sparsity: {avg_sparsity_loss:.4f}"
            )

        scheduler.step()

    training_time = time.time() - start_time
    logger.info(f"Training completed in {training_time:.2f} seconds")

    return {
        'history': history,
        'training_time': training_time,
        'final_loss': history['train_loss'][-1],
        'final_recon_loss': history['recon_loss'][-1],
        'final_sparsity_loss': history['sparsity_loss'][-1]
    }

def save_sae_model(
    sae: SparseAutoencoder,
    metrics: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save the trained SAE model and metrics.
    
    Args:
        sae: Trained SparseAutoencoder model
        metrics: Training metrics dictionary
        output_path: Path to save the model
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model state dict
    torch.save({
        'model_state_dict': sae.state_dict(),
        'input_dim': sae.input_dim,
        'latent_dim': sae.latent_dim,
        'hidden_dim': sae.hidden_dim,
        'sparsity_weight': sae.sparsity_weight,
        'target_sparsity': sae.target_sparsity
    }, str(output_path / 'sae_model.pth'))

    # Save metrics
    with open(output_path / 'sae_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"SAE model saved to {output_path}")

def main():
    """
    Main entry point for training the Sparse Autoencoder.
    """
    # Configuration
    config = {
        'dataset_path': 'data/processed/unified_ctcf_dataset.parquet',
        'model_path': 'data/models/best_ctcf_predictor.pth',
        'output_dir': 'data/interpretation',
        'latent_dim': 256,
        'hidden_dim': 512,
        'sparsity_weight': 1e-4,
        'target_sparsity': 0.05,
        'epochs': 100,
        'batch_size': 64,
        'learning_rate': 1e-3,
        'num_samples': None  # Use all samples
    }

    # Load device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")

    # Load dataset
    logger.info(f"Loading dataset from {config['dataset_path']}")
    try:
        dataset_df = pd.read_parquet(config['dataset_path'])
        logger.info(f"Loaded {len(dataset_df)} samples")
    except FileNotFoundError:
        logger.error(f"Dataset not found at {config['dataset_path']}")
        sys.exit(1)

    # Prepare features and targets
    sequence_data, chromatin_data, targets = prepare_features_targets(dataset_df)

    # Create dataloader
    dataset = torch.utils.data.TensorDataset(
        torch.tensor(sequence_data, dtype=torch.float32),
        torch.tensor(chromatin_data, dtype=torch.float32),
        torch.tensor(targets, dtype=torch.float32)
    )
    data_loader = torch.utils.data.DataLoader(
        dataset, batch_size=config['batch_size'], shuffle=False
    )

    # Load predictor model
    logger.info(f"Loading predictor model from {config['model_path']}")
    try:
        predictor = load_model(config['model_path'])
        predictor.to(device)
        predictor.eval()
        logger.info("Predictor model loaded successfully")
    except FileNotFoundError:
        logger.error(f"Predictor model not found at {config['model_path']}")
        logger.error("Please train the model first using code/models/train.py")
        sys.exit(1)

    # Extract hidden activations
    logger.info("Extracting hidden activations from predictor...")
    try:
        activations = extract_hidden_activations(
            predictor, data_loader, device, config['num_samples']
        )
        logger.info(f"Extracted {activations.shape[0]} activations with dim {activations.shape[1]}")
    except AttributeError:
        logger.error("Predictor model does not have 'get_hidden_activations' method.")
        logger.error("Please ensure code/models/predictor.py implements this method.")
        sys.exit(1)

    # Initialize SAE
    input_dim = activations.shape[1]
    sae = SparseAutoencoder(
        input_dim=input_dim,
        latent_dim=config['latent_dim'],
        hidden_dim=config['hidden_dim'],
        sparsity_weight=config['sparsity_weight'],
        target_sparsity=config['target_sparsity']
    )
    logger.info(f"Initialized SAE with input_dim={input_dim}, latent_dim={config['latent_dim']}")

    # Train SAE
    metrics = train_sae(
        sae, activations,
        epochs=config['epochs'],
        batch_size=config['batch_size'],
        learning_rate=config['learning_rate'],
        device=device
    )

    # Save model
    output_path = Path(config['output_dir'])
    save_sae_model(sae, metrics, output_path)

    # Save latent feature metadata
    latent_features_manifest = {
        'input_dim': input_dim,
        'latent_dim': config['latent_dim'],
        'hidden_dim': config['hidden_dim'],
        'sparsity_weight': config['sparsity_weight'],
        'target_sparsity': config['target_sparsity'],
        'num_activations': activations.shape[0],
        'training_epochs': config['epochs'],
        'final_loss': metrics['final_loss'],
        'final_recon_loss': metrics['final_recon_loss'],
        'final_sparsity_loss': metrics['final_sparsity_loss'],
        'training_time': metrics['training_time']
    }

    with open(output_path / 'latent_features_manifest.json', 'w') as f:
        json.dump(latent_features_manifest, f, indent=2)

    logger.info("SAE training completed successfully")
    logger.info(f"Latent features manifest saved to {output_path / 'latent_features_manifest.json'}")

if __name__ == '__main__':
    main()
