"""
Training loop for RF and Baseline models.

Implements training for both the LightweightAutoregressiveModel (RF tokens)
and the SimpleCNNBaseline (raw pixels).

CRITICAL CONSTRAINTS (Constitution VII):
1. The ONLY stopping criterion is the hard epoch limit.
2. Validation loss plateau detection is implemented for LOGGING/DIAGNOSTICS ONLY.
   It does NOT trigger early stopping.
3. Resource monitoring (T004) is integrated to enforce 4GB RAM / 12GB disk limits.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
import numpy as np

# Project imports
from config import get_config_dict, ensure_dirs
from utils.resource_monitor import ResourceMonitor, MemoryLimitExceeded
from data.preprocessing import PubLayNetPreprocessedDataset, create_preprocessing_dataloader
from models.autoregressive import create_ar_model, get_default_config as get_ar_config
from models.baseline import create_baseline_model, get_default_config as get_baseline_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int,
    config: Dict[str, Any]
) -> float:
    """
    Run a single training epoch.
    
    Args:
        model: The model to train.
        dataloader: DataLoader for training data.
        optimizer: Optimizer instance.
        device: Torch device (CPU/CUDA).
        epoch: Current epoch number.
        config: Configuration dictionary.
        
    Returns:
        Average training loss for the epoch.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch_idx, batch in enumerate(dataloader):
        # Check resource limits at the start of each batch
        # (ResourceMonitor context manager handles this globally, but explicit check is good practice)
        
        inputs = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        optimizer.zero_grad()
        
        try:
            outputs = model(
                input_ids=inputs,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss
            
            loss.backward()
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config.get('max_grad_norm', 1.0))
            
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            if batch_idx % 10 == 0:
                logger.info(f"Epoch {epoch} - Batch {batch_idx}/{len(dataloader)} - Loss: {loss.item():.4f}")
                
        except MemoryLimitExceeded as e:
            logger.error(f"Memory limit exceeded during training batch {batch_idx}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during training batch {batch_idx}: {e}")
            raise

    return total_loss / num_batches if num_batches > 0 else 0.0

def validate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    config: Dict[str, Any]
) -> float:
    """
    Run validation and return average loss.
    
    Args:
        model: The model to validate.
        dataloader: DataLoader for validation data.
        device: Torch device.
        config: Configuration dictionary.
        
    Returns:
        Average validation loss.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for batch in dataloader:
            inputs = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            try:
                outputs = model(
                    input_ids=inputs,
                    attention_mask=attention_mask,
                    labels=labels
                )
                loss = outputs.loss
                total_loss += loss.item()
                num_batches += 1
            except Exception as e:
                logger.error(f"Error during validation: {e}")
                raise

    return total_loss / num_batches if num_batches > 0 else 0.0

def train_model(
    model_name: str,
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Train a model for a fixed number of epochs.
    
    Args:
        model_name: Name of the model ('rf' or 'baseline').
        model: The model to train.
        train_loader: Training DataLoader.
        val_loader: Validation DataLoader.
        device: Torch device.
        config: Configuration dictionary.
        
    Returns:
        Dictionary containing training history and final metrics.
    """
    logger.info(f"Starting training for {model_name} model on {device}")
    
    # Initialize optimizer and scheduler
    optimizer = AdamW(
        model.parameters(),
        lr=config['learning_rate'],
        weight_decay=config.get('weight_decay', 0.01)
    )
    
    # Scheduler for learning rate adjustment (optional, for diagnostics)
    scheduler = ReduceLROnPlateau(
        optimizer, 
        mode='min', 
        factor=0.5, 
        patience=2, 
        verbose=True
    )
    
    max_epochs = config['max_epochs']
    history = {
        'train_loss': [],
        'val_loss': [],
        'learning_rates': []
    }
    
    best_val_loss = float('inf')
    plateau_counter = 0
    
    # CONSTITUTION VII WAIVER: 
    # The training loop does NOT stop on plateau. 
    # Validation loss plateau detection is for LOGGING/DIAGNOSTICS ONLY.
    # The hard epoch limit (max_epochs) is the ONLY stopping criterion.
    # Reference: Constitution VII - Hard Epoch Limit Override
    
    for epoch in range(1, max_epochs + 1):
        logger.info(f"Epoch {epoch}/{max_epochs}")
        
        start_time = time.time()
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, device, epoch, config)
        history['train_loss'].append(train_loss)
        
        # Validate
        val_loss = validate(model, val_loader, device, config)
        history['val_loss'].append(val_loss)
        history['learning_rates'].append(optimizer.param_groups[0]['lr'])
        
        end_time = time.time()
        epoch_time = end_time - start_time
        
        logger.info(f"Epoch {epoch} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Time: {epoch_time:.2f}s")
        
        # Update scheduler (for diagnostics only, does not trigger early stop)
        scheduler.step(val_loss)
        
        # Plateau detection for LOGGING ONLY (Constitution VII Waiver)
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            plateau_counter = 0
            logger.info(f"  -> New best validation loss: {best_val_loss:.4f}")
        else:
            plateau_counter += 1
            logger.warning(f"  -> Validation loss plateau detected (epoch {epoch}/{max_epochs}). "
                         f"Continuing training per Constitution VII (hard epoch limit). "
                         f"Plateau count: {plateau_counter}")
        
        # Log resource usage periodically
        # (ResourceMonitor context manager handles enforcement, but we log here for visibility)
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        logger.debug(f"  -> Current memory usage: {mem_mb:.2f} MB")
        
    # Final validation
    final_val_loss = validate(model, val_loader, device, config)
    
    results = {
        'model_name': model_name,
        'final_train_loss': history['train_loss'][-1] if history['train_loss'] else None,
        'final_val_loss': final_val_loss,
        'best_val_loss': best_val_loss,
        'epochs_completed': max_epochs,
        'history': history
    }
    
    logger.info(f"Training completed for {model_name}. Final Val Loss: {final_val_loss:.4f}")
    return results

