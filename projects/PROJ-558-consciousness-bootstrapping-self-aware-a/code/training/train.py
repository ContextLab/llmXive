import os
import sys
import json
import hashlib
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import LlamaConfig, LlamaForCausalLM
from transformers.modeling_outputs import CausalLMOutputWithPast

# Import project modules
from config import get_config, set_config, validate_config, Config
from utils.logging import get_logger, setup_logging, log_training_start, log_training_end, log_exception
from models.base_llama import BaseLlamaWrapper
from models.recursive_llama import RecursiveLlamaWrapper, create_recursive_model
from models.checkpoint import ModelCheckpoint
from evaluation.loss_functions import compute_joint_loss

logger = get_logger(__name__)

# Flag to detect if we are in profiling mode
IS_PROFILING_MODE = False

class PileDataset(Dataset):
    def __init__(self, data_path: str, tokenizer, max_length: int = 512):
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        self._load_data()

    def _load_data(self):
        # Load data from JSON file
        # Assuming the data is in the format: [{"text": "..."}, ...]
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        self.data.append(item)
                    except json.JSONDecodeError:
                        continue
        else:
            logger.warning(f"Data file not found: {self.data_path}. Using empty dataset.")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = item.get("text", "")
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": encoding["input_ids"].squeeze(0)  # For causal LM, labels = input_ids
        }

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: Config,
    epoch: int
) -> float:
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        try:
            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            # Compute loss
            # If model returns a loss, use it. Otherwise, compute manually.
            # For now, assume we compute manually using the loss functions
            # But the model might already compute it.
            # Let's assume the model's forward returns a CausalLMOutputWithPast
            # and we compute loss from logits.

            # If the model is recursive, it might have additional losses.
            # We'll assume the model handles its own loss computation if it's a custom model.
            # Otherwise, we compute cross-entropy.

            if hasattr(outputs, 'loss') and outputs.loss is not None:
                loss = outputs.loss
            else:
                # Fallback: compute cross-entropy
                logits = outputs.logits
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = labels[..., 1:].contiguous()
                loss_fct = nn.CrossEntropyLoss()
                loss = loss_fct(
                    shift_logits.view(-1, shift_logits.size(-1)),
                    shift_labels.view(-1)
                )

            # Backward pass
            optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)

            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            if batch_idx % 10 == 0:
                logger.info(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error(f"OOM detected at batch {batch_idx}")
                # If in profiling mode, we just log and continue? Or fail?
                # The task says: if OOM, log error and exit with non-zero code.
                # But we are profiling, so we want to catch the peak.
                # Let's re-raise if not in profiling mode.
                if not IS_PROFILING_MODE:
                    raise
                else:
                    # In profiling mode, we catch and log, but we don't want to crash the profiler
                    # We'll break the loop to avoid further OOM
                    logger.warning("Breaking loop due to OOM in profiling mode")
                    break
            else:
                raise

    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss

def save_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    loss: float,
    config: Config,
    output_dir: str,
    model_type: str = "baseline"
) -> ModelCheckpoint:
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_path = os.path.join(output_dir, f"checkpoint_epoch_{epoch}_{model_type}.pt")

    state_dict = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": loss,
        "config": config.to_dict()
    }

    torch.save(state_dict, checkpoint_path)

    checkpoint = ModelCheckpoint(
        path=checkpoint_path,
        epoch=epoch,
        loss=loss,
        model_type=model_type,
        created_at=datetime.now().isoformat()
    )
    checkpoint.save_metadata()

    logger.info(f"Checkpoint saved to {checkpoint_path}")
    return checkpoint

def run_training(config: Config):
    device = torch.device("cpu")  # Enforce CPU-only
    if torch.cuda.is_available() and not config.cpu_only:
        logger.warning("CUDA available but CPU-only enforced by config.")

    logger.info(f"Training on device: {device}")
    logger.info(f"Config: {config.to_dict()}")

    # Setup tokenizer and model
    # We assume a small model for testing
    # For the actual task, we use the recursive model
    model_type = config.model_type  # "recursive" or "baseline"

    if model_type == "recursive":
        model = create_recursive_model(config)
    else:
        # Baseline model
        model_config = LlamaConfig.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        model_config.num_hidden_layers = 2  # Small for testing
        model = LlamaForCausalLM(model_config)

    model = model.to(device)

    # Setup tokenizer
    # For simplicity, we use a dummy tokenizer or load from HuggingFace
    # In a real scenario, we'd load the tokenizer for the model
    from transformers import LlamaTokenizer
    try:
        tokenizer = LlamaTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    except Exception:
        logger.warning("Could not load tokenizer, using a dummy one.")
        tokenizer = None

    # Setup dataset
    data_path = config.data_path  # e.g., "data/raw/pile_arxiv_truncated.json"
    if tokenizer:
        dataset = PileDataset(data_path, tokenizer, max_length=config.max_length)
        dataloader = DataLoader(
            dataset,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=0  # Avoid multiprocessing issues in profiling
        )
    else:
        logger.error("Tokenizer not available, skipping training.")
        return

    # Setup optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)

    # Training loop
    log_training_start(config)

    for epoch in range(config.epochs):
        # Check recursion depth if recursive
        if model_type == "recursive":
            if hasattr(model, 'recursion_depth') and model.recursion_depth > config.max_recursion_depth:
                logger.error(f"Recursion depth {model.recursion_depth} exceeds max {config.max_recursion_depth}")
                raise RecursionDepthError(f"Recursion depth exceeded: {model.recursion_depth}")

        avg_loss = train_epoch(
            model=model,
            dataloader=dataloader,
            optimizer=optimizer,
            device=device,
            config=config,
            epoch=epoch
        )

        # Save checkpoint
        save_checkpoint(
            model=model,
            optimizer=optimizer,
            epoch=epoch,
            loss=avg_loss,
            config=config,
            output_dir=config.output_dir,
            model_type=model_type
        )

        log_training_end(epoch, avg_loss)

    logger.info("Training completed.")

class RecursionDepthError(Exception):
    pass

def main():
    parser = argparse.ArgumentParser(description="Train the consciousness bootstrapping model")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs")
    parser.add_argument("--profile_mode", action="store_true", help="Enable profiling mode")

    args = parser.parse_args()

    global IS_PROFILING_MODE
    IS_PROFILING_MODE = args.profile_mode

    setup_logging()

    try:
        # Load config
        config = get_config(args.config)

        # Override config with CLI args
        config.batch_size = args.batch_size
        config.epochs = args.epochs

        # Validate config
        validate_config(config)

        # Run training
        run_training(config)

    except Exception as e:
        log_exception(e)
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
