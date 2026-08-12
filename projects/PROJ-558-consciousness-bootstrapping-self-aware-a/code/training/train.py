import os
import sys
import json
import hashlib
import traceback
import gc
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
import argparse
import time

from utils.logging import get_logger, log_training_start, log_training_end, log_exception, ConfigurationError, RecursionDepthError
from utils.memory_profiler import get_current_memory_mb, get_peak_memory_mb
from config import get_config, validate_config
from models.base_llama import BaseLlamaWrapper
from models.recursive_llama import RecursiveLlamaWrapper, create_recursive_model, RecursionState
from evaluation.loss_functions import compute_joint_loss, compute_self_consistency_loss
from models.checkpoint import ModelCheckpoint

logger = get_logger(__name__)

# Constants for memory safety
MAX_MEMORY_MB = 7000  # 7GB limit as per Constitution Principle VII
RECURSION_DEPTH_LIMIT = 2

@dataclass
class TrainingState:
    epoch: int = 0
    step: int = 0
    loss_history: List[float] = field(default_factory=list)
    best_loss: Optional[float] = None
    recursion_depth: int = 0
    is_converged: bool = False

class PileDataset(torch.utils.data.Dataset):
    def __init__(self, data_path: str, tokenizer: Any, max_length: int = 512):
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        self._load_data()

    def _load_data(self):
        logger.info(f"Loading dataset from {self.data_path}")
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.data.append(json.loads(line))
        except FileNotFoundError:
            raise ConfigurationError(f"Dataset file not found: {self.data_path}")
        logger.info(f"Loaded {len(self.data)} items")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item.get('text', '')
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': encoding['input_ids'].squeeze(0)
        }

def validate_recursion_depth(depth: int) -> None:
    """
    Validates that the recursion depth does not exceed the hard limit.
    Raises RecursionDepthError if the limit is violated.
    """
    if depth > RECURSION_DEPTH_LIMIT:
        error_msg = f"Recursion depth {depth} exceeds maximum allowed limit of {RECURSION_DEPTH_LIMIT}. " \
                    f"Hard-fail triggered as per T014 requirements."
        logger.error(error_msg)
        raise RecursionDepthError(error_msg)

def check_memory_usage() -> bool:
    """
    Checks current memory usage against the limit.
    Returns True if within limits, False otherwise.
    """
    current_mb = get_current_memory_mb()
    logger.debug(f"Current memory usage: {current_mb:.2f} MB")
    if current_mb > MAX_MEMORY_MB:
        error_msg = f"Memory usage {current_mb:.2f} MB exceeds limit of {MAX_MEMORY_MB} MB. " \
                    f"Hard-fail triggered as per T014 requirements."
        logger.error(error_msg)
        return False
    return True

def train_epoch(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: Any
) -> float:
    """
    Trains the model for one epoch.
    Includes memory and recursion depth checks.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch_idx, batch in enumerate(dataloader):
        # Check memory before processing batch
        if not check_memory_usage():
            raise MemoryError("Memory limit exceeded during training.")

        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        optimizer.zero_grad()

        try:
            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss

            # Backward pass
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            if batch_idx % 10 == 0:
                logger.info(f"Batch {batch_idx}, Loss: {loss.item():.4f}")

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.critical(f"OOM detected at batch {batch_idx}: {e}")
                # Explicitly trigger hard-fail for OOM
                raise MemoryError(f"Out of Memory error at batch {batch_idx}. Hard-fail triggered.") from e
            else:
                raise

        # Periodic memory check
        if batch_idx % 50 == 0:
            if not check_memory_usage():
                raise MemoryError("Memory limit exceeded during training.")

    return total_loss / num_batches if num_batches > 0 else 0.0

def save_checkpoint(
    model: nn.Module,
    state: TrainingState,
    config: Any,
    output_dir: Path
) -> Path:
    """
    Saves the model checkpoint.
    """
    checkpoint_path = output_dir / f"checkpoint_epoch_{state.epoch}.pt"
    torch.save({
        'epoch': state.epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': None, # Optimizer not saved for simplicity in this snippet
        'loss': state.best_loss,
        'config': config
    }, checkpoint_path)
    logger.info(f"Checkpoint saved to {checkpoint_path}")
    return checkpoint_path

def run_training(
    config: Any,
    dataset_path: str,
    output_dir: str
) -> TrainingState:
    """
    Main training loop.
    Implements T014: Hard-fail on recursion depth > 2 or OOM.
    """
    # Validate Recursion Depth immediately
    validate_recursion_depth(config.recursion_depth)
    logger.info(f"Recursion depth validated: {config.recursion_depth}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Initialize Model
    if config.recursion_depth > 0:
        logger.info("Initializing Recursive Llama Model")
        model = create_recursive_model(config)
    else:
        logger.info("Initializing Base Llama Model")
        model = BaseLlamaWrapper(config)

    model = model.to(device)
    model.train()

    # Initialize Dataset and DataLoader
    dataset = PileDataset(dataset_path, model.tokenizer, max_length=config.max_length)
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=0
    )

    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)

    state = TrainingState(recursion_depth=config.recursion_depth)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        for epoch in range(config.num_epochs):
            state.epoch = epoch
            logger.info(f"Starting Epoch {epoch + 1}/{config.num_epochs}")

            # Check memory before epoch
            if not check_memory_usage():
                raise MemoryError("Memory limit exceeded before epoch.")

            epoch_loss = train_epoch(model, dataloader, optimizer, device, config)
            state.loss_history.append(epoch_loss)
            state.best_loss = epoch_loss if state.best_loss is None else min(state.best_loss, epoch_loss)

            logger.info(f"Epoch {epoch + 1} completed. Loss: {epoch_loss:.4f}")

            # Save checkpoint
            save_checkpoint(model, state, config, output_path)

            # Check for convergence (simple placeholder logic)
            if len(state.loss_history) > 5:
                recent_avg = sum(state.loss_history[-5:]) / 5
                if recent_avg < 0.01:
                    state.is_converged = True
                    logger.info("Model converged. Stopping early.")
                    break

    except RecursionDepthError as e:
        logger.critical(f"Recursion Depth Violation: {e}")
        sys.exit(1)
    except MemoryError as e:
        logger.critical(f"Memory Error / OOM: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during training: {e}")
        log_exception(e)
        sys.exit(1)

    return state

def main():
    parser = argparse.ArgumentParser(description="Train Recursive Self-Aware Model")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()

    logger.info("Starting Training Process")
    log_training_start()

    try:
        config = get_config(args.config)
        validate_config(config)

        state = run_training(config, args.dataset, args.output)

        log_training_end(state.is_converged)
        logger.info("Training completed successfully.")

    except RecursionDepthError as e:
        logger.critical(f"Training failed due to Recursion Depth Violation: {e}")
        sys.exit(1)
    except MemoryError as e:
        logger.critical(f"Training failed due to Memory Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Training failed: {e}")
        log_exception(e)
        sys.exit(1)

if __name__ == "__main__":
    main()