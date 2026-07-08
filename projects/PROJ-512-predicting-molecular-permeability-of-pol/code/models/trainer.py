import os
import logging
from typing import Optional, Dict, Any, List
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from data.utils import set_seed, get_seed, ensure_seed_initialized
import numpy as np

logger = logging.getLogger(__name__)

class Trainer:
    """
    Trainer class for the PolymerGNN model with early stopping and gradient clipping.
    """

    def __init__(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
        device: Optional[torch.device] = None,
        patience: int = 10,
        min_delta: float = 1e-4,
        max_grad_norm: float = 1.0,
        checkpoint_path: Optional[str] = None,
    ):
        """
        Initialize the Trainer.

        Args:
            model: The PyTorch model to train.
            optimizer: The optimizer for the model.
            scheduler: Optional learning rate scheduler.
            device: Device to run training on (CPU or CUDA).
            patience: Number of epochs to wait for improvement before early stopping.
            min_delta: Minimum change in the monitored quantity to qualify as an improvement.
            max_grad_norm: Maximum norm of the gradients for clipping.
            checkpoint_path: Path to save the best model checkpoint.
        """
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.device = device or (
            torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        )
        self.patience = patience
        self.min_delta = min_delta
        self.max_grad_norm = max_grad_norm
        self.checkpoint_path = checkpoint_path

        self.model.to(self.device)
        self.best_loss = float("inf")
        self.patience_counter = 0
        self.training_history: List[Dict[str, float]] = []

        logger.info(f"Trainer initialized on device: {self.device}")
        logger.info(f"Early stopping patience: {patience}, min_delta: {min_delta}")
        logger.info(f"Gradient clipping max_norm: {max_grad_norm}")

    def _clip_gradients(self) -> None:
        """Clip gradients to prevent exploding gradients."""
        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(), max_norm=self.max_grad_norm
        )

    def _early_stop_check(self, current_loss: float) -> bool:
        """
        Check if early stopping condition is met.

        Args:
            current_loss: The current validation loss.

        Returns:
            True if early stopping should be triggered, False otherwise.
        """
        if current_loss < self.best_loss - self.min_delta:
            self.best_loss = current_loss
            self.patience_counter = 0
            
            # Save best model checkpoint if path provided
            if self.checkpoint_path:
                os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
                torch.save(
                    {
                        "epoch": len(self.training_history),
                        "model_state_dict": self.model.state_dict(),
                        "optimizer_state_dict": self.optimizer.state_dict(),
                        "best_loss": self.best_loss,
                    },
                    self.checkpoint_path,
                )
                logger.debug(f"Best model saved to {self.checkpoint_path}")
            return False
        else:
            self.patience_counter += 1
            logger.debug(f"Early stopping patience: {self.patience_counter}/{self.patience}")
            return self.patience_counter >= self.patience

    def train_epoch(self, train_loader: DataLoader, epoch: int) -> float:
        """
        Train the model for one epoch.

        Args:
            train_loader: DataLoader for the training set.
            epoch: Current epoch number.

        Returns:
            Average training loss for the epoch.
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch_idx, batch in enumerate(train_loader):
            # Move batch to device
            # Assuming batch is a dict or Data object with attributes on it
            # We need to handle both PyG Data objects and dict-like batches
            if isinstance(batch, dict):
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
                # Extract target - assuming 'y' is the target key
                target = batch.get("y", batch.get("target"))
                if target is None:
                    raise ValueError("Batch must contain 'y' or 'target' key")
                input_data = {k: v for k, v in batch.items() if k not in ["y", "target"]}
                output = self.model(**input_data)
            else:
                # Assume PyG Data object
                batch = batch.to(self.device)
                target = batch.y
                output = self.model(batch)

            self.optimizer.zero_grad()
            loss = nn.MSELoss()(output.squeeze(), target.squeeze())
            loss.backward()

            # Apply gradient clipping
            self._clip_gradients()

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            if batch_idx % 100 == 0:
                logger.debug(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        logger.info(f"Epoch {epoch} Training Loss: {avg_loss:.4f}")
        return avg_loss

    def validate(self, val_loader: DataLoader) -> float:
        """
        Validate the model on the validation set.

        Args:
            val_loader: DataLoader for the validation set.

        Returns:
            Average validation loss.
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                if isinstance(batch, dict):
                    batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
                    target = batch.get("y", batch.get("target"))
                    if target is None:
                        raise ValueError("Batch must contain 'y' or 'target' key")
                    input_data = {k: v for k, v in batch.items() if k not in ["y", "target"]}
                    output = self.model(**input_data)
                else:
                    batch = batch.to(self.device)
                    target = batch.y
                    output = self.model(batch)

                loss = nn.MSELoss()(output.squeeze(), target.squeeze())
                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        logger.info(f"Validation Loss: {avg_loss:.4f}")
        return avg_loss

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int,
        verbose: bool = True,
    ) -> List[Dict[str, float]]:
        """
        Train the model with early stopping.

        Args:
            train_loader: DataLoader for the training set.
            val_loader: DataLoader for the validation set.
            epochs: Maximum number of epochs to train.
            verbose: Whether to log progress.

        Returns:
            List of training history dictionaries.
        """
        logger.info(f"Starting training for up to {epochs} epochs...")
        logger.info(f"Training set size: {len(train_loader.dataset)}")
        logger.info(f"Validation set size: {len(val_loader.dataset)}")

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader, epoch)
            val_loss = self.validate(val_loader)

            history_entry = {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
            }
            self.training_history.append(history_entry)

            if verbose:
                logger.info(
                    f"Epoch {epoch + 1}/{epochs} - Train Loss: {train_loss:.4f}, "
                    f"Val Loss: {val_loss:.4f}"
                )

            # Step scheduler if present
            if self.scheduler:
                self.scheduler.step(val_loss)

            # Check early stopping
            if self._early_stop_check(val_loss):
                logger.info(
                    f"Early stopping triggered at epoch {epoch + 1} "
                    f"(patience: {self.patience_counter})"
                )
                break

        logger.info(f"Training completed. Best validation loss: {self.best_loss:.4f}")
        return self.training_history

    def load_best_checkpoint(self) -> None:
        """Load the best model from checkpoint if it exists."""
        if self.checkpoint_path and os.path.exists(self.checkpoint_path):
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.best_loss = checkpoint.get("best_loss", float("inf"))
            logger.info(f"Loaded best model from {self.checkpoint_path}")
        else:
            logger.warning(f"No checkpoint found at {self.checkpoint_path}")


