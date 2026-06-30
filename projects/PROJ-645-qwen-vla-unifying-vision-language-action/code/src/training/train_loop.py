import os
import sys
import time
import logging
import json
import gc
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import psutil

from src.utils.logging_config import get_logger, setup_logging
from src.utils.resource_monitor import get_current_ram_gb, check_wall_time_limit
from src.models.vla_model import Qwen2VLVLA
from src.models.entities import ModelCheckpoint

# Configure logging
logger = get_logger("train_loop")

def auto_reduce_batch_size(
    current_batch_size: int,
    min_batch_size: int = 1,
    reduction_factor: float = 0.5
) -> int:
    """
    Dynamically reduce batch size if RAM usage exceeds the threshold.
    
    Args:
        current_batch_size: The current batch size being used.
        min_batch_size: The minimum allowable batch size.
        reduction_factor: Factor by which to reduce the batch size (e.g., 0.5 for half).
        
    Returns:
        The new reduced batch size.
    """
    new_batch_size = max(int(current_batch_size * reduction_factor), min_batch_size)
    if new_batch_size < current_batch_size:
        logger.warning(
            f"RAM usage exceeded 6.5GB. Reducing batch size from {current_batch_size} to {new_batch_size}."
        )
    return new_batch_size

def train_epoch(
    model: Qwen2VLVLA,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
    ram_limit_gb: float = 6.5,
    wall_time_limit: float = 21600.0,
    start_time: float = None
) -> Tuple[float, int]:
    """
    Train the model for one epoch with dynamic batch size adjustment.
    
    Args:
        model: The VLA model to train.
        dataloader: DataLoader for the training dataset.
        optimizer: Optimizer for the model parameters.
        device: Device to run training on.
        epoch: Current epoch number.
        ram_limit_gb: Maximum allowed RAM usage in GB.
        wall_time_limit: Maximum allowed wall-clock time in seconds.
        start_time: Start time of the training session.
        
    Returns:
        Tuple of (average_loss, samples_processed)
    """
    model.train()
    total_loss = 0.0
    samples_processed = 0
    current_batch_size = dataloader.batch_size
    if current_batch_size is None:
        current_batch_size = 1  # Fallback if batch_size is not set
        
    # Create a new dataloader with the initial batch size if needed
    # Note: In a real streaming scenario, we might need to reconstruct the loader
    # For this implementation, we assume the loader can handle dynamic batch size 
    # or we re-instantiate it with the new batch size.
    
    logger.info(f"Starting epoch {epoch} with batch size {current_batch_size}")

    for batch_idx, batch in enumerate(dataloader):
        # Check wall time limit
        if start_time and not check_wall_time_limit(start_time, wall_time_limit):
            logger.warning("TIMEOUT_WARNING: Wall time limit reached. Stopping training.")
            return total_loss / max(samples_processed, 1), samples_processed

        # Move batch to device
        # Assuming batch is a dict with 'images', 'actions', 'prompts' etc.
        # Adjust keys based on actual dataset structure
        try:
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
        except Exception as e:
            logger.error(f"Error moving batch to device: {e}")
            continue

        # Forward pass
        optimizer.zero_grad()
        try:
            outputs = model(**batch)
            loss = outputs.loss
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            samples_processed += batch['input_ids'].size(0) if 'input_ids' in batch else batch.get('actions', torch.tensor([])).size(0)
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                logger.warning(f"OOM error at batch {batch_idx}. Reducing batch size.")
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Reduce batch size
                new_batch_size = auto_reduce_batch_size(current_batch_size)
                if new_batch_size == current_batch_size:
                    logger.error("Cannot reduce batch size further. Stopping training.")
                    return total_loss / max(samples_processed, 1), samples_modules
                
                current_batch_size = new_batch_size
                
                # Re-create dataloader with new batch size
                # Note: This requires the dataset to support dynamic batching or re-instantiation
                # For simplicity, we assume we can re-create the dataloader
                # In a production setting, you might need to handle this more gracefully
                try:
                    # Re-create dataloader with new batch size
                    # Assuming 'dataloader.dataset' is accessible
                    dataloader = DataLoader(
                        dataloader.dataset,
                        batch_size=new_batch_size,
                        shuffle=dataloader.shuffle,
                        num_workers=dataloader.num_workers,
                        pin_memory=dataloader.pin_memory
                    )
                    logger.info(f"Resuming epoch {epoch} with new batch size {new_batch_size}")
                    # Skip to next batch to avoid re-processing current one
                    continue
                except Exception as re_loader_err:
                    logger.error(f"Failed to re-create dataloader: {re_loader_err}")
                    return total_loss / max(samples_processed, 1), samples_processed
            else:
                logger.error(f"Unexpected error during training: {e}")
                raise

        # Check RAM usage periodically (every 10 batches)
        if batch_idx % 10 == 0:
            current_ram = get_current_ram_gb()
            if current_ram > ram_limit_gb:
                logger.warning(f"RAM usage ({current_ram:.2f}GB) exceeds limit ({ram_limit_gb}GB). Reducing batch size.")
                new_batch_size = auto_reduce_batch_size(current_batch_size)
                if new_batch_size == current_batch_size:
                    logger.error("Cannot reduce batch size further. Stopping training.")
                    return total_loss / max(samples_processed, 1), samples_processed
                
                current_batch_size = new_batch_size
                # Re-create dataloader
                try:
                    dataloader = DataLoader(
                        dataloader.dataset,
                        batch_size=new_batch_size,
                        shuffle=dataloader.shuffle,
                        num_workers=dataloader.num_workers,
                        pin_memory=dataloader.pin_memory
                    )
                    logger.info(f"Resuming epoch {epoch} with new batch size {new_batch_size}")
                except Exception as re_loader_err:
                    logger.error(f"Failed to re-create dataloader: {re_loader_err}")
                    return total_loss / max(samples_processed, 1), samples_processed

    return total_loss / max(samples_processed, 1), samples_processed

