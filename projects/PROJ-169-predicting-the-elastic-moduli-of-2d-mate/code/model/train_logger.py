"""Training logging and checkpointing for the surrogate model.

This module implements the logging infrastructure for training runs,
ensuring all metrics are recorded with the mandatory disclaimers
required by the Feynman Review Response (Phase 9/10).

It writes logs to `data/results/training_logs.json` with the schema:
{
  "epoch": int,
  "loss": float,
  "metrics": {"mape": float, "rmse": float},
  "memory_peak": float,
  "disclaimer": "..."
}
"""
from __future__ import annotations

import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import torch
import psutil

# Import the project's logger utility
from utils.logger import get_logger, log_operation

# Configure standard logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class TrainingLogEntry:
    """Represents a single log entry for a training epoch."""

    def __init__(
        self,
        epoch: int,
        loss: float,
        metrics: Dict[str, float],
        memory_peak: float,
        disclaimer: str
    ) -> None:
        self.epoch = epoch
        self.loss = loss
        self.metrics = metrics
        self.memory_peak = memory_peak
        self.disclaimer = disclaimer

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "loss": self.loss,
            "metrics": self.metrics,
            "memory_peak": self.memory_peak,
            "disclaimer": self.disclaimer
        }


class TrainingLogger:
    """Manages the lifecycle of training logs and checkpointing."""

    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs: List[TrainingLogEntry] = []
        self.start_time = time.time()
        logger.info(f"Initialized TrainingLogger for {self.output_path}")

    def log_epoch(
        self,
        epoch: int,
        loss: float,
        metrics: Dict[str, float],
        memory_peak: float
    ) -> None:
        """Records an epoch's metrics."""
        disclaimer = (
            "These results are ML interpolations of DFT data, "
            "not first-principles solutions."
        )
        entry = TrainingLogEntry(
            epoch=epoch,
            loss=loss,
            metrics=metrics,
            memory_peak=memory_peak,
            disclaimer=disclaimer
        )
        self.logs.append(entry)
        logger.info(
            f"Epoch {epoch}: Loss={loss:.4f}, MAPE={metrics.get('mape', 0):.2f}%, "
            f"RMSE={metrics.get('rmse', 0):.4f}, Mem={memory_peak:.2f}GB"
        )

    def save(self) -> None:
        """Writes all accumulated logs to the output file."""
        log_data = [entry.to_dict() for entry in self.logs]
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        logger.info(f"Training logs saved to {self.output_path}")

    def get_logs(self) -> List[Dict[str, Any]]:
        return [entry.to_dict() for entry in self.logs]


@log_operation("run_training_with_logging")
def run_training_with_logging(
    model: torch.nn.Module,
    train_loader: torch.utils.data.DataLoader,
    val_loader: Optional[torch.utils.data.DataLoader] = None,
    epochs: int = 100,
    lr: float = 0.001,
    output_log_path: str = "data/results/training_logs.json"
) -> TrainingLogger:
    """
    Executes a training loop with logging and checkpointing.

    This function is designed to be called by the main training script (T018b)
    to ensure all metrics are captured and written to disk.
    """
    logger.info(f"Starting training for {epochs} epochs")
    logger = TrainingLogger(output_log_path)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.MSELoss()

    device = torch.device("cpu")
    model = model.to(device)

    # Use tracemalloc for memory tracking
    tracemalloc.start()

    try:
        for epoch in range(1, epochs + 1):
            model.train()
            epoch_loss = 0.0
            current_memory_peak = 0.0

            # Training Epoch
            for batch in train_loader:
                optimizer.zero_grad()
                # Assuming batch has 'x', 'edge_index', 'y' as per standard PyG
                x = batch.x.to(device)
                edge_index = batch.edge_index.to(device)
                y = batch.y.to(device)

                out = model(x, edge_index)
                loss = criterion(out, y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

                # Track memory
                current, peak = tracemalloc.get_traced_memory()
                peak_gb = peak / 1024**3
                if peak_gb > current_memory_peak:
                    current_memory_peak = peak_gb

            avg_loss = epoch_loss / len(train_loader)

            # Validation (Optional but good for logging)
            val_metrics = {"mape": 0.0, "rmse": 0.0}
            if val_loader:
                model.eval()
                val_loss = 0.0
                all_preds = []
                all_targets = []
                with torch.no_grad():
                    for batch in val_loader:
                        x = batch.x.to(device)
                        edge_index = batch.edge_index.to(device)
                        y = batch.y.to(device)
                        out = model(x, edge_index)
                        val_loss += torch.nn.functional.mse_loss(out, y).item()
                        all_preds.extend(out.cpu().numpy().tolist())
                        all_targets.extend(y.cpu().numpy().tolist())

                # Calculate MAPE and RMSE
                import numpy as np
                preds = np.array(all_preds)
                targets = np.array(all_targets)

                # Avoid division by zero for MAPE
                mask = targets != 0
                if np.any(mask):
                    mape = np.mean(np.abs((targets[mask] - preds[mask]) / targets[mask])) * 100
                else:
                    mape = 0.0
                
                rmse = np.sqrt(np.mean((preds - targets) ** 2))
                
                val_metrics = {"mape": float(mape), "rmse": float(rmse)}
                logger.info(f"Val Loss: {val_loss/len(val_loader):.4f}")

            # Log the epoch
            logger.log_epoch(
                epoch=epoch,
                loss=avg_loss,
                metrics=val_metrics,
                memory_peak=current_memory_peak
            )

            # Early stopping check could go here if needed

    finally:
        tracemalloc.stop()

    logger.save()
    logger.info("Training completed and logs saved.")
    return logger


def main() -> None:
    """
    Standalone entry point for testing the logger.
    Since T018c is a utility for T018b, this main block simulates a run
    to ensure the output file is generated correctly.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Train and log model")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--output", type=str, default="data/results/training_logs.json")
    args = parser.parse_args()

    # Create a dummy model and dummy data for the standalone test
    # This ensures the script writes a REAL file without needing the full pipeline
    # Note: In the real pipeline, T018b calls run_training_with_logging directly.
    
    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.lin = torch.nn.Linear(10, 1)
        def forward(self, x, edge_index):
            return self.lin(x)

    # Generate dummy data
    dummy_x = torch.randn(100, 10)
    dummy_edge_index = torch.randint(0, 100, (2, 200))
    dummy_y = torch.randn(100, 1)
    
    dummy_dataset = torch.utils.data.TensorDataset(dummy_x, dummy_edge_index, dummy_y)
    # We need a custom collate for TensorDataset to work with our simple loop logic
    # Or just use a simple list of Data objects
    
    from torch_geometric.data import Data
    pyg_dataset = []
    for i in range(10):
        # Create 10 small graphs
        x = torch.randn(10, 10)
        edge_index = torch.randint(0, 10, (2, 50))
        y = torch.randn(1, 1)
        pyg_dataset.append(Data(x=x, edge_index=edge_index, y=y))
    
    train_loader = torch.utils.data.DataLoader(pyg_dataset, batch_size=2, shuffle=False)

    model = DummyModel()
    
    logger = run_training_with_logging(
        model=model,
        train_loader=train_loader,
        epochs=args.epochs,
        lr=args.lr,
        output_log_path=args.output
    )

    print(f"Log file written to {args.output}")
    with open(args.output, 'r') as f:
        content = json.load(f)
        print(f"Generated {len(content)} log entries.")


if __name__ == "__main__":
    main()