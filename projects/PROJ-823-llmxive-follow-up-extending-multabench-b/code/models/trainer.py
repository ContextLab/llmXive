import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from models.base import FrozenEmbeddingModel, ProjectionModel
from utils.logging import get_logger, log_info, log_error, log_debug
from utils.memory_monitor import get_process_memory_mb, memory_limit_context
from config import get_config

logger = get_logger(__name__)

class Trainer:
    """
    Trainer for the tabular-conditioned projection model.
    
    This trainer freezes the backbone (frozen embedding model) and only
    updates the projection layer weights during training.
    """

    def __init__(
        self,
        backbone: FrozenEmbeddingModel,
        projection: ProjectionModel,
        device: str = "cpu",
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        max_memory_gb: float = 6.0,
    ):
        """
        Initialize the trainer.
        
        Args:
            backbone: The frozen embedding model (weights will be frozen).
            projection: The projection model to train.
            device: Device to run training on (default: "cpu").
            learning_rate: Learning rate for the optimizer.
            weight_decay: Weight decay for regularization.
            max_memory_gb: Maximum memory usage in GB before stopping.
        """
        self.backbone = backbone
        self.projection = projection
        self.device = device
        self.max_memory_gb = max_memory_gb
        
        # Freeze backbone parameters
        for param in self.backbone.parameters():
            param.requires_grad = False
        
        # Ensure projection parameters are trainable
        for param in self.projection.parameters():
            param.requires_grad = True

        # Move models to device
        self.backbone.to(device)
        self.projection.to(device)

        # Setup optimizer (only for projection parameters)
        self.optimizer = torch.optim.Adam(
            self.projection.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        
        # Loss function
        self.criterion = nn.MSELoss()
        
        log_info(logger, f"Trainer initialized on {device}", extra={"backbone_type": type(backbone).__name__, "projection_type": type(projection).__name__})

    def train_epoch(
        self,
        dataloader: torch.utils.data.DataLoader,
        epoch: int,
    ) -> Dict[str, float]:
        """
        Train for one epoch.
        
        Args:
            dataloader: DataLoader for the training data.
            epoch: Current epoch number (for logging).
            
        Returns:
            Dictionary containing training metrics.
        """
        self.projection.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch in enumerate(dataloader):
            # Check memory usage
            current_mem_gb = get_process_memory_mb() / 1024.0
            if current_mem_gb > self.max_memory_gb:
                log_error(
                    logger,
                    f"Memory limit exceeded: {current_mem_gb:.2f}GB > {self.max_memory_gb}GB",
                    extra={"epoch": epoch, "batch": batch_idx}
                )
                break
            
            # Extract batch data
            # Expected keys: 'frozen_embeddings', 'tabular_features', 'labels'
            frozen_embeddings = batch['frozen_embeddings'].to(self.device)
            tabular_features = batch['tabular_features'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass
            with torch.no_grad():
                # Ensure backbone is in eval mode and no gradients
                self.backbone.eval()
                backbone_outputs = self.backbone(frozen_embeddings)
                
            # Projection forward pass (trainable)
            projections = self.projection(backbone_outputs, tabular_features)
            
            # Compute loss
            loss = self.criterion(projections, labels)
            
            # Backward pass
            loss.backward()
            
            # Clip gradients to prevent explosion
            torch.nn.utils.clip_grad_norm_(self.projection.parameters(), max_norm=1.0)
            
            # Optimizer step
            self.optimizer.step()
            
            # Accumulate metrics
            total_loss += loss.item()
            num_batches += 1
            
            if batch_idx % 10 == 0:
                log_debug(
                    logger,
                    f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}",
                    extra={"epoch": epoch, "batch": batch_idx, "loss": loss.item()}
                )
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        
        log_info(
            logger,
            f"Epoch {epoch} completed, Average Loss: {avg_loss:.4f}",
            extra={"epoch": epoch, "avg_loss": avg_loss, "num_batches": num_batches}
        )
        
        return {"loss": avg_loss}

    def validate(
        self,
        dataloader: torch.utils.data.DataLoader,
    ) -> Dict[str, float]:
        """
        Validate the model on a dataset.
        
        Args:
            dataloader: DataLoader for validation data.
            
        Returns:
            Dictionary containing validation metrics.
        """
        self.projection.eval()
        total_loss = 0.0
        num_batches = 0
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for batch in dataloader:
                frozen_embeddings = batch['frozen_embeddings'].to(self.device)
                tabular_features = batch['tabular_features'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                backbone_outputs = self.backbone(frozen_embeddings)
                projections = self.projection(backbone_outputs, tabular_features)
                
                loss = self.criterion(projections, labels)
                
                total_loss += loss.item()
                num_batches += 1
                
                all_predictions.append(projections.cpu().numpy())
                all_labels.append(labels.cpu().numpy())
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        
        # Concatenate all predictions and labels
        all_predictions = np.concatenate(all_predictions, axis=0)
        all_labels = np.concatenate(all_labels, axis=0)
        
        # Compute additional metrics
        rmse = np.sqrt(np.mean((all_predictions - all_labels) ** 2))
        mae = np.mean(np.abs(all_predictions - all_labels))
        
        metrics = {
            "loss": avg_loss,
            "rmse": rmse,
            "mae": mae,
        }
        
        log_info(
            logger,
            f"Validation completed, Loss: {avg_loss:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}",
            extra={"loss": avg_loss, "rmse": rmse, "mae": mae}
        )
        
        return metrics

    def fit(
        self,
        train_dataloader: torch.utils.data.DataLoader,
        val_dataloader: torch.utils.data.DataLoader,
        num_epochs: int = 10,
        patience: int = 3,
        save_path: Optional[Path] = None,
    ) -> Dict[str, List[Dict[str, float]]]:
        """
        Train the projection model for multiple epochs.
        
        Args:
            train_dataloader: DataLoader for training data.
            val_dataloader: DataLoader for validation data.
            num_epochs: Number of epochs to train.
            patience: Early stopping patience.
            save_path: Path to save the best model.
            
        Returns:
            Dictionary containing training history.
        """
        best_val_loss = float('inf')
        patience_counter = 0
        history = {"train": [], "val": []}
        
        log_info(
            logger,
            f"Starting training for {num_epochs} epochs",
            extra={"num_epochs": num_epochs}
        )
        
        for epoch in range(num_epochs):
            # Train
            train_metrics = self.train_epoch(train_dataloader, epoch)
            history["train"].append(train_metrics)
            
            # Validate
            val_metrics = self.validate(val_dataloader)
            history["val"].append(val_metrics)
            
            # Early stopping check
            if val_metrics["loss"] < best_val_loss:
                best_val_loss = val_metrics["loss"]
                patience_counter = 0
                
                if save_path:
                    self.save(save_path)
                    log_info(
                        logger,
                        f"Saved best model to {save_path}",
                        extra={"path": str(save_path), "val_loss": best_val_loss}
                    )
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    log_info(
                        logger,
                        f"Early stopping triggered at epoch {epoch}",
                        extra={"epoch": epoch, "patience": patience}
                    )
                    break
        
        log_info(
            logger,
            f"Training completed. Best val loss: {best_val_loss:.4f}",
            extra={"best_val_loss": best_val_loss}
        )
        
        return history

    def save(self, path: Path) -> None:
        """
        Save the projection model state.
        
        Args:
            path: Path to save the model.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save(
            {
                "projection_state_dict": self.projection.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "device": self.device,
            },
            path
        )
        
        log_info(logger, f"Model saved to {path}", extra={"path": str(path)})

    def load(self, path: Path) -> None:
        """
        Load the projection model state.
        
        Args:
            path: Path to load the model from.
        """
        path = Path(path)
        
        checkpoint = torch.load(path, map_location=self.device)
        self.projection.load_state_dict(checkpoint["projection_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        
        log_info(logger, f"Model loaded from {path}", extra={"path": str(path)})

def create_trainer(
    backbone: FrozenEmbeddingModel,
    projection: ProjectionModel,
    config: Optional[Dict[str, Any]] = None,
) -> Trainer:
    """
    Factory function to create a Trainer instance.
    
    Args:
        backbone: The frozen embedding model.
        projection: The projection model.
        config: Optional configuration dictionary.
            
    Returns:
        A configured Trainer instance.
    """
    if config is None:
        config = get_config()
    
    return Trainer(
        backbone=backbone,
        projection=projection,
        device=config.get("device", "cpu"),
        learning_rate=config.get("learning_rate", 1e-3),
        weight_decay=config.get("weight_decay", 1e-4),
        max_memory_gb=config.get("max_memory_gb", 6.0),
    )