def train_loop(
    model: Qwen2VLVLA,
    train_loader: DataLoader,
    device: torch.device,
    num_epochs: int,
    output_dir: str,
    wall_time_limit: float = 21600.0,
    ram_limit_gb: float = 6.5,
    learning_rate: float = 1e-4
) -> List[ModelCheckpoint]:
    """
    Main training loop with batch size auto-adjustment and time limits.
    
    Args:
        model: The VLA model to train.
        train_loader: DataLoader for the training dataset.
        device: Device to run training on.
        num_epochs: Number of epochs to train for.
        output_dir: Directory to save checkpoints.
        wall_time_limit: Maximum allowed wall-clock time in seconds.
        ram_limit_gb: Maximum allowed RAM usage in GB.
        learning_rate: Learning rate for the optimizer.
        
    Returns:
        List of ModelCheckpoint entities representing saved checkpoints.
    """
    setup_logging(level=logging.INFO)
    logger.info(f"Starting training on {device}")
    
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.95)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    checkpoints = []
    
    for epoch in range(num_epochs):
        logger.info(f"--- Epoch {epoch + 1}/{num_epochs} ---")
        
        # Check wall time at start of epoch
        if not check_wall_time_limit(start_time, wall_time_limit):
            logger.warning("TIMEOUT_WARNING: Wall time limit reached before epoch start.")
            break
        
        avg_loss, samples = train_epoch(
            model=model,
            dataloader=train_loader,
            optimizer=optimizer,
            device=device,
            epoch=epoch + 1,
            ram_limit_gb=ram_limit_gb,
            wall_time_limit=wall_time_limit,
            start_time=start_time
        )
        
        scheduler.step()
        
        # Save checkpoint
        checkpoint_path = output_path / f"model_epoch_{epoch + 1}.pt"
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': avg_loss,
            'samples_processed': samples
        }, checkpoint_path)
        
        checkpoint_entity = ModelCheckpoint(
            path=str(checkpoint_path),
            epoch=epoch + 1,
            loss=avg_loss,
            samples_processed=samples,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        )
        checkpoints.append(checkpoint_entity)
        
        logger.info(f"Epoch {epoch + 1} completed. Avg Loss: {avg_loss:.4f}, Samples: {samples}")
        logger.info(f"Checkpoint saved to {checkpoint_path}")
        
        # Check wall time after epoch
        if not check_wall_time_limit(start_time, wall_time_limit):
            logger.warning("TIMEOUT_WARNING: Wall time limit reached after epoch.")
            break
    
    elapsed = time.time() - start_time
    logger.info(f"Training completed in {elapsed:.2f} seconds.")
    return checkpoints

def main():
    """
    Entry point for training loop.
    This function demonstrates the batch size auto-adjustment logic.
    """
    # Setup
    device = torch.device("cpu")  # Force CPU for this experiment
    torch.set_num_threads(2)  # Limit parallelism
    
    # Create a dummy model for demonstration
    # In a real scenario, this would be loaded from a checkpoint or initialized properly
    model = Qwen2VLVLA()
    model.to(device)
    
    # Create a dummy dataset and dataloader
    # This is a placeholder for the actual dataset loading logic
    from torch.utils.data import Dataset, DataLoader
    
    class DummyDataset(Dataset):
        def __init__(self, size=100):
            self.size = size
            
        def __len__(self):
            return self.size
            
        def __getitem__(self, idx):
            # Return dummy data matching expected model input
            return {
                'input_ids': torch.randint(0, 1000, (32,)),  # Dummy token IDs
                'attention_mask': torch.ones(32),
                'pixel_values': torch.randn(1, 3, 224, 224),  # Dummy image
                'actions': torch.randn(8, 7)  # Dummy action vector (8 steps, 7 DOF)
            }
    
    dataset = DummyDataset(size=1000)
    train_loader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=0)
    
    output_dir = "data/checkpoints"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Run training loop
    checkpoints = train_loop(
        model=model,
        train_loader=train_loader,
        device=device,
        num_epochs=1,  # Just one epoch for demo
        output_dir=output_dir,
        wall_time_limit=60.0,  # Short limit for demo
        ram_limit_gb=6.5,
        learning_rate=1e-4
    )
    
    logger.info(f"Training finished. Saved {len(checkpoints)} checkpoints.")

if __name__ == "__main__":
    main()