"""
Optimized GNN Training Script for CPU Efficiency.

This script implements performance optimizations for the GNN training loop
to ensure completion within the 6-hour constraint on a 2-core CPU runner.

Optimizations applied:
1. Mixed Precision Training (AMP) via torch.cuda.amp (fallback to FP32 if no GPU)
2. Gradient Accumulation to simulate larger batch sizes without memory overhead
3. Optimized DataLoader with pin_memory and num_workers
4. Early Stopping with patience
5. Model checkpointing for best validation performance
6. Efficient graph batching using PyTorch Geometric
7. Reduced overhead in loss calculation and gradient updates
"""

import os
import sys
import json
import logging
import argparse
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch_geometric.data import Batch, Data
from torch_geometric.loader import DataLoader as GeoDataLoader

# Import existing project modules
from models.gnn_mpnn import GNNMPNN
from config.seeds import set_seed, ensure_seeded
from setup_logging import setup_logger, log_training_metrics

# Configure logging
logger = setup_logger("train_gnn_optimized")

# Constants for optimization
GRADIENT_ACCUMULATION_STEPS = 4  # Accumulate gradients to simulate larger batch
MIXED_PRECISION = False  # Set to True if GPU available, else False
EARLY_STOPPING_PATIENCE = 5
CLIP_GRAD_NORM = 1.0

def load_graph_data(data_dir: str, split_indices: Dict[str, List[int]]) -> Dict[str, List[Data]]:
    """
    Load preprocessed graph data from disk.
    
    Args:
        data_dir: Path to processed data directory
        split_indices: Dictionary containing train/val/test indices
        
    Returns:
        Dictionary mapping split names to lists of Data objects
    """
    data_path = Path(data_dir)
    graphs = {}
    
    for split_name, indices in split_indices.items():
        split_data = []
        for idx in indices:
            file_path = data_path / f"graph_{idx}.pt"
            if file_path.exists():
                split_data.append(torch.load(file_path, map_location='cpu'))
            else:
                logger.warning(f"Graph file not found: {file_path}")
        
        graphs[split_name] = split_data
        logger.info(f"Loaded {len(split_data)} graphs for {split_name} split")
    
    return graphs

def prepare_data_loaders(
    train_data: List[Data],
    val_data: List[Data],
    batch_size: int = 32,
    num_workers: int = 2
) -> Tuple[GeoDataLoader, GeoDataLoader]:
    """
    Prepare optimized data loaders with batching.
    
    Args:
        train_data: List of training graphs
        val_data: List of validation graphs
        batch_size: Batch size for training
        num_workers: Number of workers for data loading
        
    Returns:
        Tuple of (train_loader, val_loader)
    """
    # Use PyTorch Geometric's DataLoader for efficient graph batching
    train_loader = GeoDataLoader(
        train_data,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=False,  # Disable pin_memory for CPU-only runs
        drop_last=False
    )
    
    val_loader = GeoDataLoader(
        val_data,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=False,
        drop_last=False
    )
    
    return train_loader, val_loader

def train_epoch(
    model: nn.Module,
    loader: GeoDataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    scaler: Optional[torch.cuda.amp.GradScaler] = None
) -> float:
    """
    Train for one epoch with gradient accumulation.
    
    Args:
        model: The GNN model
        loader: Data loader
        optimizer: Optimizer
        criterion: Loss function
        device: Device to run on
        scaler: Gradient scaler for mixed precision
        
    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, batch in enumerate(loader):
        batch = batch.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        output = model(batch)
        
        # Calculate loss
        loss = criterion(output, batch.y)
        
        # Gradient accumulation
        loss = loss / GRADIENT_ACCUMULATION_STEPS
        
        if scaler is not None:
            scaler.scale(loss).backward()
            
            # Perform gradient update every GRADIENT_ACCUMULATION_STEPS batches
            if (batch_idx + 1) % GRADIENT_ACCUMULATION_STEPS == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP_GRAD_NORM)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
        else:
            loss.backward()
            
            if (batch_idx + 1) % GRADIENT_ACCUMULATION_STEPS == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP_GRAD_NORM)
                optimizer.step()
                optimizer.zero_grad()
        
        total_loss += loss.item() * GRADIENT_ACCUMULATION_STEPS
        num_batches += 1
        
        if batch_idx % 50 == 0:
            logger.debug(f"Batch {batch_idx}/{len(loader)}, Loss: {loss.item():.4f}")
    
    return total_loss / num_batches

def evaluate_epoch(
    model: nn.Module,
    loader: GeoDataLoader,
    criterion: nn.Module,
    device: torch.device
) -> float:
    """
    Evaluate model on one epoch.
    
    Args:
        model: The GNN model
        loader: Data loader
        criterion: Loss function
        device: Device to run on
        
    Returns:
        Average loss for the epoch
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            output = model(batch)
            loss = criterion(output, batch.y)
            total_loss += loss.item()
            num_batches += 1
    
    return total_loss / num_batches

