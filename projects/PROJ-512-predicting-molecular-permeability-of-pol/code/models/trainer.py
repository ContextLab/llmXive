"""
Trainer module for Polymer Graph Neural Networks.
Implements training loop with gradient clipping and early stopping.
"""
import os
import logging
from typing import Optional, Dict, Any, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import Optimizer

from data.utils import set_seed, get_seed, setup_logging
from models.polymer_graph import PolymerGraph
from models.permeability_record import PermeabilityRecord

logger = logging.getLogger(__name__)

class Trainer:
    """
    Trainer class for GNN models with gradient clipping and early stopping.
    """

    def __init__(
        self,
        model: nn.Module,
        optimizer: Optimizer,
        criterion: nn.Module,
        device: str = "cpu",
        max_norm: float = 1.0,
        clip_type: str = "max_norm",
        patience: int = 10,
        min_delta: float = 1e-4,
    ):
        """
        Initialize the Trainer.

        Args:
            model: The GNN model to train.
            optimizer: The optimizer for the model parameters.
            criterion: The loss function.
            device: Device to run training on ('cpu' or 'cuda').
            max_norm: Maximum norm for gradient clipping.
            clip_type: Type of gradient clipping ('max_norm' or 'value').
            patience: Number of epochs to wait for improvement before early stopping.
            min_delta: Minimum change in monitored metric to qualify as improvement.
        """
        self.model = model.to(device)
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.max_norm = max_norm
        self.clip_type = clip_type
        self.patience = patience
        self.min_delta = min_delta

        self.best_loss = float("inf")
        self.epochs_without_improvement = 0
        self.training_history: List[Dict[str, float]] = []

    def _apply_gradient_clipping(self) -> None:
        """
        Apply gradient clipping based on the configured type.
        """
        if self.clip_type == "max_norm":
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(), max_norm=self.max_norm
            )
            logger.debug(f"Applied gradient clipping (max_norm={self.max_norm})")
        elif self.clip_type == "value":
            torch.nn.utils.clip_grad_value_(
                self.model.parameters(), clip_value=self.max_norm
            )
            logger.debug(f"Applied gradient clipping (value={self.max_norm})")
        else:
            raise ValueError(f"Unknown clip_type: {self.clip_type}")

    def train_epoch(self, dataloader: DataLoader) -> float:
        """
        Train the model for one epoch.

        Args:
            dataloader: DataLoader for training data.

        Returns:
            Average loss for the epoch.
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            # Expected batch structure: dict with 'graph', 'target' keys
            # Adapt based on actual dataloader implementation in US1/US2
            if isinstance(batch, dict):
                graphs = batch.get("graph")
                targets = batch.get("target").to(self.device)
            else:
                # Fallback for tuple-based dataloaders
                graphs, targets = batch
                targets = targets.to(self.device)

            self.optimizer.zero_grad()

            # Forward pass
            # Assuming model(graphs) returns predictions
            # The PolymerGraph entity or a custom Dataset class should handle batching
            try:
                outputs = self.model(graphs)
            except TypeError:
                # If model expects list of graphs or specific tensor format
                # This will be refined when US2 (GNN model) is implemented
                outputs = self.model(list(graphs))

            loss = self.criterion(outputs, targets)

            # Backward pass
            loss.backward()

            # Apply gradient clipping
            self._apply_gradient_clipping()

            # Update weights
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss

    def validate(self, dataloader: DataLoader) -> float:
        """
        Validate the model on a dataset.

        Args:
            dataloader: DataLoader for validation data.

        Returns:
            Average loss for the validation set.
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                if isinstance(batch, dict):
                    graphs = batch.get("graph")
                    targets = batch.get("target").to(self.device)
                else:
                    graphs, targets = batch
                    targets = targets.to(self.device)

                try:
                    outputs = self.model(graphs)
                except TypeError:
                    outputs = self.model(list(graphs))

                loss = self.criterion(outputs, targets)
                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss

    def fit(
        self,
        train_dataloader: DataLoader,
        val_dataloader: Optional[DataLoader] = None,
        epochs: int = 100,
    ) -> List[Dict[str, float]]:
        """
        Train the model for a specified number of epochs.

        Args:
            train_dataloader: DataLoader for training data.
            val_dataloader: Optional DataLoader for validation data.
            epochs: Number of epochs to train.

        Returns:
            List of training history dictionaries.
        """
        logger.info(f"Starting training for {epochs} epochs on device: {self.device}")

        for epoch in range(1, epochs + 1):
            train_loss = self.train_epoch(train_dataloader)

            if val_dataloader:
                val_loss = self.validate(val_dataloader)
                self.training_history.append(
                    {"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss}
                )
                logger.info(
                    f"Epoch {epoch}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}"
                )

                # Early stopping check
                if val_loss < self.best_loss - self.min_delta:
                    self.best_loss = val_loss
                    self.epochs_without_improvement = 0
                    # Save best model state here if needed
                else:
                    self.epochs_without_improvement += 1
                    if self.epochs_without_improvement >= self.patience:
                        logger.info(
                            f"Early stopping triggered at epoch {epoch} (val_loss: {val_loss:.4f})"
                        )
                        break
            else:
                self.training_history.append(
                    {"epoch": epoch, "train_loss": train_loss}
                )
                logger.info(f"Epoch {epoch}/{epochs} - Train Loss: {train_loss:.4f}")

        logger.info("Training completed.")
        return self.training_history

def create_trainer(
    model: nn.Module,
    optimizer: Optimizer,
    criterion: nn.Module,
    device: str = "cpu",
) -> Trainer:
    """
    Factory function to create a Trainer instance with default configuration.
    """
    max_norm = float(os.getenv("GRADIENT_CLIP_MAX_NORM", "1.0"))
    clip_type = os.getenv("GRADIENT_CLIP_TYPE", "max_norm")
    patience = int(os.getenv("EARLY_STOPPING_PATIENCE", "10"))

    return Trainer(
        model=model,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        max_norm=max_norm,
        clip_type=clip_type,
        patience=patience,
    )
