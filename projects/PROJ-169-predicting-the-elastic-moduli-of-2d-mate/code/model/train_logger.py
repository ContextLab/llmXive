"""Training logger module with scientific integrity disclaimers."""
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
    """Entry for a single training log record."""
    epoch: int
    loss: float
    metrics: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    disclaimer: str = field(default_factory=lambda: DISCLAIMER_TEXT + "\n\n" + FEYNMAN_QUOTE)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

@dataclass
class TrainingLogMetadata:
    """Metadata for the training log file."""
    run_id: str
    model_architecture: str
    dataset_path: str
    split_path: str
    hyperparameters: Dict[str, Any]
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    disclaimer: str = field(default_factory=lambda: DISCLAIMER_TEXT + "\n\n" + FEYNMAN_QUOTE)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

class TrainingLogger:
    """Logger that writes training logs with mandatory disclaimers."""

    def __init__(self, output_path: str, metadata: TrainingLogMetadata):
        self.output_path = Path(output_path)
        self.metadata = metadata
        self.entries: List[TrainingLogEntry] = []
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def log_epoch(self, epoch: int, loss: float, metrics: Dict[str, float]):
        """Log a single epoch's results."""
        entry = TrainingLogEntry(
            epoch=epoch,
            loss=loss,
            metrics=metrics
        )
        self.entries.append(entry)

    def save(self):
        """Save all logs to the output file."""
        log_data = {
            "metadata": asdict(self.metadata),
            "epochs": [asdict(e) for e in self.entries]
        }
        with open(self.output_path, "w") as f:
            json.dump(log_data, f, indent=2)

@log_operation
def run_training_with_logging(
    epochs: int,
    model: Any,
    train_loader: Any,
    val_loader: Any,
    optimizer: Any,
    device: str,
    output_log_path: str,
    hyperparameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Run training with logging and mandatory disclaimers."""
    config = get_config()
    run_id = f"run_{int(time.time())}"
    metadata = TrainingLogMetadata(
        run_id=run_id,
        model_architecture="LightweightGNN",
        dataset_path=str(config.paths.get("processed_data", "data/processed")),
        split_path=str(config.paths.get("split_indices", "data/processed/split_indices.json")),
        hyperparameters=hyperparameters
    )
    logger = TrainingLogger(output_log_path, metadata)

    best_val_loss = float("inf")
    patience_counter = 0
    patience = hyperparameters.get("patience", 5)

    for epoch in range(epochs):
        start = time.time()
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            # Forward pass
            out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            loss = model.criterion(out, batch.y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
                loss = model.criterion(out, batch.y)
                val_loss += loss.item()
        val_loss /= len(val_loader)

        metrics = {"val_loss": val_loss, "train_loss": avg_loss}
        logger.log_epoch(epoch, avg_loss, metrics)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= patience:
            break

    logger.save()
    return {"best_val_loss": best_val_loss, "epochs_run": epoch + 1}

def main():
    """CLI entry point for training logger."""
    parser = argparse.ArgumentParser(description="Train GNN with logging")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--output-log", type=str, default="data/results/training_logs.json", help="Output log path")
    parser.add_argument("--output-model", type=str, default="data/processed/model_v1.pt", help="Output model path")
    parser.add_argument("--output-predictions", type=str, default="data/results/predictions.json", help="Output predictions path")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use")

    args = parser.parse_args()

    # Mock training for demonstration if real data not available
    # In a real run, this would load data and train the model
    hyperparameters = {
        "epochs": args.epochs,
        "patience": args.patience,
        "device": args.device
    }

    # NOTE: This is a placeholder for the actual training logic.
    # The real training would load data, initialize model, and run the loop.
    # The disclaimer is injected into the log file regardless.
    run_training_with_logging(
        epochs=min(args.epochs, 3),  # Limit for demo if no real data
        model=None,  # Placeholder
        train_loader=[],
        val_loader=[],
        optimizer=None,
        device=args.device,
        output_log_path=args.output_log,
        hyperparameters=hyperparameters
    )
    print(f"Training logs written to {args.output_log}")

if __name__ == "__main__":
    main()
