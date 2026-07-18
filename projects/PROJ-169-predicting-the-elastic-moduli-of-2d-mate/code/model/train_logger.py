"""
Training logging and checkpointing module for the Surrogate Model.

This module implements the logging infrastructure required by T018c,
ensuring that all training metrics are recorded with the required schema
and disclaimers.
"""
import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field

import torch
import torch.nn as nn
from torch_geometric.data import Batch

from model.gnn import LightweightGNN
from model.train_config import TrainingConfig
from utils.logger import get_logger, log_training_metrics

# Required disclaimer constant
DISCLAIMER = "These results are ML interpolations of DFT data, not first-principles solutions."


@dataclass
class TrainingLogEntry:
    """Schema for a single training log entry as required by T018c."""
    epoch: int
    loss: float
    metrics: Dict[str, float]
    memory_peak: float
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    disclaimer: str = DISCLAIMER


class TrainingLogger:
    """
    Handles logging of training metrics to JSON and manages checkpoints.

    This class satisfies T018c requirements:
    - Logs schema includes: epoch, loss, metrics (mape, rmse), memory_peak
    - Includes metadata key 'disclaimer'
    - Writes to data/results/training_logs.json
    """

    def __init__(self, output_path: str, config: Optional[TrainingConfig] = None):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.logs: List[TrainingLogEntry] = []
        self.logger = get_logger(__name__)
        self.best_loss = float('inf')
        self.best_epoch = -1
        self.checkpoint_path = Path("data/processed/model_v1.pt")

    def log_epoch(self, epoch: int, loss: float, metrics: Dict[str, float], memory_peak: float):
        """
        Log metrics for a single epoch.

        Args:
            epoch: Current epoch number (int)
            loss: Training loss (float)
            metrics: Dict containing 'mape' and 'rmse' (float)
            memory_peak: Peak memory usage in GB (float)
        """
        entry = TrainingLogEntry(
            epoch=epoch,
            loss=loss,
            metrics=metrics,
            memory_peak=memory_peak
        )
        self.logs.append(entry)
        
        # Log to structured logger as well
        log_training_metrics(
            epoch=epoch,
            loss=loss,
            mape=metrics.get('mape', 0.0),
            rmse=metrics.get('rmse', 0.0),
            memory_peak=memory_peak
        )

        self.logger.info(
            f"Epoch {epoch}: loss={loss:.4f}, MAPE={metrics.get('mape', 0.0):.4f}, "
            f"RMSE={metrics.get('rmse', 0.0):.4f}, Memory={memory_peak:.2f}GB"
        )

    def save_logs(self):
        """
        Save all logged entries to the output JSON file.

        The output schema includes:
        - logs: List of TrainingLogEntry objects
        - metadata: Dict with disclaimer
        """
        output_data = {
            "logs": [asdict(log) for log in self.logs],
            "metadata": {
                "disclaimer": DISCLAIMER,
                "total_epochs": len(self.logs),
                "best_epoch": self.best_epoch,
                "best_loss": self.best_loss if self.best_epoch >= 0 else None
            }
        }

        with open(self.output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        self.logger.info(f"Training logs saved to {self.output_path}")

    def save_checkpoint(self, model: nn.Module, epoch: int, loss: float, is_best: bool = False):
        """
        Save model checkpoint.

        Args:
            model: The trained model
            epoch: Current epoch
            loss: Current loss
            is_best: If True, save as best model
        """
        checkpoint = {
            'epoch': epoch,
            'loss': loss,
            'model_state_dict': model.state_dict(),
            'disclaimer': DISCLAIMER
        }

        # Save latest checkpoint
        torch.save(checkpoint, self.checkpoint_path)
        
        if is_best and loss < self.best_loss:
            self.best_loss = loss
            self.best_epoch = epoch
            best_path = self.checkpoint_path.with_name("best_model.pt")
            torch.save(checkpoint, best_path)
            self.logger.info(f"New best model saved at epoch {epoch} with loss {loss:.4f}")

    def load_checkpoint(self, model: nn.Module, checkpoint_path: Optional[str] = None) -> bool:
        """
        Load model from checkpoint if available.

        Returns:
            True if checkpoint was loaded, False otherwise
        """
        path = Path(checkpoint_path) if checkpoint_path else self.checkpoint_path
        
        if path.exists():
            checkpoint = torch.load(path, map_location='cpu')
            model.load_state_dict(checkpoint['model_state_dict'])
            self.logger.info(f"Loaded checkpoint from {path} (epoch {checkpoint.get('epoch', 'unknown')})")
            return True
        
        return False


def run_training_with_logging(
    model: LightweightGNN,
    train_loader,
    val_loader,
    config: TrainingConfig,
    logger: TrainingLogger
) -> LightweightGNN:
    """
    Run training loop with full logging and checkpointing.

    This function implements the core training logic with:
    - Per-epoch logging of loss, metrics, and memory
    - Early stopping based on validation loss
    - Best model checkpointing
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=True
    )

    patience = config.patience
    patience_counter = 0
    best_val_loss = float('inf')

    model.train()
    
    for epoch in range(config.epochs):
        # Training phase
        epoch_loss = 0.0
        model.train()
        
        for batch in train_loader:
            optimizer.zero_grad()
            output = model(batch)
            loss = nn.MSELoss()(output, batch.y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_train_loss = epoch_loss / len(train_loader)

        # Validation phase
        model.eval()
        val_losses = []
        val_mapes = []
        val_rmses = []
        
        with torch.no_grad():
            for batch in val_loader:
                output = model(batch)
                val_loss = nn.MSELoss()(output, batch.y)
                val_losses.append(val_loss.item())
                
                # Calculate metrics
                y_true = batch.y.cpu().numpy()
                y_pred = output.cpu().numpy()
                
                mape = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100
                rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
                
                val_mapes.append(mape)
                val_rmses.append(rmse)

        avg_val_loss = np.mean(val_losses)
        avg_val_mape = np.mean(val_mapes)
        avg_val_rmse = np.mean(val_rmses)

        # Memory check (using tracemalloc if available)
        try:
            import tracemalloc
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                memory_peak_gb = peak / 1024 / 1024 / 1024
            else:
                memory_peak_gb = 0.0
        except Exception:
            memory_peak_gb = 0.0

        # Log epoch
        logger.log_epoch(
            epoch=epoch,
            loss=avg_train_loss,
            metrics={'mape': avg_val_mape, 'rmse': avg_val_rmse},
            memory_peak=memory_peak_gb
        )

        # Learning rate scheduling
        scheduler.step(avg_val_loss)

        # Early stopping check
        is_best = avg_val_loss < best_val_loss
        if is_best:
            best_val_loss = avg_val_loss
            patience_counter = 0
            logger.save_checkpoint(model, epoch, avg_val_loss, is_best=True)
        else:
            patience_counter += 1
            logger.save_checkpoint(model, epoch, avg_val_loss, is_best=False)

        if patience_counter >= patience:
            logger.logger.info(f"Early stopping at epoch {epoch}")
            break

    # Save final logs
    logger.save_logs()
    
    return model


def main():
    """
    Standalone entry point for testing the logger.
    
    This function creates a mock training log to verify the schema
    and output format required by T018c.
    """
    import numpy as np
    
    logger_instance = TrainingLogger("data/results/training_logs.json")
    
    # Simulate a few epochs
    for epoch in range(5):
        loss = 1.0 / (epoch + 1)
        mape = 10.0 / (epoch + 1)
        rmse = 0.5 / (epoch + 1)
        memory = 2.0 + epoch * 0.1
        
        logger_instance.log_epoch(
            epoch=epoch,
            loss=loss,
            metrics={'mape': mape, 'rmse': rmse},
            memory_peak=memory
        )
    
    logger_instance.save_logs()
    print(f"Mock training logs written to data/results/training_logs.json")
    
    # Verify output
    with open("data/results/training_logs.json", 'r') as f:
        data = json.load(f)
        print(f"Logs count: {len(data['logs'])}")
        print(f"Metadata disclaimer: {data['metadata']['disclaimer']}")
        print(f"First log entry: {data['logs'][0]}")


if __name__ == "__main__":
    main()