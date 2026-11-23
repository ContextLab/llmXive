import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from utils.config import load_config, get_project_root, get_batch_size, get_learning_rate, get_embed_dim
from utils.logging import get_logger, info, error, warning, debug
from utils.monitor import get_ram_usage_gb, get_resource_snapshot
from models.autoregressive import create_autoregressive_model
from models.diffusion import create_diffusion_model
from training.callbacks import create_logging_callback

logger = get_logger(__name__)

class TextDataset(Dataset):
    def __init__(self, data_path: str, max_length: int = 512):
        self.data_path = data_path
        self.max_length = max_length
        self.data = []
        self._load_data()

    def _load_data(self):
        """Load JSONL data into memory (assuming fits in RAM for micro-corpus)."""
        logger.info(f"Loading dataset from {self.data_path}")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if 'input_ids' in entry:
                        self.data.append(entry['input_ids'])
        logger.info(f"Loaded {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        input_ids = self.data[idx]
        # Truncate or pad if necessary
        if len(input_ids) > self.max_length:
            input_ids = input_ids[:self.max_length]
        else:
            # Simple padding with 0 (assuming 0 is pad token, adjust if needed)
            input_ids = input_ids + [0] * (self.max_length - len(input_ids))
        return torch.tensor(input_ids, dtype=torch.long)

def prepare_dataloaders(config: Dict[str, Any], batch_size: int) -> Tuple[DataLoader, DataLoader]:
    """Prepare train and validation dataloaders."""
    project_root = get_project_root()
    data_dir = project_root / "data" / "processed"
    
    train_path = data_dir / "train_split.jsonl"
    val_path = data_dir / "val_split.jsonl"

    if not train_path.exists():
        raise FileNotFoundError(f"Train split not found at {train_path}. Run T016 first.")
    if not val_path.exists():
        raise FileNotFoundError(f"Val split not found at {val_path}. Run T016 first.")

    max_seq_len = config.get('model_params', {}).get('max_seq_length', 512)

    train_dataset = TextDataset(str(train_path), max_length=max_seq_len)
    val_dataset = TextDataset(str(val_path), max_length=max_seq_len)

    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=0, 
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

class OOMRetrySignal(Exception):
    """Custom exception to signal OOM for retry logic."""
    pass

def train_epoch(
    model: nn.Module, 
    dataloader: DataLoader, 
    optimizer: torch.optim.Optimizer, 
    epoch: int, 
    device: torch.device,
    batch_size: int,
    callback: Any
) -> float:
    """Train for one epoch with dynamic batch size retry."""
    model.train()
    total_loss = 0.0
    num_batches = 0
    start_time = time.time()
    current_batch_size = batch_size

    while True:
        try:
            for batch_idx, batch in enumerate(dataloader):
                batch = batch.to(device)
                optimizer.zero_grad()

                # Forward pass
                outputs = model(batch)
                if isinstance(outputs, dict):
                    loss = outputs['loss']
                else:
                    # Assume outputs is (batch, seq, vocab) and we need to compute loss
                    # Simplified: assume model returns loss directly or we compute it
                    # For standard LM:
                    logits = outputs
                    labels = batch
                    loss = torch.nn.functional.cross_entropy(
                        logits.view(-1, logits.size(-1)), 
                        labels.view(-1), 
                        ignore_index=0
                    )

                # Backward pass
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                num_batches += 1

                # Log intermediate metrics if needed
                if callback:
                    callback.on_batch_end(epoch, batch_idx, loss.item(), current_batch_size)

            break # Success, exit retry loop

        except (RuntimeError, MemoryError) as e:
            if "out of memory" in str(e).lower() or "oom" in str(e).lower():
                warning(f"OOM detected in epoch {epoch}, batch {batch_idx}. Reducing batch size.")
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                
                if current_batch_size <= 4:
                    error(f"Batch size reduced to minimum (4) and still OOM. Failing.")
                    raise e
                
                current_batch_size = current_batch_size // 2
                info(f"Retrying epoch {epoch} with batch size {current_batch_size}")
                
                # Re-create dataloader with smaller batch size
                # Note: In a real scenario, we might want to avoid reloading data if possible,
                # but for simplicity and correctness here, we reload.
                # Optimization: The caller (train_loop) should handle the dataloader recreation
                # to avoid reloading data if the dataset is large. 
                # However, the task asks for logic in train_loop.py. 
                # We will raise a signal to let the caller handle dataloader recreation.
                raise OOMRetrySignal(f"OOM at batch_size={current_batch_size}")
            else:
                error(f"Unexpected error: {e}")
                raise e

    elapsed = time.time() - start_time
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    
    if callback:
        callback.on_epoch_end(epoch, avg_loss, elapsed, current_batch_size)
    
    return avg_loss, current_batch_size

def evaluate_epoch(
    model: nn.Module, 
    dataloader: DataLoader, 
    device: torch.device
) -> float:
    """Evaluate model on validation set."""
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for batch in dataloader:
            batch = batch.to(device)
            outputs = model(batch)
            if isinstance(outputs, dict):
                loss = outputs['loss']
            else:
                logits = outputs
                labels = batch
                loss = torch.nn.functional.cross_entropy(
                    logits.view(-1, logits.size(-1)), 
                    labels.view(-1), 
                    ignore_index=0
                )
            
            total_loss += loss.item()
            num_batches += 1

    return total_loss / num_batches if num_batches > 0 else 0.0

def train_loop(
    model_type: str, 
    config: Dict[str, Any], 
    device: torch.device
) -> Dict[str, Any]:
    """
    Main training loop with dynamic batch size adjustment.
    Implements T038a: Dynamic Batch Size logic.
    """
    logger.info(f"Starting training loop for {model_type}")
    
    # Load config values
    max_epochs = config.get('num_epochs', 10)
    initial_batch_size = config.get('batch_size', 64) # Default, overridden by dynamic logic
    learning_rate = config.get('learning_rate', 1e-4)
    
    # Prepare dataloaders
    # Note: We start with a large batch size and let the training epoch handle reduction
    # But we need a dataloader. We'll start with the config batch size.
    # If OOM happens, we catch it and recreate the dataloader with smaller batch size.
    
    try:
        train_loader, val_loader = prepare_dataloaders(config, batch_size=initial_batch_size)
    except Exception as e:
        error(f"Failed to prepare dataloaders: {e}")
        raise

    # Create model
    if model_type == "autoregressive":
        model = create_autoregressive_model(config)
    elif model_type == "diffusion":
        model = create_diffusion_model(config)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    
    # Callback setup
    callback = create_logging_callback(model_type, config)

    history = {
        'train_loss': [],
        'val_loss': [],
        'batch_size_used': [],
        'epochs': []
    }

    final_batch_size = initial_batch_size

    for epoch in range(1, max_epochs + 1):
        info(f"Epoch {epoch}/{max_epochs} (Starting batch size: {final_batch_size})")
        
        # We need to handle the case where the dataloader needs to be recreated
        # because the batch size changed.
        current_loader = train_loader
        current_val_loader = val_loader
        
        # If the batch size changed from the previous epoch's start, we need new loaders
        # But since we modify final_batch_size inside the loop, we check if we need to reload
        # A simpler approach for the loop:
        # The train_epoch function raises OOMRetrySignal if OOM occurs.
        # We catch it, reduce batch size, recreate loaders, and retry the epoch.
        
        retry_epoch = True
        while retry_epoch:
            try:
                # Ensure dataloader matches current final_batch_size
                if current_loader.batch_size != final_batch_size:
                    logger.info(f"Recreating dataloaders with batch_size={final_batch_size}")
                    current_loader, current_val_loader = prepare_dataloaders(config, final_batch_size)
                
                train_loss, final_batch_size = train_epoch(
                    model, 
                    current_loader, 
                    optimizer, 
                    epoch, 
                    device,
                    final_batch_size,
                    callback
                )
                retry_epoch = False # Success
            except OOMRetrySignal:
                # Reduce batch size for the next attempt of THIS epoch
                if final_batch_size <= 4:
                    error("Batch size hit minimum and OOM persists. Aborting training.")
                    raise
                final_batch_size = final_batch_size // 2
                logger.warning(f"OOM in epoch {epoch}. Reducing batch size to {final_batch_size} and retrying epoch.")
                # Loop continues, will recreate dataloader with new batch size
        
        # Validation
        val_loss = evaluate_epoch(model, current_val_loader, device)
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['batch_size_used'].append(final_batch_size)
        history['epochs'].append(epoch)
        
        logger.info(f"Epoch {epoch}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, Batch Size={final_batch_size}")

    return history

def main():
    """Entry point for running the training loop."""
    project_root = get_project_root()
    config_path = project_root / "code" / "config.yaml"
    
    if not config_path.exists():
        error(f"Config not found at {config_path}. Run T001 first.")
        sys.exit(1)

    config = load_config(config_path)
    
    # Check scope
    if not config.get('approved', False):
        error("Scope not approved. Run T002 check_scope.py")
        sys.exit(1)

    device = torch.device("cpu") # CPU optimized as per plan
    logger.info(f"Using device: {device}")

    # Run for both model types
    for model_type in ["autoregressive", "diffusion"]:
        try:
            history = train_loop(model_type, config, device)
            # Save history or logs here if needed, though callbacks handle logging
            logger.info(f"Training completed for {model_type}")
        except Exception as e:
            error(f"Training failed for {model_type}: {e}")
            raise

    logger.info("All training experiments completed.")

if __name__ == "__main__":
    main()