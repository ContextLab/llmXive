"""
Training loop for Autoregressive and Diffusion models.
Implements CPU-optimized training with torch.compile support.
"""
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

# Project imports
from utils.config import (
    get_config,
    get_device,
    get_learning_rate,
    get_batch_size,
    get_num_epochs,
    get_max_seq_length,
    get_vocab_size,
    get_embed_dim,
    get_num_heads,
    get_model_config,
    get_processed_dir,
    get_artifacts_dir,
    ConfigError,
)
from utils.logging import get_logger, setup_logging
from utils.monitor import get_ram_usage_gb, get_elapsed_time
from models.autoregressive import create_autoregressive_model, AutoregressiveModel
from models.diffusion import create_diffusion_model, DiffusionModel
from data.split_data import load_jsonl, split_data

# Setup logging
setup_logging()
logger = get_logger(__name__)


class TextDataset(Dataset):
    """Simple dataset wrapper for tokenized text data."""
    
    def __init__(self, data_path: str, max_seq_length: int):
        self.data_path = data_path
        self.max_seq_length = max_seq_length
        self.data = []
        self._load_data()
    
    def _load_data(self):
        """Load data from JSONL file."""
        logger.info(f"Loading dataset from {self.data_path}")
        try:
            self.data = load_jsonl(self.data_path)
            logger.info(f"Loaded {len(self.data)} samples")
        except Exception as e:
            logger.error(f"Failed to load data from {self.data_path}: {e}")
            raise
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        # Expecting 'input_ids' or 'tokens' in the JSONL
        if 'input_ids' in item:
            tokens = item['input_ids']
        elif 'tokens' in item:
            tokens = item['tokens']
        else:
            # Fallback: try to convert text to tokens if available
            raise ValueError(f"Expected 'input_ids' or 'tokens' in data item at index {idx}")
        
        # Truncate or pad to max_seq_length
        if len(tokens) > self.max_seq_length:
            tokens = tokens[:self.max_seq_length]
        
        # For causal LM, target is shifted input
        # For simplicity, we assume tokens include both input and target
        # In a real scenario, we'd separate them properly
        x = torch.tensor(tokens[:-1], dtype=torch.long)
        y = torch.tensor(tokens[1:], dtype=torch.long)
        
        return x, y


