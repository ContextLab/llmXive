import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# Project imports
from config import get_config, get_paths, get_hyperparams, get_resources
from utils.logging import get_project_logger, log_event
from utils.seeds import set_global_seed
from models.vae import create_vae_model, MolecularVAE
from data.preprocess import process_dataset

# --- Dataset Definition ---
class GraphDataset(torch.utils.data.Dataset):
    """
    PyTorch Dataset for molecular graphs.
    Expects pre-processed data where 'input_features' and 'target_features'
    are tensors or lists of tensors.
    """
    def __init__(self, data_list: List[Dict[str, Any]], transform=None):
        self.data_list = data_list
        self.transform = transform

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, idx):
        item = self.data_list[idx]
        if self.transform:
            item = self.transform(item)
        
        # Ensure tensors are on CPU for training loop
        x = item['input_features']
        if isinstance(x, torch.Tensor):
            x = x.float()
        else:
            x = torch.tensor(x, dtype=torch.float32)
        
        return x

def collate_fn(batch):
    """
    Collate function to pad variable-length graph features if necessary,
    or simply stack them if fixed size.
    For this implementation, we assume fixed-size feature vectors derived
    from the graph (e.g., node embeddings aggregated or fixed-size graph vectors).
    """
    # If items are tensors, stack them
    if isinstance(batch[0], torch.Tensor):
        return torch.stack(batch, dim=0)
    # Fallback to default list collation if mixed types
    return torch.utils.data.default_collate(batch)

# --- Training Logic ---
def train_epoch(
    model: MolecularVAE, 
    dataloader: DataLoader, 
    optimizer: optim.Optimizer, 
    device: torch.device, 
    logger
) -> float:
    """
    Executes one epoch of training.
    Returns average loss.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch_idx, data in enumerate(dataloader):
        data = data.to(device)
        optimizer.zero_grad()

        # Forward pass
        reconstruction, mu, logvar = model(data)

        # VAE Loss: Reconstruction + KL Divergence
        # Reconstruction Loss (MSE)
        recon_loss = nn.functional.mse_loss(reconstruction, data, reduction='sum')
        
        # KL Divergence Loss
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        
        # Total Loss
        loss = recon_loss + kl_loss

        # Backward pass
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

        if batch_idx % 100 == 0:
            logger.debug(f"Batch {batch_idx}, Loss: {loss.item():.4f}")

    avg_loss = total_loss / num_batches
    return avg_loss

def validate(
    model: MolecularVAE, 
    dataloader: DataLoader, 
    device: torch.device, 
    logger
) -> float:
    """
    Executes validation pass.
    Returns average loss.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for data in dataloader:
            data = data.to(device)
            reconstruction, mu, logvar = model(data)

            recon_loss = nn.functional.mse_loss(reconstruction, data, reduction='sum')
            kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
            loss = recon_loss + kl_loss

            total_loss += loss.item()
            num_batches += 1

    return total_loss / num_batches

# --- Checkpointing Logic (T017 Implementation) ---
def save_checkpoint(
    model: MolecularVAE,
    optimizer: optim.Optimizer,
    epoch: int,
    loss: float,
    checkpoint_path: Path,
    logger
) -> None:
    """
    Saves the model state, optimizer state, and training metadata to a checkpoint file.
    """
    # Ensure directory exists
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
        'hyperparams': get_hyperparams().__dict__ if hasattr(get_hyperparams(), '__dict__') else str(get_hyperparams()),
        'config': str(get_paths())
    }

    try:
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Checkpoint saved to {checkpoint_path} (Epoch {epoch}, Loss: {loss:.4f})")
        log_event("checkpoint_saved", {
            "path": str(checkpoint_path),
            "epoch": epoch,
            "loss": loss
        })
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")
        raise

