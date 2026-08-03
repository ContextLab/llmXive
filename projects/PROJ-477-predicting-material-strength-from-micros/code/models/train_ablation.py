"""
Ablation study script: Train model WITHOUT data augmentation.

This script runs independently from code/train/trainer.py to ensure a distinct
artifact for ablation analysis. It replicates the training logic but disables
all augmentation transforms.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

# Import project utilities
from data.loader import MicrostructureDataset
from models.cnn import MaterialStrengthCNN, get_model
from utils.config import (
    get_code_dir,
    get_data_dir,
    get_processed_dir,
    get_results_dir,
    set_seed,
    get_seed,
)
from utils.logging_config import get_logger, log_operation

# Import augment module to distinguish between augmented and non-augmented transforms
from train.augment import get_train_augmentations, get_val_augmentations

# Configure logging for this specific script
def setup_ablation_logging() -> logging.Logger:
    """Setup logging for the ablation study."""
    logger = get_logger("ablation", log_file="results/ablation.log")
    logger.setLevel(logging.INFO)
    return logger

def create_no_augment_transforms() -> Tuple[transforms.Compose, transforms.Compose]:
    """
    Create transforms WITHOUT data augmentation.

    Returns:
        Tuple of (train_transform, val_transform) with no augmentation.
    """
    # Base normalization only, no random flips, rotations, or brightness
    train_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    val_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    return train_transform, val_transform

def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    logger: logging.Logger,
) -> Tuple[float, float]:
    """
    Train for one epoch without augmentation (data is already preprocessed).

    Returns:
        Tuple of (avg_loss, avg_mse)
    """
    model.train()
    total_loss = 0.0
    total_mse = 0.0
    num_samples = 0

    for batch_idx, (data, target) in enumerate(loader):
        data, target = data.to(device), target.to(device)

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        # Calculate MSE for this batch
        mse = torch.mean((output - target) ** 2).item()

        total_loss += loss.item() * data.size(0)
        total_mse += mse * data.size(0)
        num_samples += data.size(0)

        if batch_idx % 50 == 0:
            logger.info(f"Train Batch {batch_idx}: Loss={loss.item():.4f}")

    avg_loss = total_loss / num_samples
    avg_mse = total_mse / num_samples
    return avg_loss, avg_mse

def validate_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    logger: logging.Logger,
) -> Tuple[float, float]:
    """
    Validate for one epoch without augmentation.

    Returns:
        Tuple of (avg_loss, avg_mse)
    """
    model.eval()
    total_loss = 0.0
    total_mse = 0.0
    num_samples = 0

    with torch.no_grad():
        for data, target in loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            mse = torch.mean((output - target) ** 2).item()

            total_loss += loss.item() * data.size(0)
            total_mse += mse * data.size(0)
            num_samples += data.size(0)

    avg_loss = total_loss / num_samples
    avg_mse = total_mse / num_samples
    return avg_loss, avg_mse

def train_with_early_stopping(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    epochs: int,
    patience: int,
    logger: logging.Logger,
    output_dir: Path,
    seed: int,
) -> Dict[str, Any]:
    """
    Train with early stopping (patience=5) and save best model.
    No data augmentation is used.

    Returns:
        Dict containing training history and metrics.
    """
    best_val_loss = float("inf")
    patience_counter = 0
    history = {"train_loss": [], "val_loss": [], "train_mse": [], "val_mse": []}
    start_time = time.time()

    logger.info(f"Starting ablation training (no augmentation) for {epochs} epochs")
    logger.info(f"Early stopping patience: {patience}")

    for epoch in range(1, epochs + 1):
        logger.info(f"Epoch {epoch}/{epochs}")

        # Train
        train_loss, train_mse = train_epoch(
            model, train_loader, criterion, optimizer, device, logger
        )
        history["train_loss"].append(train_loss)
        history["train_mse"].append(train_mse)

        # Validate
        val_loss, val_mse = validate_epoch(
            model, val_loader, criterion, device, logger
        )
        history["val_loss"].append(val_loss)
        history["val_mse"].append(val_mse)

        logger.info(
            f"Epoch {epoch} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
            f"Train MSE: {train_mse:.4f}, Val MSE: {val_mse:.4f}"
        )

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model
            best_model_path = output_dir / "model_best_ablation.pt"
            torch.save(model.state_dict(), best_model_path)
            logger.info(f"Saved best model to {best_model_path}")
        else:
            patience_counter += 1
            logger.info(f"Early stopping counter: {patience_counter}/{patience}")

        if patience_counter >= patience:
            logger.info(f"Early stopping triggered at epoch {epoch}")
            break

    end_time = time.time()
    total_time = end_time - start_time

    return {
        "epochs_completed": epoch,
        "best_val_loss": best_val_loss,
        "total_time_seconds": total_time,
        "history": history,
        "early_stopped": patience_counter >= patience,
        "augmented": False,  # Explicit flag for ablation identification
        "seed": seed,
    }

def main() -> None:
    """Main entry point for ablation training."""
    logger = setup_ablation_logging()
    logger.info("Starting ablation training script (T026)")

    # Parse arguments
    parser = argparse.ArgumentParser(description="Ablation training without augmentation")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    args = parser.parse_args()

    # Set seed
    set_seed(args.seed)
    logger.info(f"Seed set to {args.seed}")

    # Setup directories
    results_dir = get_results_dir()
    output_dir = results_dir / "ablation"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    processed_dir = get_processed_dir()
    train_dir = processed_dir / "train"
    val_dir = processed_dir / "val"

    if not train_dir.exists() or not val_dir.exists():
        logger.error("Processed train/val directories not found. Run data pipeline first.")
        sys.exit(1)

    # Create NO-AUGMENT transforms
    train_transform, val_transform = create_no_augment_transforms()
    logger.info("Created transforms WITHOUT data augmentation")

    # Load datasets
    train_dataset = MicrostructureDataset(str(train_dir), transform=train_transform)
    val_dataset = MicrostructureDataset(str(val_dir), transform=val_transform)

    logger.info(f"Train dataset size: {len(train_dataset)}")
    logger.info(f"Val dataset size: {len(val_dataset)}")

    # Create loaders
    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0
    )

    # Setup model
    device = torch.device(args.device)
    model = get_model(pretrained=False)  # No pretrained for ablation consistency
    model = model.to(device)
    logger.info(f"Model loaded on {device}")

    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # Train
    results = train_with_early_stopping(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
        epochs=args.epochs,
        patience=args.patience,
        logger=logger,
        output_dir=output_dir,
        seed=args.seed,
    )

    # Save results
    results_file = output_dir / "ablation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Ablation results saved to {results_file}")
    logger.info("Ablation training completed successfully")

if __name__ == "__main__":
    main()