"""
Training utilities for llmXive models.

Provides training loops, batch size tuning, and optimization utilities.
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from utils.logging import get_logger, log_info, log_error
from utils.memory_monitor import memory_limit_context
from models.base import ProjectionModel


logger = get_logger(__name__)


class Trainer:
    """
    Trainer class for projection models.

    Handles training loops, loss computation, and optimization.
    """

    def __init__(
        self,
        model: ProjectionModel,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: str = "cpu",
        gradient_clip: Optional[float] = None,
    ):
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.gradient_clip = gradient_clip
        self.history: Dict[str, List[float]] = {"loss": [], "val_loss": []}

    def train_epoch(
        self,
        dataloader: torch.utils.data.DataLoader,
        epoch: int,
    ) -> float:
        """
        Train for one epoch.

        Args:
            dataloader: Training data loader.
            epoch: Current epoch number.

        Returns:
            Average loss for the epoch.
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch_idx, batch in enumerate(dataloader):
            # Move data to device
            embeddings = batch["embeddings"].to(self.device)
            conditions = batch.get("conditions", None)
            if conditions is not None:
                conditions = conditions.to(self.device)
            targets = batch["targets"].to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(embeddings, conditions)

            # Compute loss
            loss = self.criterion(outputs, targets)

            # Backward pass
            loss.backward()

            # Gradient clipping
            if self.gradient_clip is not None:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.gradient_clip)

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        self.history["loss"].append(avg_loss)
        log_info(f"Epoch {epoch} - Train Loss: {avg_loss:.4f}")
        return avg_loss

    def evaluate(
        self,
        dataloader: torch.utils.data.DataLoader,
    ) -> float:
        """
        Evaluate the model on a validation/test set.

        Args:
            dataloader: Validation/test data loader.

        Returns:
            Average loss.
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                embeddings = batch["embeddings"].to(self.device)
                conditions = batch.get("conditions", None)
                if conditions is not None:
                    conditions = conditions.to(self.device)
                targets = batch["targets"].to(self.device)

                outputs = self.model(embeddings, conditions)
                loss = self.criterion(outputs, targets)

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        self.history["val_loss"].append(avg_loss)
        log_info(f"Validation Loss: {avg_loss:.4f}")
        return avg_loss

    def train(
        self,
        train_loader: torch.utils.data.DataLoader,
        val_loader: torch.utils.data.DataLoader,
        epochs: int,
        patience: int = 5,
        save_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Full training loop with early stopping.

        Args:
            train_loader: Training data loader.
            val_loader: Validation data loader.
            epochs: Maximum number of epochs.
            patience: Patience for early stopping.
            save_path: Path to save the best model.

        Returns:
            Training history.
        """
        best_val_loss = float("inf")
        patience_counter = 0

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader, epoch + 1)
            val_loss = self.evaluate(val_loader)

            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                if save_path:
                  torch.save(self.model.state_dict(), save_path)
                  log_info(f"Model saved to {save_path}")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    log_info(f"Early stopping at epoch {epoch + 1}")
                    break

        return self.history


def create_trainer(
    model: ProjectionModel,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-4,
    device: str = "cpu",
    gradient_clip: Optional[float] = None,
    loss_fn: Optional[nn.Module] = None,
) -> Trainer:
    """
    Factory function to create a Trainer instance.

    Args:
        model: The model to train.
        learning_rate: Learning rate for the optimizer.
        weight_decay: Weight decay for regularization.
        device: Device to train on.
        gradient_clip: Maximum norm for gradient clipping.
        loss_fn: Loss function (default: MSELoss).

    Returns:
        A Trainer instance.
    """
    if loss_fn is None:
        loss_fn = nn.MSELoss()

    optimizer = optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    return Trainer(
        model=model,
        optimizer=optimizer,
        criterion=loss_fn,
        device=device,
        gradient_clip=gradient_clip,
    )


def train_with_batch_size_tuning(
    model: ProjectionModel,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    max_batch_size: int = 64,
    memory_threshold_mb: float = 6000.0,
    epochs: int = 10,
    **trainer_kwargs,
) -> Tuple[Trainer, Dict[str, Any]]:
    """
    Train with automatic batch size tuning to avoid OOM.

    Args:
        model: The model to train.
        train_loader: Training data loader (will be re-sampled).
        val_loader: Validation data loader.
        max_batch_size: Maximum batch size to try.
        memory_threshold_mb: Memory limit in MB.
        epochs: Number of epochs to train.
        **trainer_kwargs: Arguments for create_trainer.

    Returns:
        Tuple of (Trainer instance, tuning results).
    """
    import gc

    best_batch_size = 1
    found_safe = False

    # Try increasing batch sizes
    for bs in [2, 4, 8, 16, 32, 64, 128]:
        if bs > max_batch_size:
            break

        try:
            # Create a small subset to test memory
            test_loader = torch.utils.data.DataLoader(
                train_loader.dataset,
                batch_size=bs,
                shuffle=False,
            )

            # Run a single forward/backward pass
            trainer = create_trainer(model, **trainer_kwargs)
            trainer.model.train()

            with memory_limit_context(memory_threshold_mb):
                batch = next(iter(test_loader))
                embeddings = batch["embeddings"].to(trainer.device)
                conditions = batch.get("conditions", None)
                if conditions is not None:
                    conditions = conditions.to(trainer.device)
                targets = batch["targets"].to(trainer.device)

                outputs = trainer.model(embeddings, conditions)
                loss = trainer.criterion(outputs, targets)
                loss.backward()

            best_batch_size = bs
            found_safe = True
            log_info(f"Batch size {bs} is safe.")
            gc.collect()
            torch.cuda.empty_cache() if hasattr(torch.cuda, 'empty_cache') else None

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                log_info(f"Batch size {bs} caused OOM. Using previous safe size.")
                break
            else:
                raise

    if not found_safe:
        log_error("Could not find a safe batch size. Using batch size 1.")
        best_batch_size = 1

    # Re-create trainer with optimal batch size
    optimal_loader = torch.utils.data.DataLoader(
        train_loader.dataset,
        batch_size=best_batch_size,
        shuffle=True,
    )

    trainer = create_trainer(model, **trainer_kwargs)
    history = trainer.train(optimal_loader, val_loader, epochs=epochs)

    return trainer, {
        "optimal_batch_size": best_batch_size,
        "max_batch_size_attempted": max_batch_size,
        "training_history": history,
    }