def load_checkpoint(
    checkpoint_path: Path,
    model: MolecularVAE,
    optimizer: Optional[optim.Optimizer] = None,
    device: Optional[torch.device] = None,
    logger=None
) -> Tuple[int, float, Optional[optim.Optimizer]]:
    """
    Loads a checkpoint, restoring model and optimizer states.
    Returns (epoch, loss, optimizer).
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")

    if device is None:
        device = torch.device("cpu")

    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    
    start_epoch = checkpoint['epoch'] + 1
    last_loss = checkpoint['loss']

    if optimizer is not None:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        # Move optimizer state to correct device if necessary
        for state in optimizer.state.values():
            for k, v in state.items():
                if isinstance(v, torch.Tensor):
                    state[k] = v.to(device)

    logger.info(f"Loaded checkpoint from {checkpoint_path} (Epoch {start_epoch - 1}, Loss: {last_loss:.4f})")
    return start_epoch, last_loss, optimizer

# --- Main Execution ---
def main():
    logger = get_project_logger("train")
    logger.info("Starting VAE Training Pipeline")

    # Configuration
    config = get_config()
    paths = get_paths()
    hyperparams = get_hyperparams()
    resources = get_resources()

    # Seed
    set_global_seed(hyperparams.seed)
    logger.info(f"Global seed set to {hyperparams.seed}")

    # Device
    device = torch.device("cpu") # Enforcing CPU as per constraints
    logger.info(f"Using device: {device}")

    # Data Loading
    logger.info("Loading and preprocessing dataset...")
    # Assuming process_dataset handles the download/prep if needed, or we load from disk
    # For T017, we assume the data is ready or T013/T014 handled it.
    # We will simulate a small dataset for the loop if no file exists, 
    # but in a real run, this should load from data/processed.
    
    data_path = paths.processed_dir / "zinc_graphs.json"
    if data_path.exists():
        logger.info(f"Loading preprocessed data from {data_path}")
        with open(data_path, 'r') as f:
            raw_data = json.load(f)
    else:
        logger.warning(f"Preprocessed data not found at {data_path}. Generating synthetic dummy data for demo.")
        # Fallback for demo if data missing (Real run would fail or require T013 to run first)
        raw_data = []
        for i in range(100):
            raw_data.append({
                "input_features": torch.randn(hyperparams.input_dim).tolist(),
                "target_features": torch.randn(hyperparams.input_dim).tolist()
            })

    dataset = GraphDataset(raw_data)
    dataloader = DataLoader(
        dataset, 
        batch_size=hyperparams.batch_size, 
        shuffle=True, 
        collate_fn=collate_fn,
        num_workers=0
    )

    # Model
    model = create_vae_model(
        input_dim=hyperparams.input_dim,
        hidden_dim=hyperparams.hidden_dim,
        latent_dim=hyperparams.latent_dim
    ).to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=hyperparams.learning_rate)

    # Checkpoint Paths
    checkpoint_dir = paths.checkpoints_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / "vae_checkpoint.pt"
    latest_path = checkpoint_dir / "vae_checkpoint_latest.pt"

    # Resume or Start
    start_epoch = 0
    best_loss = float('inf')
    
    if checkpoint_path.exists():
        try:
            start_epoch, best_loss, optimizer = load_checkpoint(
                checkpoint_path, model, optimizer, device, logger
            )
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}. Starting fresh.")
            start_epoch = 0

    # Training Loop
    logger.info(f"Starting training from epoch {start_epoch}")
    for epoch in range(start_epoch, hyperparams.epochs):
        start_time = time.time()
        
        train_loss = train_epoch(model, dataloader, optimizer, device, logger)
        val_loss = validate(model, dataloader, device, logger)
        
        elapsed = time.time() - start_time
        logger.info(f"Epoch {epoch+1}/{hyperparams.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Time: {elapsed:.2f}s")

        # Save Checkpoint (T017)
        # Save the "latest" checkpoint every epoch
        save_checkpoint(model, optimizer, epoch, val_loss, latest_path, logger)
        
        # Save the "best" checkpoint if improved
        if val_loss < best_loss:
            best_loss = val_loss
            best_path = checkpoint_dir / "vae_checkpoint_best.pt"
            save_checkpoint(model, optimizer, epoch, val_loss, best_path, logger)
            # Also update the generic checkpoint path to the best one for easy reference
            save_checkpoint(model, optimizer, epoch, val_loss, checkpoint_path, logger)

    logger.info("Training complete.")
    log_event("training_finished", {"final_loss": best_loss, "epochs": hyperparams.epochs})

if __name__ == "__main__":
    main()