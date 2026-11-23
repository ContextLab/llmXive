"""
Core training loop for the Sparse Autoencoder (SAE) with retry logic.
Implements hippocampal-like pattern separation training.

Retry Logic:
- Uses config.random_seed as base_seed.
- Increments seed by (base_seed + retry_count) for each retry (max 3 retries).
- Retry Condition: If mean(sparsity_ratio) over the entire validation epoch > 0.20.
- Failure: If sparsity constraint not met after 3 retries, raises Error with code E003.
- Output: Saves trained weights to data/results/sae_weights.pt.

Requires:
- T025: models.sparse_autoencoder.SparseAutoencoder
- T027: models.gating_module.PrefrontalGatingModule
- T008: config.get_config
- T009: utils.logging_config
"""

import os
import sys
import random
import time
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Project imports
from config import get_config
from utils.logging_config import get_logger, info, error, warning, log_error
from models.sparse_autoencoder import SparseAutoencoder, create_sparse_autoencoder
from models.gating_module import PrefrontalGatingModule, create_prefrontal_gating_module
from utils.checksums import compute_sha256

# Constants
MAX_RETRIES = 3
SPARSITY_THRESHOLD = 0.20
E003_CODE = "E003"

logger = get_logger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_sample_data(batch_size: int = 32) -> torch.Tensor:
    """
    Load a sample batch of data for training.
    Since T019 (ROCStories) and T014-T016 (fMRI) are prerequisites,
    we assume processed data exists or use a placeholder tensor if strictly
    needed for the loop structure before real data injection.
    However, per constraints, we must use REAL data.
    We will attempt to load from the expected processed path derived from US1.
    """
    # Attempt to load from US1 output: data/processed/event_averages.csv or similar
    # If not present, we cannot proceed with real data training.
    # The task description implies we are training the SAE.
    # We need a tensor of shape (batch_size, input_dim).
    # For now, we construct a minimal loader that expects data to be present.
    # In a real pipeline, this would load from data/processed/roi_timecourses.csv or similar.
    
    data_path = Path("data/processed/event_averages.csv")
    if not data_path.exists():
        # Fallback to a small synthetic tensor ONLY if the file is missing to allow code structure,
        # but per "Real data only" constraints, this should ideally fail or load real data.
        # Given the "Real data only" constraint, we must raise if real data is missing.
        raise FileNotFoundError(
            f"Real data file not found: {data_path}. "
            "Prerequisites T014-T019 must be completed to provide real input."
        )
    
    import pandas as pd
    df = pd.read_csv(data_path)
    # Select numeric columns for features
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in data file.")
    
    data = df[numeric_cols].values.astype('float32')
    if len(data) < batch_size:
        raise ValueError(f"Dataset size ({len(data)}) is smaller than batch_size ({batch_size}).")
    
    # Sample a batch
    indices = torch.randperm(len(data))[:batch_size]
    batch = torch.tensor(data[indices])
    return batch

def calculate_sparsity_loss(activations: torch.Tensor) -> torch.Tensor:
    """
    Calculate sparsity loss based on the mean activation.
    We want the mean activation to be close to a target sparsity (e.g., 0.05).
    Here we just return the mean activation as the metric to check against threshold.
    """
    return torch.mean(activations > 0).item()

def train_epoch(model: SparseAutoencoder, optimizer: optim.Optimizer, 
                data_loader: torch.utils.data.DataLoader, device: torch.device) -> float:
    """Train the model for one epoch."""
    model.train()
    total_loss = 0.0
    for batch in data_loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        # Forward pass
        activations, reconstructed = model(batch)
        
        # Reconstruction loss
        recon_loss = nn.functional.mse_loss(reconstructed, batch)
        
        # Sparsity penalty (L1 on activations)
        sparsity_penalty = torch.mean(torch.abs(activations))
        
        # Total loss
        loss = recon_loss + 0.01 * sparsity_penalty
        
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    return total_loss / len(data_loader)

