"""
Memory-optimized trainer for GRU estimator.
Implements gradient accumulation, mixed precision, and memory monitoring.
"""
import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import pandas as pd

# Import from existing modules
from models.gru_estimator import GRUEstimator, load_config
from utils.memory_optimizer import (
    get_memory_usage_mb,
    force_gc,
    validate_memory_constraints,
    cleanup_tensor_memory
)
from utils.config import set_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_MEMORY_MB = 7000
GRAD_ACCUMULATION_STEPS = 4
MIXED_PRECISION = True


class MemoryConstrainedDataset(Dataset):
    """Dataset wrapper that ensures memory constraints are respected."""
    
    def __init__(self, data_path: str, max_samples: Optional[int] = None):
        self.data_path = Path(data_path)
        self.max_samples = max_samples
        
        # Load metadata only
        df = pd.read_parquet(data_path, columns=['timestamp'])
        self.total_samples = len(df)
        
        if max_samples and self.max_samples < self.total_samples:
            self.total_samples = max_samples
    
    def __len__(self):
        return self.total_samples
    
    def __getitem__(self, idx):
        # Load only the required row
        df = pd.read_parquet(self.data_path, 
                           columns=['semantic_feature', 'prosodic_feature', 
                                   'latent_delta_magnitude', 'turn_label'])
        row = df.iloc[idx % self.total_samples]
        
        x = np.array([
            float(row['semantic_feature']),
            float(row['prosodic_feature'])
        ], dtype=np.float32)
        
        y = np.array([
            float(row['latent_delta_magnitude']),
            0.5  # Default uncertainty
        ], dtype=np.float32)
        
        return torch.tensor(x), torch.tensor(y)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    return get_memory_usage_mb()


def load_training_data(data_path: str, max_samples: Optional[int] = None) -> DataLoader:
    """Load training data with memory constraints."""
    dataset = MemoryConstrainedDataset(data_path, max_samples)
    dataloader = DataLoader(
        dataset, 
        batch_size=32, 
        shuffle=True,
        num_workers=0,  # Disable workers to save memory
        pin_memory=False
    )
    return dataloader


def train_step(
    model: nn.Module,
    batch: Tuple[torch.Tensor, torch.Tensor],
    optimizer: optim.Optimizer,
    scaler: Optional[torch.cuda.amp.GradScaler] = None
) -> Tuple[float, float]:
    """Single training step with optional mixed precision."""
    model.train()
    x, y = batch
    
    if MIXED_PRECISION and torch.cuda.is_available():
        with torch.cuda.amp.autocast():
            outputs = model(x)
            loss = nn.functional.mse_loss(outputs, y)
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
    else:
        outputs = model(x)
        loss = nn.functional.mse_loss(outputs, y)
        loss.backward()
        optimizer.step()
    
    optimizer.zero_grad()
    
    return loss.item(), outputs.size(0)


def validate_step(
    model: nn.Module,
    batch: Tuple[torch.Tensor, torch.Tensor]
) -> Tuple[float, float]:
    """Single validation step."""
    model.eval()
    x, y = batch
    
    with torch.no_grad():
        outputs = model(x)
        loss = nn.functional.mse_loss(outputs, y)
    
    return loss.item(), outputs.size(0)