def prepare_dataloaders(
    train_split: List[Dict[str, Any]],
    val_split: List[Dict[str, Any]],
    batch_size: int,
    max_seq_length: int,
) -> Tuple[DataLoader, DataLoader]:
    """Create train and validation dataloaders."""
    train_dataset = TextDataset.__new__(TextDataset)
    train_dataset.data = train_split
    train_dataset.max_seq_length = max_seq_length
    
    val_dataset = TextDataset.__new__(TextDataset)
    val_dataset.data = val_split
    val_dataset.max_seq_length = max_seq_length
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,  # CPU only, avoid multiprocessing overhead
        pin_memory=False,
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False,
    )
    
    return train_loader, val_loader


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int,
    use_compile: bool = True,
) -> float:
    """Train one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    start_time = time.time()
    
    for batch_idx, (x, y) in enumerate(dataloader):
        x = x.to(device)
        y = y.to(device)
        
        optimizer.zero_grad()
        
        # Forward pass
        if isinstance(model, AutoregressiveModel):
            # For autoregressive models, forward returns logits
            logits = model(x)
        elif isinstance(model, DiffusionModel):
            # For diffusion models, we need to handle the diffusion process
            # Simplified: treat as a standard forward pass for now
            logits = model(x)
        else:
            raise ValueError(f"Unsupported model type: {type(model)}")
        
        # Compute loss (cross-entropy)
        loss = nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)),
            y.view(-1),
            ignore_index=-100,
        )
        
        # Backward pass
        loss.backward()
        
        # Gradient clipping (optional, but good practice)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        
        if batch_idx % 10 == 0:
            current_loss = total_loss / num_batches
            elapsed = time.time() - start_time
            logger.debug(
                f"Epoch {epoch}, Batch {batch_idx}, Loss: {current_loss:.4f}, "
                f"Time: {elapsed:.2f}s, RAM: {get_ram_usage_gb():.2f}GB"
            )
    
    avg_loss = total_loss / max(num_batches, 1)
    return avg_loss


def evaluate_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    use_compile: bool = True,
) -> float:
    """Evaluate one epoch."""
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for x, y in dataloader:
            x = x.to(device)
            y = y.to(device)
            
            # Forward pass
            if isinstance(model, AutoregressiveModel):
                logits = model(x)
            elif isinstance(model, DiffusionModel):
                logits = model(x)
            else:
                raise ValueError(f"Unsupported model type: {type(model)}")
            
            # Compute loss
            loss = nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)),
                y.view(-1),
                ignore_index=-100,
            )
            
            total_loss += loss.item()
            num_batches += 1
    
    avg_loss = total_loss / max(num_batches, 1)
    return avg_loss


def train_loop(
    model_type: str,
    train_data_path: str,
    val_data_path: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main training loop for a single model.
    
    Args:
        model_type: 'autoregressive' or 'diffusion'
        train_data_path: Path to training data JSONL
        val_data_path: Path to validation data JSONL
        output_dir: Directory to save training logs and checkpoints
    
    Returns:
        Dictionary containing training metrics and results
    """
    logger.info(f"Starting training loop for {model_type} model")
    
    # Get configuration
    try:
        config = get_config()
    except ConfigError as e:
        logger.error(f"Failed to load config: {e}")
        raise
    
    device = get_device()
    batch_size = get_batch_size()
    num_epochs = get_num_epochs()
    max_seq_length = get_max_seq_length()
    learning_rate = get_learning_rate()
    embed_dim = get_embed_dim()
    num_heads = get_num_heads()
    vocab_size = get_vocab_size()
    
    logger.info(f"Device: {device}, Batch size: {batch_size}, Epochs: {num_epochs}")
    logger.info(f"Embed dim: {embed_dim}, Heads: {num_heads}, Vocab: {vocab_size}")
    
    # Prepare data
    logger.info("Preparing dataloaders...")
    train_split = load_jsonl(train_data_path)
    val_split = load_jsonl(val_data_path)
    
    train_loader, val_loader = prepare_dataloaders(
        train_split, val_split, batch_size, max_seq_length
    )
    
    # Create model
    logger.info(f"Creating {model_type} model...")
    if model_type == "autoregressive":
        model = create_autoregressive_model(
            embed_dim=embed_dim,
            num_heads=num_heads,
            vocab_size=vocab_size,
            max_seq_length=max_seq_length,
        )
    elif model_type == "diffusion":
        model = create_diffusion_model(
            embed_dim=embed_dim,
            num_heads=num_heads,
            vocab_size=vocab_size,
            max_seq_length=max_seq_length,
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model = model.to(device)
    logger.info(f"Model created with {sum(p.numel() for p in model.parameters()):,} parameters")
    
    # Compile model if using torch.compile (CPU-optimized)
    use_compile = True  # Always use compile for CPU as per task requirement
    if use_compile and device.type == "cpu":
        logger.info("Compiling model with torch.compile...")
        try:
            model = torch.compile(model, mode="reduce-overhead")
            logger.info("Model compiled successfully")
        except Exception as e:
            logger.warning(f"Failed to compile model: {e}. Continuing without compilation.")
            use_compile = False
    
    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    
    # Training history
    history = {
        "epoch": [],
        "train_loss": [],
        "val_loss": [],
        "gap": [],
        "time_per_epoch": [],
        "ram_per_epoch": [],
    }
    
    # Training loop
    logger.info("Starting training...")
    start_total_time = time.time()
    
    for epoch in range(1, num_epochs + 1):
        epoch_start = time.time()
        
        # Train
        train_loss = train_epoch(
            model, train_loader, optimizer, device, epoch, use_compile
        )
        
        # Validate
        val_loss = evaluate_epoch(model, val_loader, device, use_compile)
        
        # Calculate generalization gap
        gap = val_loss - train_loss
        
        # Record metrics
        epoch_time = time.time() - epoch_start
        ram_usage = get_ram_usage_gb()
        
        history["epoch"].append(epoch)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["gap"].append(gap)
        history["time_per_epoch"].append(epoch_time)
        history["ram_per_epoch"].append(ram_usage)
        
        logger.info(
            f"Epoch {epoch}/{num_epochs} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Gap: {gap:.4f} | "
            f"Time: {epoch_time:.2f}s | "
            f"RAM: {ram_usage:.2f}GB"
        )
        
        # Early stopping check (optional)
        if val_loss > 10.0:  # Sanity check
            logger.warning("Validation loss too high, stopping early")
            break
    
    total_time = time.time() - start_total_time
    logger.info(f"Training completed in {total_time:.2f}s")
    
    # Save history
    if output_dir:
        output_path = Path(output_dir) / f"{model_type}_training_history.json"
        import json
        with open(output_path, "w") as f:
            json.dump(history, f, indent=2)
        logger.info(f"Training history saved to {output_path}")
    
    return {
        "model_type": model_type,
        "history": history,
        "total_time": total_time,
        "final_train_loss": history["train_loss"][-1] if history["train_loss"] else None,
        "final_val_loss": history["val_loss"][-1] if history["val_loss"] else None,
        "final_gap": history["gap"][-1] if history["gap"] else None,
    }


def main():
    """Main entry point for training."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train a model on the micro-corpus")
    parser.add_argument(
        "--model-type",
        type=str,
        choices=["autoregressive", "diffusion"],
        required=True,
        help="Type of model to train",
    )
    parser.add_argument(
        "--train-data",
        type=str,
        default=str(Path(get_processed_dir()) / "train.jsonl"),
        help="Path to training data JSONL",
    )
    parser.add_argument(
        "--val-data",
        type=str,
        default=str(Path(get_processed_dir()) / "val.jsonl"),
        help="Path to validation data JSONL",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(get_artifacts_dir()),
        help="Directory to save training outputs",
    )
    
    args = parser.parse_args()
    
    # Run training
    results = train_loop(
        model_type=args.model_type,
        train_data_path=args.train_data,
        val_data_path=args.val_data,
        output_dir=args.output_dir,
    )
    
    logger.info(f"Training results: {results}")
    return results


if __name__ == "__main__":
    main()