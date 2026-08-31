"""Training logger with scientific integrity disclaimers."""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_config
from utils.logger import log_operation
from utils.disclaimer_template import DISCLAIMER_TEXT, FEYNMAN_QUOTE

@dataclass
class TrainingLogEntry:
    """Structured log entry for training events."""
    epoch: int = 0
    loss: float = 0.0
    metric: str = ""
    value: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TrainingLogMetadata:
    """Metadata for the training run."""
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    total_epochs: int = 0
    final_loss: float = 0.0
    best_epoch: int = 0
    best_loss: float = float('inf')
    disclaimer_injected: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class TrainingLogger:
    """Logger that enforces scientific integrity disclaimers."""

    def __init__(self, log_path: str = "data/results/training_logs.json"):
        self.log_path = log_path
        self.entries: List[TrainingLogEntry] = []
        self.metadata = TrainingLogMetadata()
        self._ensure_dir()

    def _ensure_dir(self):
        """Ensure the log directory exists."""
        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)

    def log_epoch(self, epoch: int, loss: float, metric: str = "loss", value: float = 0.0, **kwargs):
        """Log a training epoch."""
        entry = TrainingLogEntry(
            epoch=epoch,
            loss=loss,
            metric=metric,
            value=value,
            metadata=kwargs
        )
        self.entries.append(entry)
        if loss < self.metadata.best_loss:
            self.metadata.best_loss = loss
            self.metadata.best_epoch = epoch
        self.metadata.total_epochs = epoch

    def finalize(self, final_loss: float):
        """Finalize the training log."""
        self.metadata.end_time = datetime.utcnow().isoformat()
        self.metadata.final_loss = final_loss
        self._write_log()

    def _write_log(self):
        """Write the log to disk with disclaimers."""
        log_data = {
            "metadata": self.metadata.to_dict(),
            "entries": [e.to_dict() for e in self.entries],
            "scientific_integrity": {
                "statement": DISCLAIMER_TEXT,
                "feynman_quote": FEYNMAN_QUOTE,
                "injected_at": datetime.utcnow().isoformat()
            }
        }
        with open(self.log_path, "w") as f:
            json.dump(log_data, f, indent=2)

@log_operation
def run_training_with_logging(
    model: Any,
    train_loader: Any,
    val_loader: Any,
    epochs: int,
    lr: float,
    patience: int,
    device: str = "cpu"
) -> Dict[str, Any]:
    """Run a training loop with automatic logging and disclaimers.

    This wrapper ensures that every training run produces a log file that
    explicitly includes the Scientific Integrity Statement and Feynman quote,
    satisfying the project's requirement to distinguish between interpolation
    and first-principles physics.
    """
    logger = TrainingLogger(log_path="data/results/training_logs.json")
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=patience // 2)

    best_loss = float('inf')
    patience_counter = 0

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            # Assume batch has 'x', 'edge_index', 'y'
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = criterion(out, batch.y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                out = model(batch.x, batch.edge_index, batch.batch)
                val_loss += criterion(out, batch.y).item()
        val_loss /= len(val_loader)

        logger.log_epoch(epoch, avg_loss, "val_loss", val_loss)
        scheduler.step(val_loss)

        if val_loss < best_loss:
            best_loss = val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), "data/processed/model_v1.pt")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    logger.finalize(best_loss)
    return {
        "status": "completed",
        "best_loss": best_loss,
        "epochs_run": epoch + 1,
        "log_path": logger.log_path,
        "disclaimer": DISCLAIMER_TEXT + "\n\n" + FEYNMAN_QUOTE
    }

def main():
    """CLI entry point for training logger demo (for testing)."""
    parser = argparse.ArgumentParser(description="Test training logger")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    args = parser.parse_args()

    # This is a stub for testing the logger structure; real training
    # is handled by train.py which calls run_training_with_logging.
    logger = TrainingLogger(log_path="data/results/training_logs.json")
    for i in range(args.epochs):
        logger.log_epoch(i, 1.0 / (i + 1), "loss", 1.0 / (i + 1))
    logger.finalize(0.1)
    print(f"Training log written to {logger.log_path}")
    print(f"Disclaimer included: {DISCLAIMER_TEXT[:50]}...")

if __name__ == "__main__":
    main()