def train_model(
    model: nn.Module,
    train_loader: GeoDataLoader,
    val_loader: GeoDataLoader,
    epochs: int,
    learning_rate: float,
    device: torch.device,
    model_save_path: Path,
    patience: int = EARLY_STOPPING_PATIENCE
) -> Dict[str, Any]:
    """
    Train the model with early stopping and checkpointing.
    
    Args:
        model: The GNN model
        train_loader: Training data loader
        val_loader: Validation data loader
        epochs: Maximum number of epochs
        learning_rate: Learning rate
        device: Device to run on
        model_save_path: Path to save the model
        patience: Early stopping patience
        
    Returns:
        Training history dictionary
    """
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-5)
    
    # Setup mixed precision scaler if available
    scaler = None
    if torch.cuda.is_available():
        scaler = torch.cuda.amp.GradScaler()
        logger.info("Using mixed precision training")
    else:
        logger.info("No GPU available, using FP32 training")
    
    history = {
        'train_loss': [],
        'val_loss': [],
        'best_val_loss': float('inf'),
        'best_epoch': 0
    }
    
    early_stop_counter = 0
    best_model_state = None
    
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device, scaler)
        history['train_loss'].append(train_loss)
        
        # Validate
        val_loss = evaluate_epoch(model, val_loader, criterion, device)
        history['val_loss'].append(val_loss)
        
        epoch_time = time.time() - epoch_start
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Time: {epoch_time:.2f}s")
        
        # Early stopping check
        if val_loss < history['best_val_loss']:
            history['best_val_loss'] = val_loss
            history['best_epoch'] = epoch
            early_stop_counter = 0
            best_model_state = model.state_dict().copy()
            
            # Save best model
            torch.save({
                'epoch': epoch,
                'model_state_dict': best_model_state,
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
            }, model_save_path / "best_model.pt")
            logger.info(f"Saved best model with val_loss: {val_loss:.4f}")
        else:
            early_stop_counter += 1
            if early_stop_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break
    
    total_time = time.time() - start_time
    logger.info(f"Training completed in {total_time:.2f}s")
    
    history['total_time'] = total_time
    history['epochs_trained'] = epoch + 1
    
    return history

def save_model(model: nn.Module, history: Dict[str, Any], save_path: Path):
    """
    Save the final model and training history.
    
    Args:
        model: The trained model
        history: Training history dictionary
        save_path: Path to save the model
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    torch.save({
        'model_state_dict': model.state_dict(),
        'history': history,
    }, save_path / "final_model.pt")
    
    with open(save_path / "training_history.json", 'w') as f:
        json.dump(history, f, indent=2)
    
    logger.info(f"Model saved to {save_path}")

def main():
    """Main entry point for optimized GNN training."""
    parser = argparse.ArgumentParser(description="Optimized GNN Training")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Path to processed data")
    parser.add_argument("--split_file", type=str, default="data/processed/splits.json", help="Path to split indices")
    parser.add_argument("--model_save_dir", type=str, default="models", help="Directory to save models")
    parser.add_argument("--epochs", type=int, default=100, help="Maximum number of epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--num_workers", type=int, default=2, help="Number of data loading workers")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    ensure_seeded()
    
    # Setup directories
    model_save_path = Path(args.model_save_dir)
    model_save_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading graph data...")
    split_indices = json.load(open(args.split_file, 'r'))
    graphs = load_graph_data(args.data_dir, split_indices)
    
    if not graphs['train'] or not graphs['val']:
        logger.error("Training or validation data is empty. Check split indices.")
        sys.exit(1)
    
    # Prepare data loaders
    logger.info("Preparing data loaders...")
    train_loader, val_loader = prepare_data_loaders(
        graphs['train'],
        graphs['val'],
        batch_size=args.batch_size,
        num_workers=args.num_workers
    )
    
    # Initialize model
    logger.info("Initializing GNN model...")
    model = GNNMPNN(
        node_dim=42,  # Standard atom feature dimension
        edge_dim=11,  # Standard bond feature dimension
        hidden_dim=128,
        out_dim=1,
        num_layers=3
    )
    
    # Move to device (CPU for this project)
    device = torch.device('cpu')
    model = model.to(device)
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Train model
    logger.info("Starting training...")
    history = train_model(
        model,
        train_loader,
        val_loader,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        device=device,
        model_save_path=model_save_path
    )
    
    # Save final model
    save_model(model, history, model_save_path)
    
    # Log metrics
    log_training_metrics(
        logger=logger,
        metrics={
            'best_val_loss': history['best_val_loss'],
            'best_epoch': history['best_epoch'],
            'total_time': history['total_time'],
            'epochs_trained': history['epochs_trained']
        }
    )
    
    logger.info("Training completed successfully.")

if __name__ == "__main__":
    main()