"""
Training loop for the GNN model on 2D material elastic moduli.

This script consumes the pre-computed split indices, trains the GNN model
with dynamic memory enforcement, and outputs predictions and logs.
"""
from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch_geometric.data import DataLoader as PyGDataLoader
from torch_geometric.data import Data
from torch.utils.data import Dataset
from tqdm import tqdm

# Project imports
from model.gnn import LightweightGNN, create_model
from model.memory_enforcer import enforce_memory_limit, get_memory_peak_mb
from model.train_config import TrainingConfig, load_config_from_args
from model.train_logger import TrainingLogger, run_training_with_logging
from utils.config import enforce_reproducibility, get_config
from utils.disclaimer_template import DISCLAIMER_STRING
from utils.logger import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
reproducibility_logger = get_logger("training")

def load_graphs_from_parquet(parquet_path: str) -> List[Dict[str, Any]]:
    """Load graphs from a parquet file."""
    import pandas as pd

    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Graph file not found: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    graphs = []
    for _, row in df.iterrows():
        graphs.append(row.to_dict())
    return graphs

def load_split_indices(split_path: str) -> Dict[str, List[int]]:
    """Load split indices from JSON."""
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split indices not found: {split_path}")
    with open(split_path, "r") as f:
        return json.load(f)

def filter_graphs_by_split(
    graphs: List[Dict[str, Any]], split_indices: Dict[str, List[int]], split_name: str
) -> List[Dict[str, Any]]:
    """Filter graphs based on split indices."""
    indices = split_indices.get(split_name, [])
    return [graphs[i] for i in indices if i < len(graphs)]

def convert_to_pyg_graph(graph_dict: Dict[str, Any]) -> Data:
    """Convert a dictionary graph to a PyTorch Geometric Data object."""
    node_features = np.array(graph_dict.get("node_features", []), dtype=np.float32)
    edge_index = np.array(graph_dict.get("edge_index", []), dtype=np.int64)
    edge_features = np.array(graph_dict.get("edge_features", []), dtype=np.float32)
    target_moduli = graph_dict.get("target_moduli", {})

    # Ensure edge_index is 2x num_edges
    if edge_index.ndim == 1:
        # Reshape if it's a flat list of [src, dst, src, dst, ...]
        edge_index = edge_index.reshape(2, -1)

    y = np.array(
        [
            target_moduli.get("youngs_modulus", 0.0),
            target_moduli.get("shear_modulus", 0.0),
            target_moduli.get("poisson_ratio", 0.0),
        ],
        dtype=np.float32,
    )

    data = Data(
        x=node_features,
        edge_index=edge_index,
        edge_attr=edge_features,
        y=y,
    )
    return data

class GraphDataset(Dataset):
    """Custom Dataset for PyTorch Geometric."""

    def __init__(self, graphs: List[Dict[str, Any]]):
        self.graphs = graphs
        self.pyg_graphs = [convert_to_pyg_graph(g) for g in graphs]

    def __len__(self):
        return len(self.pyg_graphs)

    def __getitem__(self, idx):
        return self.pyg_graphs[idx]

def collate_fn(batch: List[Data]) -> Data:
    """Collate function for DataLoader."""
    return PyGDataLoader.default_collate(batch)

def train_epoch(
    model: nn.Module,
    loader: PyGDataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    """Train the model for one epoch."""
    model.train()
    total_loss = 0.0
    count = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch)
        loss = nn.functional.mse_loss(out, batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
        count += batch.num_graphs
    return total_loss / count if count > 0 else 0.0

def evaluate(
    model: nn.Module,
    loader: PyGDataLoader,
    device: torch.device,
) -> Tuple[float, Dict[str, List[float]]]:
    """Evaluate the model."""
    model.eval()
    total_loss = 0.0
    count = 0
    predictions = {"youngs": [], "shear": [], "poisson": []}
    targets = {"youngs": [], "shear": [], "poisson": []}

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch)
            loss = nn.functional.mse_loss(out, batch.y)
            total_loss += loss.item() * batch.num_graphs
            count += batch.num_graphs

            # Extract predictions and targets
            preds = out.cpu().numpy()
            targs = batch.y.cpu().numpy()

            predictions["youngs"].extend(preds[:, 0].tolist())
            predictions["shear"].extend(preds[:, 1].tolist())
            predictions["poisson"].extend(preds[:, 2].tolist())

            targets["youngs"].extend(targs[:, 0].tolist())
            targets["shear"].extend(targs[:, 1].tolist())
            targets["poisson"].extend(targs[:, 2].tolist())

    return total_loss / count if count > 0 else 0.0, predictions

