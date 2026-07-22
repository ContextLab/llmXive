"""
Training loop for CPU-optimized Autoencoders.

Implements the training logic for compressing DomainShuttle embeddings
into latent vectors of target dimensions using Cosine Similarity loss.
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from src.config.settings import get_config
from src.utils.timeout import with_timeout, timeout_wrapper
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration keys
TRAINING_CONFIG = {
    "epochs": 50,
    "batch_size": 1,
    "learning_rate": 1e-4,
    "gradient_accumulation_steps": 1,
    "patience": 10,
    "early_stopping_threshold": 1e-6,
}

def _validate_device():
    """Ensure training runs on CPU as required."""
    if torch.cuda.is_available():
        logger.warning("GPU detected but CPU-only training enforced. Forcing CPU.")
    return torch.device("cpu")

def _create_dataloader(embeddings: torch.Tensor, batch_size: int = 1):
    """Create a DataLoader for the embeddings."""
    dataset = TensorDataset(embeddings)
    return DataLoader(dataset, batch_size=batch_size, shuffle=False)

def _compute_cosine_loss(
    original: torch.Tensor,
    reconstructed: torch.Tensor,
    device: torch.device
) -> torch.Tensor:
    """
    Compute Cosine Similarity loss (1 - cosine_similarity).
    
    This implements the FR-004 requirement to use Cosine Similarity loss
    instead of MSELoss.
    """
    # Normalize vectors
    orig_norm = torch.nn.functional.normalize(original, p=2, dim=1)
    recon_norm = torch.nn.functional.normalize(reconstructed, p=2, dim=1)
    
    # Cosine similarity (should be close to 1 for perfect reconstruction)
    cosine_sim = torch.sum(orig_norm * recon_norm, dim=1)
    
    # Loss = 1 - cosine_similarity (minimize this)
    loss = 1.0 - cosine_sim
    return loss.mean()

def train_autoencoder(
    model: nn.Module,
    embeddings: torch.Tensor,
    target_dimension: int,
    output_dir: str = "data/processed/compressed_models",
    timeout_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Train an autoencoder for a specific target dimension.
    
    Args:
        model: Autoencoder model instance (already configured for target_dimension)
        embeddings: Input tensors of shape (N, original_dim)
        target_dimension: The target latent dimension size
        output_dir: Directory to save the trained model checkpoint
        timeout_seconds: Optional timeout for the training process (uses T017 utility)
    
    Returns:
        Dictionary containing training metrics and paths
    """
    # Validate inputs
    if embeddings is None or embeddings.numel() == 0:
        raise ValueError("Embeddings tensor cannot be empty")
    
    if model is None:
        raise ValueError("Model instance cannot be None")

    device = _validate_device()
    model = model.to(device)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Prepare data
    dataloader = _create_dataloader(embeddings, batch_size=TRAINING_CONFIG["batch_size"])
    
    # Setup optimizer
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=TRAINING_CONFIG["learning_rate"]
    )
    
    # Training state
    best_loss = float('inf')
    patience_counter = 0
    loss_history = []
    
    logger.info(f"Starting training for dimension {target_dimension}")
    logger.info(f"Loss function: Cosine Similarity (1 - cosine_similarity)")
    logger.info(f"Device: {device}")
    logger.info(f"Batch size: {TRAINING_CONFIG['batch_size']}")
    
    start_time = time.time()
    
    # Training loop
    for epoch in range(TRAINING_CONFIG["epochs"]):
        epoch_loss = 0.0
        num_batches = 0
        
        model.train()
        with tqdm(dataloader, desc=f"Epoch {epoch+1}/{TRAINING_CONFIG['epochs']}") as pbar:
            for batch in pbar:
                inputs = batch[0].to(device)
                
                optimizer.zero_grad()
                
                # Forward pass
                reconstructed = model(inputs)
                
                # Compute loss using Cosine Similarity
                loss = _compute_cosine_loss(inputs, reconstructed, device)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
                
                pbar.set_postfix({"loss": f"{loss.item():.6f}"})
        
        avg_loss = epoch_loss / max(num_batches, 1)
        loss_history.append(avg_loss)
        
        # Early stopping check
        if avg_loss < best_loss - TRAINING_CONFIG["early_stopping_threshold"]:
            best_loss = avg_loss
            patience_counter = 0
            # Save best model
            checkpoint_path = output_path / f"{target_dimension}_ae.pt"
            torch.save({
                "model_state_dict": model.state_dict(),
                "target_dimension": target_dimension,
                "best_loss": best_loss,
                "epoch": epoch + 1,
            }, checkpoint_path)
            logger.debug(f"Saved checkpoint at epoch {epoch+1} with loss {best_loss:.6f}")
        else:
            patience_counter += 1
        
        if patience_counter >= TRAINING_CONFIG["patience"]:
            logger.info(f"Early stopping at epoch {epoch+1}")
            break
    
    end_time = time.time()
    training_duration = end_time - start_time
    
    # Prepare results
    results = {
        "target_dimension": target_dimension,
        "final_loss": loss_history[-1] if loss_history else None,
        "best_loss": best_loss,
        "epochs_trained": len(loss_history),
        "training_duration_seconds": training_duration,
        "checkpoint_path": str(output_path / f"{target_dimension}_ae.pt"),
        "loss_history": loss_history,
        "loss_type": "cosine_similarity",
    }
    
    logger.info(f"Training completed for dimension {target_dimension}")
    logger.info(f"Final loss: {results['final_loss']:.6f}")
    logger.info(f"Best loss: {results['best_loss']:.6f}")
    logger.info(f"Duration: {training_duration:.2f}s")
    
    return results

def train_autoencoder_with_timeout(
    model: nn.Module,
    embeddings: torch.Tensor,
    target_dimension: int,
    output_dir: str = "data/processed/compressed_models",
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Wrapper for train_autoencoder with timeout enforcement using T017 utility.
    
    Args:
        model: Autoencoder model instance
        embeddings: Input tensors
        target_dimension: Target latent dimension
        output_dir: Output directory for checkpoint
        timeout_seconds: Timeout in seconds (default 300)
    
    Returns:
        Training results dictionary or timeout error info
    """
    logger.info(f"Starting training with {timeout_seconds}s timeout for dimension {target_dimension}")
    
    # Wrap the training function with timeout
    wrapped_train = with_timeout(
        train_autoencoder,
        timeout_seconds=timeout_seconds,
        sample_id=f"dim_{target_dimension}"
    )
    
    try:
        results = wrapped_train(
            model=model,
            embeddings=embeddings,
            target_dimension=target_dimension,
            output_dir=output_dir
        )
        return results
    except TimeoutError as e:
        logger.error(f"Training timed out for dimension {target_dimension}: {str(e)}")
        return {
            "target_dimension": target_dimension,
            "status": "timeout",
            "error": str(e),
            "checkpoint_path": None,
        }