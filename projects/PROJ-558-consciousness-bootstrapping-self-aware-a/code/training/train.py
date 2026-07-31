import os
import sys
import json
import hashlib
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import LlamaConfig, LlamaForCausalLM

# Import project modules using the exact API surface provided
from utils.logging import get_logger, RecursionDepthError, ConfigurationError
from utils.config import get_config, validate_config
from models.checkpoint import ModelCheckpoint
from models.recursive_llama import RecursiveLlamaWrapper, create_recursive_model
from evaluation.loss_functions import compute_joint_loss

logger = get_logger(__name__)

# --- Configuration Constants ---
MAX_RECURSION_DEPTH = 2
MAX_MEMORY_MB = 7000  # 7GB limit as per constraints

class PileDataset(Dataset):
    """
    Minimal dataset wrapper for the truncated Pile data.
    Expects pre-processed JSON files under data/raw/.
    """
    def __init__(self, data_path: str, tokenizer: Any, max_length: int = 512):
        super().__init__()
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []

        logger.info(f"Loading dataset from {data_path}")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset file not found: {data_path}")

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.data.append(json.loads(line))
        logger.info(f"Loaded {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # Assuming 'text' key exists in the JSON
        text = item.get('text', '')
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length'
        )
        return {
            'input_ids': torch.tensor(encoding['input_ids'], dtype=torch.long),
            'attention_mask': torch.tensor(encoding['attention_mask'], dtype=torch.long),
            'labels': torch.tensor(encoding['input_ids'], dtype=torch.long)
        }

def validate_recursion_depth(depth: int, model_name: str = "RecursiveLlama") -> None:
    """
    Validates that the recursion depth does not exceed the hard limit (2).
    Implements the hard-fail requirement: if depth > 2, log error and raise RecursionDepthError.
    MUST NOT automatically reduce depth.
    """
    if depth > MAX_RECURSION_DEPTH:
        error_msg = (
            f"CRITICAL: Recursion depth {depth} exceeds maximum allowed depth {MAX_RECURSION_DEPTH} "
            f"for model '{model_name}'. This violates the safety constraint. "
            f"Exiting to prevent unbounded resource consumption."
        )
        logger.error(error_msg)
        # Raise a specific exception to ensure the process exits with non-zero code
        raise RecursionDepthError(error_msg)
    logger.info(f"Recursion depth validation passed: {depth} <= {MAX_RECURSION_DEPTH}")

