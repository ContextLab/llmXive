"""
Training loop for the Lightweight GNN on 2D material elastic moduli.
Consumes split_indices from T017, enforces CPU-only, logs memory, and outputs predictions.
"""
from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import sys
import time
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
from model.train_config import TrainingConfig, load_config_from_args
from model.train_logger import TrainingLogger
from utils.config import get_config
from utils.logger import get_logger, log_operation

# Constants
MAX_MEMORY_GB = 7.0
DEVICE = "cpu"  # Enforce CPU-only as per requirement

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
reproducibility_logger = get_logger()

class GraphDataset(Dataset):
    """PyTorch Dataset wrapping pre-loaded graphs."""

    def __init__(self, graphs: List[Dict[str, Any]]):
        self.graphs = graphs

    def __len__(self) -> int:
        return len(self.graphs)

    def __getitem__(self, idx: int) -> Data:
        g = self.graphs[idx]
        # Convert dict to PyG Data object
        # Expected keys: x (node features), edge_index, edge_attr (optional), y (target), id
        x = torch.tensor(g["node_features"], dtype=torch.float32)
        edge_index = torch.tensor(g["edge_index"], dtype=torch.long)
        if "edge_features" in g and g["edge_features"] is not None:
            edge_attr = torch.tensor(g["edge_features"], dtype=torch.float32)
        else:
            edge_attr = None

        # Target: usually a vector of moduli (Young's, Shear, Poisson) or a scalar
        # Assuming target_moduli is a list/array of 3 values [E, G, nu]
        y = torch.tensor(g["target_moduli"], dtype=torch.float32)
        
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y, id=g.get("id", f"idx_{idx}"))

def collate_fn(batch: List[Data]) -> Tuple[Data, List[str]]:
    """Custom collate to handle batched data and preserve IDs."""
    # PyG DataLoader handles batching automatically if we pass a list of Data objects
    # We just need to return the batch and a list of IDs
    ids = [item.id for item in batch]
    # The DataLoader's default collate_fn works for PyG Data objects
    # We return the batched data and the ids
    return batch, ids

