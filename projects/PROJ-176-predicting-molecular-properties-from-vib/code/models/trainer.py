"""
Trainer module for the molecular property prediction model.
Implements training loop with early stopping and TensorBoard logging.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.tensorboard import SummaryWriter

# Import from local modules
from models.cnn_1d import MolecularPropertyCNN
from utils.logging_utils import setup_logging, get_logger
from utils.seed_utils import set_seed

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
MODEL_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
RUNS_DIR = PROJECT_ROOT / "runs" / "training"

class Trainer:
    """
    Trainer class for the molecular property prediction model.
    """
    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 1e-3,
        patience: int = 10,
        device: str = "cpu",
        log_dir: Optional[Path] = None
    ):
        """
        Initialize the trainer.

        Args:
            model: Model to train.
            learning_rate: Learning rate for Adam optimizer.
            patience: Patience for early stopping.
            device: Device to train on.
            log_dir: Directory for TensorBoard logs.
        """
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate
        self.patience = patience

        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)

        # Loss function (MSE for regression)
        self.criterion = nn.MSELoss()

        # Early stopping
        self.best_val_loss = float('inf')
        self.patience_counter = 0

        # TensorBoard writer
        if log_dir is None:
            log_dir = RUNS_DIR

        log_dir.mkdir(parents=True, exist_ok=True)
        self.writer = SummaryWriter(log_dir=str(log_dir))

        self.logger = get_logger()

    def train_epoch(
        self,
        dataloader: DataLoader,
        epoch: int
    ) -> float:
        """
        Train for one epoch.

        Args:
            dataloader: Training data loader.
            epoch: Current epoch number.

        Returns:
            Average training loss for the epoch.
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            x, y = batch
            x, y = x.to(self.device), y.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(x)
            loss = self.criterion(outputs, y)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches

        # Log to TensorBoard
        self.writer.add_scalar("Loss/train", avg_loss, epoch)

        return avg_loss

    def validate(
        self,
        dataloader: DataLoader,
        epoch: int
    ) -> float:
        """
        Validate the model.

        Args:
            dataloader: Validation data loader.
            epoch: Current epoch number.

        Returns:
            Average validation loss for the epoch.
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                x, y = batch
                x, y = x.to(self.device), y.to(self.device)

                outputs = self.model(x)
                loss = self.criterion(outputs, y)

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches

        # Log to TensorBoard
        self.writer.add_scalar("Loss/val", avg_loss, epoch)

        return avg_loss

    def early_stopping(self, val_loss: float) -> bool:
        """
        Check if early stopping should be triggered.

        Args:
            val_loss: Current validation loss.

        Returns:
            True if early stopping should be triggered, False otherwise.
        """
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.patience_counter = 0
            return False
        else:
            self.patience_counter += 1
            if self.patience_counter >= self.patience:
                self.logger.info(f"Early stopping triggered at epoch with patience={self.patience}")
                return True
            return False

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 100
    ) -> Dict[str, Any]:
        """
        Train the model.

        Args:
            train_loader: Training data loader.
            val_loader: Validation data loader.
            num_epochs: Maximum number of epochs.

        Returns:
            Dictionary with training history and best model state.
        """
        history = {
            "train_loss": [],
            "val_loss": [],
            "best_epoch": 0
        }

        self.logger.info(f"Starting training for {num_epochs} epochs")

        best_model_state = None
        best_epoch = 0

        for epoch in range(num_epochs):
            # Train
            train_loss = self.train_epoch(train_loader, epoch)
            history["train_loss"].append(train_loss)

            # Validate
            val_loss = self.validate(val_loader, epoch)
            history["val_loss"].append(val_loss)

            self.logger.info(f"Epoch {epoch + 1}/{num_epochs} - "
                           f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            # Check for best model
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                best_model_state = self.model.state_dict().copy()
                best_epoch = epoch + 1

            # Early stopping
            if self.early_stopping(val_loss):
                self.logger.info(f"Training stopped early at epoch {epoch + 1}")
                break

        history["best_epoch"] = best_epoch
        history["best_val_loss"] = self.best_val_loss

        self.writer.close()

        return history, best_model_state

def main():
    """
    Main entry point for the trainer script.
    """
    # Set up logging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(LOGS_DIR)
    logger.info("Starting training")

    # Set seed for reproducibility
    set_seed(42)

    try:
        # Load data
        data_path = PREPROCESSED_DIR / "aligned_data.npz"
        if not data_path.exists():
            raise FileNotFoundError(f"Preprocessed data not found at {data_path}")

        data = np.load(data_path)
        X = data["X"]
        y = data["y"]

        # Split into train/val/test
        split_idx = int(len(X) * 0.8)
        train_idx = int(split_idx * 0.8)

        X_train, y_train = X[:train_idx], y[:train_idx]
        X_val, y_val = X[train_idx:split_idx], y[train_idx:split_idx]
        X_test, y_test = X[split_idx:], y[split_idx:]

        logger.info(f"Data split: {len(X_train)} train, {len(X_val)} val, {len(X_test)} test")

        # Create data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val),
            torch.FloatTensor(y_val)
        )

        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

        # Create model
        input_dim = X_train.shape[1]
        model = MolecularPropertyCNN(input_dim=input_dim)

        # Create trainer
        trainer = Trainer(
            model=model,
            learning_rate=1e-3,
            patience=10,
            device="cpu"
        )

        # Train
        history, best_model_state = trainer.train(train_loader, val_loader, num_epochs=100)

        # Save best model
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        checkpoint_path = MODEL_DIR / "model_best.pt"

        torch.save({
            "model_state_dict": best_model_state,
            "model_config": {
                "input_dim": input_dim,
                "num_targets": 3
            },
            "best_epoch": history["best_epoch"],
            "best_val_loss": history["best_val_loss"]
        }, checkpoint_path)

        logger.info(f"Best model saved to {checkpoint_path}")
        logger.info("Training completed successfully")

    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
