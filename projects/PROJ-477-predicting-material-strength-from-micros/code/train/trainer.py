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
from tqdm import tqdm

# Project imports
from utils.config import get_project_root, get_data_dir, get_processed_dir, get_results_dir, set_seed, get_seed
from data.loader import MicrostructureDataset, OOMSafeDataLoader, get_optimal_batch_size
from models.cnn import MaterialStrengthCNN, get_model
from train.augment import get_train_augmentations, get_val_augmentations
from utils.logging_config import get_logger, log_metric

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    logger: logging.Logger
) -> Dict[str, float]:
    """
    Train the model for one epoch.
    Returns a dictionary with 'loss' and 'mse' metrics.
    """
    model.train()
    total_loss = 0.0
    total_mse = 0.0
    num_batches = 0

    pbar = tqdm(dataloader, desc="Training", leave=False)
    for batch in pbar:
        images = batch["image"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()
        outputs = model(images)
        
        # Flatten outputs and labels for MSE calculation
        outputs = outputs.squeeze()
        labels = labels.squeeze()

        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # Calculate MSE for this batch
        mse = torch.mean((outputs - labels) ** 2).item()

        total_loss += loss.item()
        total_mse += mse
        num_batches += 1

        pbar.set_postfix({"loss": f"{loss.item():.4f}", "mse": f"{mse:.4f}"})

    avg_loss = total_loss / num_batches
    avg_mse = total_mse / num_batches

    logger.info(f"Train Epoch - Loss: {avg_loss:.4f}, MSE: {avg_mse:.4f}")
    return {"loss": avg_loss, "mse": avg_mse}

def validate_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    logger: logging.Logger
) -> Dict[str, float]:
    """
    Validate the model for one epoch.
    Returns a dictionary with 'loss' and 'mse' metrics.
    """
    model.eval()
    total_loss = 0.0
    total_mse = 0.0
    num_batches = 0

    with torch.no_grad():
        pbar = tqdm(dataloader, desc="Validating", leave=False)
        for batch in pbar:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)

            outputs = model(images)
            outputs = outputs.squeeze()
            labels = labels.squeeze()

            loss = criterion(outputs, labels)
            mse = torch.mean((outputs - labels) ** 2).item()

            total_loss += loss.item()
            total_mse += mse
            num_batches += 1

            pbar.set_postfix({"loss": f"{loss.item():.4f}", "mse": f"{mse:.4f}"})

    avg_loss = total_loss / num_batches
    avg_mse = total_mse / num_batches

    logger.info(f"Val Epoch - Loss: {avg_loss:.4f}, MSE: {avg_mse:.4f}")
    return {"loss": avg_loss, "mse": avg_mse}

def train_with_early_stopping(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epochs: int,
    patience: int,
    checkpoint_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Training loop with early stopping and checkpoint saving.
    """
    best_val_mse = float('inf')
    patience_counter = 0
    best_model_state = None
    training_history = {
        "train_loss": [],
        "train_mse": [],
        "val_loss": [],
        "val_mse": []
    }

    checkpoint_path = checkpoint_dir / "best_model.pth"
    history_path = checkpoint_dir / "training_history.json"

    logger.info(f"Starting training for {epochs} epochs with patience={patience}")
    logger.info(f"Checkpoints will be saved to: {checkpoint_dir}")

    for epoch in range(1, epochs + 1):
        logger.info(f"\n--- Epoch {epoch}/{epochs} ---")

        # Training phase
        train_metrics = train_epoch(model, train_loader, criterion, optimizer, device, logger)
        
        # Validation phase
        val_metrics = validate_epoch(model, val_loader, criterion, device, logger)

        # Record history
        training_history["train_loss"].append(train_metrics["loss"])
        training_history["train_mse"].append(train_metrics["mse"])
        training_history["val_loss"].append(val_metrics["loss"])
        training_history["val_mse"].append(val_metrics["mse"])

        # Early stopping logic
        current_val_mse = val_metrics["mse"]
        if current_val_mse < best_val_mse:
            best_val_mse = current_val_mse
            patience_counter = 0
            
            # Save best model
            if best_model_state is not None:
                model.load_state_dict(best_model_state)
            
            best_model_state = model.state_dict().copy()
            
            # Save checkpoint
            torch.save({
                "epoch": epoch,
                "model_state_dict": best_model_state,
                "optimizer_state_dict": optimizer.state_dict(),
                "val_mse": best_val_mse,
                "train_mse": train_metrics["mse"],
            }, checkpoint_path)
            
            logger.info(f"New best model found! Val MSE: {best_val_mse:.4f}. Saved to {checkpoint_path}")
        else:
            patience_counter += 1
            logger.info(f"Val MSE did not improve. Patience: {patience_counter}/{patience}")

        if patience_counter >= patience:
            logger.info(f"Early stopping triggered at epoch {epoch}. Best Val MSE: {best_val_mse:.4f}")
            break

    # Save final history
    with open(history_path, "w") as f:
        json.dump(training_history, f, indent=2)
    logger.info(f"Training history saved to {history_path}")

    # Load best model state back into the model for final return
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    return {
        "best_val_mse": best_val_mse,
        "epochs_run": epoch,
        "history": training_history,
        "checkpoint_path": str(checkpoint_path)
    }

def main():
    parser = argparse.ArgumentParser(description="Train Material Strength CNN with Early Stopping")
    parser.add_argument("--epochs", type=int, default=50, help="Maximum number of epochs")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size (auto-detected if None)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--no-augmentation", action="store_true", help="Disable data augmentation")
    
    args = parser.parse_args()

    # Setup
    set_seed(args.seed)
    project_root = get_project_root()
    processed_dir = get_processed_dir()
    results_dir = get_results_dir()
    checkpoint_dir = results_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    logger = get_logger("trainer")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Using seed: {args.seed}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    # Load Datasets
    logger.info("Loading datasets...")
    train_dataset = MicrostructureDataset(
        split="train",
        transform=None if args.no_augmentation else get_train_augmentations(),
        processed_dir=processed_dir
    )
    val_dataset = MicrostructureDataset(
        split="val",
        transform=get_val_augmentations(),
        processed_dir=processed_dir
    )

    if len(train_dataset) == 0 or len(val_dataset) == 0:
        logger.error("Dataset is empty. Please run the data preprocessing pipeline first.")
        sys.exit(1)

    # Determine batch size
    batch_size = args.batch_size
    if batch_size is None:
        batch_size = get_optimal_batch_size(train_dataset, device)
        logger.info(f"Auto-detected optimal batch size: {batch_size}")

    train_loader = OOMSafeDataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0, # Keep 0 for simplicity in this script to avoid multiprocessing issues in some envs
        pin_memory=True if device.type == "cuda" else False
    )
    val_loader = OOMSafeDataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True if device.type == "cuda" else False
    )

    # Model
    logger.info("Initializing model...")
    model = MaterialStrengthCNN()
    model = model.to(device)

    # Loss and Optimizer
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # Train
    logger.info("Starting training loop...")
    results = train_with_early_stopping(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
        epochs=args.epochs,
        patience=args.patience,
        checkpoint_dir=checkpoint_dir,
        logger=logger
    )

    logger.info("Training complete.")
    logger.info(f"Best Validation MSE: {results['best_val_mse']:.4f}")
    logger.info(f"Epochs Run: {results['epochs_run']}")
    logger.info(f"Checkpoint saved at: {results['checkpoint_path']}")

    # Log final metrics
    log_metric("best_val_mse", results['best_val_mse'])
    log_metric("epochs_run", results['epochs_run'])

    return results

if __name__ == "__main__":
    main()