def validate_model(model: SparseAutoencoder, data_loader: torch.utils.data.DataLoader, 
                   device: torch.device) -> float:
    """
    Validate the model and return the mean sparsity ratio over the validation set.
    Returns the mean of (activations > 0) across all validation batches.
    """
    model.eval()
    sparsity_ratios = []
    
    with torch.no_grad():
        for batch in data_loader:
            batch = batch.to(device)
            activations, _ = model(batch)
            # Calculate sparsity ratio for this batch
            batch_sparsity = torch.mean(activations > 0).item()
            sparsity_ratios.append(batch_sparsity)
    
    if not sparsity_ratios:
        return 0.0
    
    return sum(sparsity_ratios) / len(sparsity_ratios)

def train_with_seed(base_seed: int, retry_count: int, device: torch.device) -> Tuple[bool, Optional[SparseAutoencoder], float]:
    """
    Train the model with a specific seed (base_seed + retry_count).
    Returns (success, model, final_sparsity_ratio).
    """
    current_seed = base_seed + retry_count
    set_seed(current_seed)
    logger.info(f"Starting training attempt {retry_count + 1}/{MAX_RETRIES} with seed {current_seed}")
    
    try:
        # Load data
        batch_size = 32
        data = load_sample_data(batch_size)
        dataset = torch.utils.data.TensorDataset(data)
        data_loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Initialize model
        input_dim = data.shape[1]
        model = create_sparse_autoencoder(input_dim=input_dim, hidden_dim=input_dim * 4)
        model = model.to(device)
        
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # Train for a few epochs
        num_epochs = 10
        for epoch in range(num_epochs):
            train_epoch(model, optimizer, data_loader, device)
            val_sparsity = validate_model(model, data_loader, device)
            logger.debug(f"Epoch {epoch+1}/{num_epochs}, Validation Sparsity: {val_sparsity:.4f}")
        
        final_sparsity = validate_model(model, data_loader, device)
        logger.info(f"Training attempt {retry_count + 1} finished. Final Sparsity Ratio: {final_sparsity:.4f}")
        
        # Check constraint
        if final_sparsity <= SPARSITY_THRESHOLD:
            return True, model, final_sparsity
        else:
            return False, model, final_sparsity
            
    except Exception as e:
        logger.error(f"Training attempt {retry_count + 1} failed with exception: {e}")
        return False, None, 0.0

def main():
    """Main entry point for the training loop."""
    config = get_config()
    device = torch.device("cpu") # Enforce CPU only as per project constraints
    
    base_seed = config.get("random_seed", 42)
    final_model = None
    final_sparsity = 1.0
    
    logger.info(f"Starting SAE Training Loop. Base Seed: {base_seed}, Max Retries: {MAX_RETRIES}")
    
    for retry_count in range(MAX_RETRIES):
        success, model, sparsity_ratio = train_with_seed(base_seed, retry_count, device)
        
        if success:
            final_model = model
            final_sparsity = sparsity_ratio
            logger.info(f"Sparsity constraint (<= {SPARSITY_THRESHOLD}) met at attempt {retry_count + 1}.")
            break
        else:
            logger.warning(f"Attempt {retry_count + 1} failed sparsity check (ratio: {sparsity_ratio:.4f}). Retrying...")
            final_model = model # Keep the last model in case we need to log it, though we fail
            final_sparsity = sparsity_ratio

    if final_model is None:
        log_error(E003_CODE, "Model training failed to meet sparsity constraint after 3 retries.")
        raise RuntimeError(f"Training failed: Sparsity constraint not met after {MAX_RETRIES} retries. Final ratio: {final_sparsity:.4f}")
    
    if final_sparsity > SPARSITY_THRESHOLD:
        log_error(E003_CODE, "Model training failed to meet sparsity constraint after 3 retries.")
        raise RuntimeError(f"Training failed: Sparsity constraint not met after {MAX_RETRIES} retries. Final ratio: {final_sparsity:.4f}")
    
    # Save weights
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sae_weights.pt"
    
    torch.save({
        'model_state_dict': final_model.state_dict(),
        'sparsity_ratio': final_sparsity,
        'seed': base_seed + (MAX_RETRIES - 1), # The seed that succeeded or last tried
        'config': config
    }, output_path)
    
    logger.info(f"Training complete. Weights saved to {output_path}")
    logger.info(f"Final Sparsity Ratio: {final_sparsity:.4f}")
    
    # Update checksums for the new file
    from code.utils.checksums import compute_sha256, update_state_file
    checksum = compute_sha256(output_path)
    update_state_file(output_path, checksum)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())