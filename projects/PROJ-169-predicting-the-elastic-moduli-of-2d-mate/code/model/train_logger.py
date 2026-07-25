"""Training logger with mandatory surrogate model disclaimers."""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any

# Import existing project utilities
from utils.config import get_config
from utils.logger import get_logger, log_operation, LogEntry

# ============================================================================
# SCIENTIFIC INTEGRITY DISCLAIMER (T046 Requirement)
# ============================================================================
SURROGATE_DISCLAIMER = (
    "These results are derived from a machine learning surrogate model "
    "interpolating pre-computed DFT data. They do not represent "
    "first-principles calculations or solutions to the Schrödinger equation."
)

FEYNMAN_QUOTE = (
    "The first principle is that you must not fool yourself — and you are "
    "the easiest person to fool."
)

SCIENTIFIC_INTEGRITY_STATEMENT = (
    f"Scientific Integrity Statement:\n"
    f"{FEYNMAN_QUOTE}\n\n"
    f"{SURROGATE_DISCLAIMER}"
)
# ============================================================================

@dataclass
class TrainingLogEntry:
    """Structured log entry for training events."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    epoch: Optional[int] = None
    phase: Optional[str] = None  # 'train', 'val', 'test'
    loss: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    memory_peak_mb: Optional[float] = None
    batch_size: Optional[int] = None
    learning_rate: Optional[float] = None
    # T046: Add disclaimer field to metadata
    disclaimer: str = SURROGATE_DISCLAIMER

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

@dataclass
class TrainingLogMetadata:
    """Metadata for the training run, including the mandatory disclaimer."""
    run_id: str
    model_architecture: str
    dataset_path: str
    split_path: str
    hyperparameters: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    # T046: Mandatory disclaimer in metadata
    disclaimer: str = SURROGATE_DISCLAIMER
    scientific_integrity: str = SCIENTIFIC_INTEGRITY_STATEMENT

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

class TrainingLogger:
    """Logger that writes training metrics to JSON with disclaimers."""

    def __init__(self, output_log_path: str):
        self.output_log_path = output_log_path
        self.logger = get_logger("training")
        self.entries: list[TrainingLogEntry] = []
        self.metadata: Optional[TrainingLogMetadata] = None

    def set_metadata(self, metadata: TrainingLogMetadata) -> None:
        self.metadata = metadata

    def log_epoch(self, epoch: int, phase: str, loss: float, metrics: Dict[str, float],
                  memory_peak_mb: float, batch_size: int, learning_rate: float) -> None:
        entry = TrainingLogEntry(
            epoch=epoch,
            phase=phase,
            loss=loss,
            metrics=metrics,
            memory_peak_mb=memory_peak_mb,
            batch_size=batch_size,
            learning_rate=learning_rate
        )
        self.entries.append(entry)
        # Log to stdout/stderr as well
        self.logger.log("training_epoch", entry=entry.to_json())

    def save(self) -> None:
        """Save all logs and metadata to the output file."""
        if not self.metadata:
            raise RuntimeError("Metadata not set. Call set_metadata() before save().")

        log_data = {
            "metadata": json.loads(self.metadata.to_json()),
            "entries": [json.loads(e.to_json()) for e in self.entries]
        }

        os.makedirs(os.path.dirname(self.output_log_path), exist_ok=True)
        with open(self.output_log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)

        log_operation("training_logs_saved", path=self.output_log_path)

def run_training_with_logging(
    epochs: int,
    model: Any,
    train_loader: Any,
    val_loader: Any,
    output_log_path: str,
    device: str = "cpu"
) -> TrainingLogger:
    """
    Wrapper to run a mock training loop with logging.
    In a real implementation, this would call the actual training loop.
    For T046, we ensure the logger structure includes the disclaimer.
    """
    logger = TrainingLogger(output_log_path)

    # Mock metadata for demonstration of the disclaimer injection
    config = get_config()
    metadata = TrainingLogMetadata(
        run_id="mock_run_t046",
        model_architecture="LightweightGNN",
        dataset_path=str(config.paths.get("data_processed", "data/processed")),
        split_path=str(config.paths.get("split_indices", "data/processed/split_indices.json")),
        hyperparameters={"epochs": epochs, "device": device}
    )
    logger.set_metadata(metadata)

    # Simulate a few epochs to demonstrate logging structure
    for epoch in range(min(epochs, 3)):
        # Mock metrics
        mock_loss = 0.5 * (0.9 ** epoch)
        mock_metrics = {"mape": mock_loss * 100, "rmse": mock_loss * 5}
        logger.log_epoch(
            epoch=epoch + 1,
            phase="train",
            loss=mock_loss,
            metrics=mock_metrics,
            memory_peak_mb=100.0,
            batch_size=32,
            learning_rate=0.001
        )

    logger.save()
    return logger

def main():
    parser = argparse.ArgumentParser(description="Training Logger with Disclaimers")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--output-log", type=str, default="data/results/training_logs.json",
                        help="Output path for training logs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger = run_training_with_logging(
        epochs=args.epochs,
        model=None,  # Mock model
        train_loader=None,
        val_loader=None,
        output_log_path=args.output_log
    )
    print(f"Training logs saved to {args.output_log}")
    # Verify disclaimer is present
    with open(args.output_log, 'r') as f:
        data = json.load(f)
        assert "disclaimer" in data["metadata"], "Disclaimer missing from metadata"
        print("Disclaimer verified in output.")

if __name__ == "__main__":
    main()
