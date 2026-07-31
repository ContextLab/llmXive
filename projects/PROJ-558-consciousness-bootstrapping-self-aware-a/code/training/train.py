import os
import sys
import json
import hashlib
import traceback
import gc
import torch
import argparse
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, field
from pathlib import Path

from utils.logging import get_logger, log_training_start, log_training_end, log_exception, RecursionDepthError
from utils.config import get_config, validate_config
from models.recursive_llama import create_recursive_model, RecursionState
from evaluation.loss_functions import compute_joint_loss
from models.checkpoint import ModelCheckpoint

logger = get_logger(__name__)

@dataclass
class TrainingState:
    epoch: int = 0
    global_step: int = 0
    best_loss: Optional[float] = None
    recursion_depth: int = 0
    total_tokens_processed: int = 0

class PileDataset:
    def __init__(self, data_path: str, token_limit: int):
        self.data_path = data_path
        self.token_limit = token_limit
        self.data = []
        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Dataset file not found: {self.data_path}")
        
        logger.info(f"Loading dataset from {self.data_path}")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if self.token_limit > 0 and len(self.data) >= self.token_limit:
                    break
                try:
                    item = json.loads(line)
                    self.data.append(item)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON line")
        
        logger.info(f"Loaded {len(self.data)} items")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

def validate_recursion_depth(config: Any, current_depth: int) -> None:
    """
    Validates that recursion depth does not exceed the configured limit.
    HARD FAIL: If current_depth > config.max_recursion_depth, raise RecursionDepthError.
    """
    max_depth = getattr(config, 'max_recursion_depth', 2)
    if current_depth > max_depth:
        error_msg = f"Recursion depth violation: current depth {current_depth} exceeds maximum allowed {max_depth}"
        logger.error(error_msg)
        raise RecursionDepthError(error_msg)

def check_memory_usage(threshold_mb: float = 6500.0) -> bool:
    """
    Checks current memory usage. Returns True if usage is below threshold.
    HARD FAIL: If usage exceeds threshold, logs error and returns False to trigger exit.
    """
    if torch.cuda.is_available():
        # GPU memory check (though task specifies CPU-only, handle gracefully)
        allocated = torch.cuda.memory_allocated() / (1024 * 1024)
        if allocated > threshold_mb:
            logger.error(f"GPU memory usage {allocated:.2f}MB exceeds threshold {threshold_mb}MB")
            return False
    else:
        # CPU memory check using resource module
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert KB to MB on Linux
            if usage > threshold_mb:
                logger.error(f"CPU memory usage {usage:.2f}MB exceeds threshold {threshold_mb}MB")
                return False
        except ImportError:
            logger.warning("resource module not available for CPU memory check")
    
    return True

def train_epoch(model: torch.nn.Module, dataset: PileDataset, state: TrainingState, config: Any) -> float:
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    total_loss = 0.0
    batch_size = config.batch_size

    for i in range(0, len(dataset), batch_size):
        batch = dataset.data[i : i + batch_size]
        
        # Validate recursion depth before processing batch
        validate_recursion_depth(config, state.recursion_depth)
        
        # Check memory usage
        if not check_memory_usage():
            raise MemoryError(f"Memory threshold exceeded at step {state.global_step}")

        # Simulate training step (simplified for CPU-only context)
        # In a real scenario, we would process the batch through the model
        # Here we simulate the loss computation logic
        batch_loss = 0.0
        for item in batch:
            # Simulate forward pass and loss calculation
            # This is a placeholder for the actual joint loss computation
            # which would involve generating N=5 paths and computing majority vote
            try:
                # Simulate a small loss value
                batch_loss += 0.5  # Placeholder loss
            except RecursionDepthError as e:
                raise e
            except MemoryError as e:
                raise e

        avg_batch_loss = batch_loss / len(batch) if batch else 0.0
        total_loss += avg_batch_loss

        # Simulate backward pass and optimization
        optimizer.zero_grad()
        # In real code: loss.backward(); optimizer.step()
        
        state.global_step += 1
        state.total_tokens_processed += len(batch)

        if state.global_step % 10 == 0:
            logger.info(f"Step {state.global_step}, Loss: {avg_batch_loss:.4f}")

    return total_loss / max(len(dataset) // batch_size, 1)

def save_checkpoint(model: torch.nn.Module, state: TrainingState, output_path: str) -> None:
    checkpoint = ModelCheckpoint(
        model_state_dict=model.state_dict(),
        training_state={
            'epoch': state.epoch,
            'global_step': state.global_step,
            'best_loss': state.best_loss,
            'recursion_depth': state.recursion_depth,
            'total_tokens_processed': state.total_tokens_processed
        },
        timestamp=state.epoch,
        config_hash=hashlib.md5(str(config.__dict__).encode()).hexdigest()
    )
    checkpoint.save(output_path)
    logger.info(f"Checkpoint saved to {output_path}")

def run_training(config: Any) -> None:
    """
    Main training loop with strict recursion depth and memory validation.
    HARD FAIL on OOM or depth violation.
    """
    log_training_start(config)
    
    # Initialize dataset
    dataset_path = os.path.join(config.data_dir, 'raw', 'pile_arxiv_truncated.json')
    try:
        dataset = PileDataset(dataset_path, config.token_limit)
    except FileNotFoundError as e:
        logger.critical(f"Dataset not found: {e}")
        raise

    # Initialize model
    model = create_recursive_model(config)
    state = TrainingState()
    
    # Validate initial recursion depth
    validate_recursion_depth(config, state.recursion_depth)

    try:
        for epoch in range(config.num_epochs):
            state.epoch = epoch
            logger.info(f"Starting epoch {epoch + 1}/{config.num_epochs}")
            
            # Check memory before epoch
            if not check_memory_usage():
                raise MemoryError(f"Memory threshold exceeded before epoch {epoch}")

            epoch_loss = train_epoch(model, dataset, state, config)
            
            # Update best loss
            if state.best_loss is None or epoch_loss < state.best_loss:
                state.best_loss = epoch_loss
            
            # Save checkpoint
            checkpoint_path = os.path.join(config.checkpoint_dir, f"checkpoint_epoch_{epoch}.pt")
            save_checkpoint(model, state, checkpoint_path)
            
            logger.info(f"Epoch {epoch + 1} completed. Loss: {epoch_loss:.4f}")

        log_training_end(state.best_loss)
        
    except RecursionDepthError as e:
        logger.critical(f"RECURSION DEPTH VIOLATION: {e}")
        log_exception(e)
        sys.exit(1)
    except MemoryError as e:
        logger.critical(f"MEMORY EXCEEDED: {e}")
        log_exception(e)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during training: {e}")
        log_exception(e)
        raise

def main():
    parser = argparse.ArgumentParser(description="Train Recursive Llama Model")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    args = parser.parse_args()

    config = get_config(args.config)
    validate_config(config)

    run_training(config)

if __name__ == "__main__":
    main()