def create_trainer(
    model: nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    device: Optional[torch.device] = None,
    patience: int = 10,
    min_delta: float = 1e-4,
    max_grad_norm: float = 1.0,
    checkpoint_path: Optional[str] = None,
) -> Trainer:
    """
    Factory function to create a Trainer instance.

    Args:
        model: The PyTorch model to train.
        optimizer: The optimizer (will use Adam if not provided).
        scheduler: Optional learning rate scheduler.
        device: Device to run training on.
        patience: Early stopping patience.
        min_delta: Minimum improvement threshold.
        max_grad_norm: Maximum gradient norm for clipping.
        checkpoint_path: Path to save best model.

    Returns:
        A configured Trainer instance.
    """
    if optimizer is None:
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    ensure_seed_initialized()
    seed = get_seed()
    set_seed(seed)
    
    return Trainer(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        patience=patience,
        min_delta=min_delta,
        max_grad_norm=max_grad_norm,
        checkpoint_path=checkpoint_path,
    )


def main() -> None:
    """
    Main function to demonstrate the trainer usage.
    This is a placeholder for integration with the full pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Trainer module loaded successfully.")
    
    # Example usage (would be replaced by actual pipeline integration)
    # model = create_gnn_model(...)
    # trainer = create_trainer(model, patience=10, max_grad_norm=1.0)
    # trainer.fit(train_loader, val_loader, epochs=100)

    logger.info("Trainer main function executed.")


if __name__ == "__main__":
    main()