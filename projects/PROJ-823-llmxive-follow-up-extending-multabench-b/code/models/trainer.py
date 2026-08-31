"""
Training utilities for the llmXive pipeline.

Implements training loops for:
- Frozen baseline classifiers (US1)
- Tabular-conditioned projection modules (US2)

Supports CPU-only training with memory-safe batch sizing.
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.memory_monitor import get_process_memory_mb, memory_limit_context
from models.base import ProjectionModel
from embeddings.generator import EmbeddingGenerator

logger = get_logger(__name__)

class Trainer:
    """
    Trainer class for projection models.

    Handles training loop, gradient freezing, and evaluation.
    """

    def __init__(
        self,
        model: ProjectionModel,
        optimizer: Optional[torch.optim.Optimizer] = None,
        criterion: Optional[nn.Module] = None,
        device: str = "cpu",
        config: Optional[Dict[str, Any]] = None
    ):
        self.model = model
        self.device = device
        self.config = config or {}

        if optimizer is None:
            self.optimizer = optim.Adam(model.parameters(), lr=1e-3)
        else:
            self.optimizer = optimizer

        if criterion is None:
            self.criterion = nn.MSELoss()
        else:
            self.criterion = criterion

        self.history = {
            'train_loss': [],
            'val_loss': []
        }

    def train_epoch(
        self,
        dataloader: torch.utils.data.DataLoader,
        seed: int = 42
    ) -> float:
        """
        Train for one epoch.

        Args:
            dataloader: Training data loader
            seed: Random seed for reproducibility

        Returns:
            Average training loss
        """
        self.model.train()
        torch.manual_seed(seed)

        total_loss = 0.0
        num_batches = 0

        for batch_idx, batch in enumerate(dataloader):
            embeddings = batch['embeddings'].to(self.device)
            tabular = batch['tabular'].to(self.device)
            labels = batch['labels'].to(self.device)

            self.optimizer.zero_grad()

            with torch.no_grad():
                # Embeddings are frozen
                pass

            outputs = self.model.project(embeddings, tabular)

            # Depending on task, loss calculation may vary
            # For now, assume regression task
            loss = self.criterion(outputs, labels)

            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        self.history['train_loss'].append(avg_loss)
        return avg_loss

    def validate(
        self,
        dataloader: torch.utils.data.DataLoader
    ) -> float:
        """
        Validate on a dataset.

        Args:
            dataloader: Validation data loader

        Returns:
            Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                embeddings = batch['embeddings'].to(self.device)
                tabular = batch['tabular'].to(self.device)
                labels = batch['labels'].to(self.device)

                outputs = self.model.project(embeddings, tabular)
                loss = self.criterion(outputs, labels)

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        self.history['val_loss'].append(avg_loss)
        return avg_loss

    def fit(
        self,
        train_loader: torch.utils.data.DataLoader,
        val_loader: torch.utils.data.DataLoader,
        epochs: int = 10,
        seed: int = 42
    ) -> Dict[str, List[float]]:
        """
        Full training loop.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            epochs: Number of epochs
            seed: Random seed

        Returns:
            Training history
        """
        log_info(logger, f"Starting training for {epochs} epochs")

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader, seed=seed)
            val_loss = self.validate(val_loader)

            log_info(logger, f"Epoch {epoch+1}/{epochs}: "
                             f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

        return self.history

    def save_checkpoint(self, path: Union[str, Path], epoch: int) -> None:
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state': self.model.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'history': self.history
        }
        torch.save(checkpoint, path)
        log_info(logger, f"Checkpoint saved to {path}")

    def load_checkpoint(self, path: Union[str, Path]) -> None:
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        self.history = checkpoint['history']
        log_info(logger, f"Checkpoint loaded from {path}")

def create_trainer(
    model: ProjectionModel,
    device: str = "cpu",
    config: Optional[Dict[str, Any]] = None
) -> Trainer:
    """
    Factory function to create a trainer.

    Args:
        model: Projection model to train
        device: Device to train on
        config: Training configuration

    Returns:
        Trainer instance
    """
    return Trainer(model, device=device, config=config)

def train_with_batch_size_tuning(
    model: ProjectionModel,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    max_batch_size: int = 32,
    memory_threshold_mb: float = 6000.0,
    epochs: int = 10,
    device: str = "cpu"
) -> Tuple[Trainer, int]:
    """
    Train with automatic batch size tuning based on memory usage.

    Args:
        model: Model to train
        train_loader: Training data loader
        val_loader: Validation data loader
        max_batch_size: Maximum allowed batch size
        memory_threshold_mb: Memory threshold in MB
        epochs: Number of epochs
        device: Device to train on

    Returns:
        Tuple of (Trainer, optimal_batch_size)
    """
    # Start with a small batch size
    batch_size = 2
    optimal_batch_size = 2

    while batch_size <= max_batch_size:
        try:
            # Create a temporary dataloader with current batch size
            temp_train = torch.utils.data.DataLoader(
                train_loader.dataset,
                batch_size=batch_size,
                shuffle=train_loader.shuffle,
                num_workers=0  # Keep it simple for memory monitoring
            )

            trainer = create_trainer(model, device=device)

            # Run a single batch to check memory
            for batch in temp_train:
                embeddings = batch['embeddings'].to(device)
                tabular = batch['tabular'].to(device)

                with torch.cuda.amp.autocast(enabled=False):
                    _ = trainer.model.project(embeddings, tabular)

                mem_mb = get_process_memory_mb()
                log_info(logger, f"Batch size {batch_size}: Memory usage {mem_mb:.1f} MB")

                if mem_mb > memory_threshold_mb:
                    log_warning(logger, f"Memory threshold exceeded at batch size {batch_size}")
                    break

                # If successful, try next batch size
                batch_size *= 2
                optimal_batch_size = batch_size // 2
                break

        except Exception as e:
            log_error(logger, f"Error at batch size {batch_size}: {str(e)}")
            break

    log_info(logger, f"Optimal batch size determined: {optimal_batch_size}")

    # Create final trainer with optimal batch size
    final_train = torch.utils.data.DataLoader(
        train_loader.dataset,
        batch_size=optimal_batch_size,
        shuffle=train_loader.shuffle
    )

    trainer = create_trainer(model, device=device)
    trainer.fit(final_train, val_loader, epochs=epochs)

    return trainer, optimal_batch_size
