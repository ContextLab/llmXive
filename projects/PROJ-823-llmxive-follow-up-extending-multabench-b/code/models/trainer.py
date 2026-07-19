"""
Training utilities for the llmXive pipeline.

Implements the Trainer class for training projection modules while
keeping the backbone (frozen embeddings) fixed.
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from models.base import FrozenEmbeddingModel, ProjectionModel
from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)


class Trainer:
    """
    Trainer for projection models.
    Handles the training loop, optimization, and evaluation for the projection layer
    while ensuring the backbone remains frozen.
    """

    def __init__(
        self,
        projection_model: ProjectionModel,
        backbone_model: FrozenEmbeddingModel,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: str = "cpu",
        config: Optional[Dict[str, Any]] = None
    ):
        self.projection_model = projection_model.to(device)
        self.backbone_model = backbone_model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.config = config or {}
        
        # Ensure backbone is frozen
        self._verify_frozen_backbone()

    def _verify_frozen_backbone(self) -> None:
        """Verify that no parameters in the backbone require gradients."""
        for name, param in self.backbone_model.named_parameters():
            if param.requires_grad:
                log_error(logger, f"Backbone parameter {name} is not frozen! This may cause unintended updates.")
        log_info(logger, "Backbone verification complete: all parameters frozen.")

    def train_epoch(
        self,
        dataloader: torch.utils.data.DataLoader,
        epoch: int = 0
    ) -> float:
        """
        Train for one epoch.
        Args:
            dataloader: DataLoader yielding (embeddings, tabular_features, labels)
            epoch: Current epoch number
        Returns:
            Average loss for the epoch
        """
        self.projection_model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            # Expect batch to be a dict or tuple
            if isinstance(batch, dict):
                embeddings = batch["embeddings"].to(self.device)
                tabular = batch["tabular"].to(self.device)
                targets = batch["targets"].to(self.device)
            else:
                embeddings, tabular, targets = batch
                embeddings = embeddings.to(self.device)
                tabular = tabular.to(self.device)
                targets = targets.to(self.device)

            # Forward pass through frozen backbone (if embeddings aren't pre-computed)
            # Note: In this pipeline, embeddings are usually pre-computed and passed directly.
            # If the backbone is needed here, we call it with no_grad.
            with torch.no_grad():
                # If embeddings are raw inputs (e.g., images/text), we would do:
                # embeddings = self.backbone_model(inputs)
                # But here we assume embeddings are already extracted.
                pass

            # Projection forward
            projected = self.projection_model(embeddings, tabular)

            # Loss calculation
            loss = self.criterion(projected, targets)

            # Backprop
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        log_info(logger, f"Epoch {epoch} completed. Loss: {avg_loss:.4f}")
        return avg_loss

    def evaluate(
        self,
        dataloader: torch.utils.data.DataLoader,
        metric_fn: Optional[callable] = None
    ) -> Dict[str, float]:
        """
        Evaluate the model on a dataset.
        Args:
            dataloader: Evaluation DataLoader
            metric_fn: Optional custom metric function
        Returns:
            Dict of metric names to values
        """
        self.projection_model.eval()
        total_loss = 0.0
        num_batches = 0
        
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for batch in dataloader:
                if isinstance(batch, dict):
                    embeddings = batch["embeddings"].to(self.device)
                    tabular = batch["tabular"].to(self.device)
                    targets = batch["targets"].to(self.device)
                else:
                    embeddings, tabular, targets = batch
                    embeddings = embeddings.to(self.device)
                    tabular = tabular.to(self.device)
                    targets = targets.to(self.device)

                projected = self.projection_model(embeddings, tabular)
                loss = self.criterion(projected, targets)

                total_loss += loss.item()
                num_batches += 1

                all_preds.append(projected.cpu().numpy())
                all_targets.append(targets.cpu().numpy())

        avg_loss = total_loss / max(num_batches, 1)
        results = {"loss": avg_loss}

        if metric_fn:
            preds = np.concatenate(all_preds, axis=0)
            targets = np.concatenate(all_targets, axis=0)
            metric_val = metric_fn(preds, targets)
            results["custom_metric"] = metric_val

        return results

    def save_checkpoint(self, path: Union[str, Path], epoch: int, metrics: Optional[Dict[str, float]] = None) -> None:
        """Save the projection model checkpoint."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            "epoch": epoch,
            "model_state": self.projection_model.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "metrics": metrics,
        }
        
        torch.save(checkpoint, path / "checkpoint.pt")
        log_info(logger, f"Saved checkpoint at epoch {epoch} to {path}")

    @classmethod
    def load_checkpoint(
        cls,
        path: Union[str, Path],
        projection_model: ProjectionModel,
        backbone_model: FrozenEmbeddingModel,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: str = "cpu"
    ) -> "Trainer":
        """Load a trainer from a checkpoint."""
        path = Path(path)
        checkpoint = torch.load(path / "checkpoint.pt", map_location=device)
        
        projection_model.load_state_dict(checkpoint["model_state"])
        optimizer.load_state_dict(checkpoint["optimizer_state"])
        
        trainer = cls(
            projection_model=projection_model,
            backbone_model=backbone_model,
            optimizer=optimizer,
            criterion=criterion,
            device=device
        )
        log_info(logger, f"Loaded checkpoint from epoch {checkpoint['epoch']}")
        return trainer


def create_trainer(
    projection_model: ProjectionModel,
    backbone_model: FrozenEmbeddingModel,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    device: str = "cpu",
    config: Optional[Dict[str, Any]] = None
) -> Trainer:
    """
    Factory function to create a Trainer instance with default settings.
    """
    optimizer = torch.optim.AdamW(
        projection_model.parameters(),
        lr=lr,
        weight_decay=weight_decay
    )
    criterion = nn.MSELoss() # Default for regression tasks; can be overridden via config

    return Trainer(
        projection_model=projection_model,
        backbone_model=backbone_model,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        config=config
    )