def main():
    """Main entry point for training."""
    logger.info("Starting training pipeline...")
    
    # Load configuration
    config = get_config_dict()
    ensure_dirs()
    
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() and not config.get('force_cpu', False) else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Initialize resource monitor (4GB RAM, 12GB Disk)
    # This is a context manager that will raise MemoryLimitExceeded if limits are exceeded
    resource_monitor = ResourceMonitor(
        memory_limit_mb=4096,
        disk_limit_gb=12,
        check_interval_sec=10,
        log_interval_sec=30
    )
    
    # Prepare data loaders
    # T023: create_preprocessing_dataloader returns train/val loaders
    try:
        train_loader, val_loader = create_preprocessing_dataloader(
            data_dir=config['data_dir'],
            batch_size=config.get('batch_size', 4),
            max_length=config.get('max_seq_length', 512)
        )
        logger.info(f"Data loaders created. Train: {len(train_loader)}, Val: {len(val_loader)}")
    except Exception as e:
        logger.error(f"Failed to create data loaders: {e}")
        raise

    # Train RF Model
    logger.info("=== Training RF Model ===")
    rf_model = create_ar_model(config)
    rf_model.to(device)
    
    rf_results = None
    try:
        with resource_monitor:
            rf_results = train_model(
                model_name='rf',
                model=rf_model,
                train_loader=train_loader,
                val_loader=val_loader,
                device=device,
                config=config
            )
    except MemoryLimitExceeded as e:
        logger.error(f"Training aborted due to resource limits: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during RF model training: {e}")
        raise

    # Train Baseline Model
    logger.info("=== Training Baseline Model ===")
    baseline_model = create_baseline_model(config)
    baseline_model.to(device)
    
    baseline_results = None
    try:
        with resource_monitor:
            baseline_results = train_model(
                model_name='baseline',
                model=baseline_model,
                train_loader=train_loader,
                val_loader=val_loader,
                device=device,
                config=config
            )
    except MemoryLimitExceeded as e:
        logger.error(f"Training aborted due to resource limits: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during Baseline model training: {e}")
        raise

    # Save results
    results_dir = Path(config['results_dir'])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / 'training_log.json'
    with open(output_path, 'w') as f:
        json.dump({
            'rf_model': rf_results,
            'baseline_model': baseline_results,
            'config': config
        }, f, indent=2)
    
    logger.info(f"Training results saved to {output_path}")
    return rf_results, baseline_results

if __name__ == '__main__':
    main()