def load_split_indices(split_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load split indices from JSON."""
    path = Path(split_path)
    if not path.exists():
        raise FileNotFoundError(f"Split indices file not found: {split_path}")
    
    with open(path, "r") as f:
        data = json.load(f)
    
    # Expected format: {"train": [...], "val": [...], "test": [...]}
    # Each item in the list is {"id": "...", "family_id": "..."}
    return data

def load_graphs_from_parquet(parquet_path: str) -> List[Dict[str, Any]]:
    """Load graphs from parquet file."""
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        # Convert dataframe rows to list of dicts
        # Ensure columns are named correctly: node_features, edge_index, edge_features, target_moduli, id
        graphs = []
        for _, row in df.iterrows():
            graph = {
                "id": row.get("id"),
                "node_features": row["node_features"],
                "edge_index": row["edge_index"],
                "target_moduli": row["target_moduli"],
            }
            if "edge_features" in row:
                graph["edge_features"] = row["edge_features"]
            graphs.append(graph)
        return graphs
    except Exception as e:
        logger.error(f"Failed to load graphs from {parquet_path}: {e}")
        raise

def filter_graphs_by_split(
    all_graphs: List[Dict[str, Any]], 
    split_indices: Dict[str, List[Dict[str, Any]]], 
    split_name: str
) -> List[Dict[str, Any]]:
    """Filter graphs based on split indices."""
    if split_name not in split_indices:
        raise ValueError(f"Split name '{split_name}' not found in split indices.")
    
    split_ids = {item["id"] for item in split_indices[split_name]}
    return [g for g in all_graphs if g["id"] in split_ids]

def get_memory_peak() -> float:
    """Get peak memory usage in GB."""
    # tracemalloc should be started before the training loop
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 ** 3)

def train_epoch(
    model: nn.Module, 
    loader: PyGDataLoader, 
    optimizer: torch.optim.Optimizer, 
    criterion: nn.Module,
    device: str
) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    for batch, _ in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch.x, batch.edge_index, batch.edge_attr)
        loss = criterion(out, batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)

def evaluate(
    model: nn.Module, 
    loader: PyGDataLoader, 
    criterion: nn.Module,
    device: str
) -> Tuple[float, List[np.ndarray], List[np.ndarray]]:
    """Evaluate model and return loss, predictions, targets."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch, _ in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr)
            loss = criterion(out, batch.y)
            total_loss += loss.item()
            all_preds.append(out.cpu().numpy())
            all_targets.append(batch.y.cpu().numpy())
    
    avg_loss = total_loss / len(loader)
    preds = np.concatenate(all_preds, axis=0)
    targets = np.concatenate(all_targets, axis=0)
    return avg_loss, preds, targets

def main():
    parser = argparse.ArgumentParser(description="Train GNN on 2D material elastic moduli")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--data_path", type=str, required=True, help="Path to graphs_v1.parquet")
    parser.add_argument("--split_path", type=str, required=True, help="Path to split_indices.json")
    parser.add_argument("--output_log", type=str, default="data/results/training_logs.json", help="Output log path")
    parser.add_argument("--output_predictions", type=str, default="data/results/predictions.json", help="Output predictions path")
    parser.add_argument("--model_path", type=str, default="data/processed/model_v1.pt", help="Output model path")
    
    args = parser.parse_args()

    # Load config
    if args.config:
        config = load_config_from_args(args.config)
    else:
        config = TrainingConfig(
            epochs=args.epochs,
            patience=args.patience,
            batch_size=args.batch_size,
            lr=args.lr,
            hidden_dim=64,
            num_layers=3,
            dropout=0.1
        )

    # Setup seeds
    seed = 42
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    logger.info(f"Starting training with config: {config}")
    logger.info(f"Device: {DEVICE}")

    # Load data
    logger.info(f"Loading graphs from {args.data_path}")
    all_graphs = load_graphs_from_parquet(args.data_path)
    logger.info(f"Loaded {len(all_graphs)} graphs")

    logger.info(f"Loading split indices from {args.split_path}")
    split_indices = load_split_indices(args.split_path)
    logger.info(f"Split sizes: train={len(split_indices['train'])}, val={len(split_indices['val'])}, test={len(split_indices['test'])}")

    # Filter graphs
    train_graphs = filter_graphs_by_split(all_graphs, split_indices, "train")
    val_graphs = filter_graphs_by_split(all_graphs, split_indices, "val")
    test_graphs = filter_graphs_by_split(all_graphs, split_indices, "test")

    if not train_graphs:
        raise ValueError("No training graphs found. Check split indices and data.")

    # Create datasets and loaders
    train_dataset = GraphDataset(train_graphs)
    val_dataset = GraphDataset(val_graphs)
    test_dataset = GraphDataset(test_graphs)

    train_loader = PyGDataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    val_loader = PyGDataLoader(val_dataset, batch_size=config.batch_size, shuffle=False)
    test_loader = PyGDataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)

    # Create model
    model = create_model(
        node_dim=train_graphs[0]["node_features"].shape[1] if train_graphs else 64,
        edge_dim=train_graphs[0]["edge_features"].shape[1] if train_graphs and "edge_features" in train_graphs[0] and train_graphs[0]["edge_features"] is not None else None,
        hidden_dim=config.hidden_dim,
        num_layers=config.num_layers,
        output_dim=3  # Assuming 3 targets: E, G, nu
    ).to(DEVICE)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    # Training logger
    training_logger = TrainingLogger(output_path=args.output_log)

    # Start memory tracking
    tracemalloc.start()

    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None

    logger.info("Starting training loop...")
    for epoch in range(config.epochs):
        start_time = time.time()
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        
        # Validate
        val_loss, _, _ = evaluate(model, val_loader, criterion, DEVICE)
        
        # Schedule
        scheduler.step(val_loss)

        # Memory check
        mem_peak = get_memory_peak()
        if mem_peak > MAX_MEMORY_GB:
            logger.error(f"SC-004 Violation: Peak memory {mem_peak:.2f}GB exceeds {MAX_MEMORY_GB}GB limit.")
            sys.exit(1)

        # Log
        log_entry = training_logger.log_epoch(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            lr=optimizer.param_groups[0]['lr'],
            memory_peak=mem_peak
        )
        logger.info(f"Epoch {epoch}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, LR={optimizer.param_groups[0]['lr']:.6f}, Mem={mem_peak:.2f}GB")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict()
        else:
            patience_counter += 1
            if patience_counter >= config.patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break

        # Garbage collection
        gc.collect()

    # Save best model
    if best_model_state:
        model.load_state_dict(best_model_state)
        torch.save(model.state_dict(), args.model_path)
        logger.info(f"Model saved to {args.model_path}")

    # Evaluate on test set
    logger.info("Evaluating on test set...")
    test_loss, test_preds, test_targets = evaluate(model, test_loader, criterion, DEVICE)
    logger.info(f"Test Loss: {test_loss:.4f}")

    # Save predictions
    predictions_data = {
        "predictions": test_preds.tolist(),
        "targets": test_targets.tolist(),
        "test_loss": test_loss,
        "metadata": {
            "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions.",
            "device": DEVICE,
            "epochs_trained": epoch + 1,
            "best_val_loss": best_val_loss
        }
    }
    
    with open(args.output_predictions, "w") as f:
        json.dump(predictions_data, f, indent=2)
    logger.info(f"Predictions saved to {args.output_predictions}")

    # Final memory check
    mem_peak = get_memory_peak()
    if mem_peak > MAX_MEMORY_GB:
        logger.error(f"SC-004 Violation: Final peak memory {mem_peak:.2f}GB exceeds {MAX_MEMORY_GB}GB limit.")
        sys.exit(1)

    tracemalloc.stop()
    logger.info("Training completed successfully.")

if __name__ == "__main__":
    main()
