"""
Ablation study script: Train the CNN model WITHOUT data augmentation.

This script runs independently from code/train/trainer.py to ensure a distinct
artifact for ablation analysis. It uses the exact same architecture and hyperparameters
but disables all augmentation transforms defined in code/train/augment.py.

Task: T026 [US2]
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms

# Project imports
from utils.config import (
    get_project_root,
    get_data_dir,
    get_processed_dir,
    get_results_dir,
    get_code_dir,
    set_seed,
    get_seed,
)
from data.loader import MicrostructureDataset, OOMSafeDataLoader
from models.cnn import MaterialStrengthCNN, get_model
from train.augment import get_train_augmentations, get_val_augmentations

# Setup logger
def setup_ablation_logging() -> logging.Logger:
    """Configure logging for the ablation training script."""
    logger = logging.getLogger("train_ablation")
    logger.setLevel(logging.INFO)

    # File handler
    results_dir = get_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    log_path = results_dir / "ablation_training.log"

    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def create_no_augment_transforms() -> Dict[str, Any]:
    """
    Create transforms for training WITHOUT augmentation.
    
    Only applies the base preprocessing: Resize and Normalize.
    This is the key difference from the standard trainer which uses
    get_train_augmentations().
    """
    base_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    return {
        "train": base_transform,
        "val": base_transform,
        "test": base_transform,
    }

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    logger: logging.Logger,
) -> float:
    """Train the model for one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch_idx, (images, labels) in enumerate(dataloader):
        images = images.to(device)
        labels = labels.float().to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    avg_loss = total_loss / num_batches
    logger.info(f"Train Epoch Loss: {avg_loss:.4f}")
    return avg_loss

def validate_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    logger: logging.Logger,
) -> float:
    """Validate the model for one epoch."""
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.float().to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item()
            num_batches += 1

    avg_loss = total_loss / num_batches
    logger.info(f"Val Epoch Loss: {avg_loss:.4f}")
    return avg_loss

def train_with_early_stopping(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epochs: int,
    patience: int,
    logger: logging.Logger,
    checkpoint_path: Path,
) -> Dict[str, Any]:
    """
    Train with early stopping.
    
    Returns a dictionary with training metrics.
    """
    best_val_loss = float("inf")
    patience_counter = 0
    best_model_state = None
    training_log = {
        "train_losses": [],
        "val_losses": [],
        "early_stopped": False,
        "best_epoch": 0,
        "epochs_run": 0,
    }

    logger.info(f"Starting training for {epochs} epochs with patience {patience}")

    for epoch in range(1, epochs + 1):
        logger.info(f"--- Epoch {epoch}/{epochs} ---")

        train_loss = train_epoch(model, train_loader, criterion, optimizer, device, logger)
        val_loss = validate_epoch(model, val_loader, criterion, device, logger)

        training_log["train_losses"].append(train_loss)
        training_log["val_losses"].append(val_loss)
        training_log["epochs_run"] = epoch

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            patience_counter = 0
            training_log["best_epoch"] = epoch
            logger.info(f"New best model found at epoch {epoch} (val_loss: {val_loss:.4f})")
            # Save best model
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": best_model_state,
                    "val_loss": val_loss,
                },
                checkpoint_path,
            )
        else:
            patience_counter += 1
            logger.info(f"Patience counter: {patience_counter}/{patience}")

            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch}")
                training_log["early_stopped"] = True
                break

    return training_log

def main():
    """Main entry point for ablation training."""
    parser = argparse.ArgumentParser(description="Train CNN without augmentation (Ablation)")
    parser.add_argument(
        "--epochs", type=int, default=20, help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size"
    )
    parser.add_argument(
        "--lr", type=float, default=1e-4, help="Learning rate"
    )
    parser.add_argument(
        "--patience", type=int, default=5, help="Early stopping patience"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Output directory for artifacts"
    )
    args = parser.parse_args()

    # Setup
    logger = setup_ablation_logging()
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Paths
    project_root = get_project_root()
    processed_dir = get_processed_dir()
    results_dir = get_results_dir()
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = results_dir / "ablation"
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = output_dir / "model_ablation_best.pt"
    log_path = output_dir / "training_log_ablation.json"

    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Checkpoint path: {checkpoint_path}")

    # Load transforms (NO AUGMENTATION)
    transforms_dict = create_no_augment_transforms()
    logger.info("Using NO data augmentation (ablation study)")

    # Load datasets
    train_manifest = processed_dir / "train" / "manifest.csv"
    val_manifest = processed_dir / "val" / "manifest.csv"

    if not train_manifest.exists() or not val_manifest.exists():
        logger.error("Train or Val manifest not found. Run data pipeline first.")
        sys.exit(1)

    logger.info("Loading datasets...")
    train_dataset = MicrostructureDataset(
        manifest_path=train_manifest,
        transform=transforms_dict["train"],
    )
    val_dataset = MicrostructureDataset(
        manifest_path=val_manifest,
        transform=transforms_dict["val"],
    )

    logger.info(f"Train size: {len(train_dataset)}, Val size: {len(val_dataset)}")

    # DataLoaders
    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0
    )

    # Model
    logger.info("Initializing model (MobileNetV2 backbone)...")
    model = get_model(pretrained=True, freeze_backbone=False)
    model = model.to(device)

    # Loss and Optimizer
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # Train
    logger.info("Starting training (no augmentation)...")
    training_log = train_with_early_stopping(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
        epochs=args.epochs,
        patience=args.patience,
        logger=logger,
        checkpoint_path=checkpoint_path,
    )

    # Save final log
    training_log["config"] = {
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "patience": args.patience,
        "seed": args.seed,
        "augmentation": "NONE (Ablation)",
        "device": str(device),
    }

    with open(log_path, "w") as f:
        json.dump(training_log, f, indent=2)

    logger.info(f"Training complete. Log saved to {log_path}")
    logger.info(f"Best model saved to {checkpoint_path}")
    logger.info(f"Best validation loss: {training_log['val_losses'][training_log['best_epoch']-1]:.4f}")

    if not training_log["early_stopped"]:
        logger.info("Training completed without early stopping.")

    return 0

if __name__ == "__main__":
    sys.exit(main())