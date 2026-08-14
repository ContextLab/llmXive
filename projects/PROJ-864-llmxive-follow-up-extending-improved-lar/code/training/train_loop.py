import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torch.cuda.amp import autocast, GradScaler

# Import from project API surface
from utils.logging import get_logger, info, error, warning
from utils.monitor import get_ram_usage_gb, check_ram_threshold
from utils.config import get_config, get_device, get_learning_rate, get_batch_size, get_num_epochs, get_max_seq_length, get_vocab_size
from models.config import get_embed_dim, get_num_heads, get_num_layers
from training.callbacks import create_logging_callback, TrainingMetrics
from training.helpers import ensure_training_dirs

logger = get_logger(__name__)

class TextDataset(Dataset):
    """
    Dataset for tokenized text corpus.
    Expects a JSONL file with 'input_ids' lists.
    """
    def __init__(self, file_path: str, max_length: int = 512):
        super().__init__()
        self.file_path = file_path
        self.max_length = max_length
        self.data = []
        
        logger.info(f"Loading dataset from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                import json
                try:
                    item = json.loads(line)
                    if 'input_ids' in item:
                        # Truncate if necessary
                        ids = item['input_ids'][:max_length]
                        if len(ids) > 1: # Need at least 2 for loss calculation (input + target)
                            self.data.append(torch.tensor(ids, dtype=torch.long))
                except json.JSONDecodeError:
                    continue
        
        logger.info(f"Loaded {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

def prepare_dataloaders(train_path: str, test_path: str, batch_size: int) -> Tuple[DataLoader, DataLoader]:
    """
    Prepare train and test dataloaders.
    """
    max_seq_len = get_max_seq_length()
    train_dataset = TextDataset(train_path, max_length=max_seq_len)
    test_dataset = TextDataset(test_path, max_length=max_seq_len)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    return train_loader, test_loader

def train_epoch(
    model: nn.Module, 
    dataloader: DataLoader, 
    optimizer: optim.Optimizer, 
    scaler: GradScaler, 
    device: torch.device, 
    epoch: int,
    max_steps: Optional[int] = None
) -> float:
    """
    Train for one epoch.
    Returns average training loss.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    # Compile model if not already compiled and we are on the first epoch
    if not hasattr(model, '_is_compiled') or not model._is_compiled:
        try:
            model = torch.compile(model)
            model._is_compiled = True
            logger.info("Model compiled with torch.compile")
        except Exception as e:
            warning(f"torch.compile failed: {e}. Running in eager mode.")
            model._is_compiled = False

    for batch_idx, batch in enumerate(dataloader):
        if max_steps and batch_idx >= max_steps:
            break

        batch = batch.to(device)
        # Shift for causal LM: input is batch[:, :-1], target is batch[:, 1:]
        if batch.size(1) < 2:
            continue
        
        input_ids = batch[:, :-1]
        labels = batch[:, 1:]

        optimizer.zero_grad()

        # Mixed precision training
        with autocast(device_type='cpu', dtype=torch.float16):
            outputs = model(input_ids=input_ids)
            # Handle both autoregressive and diffusion outputs
            if isinstance(outputs, dict):
                logits = outputs.get('logits', outputs.get('predictions'))
            else:
                logits = outputs
            
            # Ensure logits and labels match
            if logits is not None:
                # Flatten for loss calculation
                loss_fct = nn.CrossEntropyLoss()
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = labels.contiguous()
                loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            else:
                # Fallback if model returns loss directly (unlikely for our custom models)
                loss = outputs

        # Backward pass with mixed precision
        if scaler is not None:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        total_loss += loss.item()
        num_batches += 1

        # Log progress
        if batch_idx % 10 == 0:
            current_ram = get_ram_usage_gb()
            if current_ram > 6.0:
                warning(f"Epoch {epoch}, Batch {batch_idx}: High RAM usage detected ({current_ram:.2f} GB)")

    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss

def evaluate_epoch(
    model: nn.Module, 
    dataloader: DataLoader, 
    device: torch.device
) -> float:
    """
    Evaluate model on validation set.
    Returns average validation loss.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for batch in dataloader:
            batch = batch.to(device)
            if batch.size(1) < 2:
                continue
            
            input_ids = batch[:, :-1]
            labels = batch[:, 1:]

            # Mixed precision for evaluation
            with autocast(device_type='cpu', dtype=torch.float16):
                outputs = model(input_ids=input_ids)
                if isinstance(outputs, dict):
                    logits = outputs.get('logits', outputs.get('predictions'))
                else:
                    logits = outputs
                
                if logits is not None:
                    loss_fct = nn.CrossEntropyLoss()
                    shift_logits = logits[..., :-1, :].contiguous()
                    shift_labels = labels.contiguous()
                    loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                else:
                    loss = torch.tensor(0.0)

            total_loss += loss.item()
            num_batches += 1

    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss

def train_loop(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    model_type: str,
    seed_id: int,
    num_epochs: int = 100,
    learning_rate: float = 1e-4,
    max_wall_time_seconds: int = 21600  # 6 hours
) -> List[Dict[str, Any]]:
    """
    Main training loop with mixed precision and resource monitoring.
    Returns list of epoch metrics.
    """
    device = get_device()
    logger.info(f"Starting training for {model_type} model (seed={seed_id}) on {device}")
    
    # Setup optimizer
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    
    # Setup GradScaler for mixed precision
    scaler = GradScaler() if device.type == 'cpu' else None 
    # Note: torch.cpu.amp is supported in recent PyTorch versions, but often less stable than CUDA.
    # We will attempt it if RAM > 6.0GB as per task requirement, otherwise eager mode.
    use_amp = False
    if get_ram_usage_gb() > 6.0:
        logger.info("Peak RAM > 6.0GB, enabling mixed precision (FP16) on CPU")
        use_amp = True
        scaler = GradScaler()
    else:
        logger.info("Peak RAM <= 6.0GB, running in FP32 (no mixed precision)")
        scaler = None

    # Setup callback
    callback = create_logging_callback(model_type, seed_id)
    start_time = time.time()
    
    metrics_log = []

    for epoch in range(num_epochs):
        epoch_start = time.time()
        
        # Check wall clock time
        elapsed = time.time() - start_time
        if elapsed > max_wall_time_seconds:
            warning(f"Wall clock time limit ({max_wall_time_seconds}s) reached. Stopping early.")
            break

        # Train
        train_loss = train_epoch(model, train_loader, optimizer, scaler, device, epoch)
        
        # Evaluate
        val_loss = evaluate_epoch(model, val_loader, device)
        
        # Calculate generalization gap
        gap = val_loss - train_loss
        
        # Resource snapshot
        current_ram = get_ram_usage_gb()
        epoch_time = time.time() - epoch_start
        
        # Create metrics dict
        metrics = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "gap": gap,
            "time": epoch_time,
            "ram_gb": current_ram,
            "seed_id": seed_id,
            "model_type": model_type,
            "status": "RUNNING"
        }
        
        metrics_log.append(metrics)
        
        # Callback
        callback.on_epoch_end(TrainingMetrics(**metrics))
        
        logger.info(f"Epoch {epoch+1}/{num_epochs}: Train={train_loss:.4f}, Val={val_loss:.4f}, Gap={gap:.4f}, RAM={current_ram:.2f}GB, Time={epoch_time:.2f}s")

    # Final status
    final_status = "COMPLETED" if len(metrics_log) == num_epochs else "TRUNCATED"
    for m in metrics_log:
        if m['epoch'] == len(metrics_log):
            m['status'] = final_status
    
    return metrics_log

def main():
    """
    Entry point for running the training loop directly.
    Usage: python -m training.train_loop --model_type autoregressive --seed 42
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run training loop")
    parser.add_argument('--model_type', type=str, default='autoregressive', choices=['autoregressive', 'diffusion'], help='Model architecture')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--train_data', type=str, default='data/processed/micro_corpus_train.jsonl', help='Path to training data')
    parser.add_argument('--val_data', type=str, default='data/processed/micro_corpus_test.jsonl', help='Path to validation data')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    args = parser.parse_args()

    # Ensure directories exist
    ensure_training_dirs()

    # Load config
    cfg = get_config()
    batch_size = get_batch_size()
    learning_rate = get_learning_rate()
    num_epochs = args.epochs

    # Import model creation functions dynamically based on type
    if args.model_type == 'autoregressive':
        from models.autoregressive import create_autoregressive_model
        model = create_autoregressive_model()
    elif args.model_type == 'diffusion':
        from models.diffusion import create_diffusion_model
        model = create_diffusion_model()
    else:
        raise ValueError(f"Unknown model type: {args.model_type}")

    device = get_device()
    model.to(device)

    # Prepare data
    train_loader, val_loader = prepare_dataloaders(args.train_data, args.val_data, batch_size)

    # Run training
    metrics = train_loop(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        model_type=args.model_type,
        seed_id=args.seed,
        num_epochs=num_epochs,
        learning_rate=learning_rate
    )

    logger.info(f"Training finished. Logged {len(metrics)} epochs.")
    
    # Save final metrics to a temporary file for verification if needed
    import json
    output_path = Path("data/artifacts") / f"train_loop_{args.model_type}_seed{args.seed}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics

if __name__ == "__main__":
    main()