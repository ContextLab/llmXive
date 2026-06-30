import os
import time
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import psutil

from src.data.dataset_loader import load_open_x_embodiment_single_platform
from src.data.preprocess_actions import ActionTokenizer, load_action_config, preprocess_actions
from src.models.vla_model import QwenVLActionModel
from src.utils.resource_monitor import ResourceMonitor, resource_monitor_context
from src.utils.logging_config import setup_logging, log_model_checkpoint
from src.models.entities import ModelCheckpoint

# Constants
RAM_THRESHOLD_GB = 6.5
WALL_TIME_LIMIT_SECONDS = 21600  # 6 hours
DEVICE = "cpu"
DEFAULT_BATCH_SIZE = 32
MIN_BATCH_SIZE = 1
EPOCHS = 1
OUTPUT_DIR = Path("data/checkpoints")
CHECKPOINT_PREFIX = "model_epoch"

logger = logging.getLogger(__name__)


def auto_adjust_batch_size(
    current_batch_size: int,
    resource_monitor: ResourceMonitor,
    min_batch_size: int = MIN_BATCH_SIZE,
) -> int:
    """
    Dynamically adjust batch size if RSS > RAM_THRESHOLD_GB.
    Returns the new batch size.
    """
    if current_batch_size <= min_batch_size:
        return min_batch_size

    current_rss_gb = resource_monitor.get_current_rss_gb()
    if current_rss_gb > RAM_THRESHOLD_GB:
        new_size = max(min_batch_size, current_batch_size // 2)
        logger.warning(
            f"RAM usage ({current_rss_gb:.2f} GB) exceeded {RAM_THRESHOLD_GB} GB. "
            f"Reducing batch size from {current_batch_size} to {new_size}."
        )
        return new_size
    return current_batch_size


def train_epoch(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    resource_monitor: ResourceMonitor,
    start_time: float,
    batch_size: int,
) -> Dict[str, float]:
    """
    Run a single training epoch with RAM and time monitoring.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    current_batch_size = batch_size

    for batch_idx, batch in enumerate(dataloader):
        # Check wall time limit
        elapsed = time.time() - start_time
        if elapsed >= WALL_TIME_LIMIT_SECONDS:
            logger.warning("TIMEOUT_WARNING: Wall time limit (6h) reached. Stopping training gracefully.")
            break

        # Auto-adjust batch size if needed
        current_batch_size = auto_adjust_batch_size(current_batch_size, resource_monitor)

        # Prepare batch
        inputs = batch["inputs"]
        targets = batch["targets"]

        if inputs.shape[0] != current_batch_size:
            # Slice if the loader returned a different size (e.g., last batch or downsampled)
            inputs = inputs[:current_batch_size]
            targets = targets[:current_batch_size]

        inputs = inputs.to(DEVICE)
        targets = targets.to(DEVICE)

        optimizer.zero_grad()

        try:
            outputs = model(inputs)
            loss = outputs.loss
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            # Log progress every 100 batches
            if (batch_idx + 1) % 100 == 0:
                avg_loss = total_loss / num_batches
                logger.info(
                    f"Epoch {epoch} | Batch {batch_idx + 1} | Loss: {avg_loss:.4f} | "
                    f"Batch Size: {current_batch_size} | RAM: {resource_monitor.get_current_rss_gb():.2f} GB"
                )

        except RuntimeError as e:
            logger.error(f"Runtime error during training (batch {batch_idx}): {e}")
            # Attempt recovery by reducing batch size
            current_batch_size = auto_adjust_batch_size(current_batch_size, resource_monitor)
            continue

    return {
        "avg_loss": total_loss / num_batches if num_batches > 0 else 0.0,
        "batches_completed": num_batches,
    }


def create_dataloader(
    df: pd.DataFrame,
    tokenizer: ActionTokenizer,
    batch_size: int,
    shuffle: bool = True,
) -> torch.utils.data.DataLoader:
    """
    Create a PyTorch DataLoader from the preprocessed DataFrame.
    """
    dataset = torch.utils.data.TensorDataset(
        torch.tensor(df["inputs"].tolist(), dtype=torch.float32),
        torch.tensor(df["targets"].tolist(), dtype=torch.float32),
    )
    return torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=shuffle
    )


def main(args: Optional[argparse.Namespace] = None):
    """
    Main training loop entry point.
    """
    # Setup logging
    setup_logging(level=logging.INFO)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load configuration and tokenizer
    config = load_action_config()
    tokenizer = ActionTokenizer(config)

    logger.info("Loading dataset...")
    # Load the single-platform dataset (franka) as per T012b
    df = load_open_x_embodiment_single_platform()

    logger.info("Preprocessing actions...")
    # Preprocess actions to token space
    processed_df = preprocess_actions(df, tokenizer)

    # Drop rows where preprocessing failed (NaN targets)
    processed_df = processed_df.dropna(subset=["targets"])
    logger.info(f"Dataset size after preprocessing: {len(processed_df)} samples")

    # Initialize model
    logger.info("Initializing Qwen-VL Action Model...")
    model = QwenVLActionModel()
    model.to(DEVICE)

    # Initialize optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    # Initialize resource monitor
    resource_monitor = ResourceMonitor()

    # Set number of threads for CPU training
    torch.set_num_threads(2)

    start_time = time.time()
    epoch_stats = []

    logger.info(f"Starting training on CPU. Limit: {WALL_TIME_LIMIT_SECONDS}s, RAM threshold: {RAM_THRESHOLD_GB}GB")

    # Training loop
    for epoch in range(1, EPOCHS + 1):
        logger.info(f"--- Starting Epoch {epoch} ---")

        # Create dataloader with initial batch size
        batch_size = args.batch_size if args and args.batch_size else DEFAULT_BATCH_SIZE
        dataloader = create_dataloader(processed_df, tokenizer, batch_size)

        stats = train_epoch(
            model=model,
            dataloader=dataloader,
            optimizer=optimizer,
            epoch=epoch,
            resource_monitor=resource_monitor,
            start_time=start_time,
            batch_size=batch_size,
        )

        epoch_stats.append(stats)

        # Save checkpoint
        checkpoint_path = OUTPUT_DIR / f"{CHECKPOINT_PREFIX}_{epoch}.pt"
        checkpoint_data = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "loss": stats["avg_loss"],
        }
        torch.save(checkpoint_data, checkpoint_path)

        # Log checkpoint
        checkpoint_entity = ModelCheckpoint(
            path=str(checkpoint_path),
            epoch=epoch,
            loss=stats["avg_loss"],
            timestamp=datetime.now().isoformat(),
            size_bytes=os.path.getsize(checkpoint_path),
        )
        log_model_checkpoint(checkpoint_entity)

        logger.info(f"Epoch {epoch} completed. Avg Loss: {stats['avg_loss']:.4f}")

        # Check final wall time
        elapsed = time.time() - start_time
        if elapsed >= WALL_TIME_LIMIT_SECONDS:
            logger.warning("TIMEOUT_WARNING: Wall time limit reached after final epoch.")
            break

    # Final summary
    total_time = time.time() - start_time
    peak_ram = resource_monitor.get_peak_rss_gb()
    logger.info(f"Training completed. Total time: {total_time:.2f}s, Peak RAM: {peak_ram:.2f}GB")

    return epoch_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Qwen-VL Action Model on CPU")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Initial batch size")
    parser.add_argument("--epochs", type=int, default=EPOCHS, help="Number of epochs")
    args = parser.parse_args()

    main(args)
