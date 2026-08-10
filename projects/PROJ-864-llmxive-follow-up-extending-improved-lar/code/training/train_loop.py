"""
Training loop implementation for autoregressive and diffusion models.
Supports CPU-optimized training with mixed precision and resource monitoring.
"""
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.cuda.amp import autocast, GradScaler
import numpy as np
import json

from utils.logging import get_logger, info, error, warning
from utils.config import get_config, get_device, get_batch_size, get_learning_rate
from utils.monitor import get_ram_usage_gb, check_ram_threshold
from training.callbacks import create_logging_callback, LoggingCallback
from training.helpers import ensure_training_dirs

logger = get_logger(__name__)

class TextDataset(Dataset):
    """Simple text dataset wrapper for tokenized data."""
    def __init__(self, data_path: Path, max_length: int = 512):
        self.data_path = data_path
        self.max_length = max_length
        self.data = []
        
        logger.info(f"Loading dataset from {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        self.data.append(item)
                    except json.JSONDecodeError:
                        continue
        
        logger.info(f"Loaded {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # Assume 'input_ids' key exists in the JSONL
        input_ids = item.get('input_ids', [])
        if len(input_ids) > self.max_length:
            input_ids = input_ids[:self.max_length]
        
        return torch.tensor(input_ids, dtype=torch.long)

def prepare_dataloaders(data_dir: Path, batch_size: Optional[int] = None, 
                         max_length: int = 512, train_split: float = 0.9) -> Tuple[DataLoader, DataLoader]:
    """
    Prepare train and validation dataloaders from processed data.
    
    Args:
        data_dir: Path to the directory containing processed data.
        batch_size: Batch size for training.
        max_length: Maximum sequence length.
        train_split: Fraction of data to use for training.
        
    Returns:
        Tuple of (train_dataloader, val_dataloader)
    """
    if batch_size is None:
        batch_size = get_batch_size()
    
    train_path = data_dir / "train.jsonl"
    val_path = data_dir / "val.jsonl"
    
    if not train_path.exists() or not val_path.exists():
        error(f"Training data not found at {train_path} or {val_path}")
        raise FileNotFoundError("Training data files missing. Please run data preprocessing first.")
    
    train_dataset = TextDataset(train_path, max_length)
    val_dataset = TextDataset(val_path, max_length)
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True,
        num_workers=0,  # CPU-safe
        pin_memory=False
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )
    
    return train_loader, val_loader

def train_epoch(model: nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer, 
                epoch: int, device: torch.device, scaler: Optional[GradScaler] = None) -> float:
    """
    Train for one epoch.
    
    Returns:
        Average training loss for the epoch.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    use_amp = scaler is not None
    
    for batch_idx, batch in enumerate(dataloader):
        batch = batch.to(device)
        optimizer.zero_grad()
        
        if use_amp:
            with autocast():
                outputs = model(batch)
                loss = outputs.loss
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        
        if batch_idx % 100 == 0:
            info(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss

def evaluate_epoch(model: nn.Module, dataloader: DataLoader, 
                   device: torch.device, scaler: Optional[GradScaler] = None) -> float:
    """
    Evaluate model on validation set for one epoch.
    
    Returns:
        Average validation loss.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    use_amp = scaler is not None
    
    with torch.no_grad():
        for batch in dataloader:
            batch = batch.to(device)
            
            if use_amp:
                with autocast():
                    outputs = model(batch)
                    loss = outputs.loss
            else:
                outputs = model(batch)
                loss = outputs.loss
            
            total_loss += loss.item()
            num_batches += 1
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss

def train_loop(model: nn.Module, train_loader: DataLoader, val_loader: DataLoader,
               num_epochs: int, seed_id: int, device: torch.device,
               learning_rate: Optional[float] = None, batch_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Main training loop with logging and resource monitoring.
    
    Args:
        model: The model to train.
        train_loader: Training data loader.
        val_loader: Validation data loader.
        num_epochs: Number of epochs to train.
        seed_id: Identifier for this training run.
        device: Torch device to use.
        learning_rate: Learning rate (optional, uses config if None).
        batch_size: Batch size (optional, uses config if None).
        
    Returns:
        Dictionary containing training results and metrics.
    """
    if learning_rate is None:
        learning_rate = get_learning_rate()
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    scaler = GradScaler() if device.type == 'cuda' else None
    
    # Setup logging
    dirs = ensure_training_dirs()
    callback = create_logging_callback(dirs["logs"], seed_id)
    
    info(f"Starting training for seed {seed_id} on {device}")
    info(f"Training for {num_epochs} epochs with lr={learning_rate}, batch_size={batch_size}")
    
    training_results = {
        "seed_id": seed_id,
        "epochs_completed": 0,
        "status": "COMPLETED",
        "final_train_loss": None,
        "final_val_loss": None,
        "history": []
    }
    
    start_time = time.time()
    
    try:
        for epoch in range(num_epochs):
            callback.on_epoch_start(epoch)
            
            # Check RAM before epoch
            ram_gb = get_ram_usage_gb()
            if ram_gb > 6.5:  # Safety threshold
                warning(f"High RAM usage detected: {ram_gb:.2f}GB. Consider reducing batch size.")
            
            train_loss = train_epoch(model, train_loader, optimizer, epoch, device, scaler)
            val_loss = evaluate_epoch(model, val_loader, device, scaler)
            
            callback.on_epoch_end(epoch, train_loss, val_loss)
            
            training_results["history"].append({
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "gap": val_loss - train_loss
            })
            
            training_results["epochs_completed"] = epoch + 1
            training_results["final_train_loss"] = train_loss
            training_results["final_val_loss"] = val_loss
            
            # Check for early stopping or timeout (simplified)
            if epoch > 0 and (val_loss > train_loss * 2):  # Simple overfitting check
                warning("Significant overfitting detected. Training may be truncated.")
    
    except KeyboardInterrupt:
        info("Training interrupted by user.")
        training_results["status"] = "TRUNCATED"
        callback.on_training_end("TRUNCATED")
    
    except Exception as e:
        error(f"Training failed with error: {str(e)}")
        training_results["status"] = "FAILED"
        raise
    
    finally:
        callback.on_training_end(training_results["status"])
        total_time = time.time() - start_time
        info(f"Training finished in {total_time:.2f} seconds")
    
    return training_results

def main():
    """
    Entry point for standalone training execution.
    """
    info("Running training loop main...")
    
    # This is a placeholder for actual execution
    # In a real scenario, this would load a model and dataset
    # and run the training loop
    
    logger.info("Training loop module loaded successfully.")