def check_memory_usage() -> None:
    """
    Checks current memory usage. If it exceeds the limit, raises an error.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # maxrss is in KB on Linux/macOS
        current_mb = usage.ru_maxrss / 1024
        if current_mb > MAX_MEMORY_MB:
            error_msg = (
                f"CRITICAL: Memory usage {current_mb:.2f}MB exceeds limit {MAX_MEMORY_MB}MB. "
                f"Training aborted to prevent OOM crash."
            )
            logger.error(error_msg)
            raise MemoryError(error_msg)
    except ImportError:
        logger.warning("resource module not available, skipping memory check.")

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int,
    recursion_depth: int
) -> float:
    """
    Trains the model for one epoch.
    Includes OOM detection and recursion depth validation.
    """
    model.train()
    total_loss = 0.0
    batch_count = 0

    # Validate recursion depth at the start of training (Hard Fail)
    try:
        validate_recursion_depth(recursion_depth)
    except RecursionDepthError as e:
        # Re-raise to ensure the script exits
        raise e

    logger.info(f"Starting Epoch {epoch+1} with recursion depth {recursion_depth}")

    for batch_idx, batch in enumerate(dataloader):
        try:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            optimizer.zero_grad()

            # Forward pass
            # Note: In a real scenario, we'd pass recursion_depth to the forward method
            # if the model supports dynamic depth, or it's fixed at init.
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
            batch_count += 1

            if batch_idx % 10 == 0:
                logger.info(f"Epoch {epoch+1}, Batch {batch_idx}, Loss: {loss.item():.4f}")

            # Check memory periodically
            if batch_idx % 50 == 0:
                check_memory_usage()

        except torch.cuda.OutOfMemoryError:
            logger.critical(f"OOM Error at batch {batch_idx}. Aborting training.")
            raise
        except MemoryError as e:
            logger.critical(str(e))
            raise
        except Exception as e:
            logger.error(f"Unexpected error during batch {batch_idx}: {str(e)}")
            raise

    avg_loss = total_loss / batch_count if batch_count > 0 else 0.0
    return avg_loss

def save_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    loss: float,
    path: str
) -> ModelCheckpoint:
    """Saves the model state to a checkpoint file."""
    checkpoint_dir = os.path.dirname(path)
    os.makedirs(checkpoint_dir, exist_ok=True)

    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
    }, path)

    # Create metadata
    checkpoint = ModelCheckpoint(
        path=path,
        epoch=epoch,
        loss=loss,
        timestamp=datetime.now().isoformat(),
        model_type="RecursiveLlama"
    )
    checkpoint.save_metadata()
    logger.info(f"Checkpoint saved to {path}")
    return checkpoint

def run_training(
    config: Dict[str, Any],
    dataset_path: str,
    output_dir: str,
    model_type: str = "recursive"
) -> List[ModelCheckpoint]:
    """
    Main training loop.
    Orchestrates dataset loading, model creation, and training epochs.
    """
    logger.info("Starting training run...")
    
    # Validate config
    validate_config(config)
    
    # Determine device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load Tokenizer (Mocking for now as per API surface constraints, 
    # assuming a standard Llama tokenizer is available or configured)
    # In a full implementation, this would load from a path in config
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    except Exception:
        logger.warning("Could not load tokenizer, using a placeholder strategy.")
        # Fallback for testing if real model not available
        tokenizer = None

    # Load Dataset
    train_dataset = PileDataset(data_path=dataset_path, tokenizer=tokenizer)
    train_loader = DataLoader(
        train_dataset, 
        batch_size=config.get('batch_size', 4), 
        shuffle=True
    )

    # Create Model
    logger.info(f"Creating {model_type} model...")
    if model_type == "recursive":
        # Validate depth before model creation
        depth = config.get('recursion_depth', 1)
        validate_recursion_depth(depth)
        model = create_recursive_model(config)
    else:
        # Baseline model (non-recursive)
        config_val = LlamaConfig.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        model = LlamaForCausalLM(config_val)

    model = model.to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.get('learning_rate', 1e-4))

    checkpoints = []
    epochs = config.get('epochs', 1)

    try:
        for epoch in range(epochs):
            logger.info(f"--- Epoch {epoch+1}/{epochs} ---")
            epoch_loss = train_epoch(
                model, train_loader, optimizer, device, epoch, 
                recursion_depth=config.get('recursion_depth', 1)
            )
            
            logger.info(f"Epoch {epoch+1} completed. Average Loss: {epoch_loss:.4f}")
            
            # Save checkpoint
            ckpt_path = os.path.join(output_dir, f"checkpoint_epoch_{epoch+1}.pt")
            ckpt = save_checkpoint(model, optimizer, epoch, epoch_loss, ckpt_path)
            checkpoints.append(ckpt)

    except RecursionDepthError as e:
        logger.critical(f"Training aborted due to recursion depth violation: {e}")
        sys.exit(1)
    except MemoryError as e:
        logger.critical(f"Training aborted due to memory limit: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed with unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

    logger.info("Training completed successfully.")
    return checkpoints

def main():
    """Entry point for the training script."""
    parser = argparse.ArgumentParser(description="Train Recursive Self-Aware Model")
    parser.add_argument("--config", type=str, default="code/utils/config.py", help="Path to config")
    parser.add_argument("--dataset", type=str, default="data/raw/pile_arxiv_truncated.json", help="Dataset path")
    parser.add_argument("--output", type=str, default="artifacts/checkpoints", help="Output directory")
    parser.add_argument("--model-type", type=str, default="recursive", choices=["recursive", "baseline"])
    parser.add_argument("--recursion-depth", type=int, default=2, help="Recursion depth to validate")

    args = parser.parse_args()

    # Load config (simplified for this task)
    config = {
        'batch_size': 4,
        'learning_rate': 1e-4,
        'epochs': 1,
        'recursion_depth': args.recursion_depth,
        'token_limit': 100000
    }

    # Explicitly validate the recursion depth argument passed via CLI
    # This ensures the hard-fail requirement is met even before training starts
    try:
        validate_recursion_depth(args.recursion_depth)
    except RecursionDepthError:
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    run_training(config, args.dataset, args.output, args.model_type)

if __name__ == "__main__":
    main()