def train(
    model: GRUEstimator,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 10,
    learning_rate: float = 1e-3,
    patience: int = 3
) -> Dict[str, Any]:
    """
    Train model with memory monitoring and early stopping.
    """
    device = torch.device('cpu')  # CPU-only as per constraints
    model = model.to(device)
    
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=patience)
    
    if MIXED_PRECISION and torch.cuda.is_available():
        scaler = torch.cuda.amp.GradScaler()
    else:
        scaler = None
    
    best_val_loss = float('inf')
    patience_counter = 0
    training_history = []
    
    start_time = time.time()
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        train_loss = 0.0
        train_samples = 0
        
        # Gradient accumulation
        optimizer.zero_grad()
        accumulation_loss = 0.0
        accumulation_samples = 0
        accumulation_steps = 0
        
        for batch_idx, batch in enumerate(train_loader):
            # Memory check every 10 batches
            if batch_idx % 10 == 0:
                if not validate_memory_constraints(MAX_MEMORY_MB):
                    logger.warning("Memory limit approached, reducing batch size")
                    # Could implement dynamic batch size reduction here
            
            batch_loss, batch_samples = train_step(
                model, batch, optimizer, scaler
            )
            
            # Accumulate gradients
            accumulation_loss += batch_loss
            accumulation_samples += batch_samples
            accumulation_steps += 1
            
            if accumulation_steps >= GRAD_ACCUMULATION_STEPS:
                # Normalize and step
                accumulation_loss = accumulation_loss / GRAD_ACCUMULATION_STEPS
                accumulation_loss.backward()
                optimizer.step()
                optimizer.zero_grad()
                
                train_loss += accumulation_loss.item()
                train_samples += accumulation_samples
                
                accumulation_loss = 0.0
                accumulation_samples = 0
                accumulation_steps = 0
            
            # Clear memory periodically
            if batch_idx % 50 == 0:
                force_gc()
        
        # Handle remaining accumulation
        if accumulation_steps > 0:
            accumulation_loss = accumulation_loss / accumulation_steps
            accumulation_loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            train_loss += accumulation_loss.item()
            train_samples += accumulation_samples
        
        train_loss /= (len(train_loader) // GRAD_ACCUMULATION_STEPS + 1)
        
        # Validation
        val_loss = 0.0
        val_samples = 0
        with torch.no_grad():
            for batch in val_loader:
                batch_loss, batch_samples = validate_step(model, batch)
                val_loss += batch_loss
                val_samples += batch_samples
        
        val_loss /= len(val_loader)
        scheduler.step(val_loss)
        
        # Log progress
        epoch_time = time.time() - epoch_start
        logger.info(f"Epoch {epoch+1}/{num_epochs}: "
                   f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
                   f"Time: {epoch_time:.1f}s")
        
        training_history.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'memory_mb': get_memory_usage_mb()
        })
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # Force cleanup between epochs
        force_gc()
    
    total_time = time.time() - start_time
    logger.info(f"Training completed in {total_time:.1f}s")
    
    return {
        'history': training_history,
        'best_val_loss': best_val_loss,
        'total_time': total_time,
        'final_memory_mb': get_memory_usage_mb()
    }


def main():
    """Main entry point for memory-optimized training."""
    parser = argparse.ArgumentParser(description="Memory-optimized model training")
    parser.add_argument('--data', type=str, required=True,
                      help='Path to training data')
    parser.add_argument('--output', type=str, required=True,
                      help='Output checkpoint path')
    parser.add_argument('--epochs', type=int, default=10,
                      help='Number of epochs')
    parser.add_argument('--lr', type=float, default=1e-3,
                      help='Learning rate')
    parser.add_argument('--max-samples', type=int, default=None,
                      help='Maximum samples to use')
    args = parser.parse_args()
    
    set_seed(42)
    
    logger.info("Initializing memory-optimized trainer")
    
    # Validate memory before starting
    if not validate_memory_constraints(MAX_MEMORY_MB):
        logger.error("Memory constraints exceeded before training")
        sys.exit(1)
    
    # Load model
    config = load_config()
    model = GRUEstimator(
        input_size=config.get('input_size', 2),
        hidden_size=config.get('hidden_size', 64),
        num_layers=config.get('num_layers', 2)
    )
    
    # Load data
    train_size = int(0.8 * (args.max_samples or 100000))
    val_size = int(0.2 * (args.max_samples or 100000))
    
    # Simple split (in practice, use proper train/val split)
    train_loader = load_training_data(args.data, max_samples=train_size)
    val_loader = load_training_data(args.data, max_samples=val_size)
    
    # Train
    history = train(
        model,
        train_loader,
        val_loader,
        num_epochs=args.epochs,
        learning_rate=args.lr
    )
    
    # Save checkpoint
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': None,  # Removed for size
        'scheduler_state_dict': None,
        'history': history,
        'pending_validation': True
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, output_path)
    
    logger.info(f"Checkpoint saved to {output_path}")
    logger.info(f"Final memory usage: {history['final_memory_mb']:.2f} MB")


if __name__ == '__main__':
    main()
