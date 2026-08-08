"""
run_experiment.py

Orchestrates training for multiple models (1 AR, 1 MDM) for a specified number of epochs
and generates training_logs.csv in the artifacts directory.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import torch

# Project imports matching the API surface
from utils.config import (
    get_config,
    get_num_epochs,
    get_learning_rate,
    get_batch_size,
    get_device,
    get_artifacts_dir,
    get_processed_dir,
    ConfigError,
)
from utils.logging import setup_logging, get_logger, info, error, warning, debug
from utils.monitor import get_ram_usage_gb, get_elapsed_time, get_resource_snapshot
from models.autoregressive import create_autoregressive_model
from models.diffusion import create_diffusion_model
from training.train_loop import prepare_dataloaders, train_epoch, evaluate_epoch
from training.callbacks import create_logging_callback, TrainingMetrics


def run_single_model_training(
    model_name: str,
    model_creator,
    num_epochs: int,
    log_callback,
    device: str,
    artifacts_dir: Path,
) -> List[Dict[str, Any]]:
    """
    Train a single model for num_epochs and return the logged metrics.
    """
    info(f"Starting training for model: {model_name}")

    # Create model
    try:
        model = model_creator()
        model = model.to(device)
        info(f"Model {model_name} created and moved to {device}")
    except Exception as e:
        error(f"Failed to create model {model_name}: {e}")
        raise

    # Prepare data loaders
    try:
        train_loader, val_loader = prepare_dataloaders()
        info(f"Data loaders prepared for {model_name}")
    except Exception as e:
        error(f"Failed to prepare data loaders for {model_name}: {e}")
        raise

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=get_learning_rate(),
        weight_decay=0.01,
    )

    # Training loop
    epoch_logs = []
    start_time = time.time()

    for epoch in range(1, num_epochs + 1):
        epoch_start = time.time()

        # Train one epoch
        train_loss = train_epoch(
            model, train_loader, optimizer, device, epoch
        )

        # Evaluate one epoch
        val_loss = evaluate_epoch(model, val_loader, device)

        # Callback logging
        metrics = TrainingMetrics(
            epoch=epoch,
            model_name=model_name,
            train_loss=train_loss,
            val_loss=val_loss,
            gap=val_loss - train_loss,
            ram_gb=get_ram_usage_gb(),
            elapsed_time=get_elapsed_time(start_time),
            epoch_time=time.time() - epoch_start,
        )

        log_callback.on_epoch_end(metrics)
        epoch_logs.append(metrics.to_dict())

        info(
            f"Epoch {epoch}/{num_epochs} [{model_name}] - "
            f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
            f"Gap: {metrics.gap:.4f}, RAM: {metrics.ram_gb:.2f} GB"
        )

        # Optional: early stop if loss explodes (safety)
        if train_loss > 100.0:
            warning(f"Loss exploded at epoch {epoch} for {model_name}, stopping early.")
            break

    total_time = time.time() - start_time
    info(f"Training completed for {model_name} in {total_time:.2f} seconds")

    return epoch_logs


def save_logs_to_csv(all_logs: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save all training logs to a single CSV file.
    """
    if not all_logs:
        warning("No logs to save.")
        return

    fieldnames = list(all_logs[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_logs)

    info(f"Training logs saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate training for AR and Diffusion models."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override number of epochs (default from config).",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["ar", "mdm"],
        choices=["ar", "mdm"],
        help="Which models to train (ar, mdm).",
    )
    args = parser.parse_args()

    # Setup
    setup_logging()
    logger = get_logger(__name__)

    try:
        config = get_config()
    except ConfigError as e:
        error(f"Configuration error: {e}")
        sys.exit(1)

    num_epochs = args.epochs if args.epochs else get_num_epochs()
    device = get_device()
    artifacts_dir = get_artifacts_dir()
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    info(f"Starting experiment: {num_epochs} epochs, models={args.models}, device={device}")

    all_logs: List[Dict[str, Any]] = []
    callback = create_logging_callback()

    model_creators = {
        "ar": lambda: create_autoregressive_model(),
        "mdm": lambda: create_diffusion_model(),
    }

    for model_key in args.models:
        model_name = model_key.upper()
        creator = model_creators[model_key]

        logs = run_single_model_training(
            model_name=model_name,
            model_creator=creator,
            num_epochs=num_epochs,
            log_callback=callback,
            device=device,
            artifacts_dir=artifacts_dir,
        )
        all_logs.extend(logs)

    # Write combined logs to CSV
    output_path = artifacts_dir / "training_logs.csv"
    save_logs_to_csv(all_logs, output_path)

    info("Experiment completed successfully.")


if __name__ == "__main__":
    main()