def main():
    """Main training entry point."""
    parser = argparse.ArgumentParser(description="Train GNN for elastic moduli prediction")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--data_path", type=str, required=True, help="Path to graphs parquet")
    parser.add_argument("--split_path", type=str, required=True, help="Path to split indices JSON")
    parser.add_argument("--output_log", type=str, default="data/results/training_logs.json", help="Output log path")
    parser.add_argument("--output_model", type=str, default="data/processed/model_v1.pt", help="Output model path")
    parser.add_argument("--output_predictions", type=str, default="data/results/predictions.json", help="Output predictions path")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use (cpu/cuda)")

    args = parser.parse_args()

    # Enforce reproducibility
    config = get_config()
    enforce_reproducibility(config.seed)

    logger.info(f"Starting training with config: {args}")

    # Load data
    logger.info(f"Loading graphs from {args.data_path}")
    raw_graphs = load_graphs_from_parquet(args.data_path)
    logger.info(f"Loaded {len(raw_graphs)} graphs")

    logger.info(f"Loading split indices from {args.split_path}")
    split_indices = load_split_indices(args.split_path)

    train_graphs = filter_graphs_by_split(raw_graphs, split_indices, "train")
    test_graphs = filter_graphs_by_split(raw_graphs, split_indices, "test")

    logger.info(f"Train size: {len(train_graphs)}, Test size: {len(test_graphs)}")

    if len(train_graphs) == 0 or len(test_graphs) == 0:
        logger.error("Empty train or test set. Exiting.")
        sys.exit(1)

    # Create datasets and loaders
    train_dataset = GraphDataset(train_graphs)
    test_dataset = GraphDataset(test_graphs)

    # Memory enforcement: start with requested batch size, reduce if needed
    current_batch_size = args.batch_size
    max_memory_gb = config.MAX_MEMORY_GB if hasattr(config, "MAX_MEMORY_GB") else 7.0

    device = torch.device(args.device if torch.cuda.is_available() or args.device == "cpu" else "cpu")
    logger.info(f"Using device: {device}")

    # Initialize model
    model = create_model()
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=5)

    # Training loop with memory enforcement
    best_loss = float("inf")
    patience_counter = 0
    final_batch_size = current_batch_size
    training_logs = {
        "epochs": [],
        "best_loss": best_loss,
        "final_batch_size": final_batch_size,
        "config": vars(args),
        "disclaimer": DISCLAIMER_STRING,
    }

    tracemalloc.start()

    for epoch in range(args.epochs):
        # Check memory before training epoch
        current_mem = get_memory_peak_mb()
        if current_mem > max_memory_gb * 1024:
            logger.warning(f"Memory usage ({current_mem} MB) exceeds limit ({max_memory_gb} GB). Reducing batch size.")
            current_batch_size = max(1, current_batch_size // 2)
            final_batch_size = current_batch_size
            if current_batch_size == 1:
                logger.error("SC-004 Failed: Memory limit exceeded even with batch size 1.")
                sys.exit(1)
            # Recreate loader with new batch size
            train_loader = PyGDataLoader(train_dataset, batch_size=current_batch_size, shuffle=True)
            test_loader = PyGDataLoader(test_dataset, batch_size=current_batch_size, shuffle=False)
            continue

        train_loader = PyGDataLoader(train_dataset, batch_size=current_batch_size, shuffle=True)
        test_loader = PyGDataLoader(test_dataset, batch_size=current_batch_size, shuffle=False)

        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss, _ = evaluate(model, test_loader, device)

        scheduler.step(val_loss)

        epoch_log = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "lr": optimizer.param_groups[0]["lr"],
            "batch_size": current_batch_size,
        }
        training_logs["epochs"].append(epoch_log)
        logger.info(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}")

        if val_loss < best_loss:
            best_loss = val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), args.output_model)
            logger.info(f"Saved best model with loss {best_loss:.4f}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

        gc.collect()

    tracemalloc.stop()

    # Final evaluation on test set
    test_loader = PyGDataLoader(test_dataset, batch_size=current_batch_size, shuffle=False)
    final_loss, predictions = evaluate(model, test_loader, device)

    # Save predictions
    predictions_output = {
        "predictions": predictions,
        "disclaimer": DISCLAIMER_STRING,
        "final_loss": final_loss,
    }
    with open(args.output_predictions, "w") as f:
        json.dump(predictions_output, f, indent=2)
    logger.info(f"Saved predictions to {args.output_predictions}")

    # Save training logs
    training_logs["final_loss"] = final_loss
    with open(args.output_log, "w") as f:
        json.dump(training_logs, f, indent=2)
    logger.info(f"Saved training logs to {args.output_log}")

    logger.info("Training completed successfully.")

if __name__ == "__main__":
    main()