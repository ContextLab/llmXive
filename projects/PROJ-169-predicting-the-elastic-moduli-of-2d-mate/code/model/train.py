"""
Training loop for the Lightweight GNN on 2D material elastic moduli.

This script implements the training process for User Story 2.
It consumes split indices, enforces CPU-only execution, monitors memory,
and saves the model weights and predictions.
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
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.loader import DataLoader as PyGDataLoader
import pandas as pd

# Project imports based on API surface
from model.gnn import LightweightGNN, create_model
from model.train_config import TrainingConfig, load_config_from_args
from utils.logger import get_logger, log_operation, configure_log_file, log_training_metrics
from utils.config import set_global_config, get_config

# Constants
MAX_MEMORY_GB = 7.0
DEVICE = "cpu"  # Enforced CPU-only

# Setup logging
logger = get_logger("train_loop")
configure_log_file("data/results/training.log")

class GraphDataset(Dataset):
    """PyTorch Dataset wrapper for MaterialGraph data loaded from parquet."""

    def __init__(self, graphs: List[Dict[str, Any]], device: str = DEVICE):
        self.graphs = graphs
        self.device = device

    def __len__(self) -> int:
        return len(self.graphs)

    def __getitem__(self, idx: int) -> Data:
        g = self.graphs[idx]
        # Convert dict to torch_geometric Data
        # Expecting: node_features (N x F), edge_index (2 x E), edge_features (E x F_e), target (scalar or vector)
        x = torch.tensor(g["node_features"], dtype=torch.float32)
        edge_index = torch.tensor(g["edge_index"], dtype=torch.long)
        y = torch.tensor(g["target_moduli"], dtype=torch.float32)
        
        # Handle edge features if present, otherwise create dummy
        if "edge_features" in g and g["edge_features"] is not None:
            edge_attr = torch.tensor(g["edge_features"], dtype=torch.float32)
        else:
            # Dummy edge attribute if not present (assuming 0-dim or 1-dim)
            edge_attr = torch.zeros((edge_index.size(1), 1), dtype=torch.float32)

        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)

def collate_fn(batch: List[Data]) -> Data:
    """Custom collate function if needed, though PyG Data collator usually works."""
    # PyTorch Geometric's default collate handles Data objects well
    # We rely on PyG's DataLoader which uses this internally or a similar mechanism
    return torch_geometric.data.Batch.from_data_list(batch)

def load_graphs_from_parquet(path: Path) -> List[Dict[str, Any]]:
    """Load graphs from a parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Graphs file not found: {path}")
    
    df = pd.read_parquet(path)
    graphs = []
    for _, row in df.iterrows():
        # Reconstruct graph dict from dataframe row
        # Assumes columns: 'node_features', 'edge_index', 'edge_features', 'target_moduli'
        # edge_index might be stored as a list or string representation
        graph = {
            "node_features": row["node_features"],
            "edge_index": row["edge_index"],
            "edge_features": row.get("edge_features"),
            "target_moduli": row["target_moduli"],
            "family_id": row.get("family_id")
        }
        graphs.append(graph)
    return graphs

def load_split_indices(path: Path) -> Dict[str, List[int]]:
    """Load split indices from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Split indices file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def filter_graphs_by_split(graphs: List[Dict[str, Any]], split_indices: Dict[str, List[int]], split_name: str = "train") -> List[Dict[str, Any]]:
    """Filter graphs based on split indices."""
    indices = split_indices.get(split_name, [])
    return [graphs[i] for i in indices if i < len(graphs)]

def get_memory_peak() -> float:
    """Get current peak memory usage in GB."""
    # tracemalloc should be started before this call in main
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 ** 3)

def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, device: str) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch)
        # Assuming simple MSE for now, adjust if targets are multi-dimensional
        loss = nn.MSELoss()(out, batch.y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * batch.num_graphs
        total_samples += batch.num_graphs

        # Memory check
        mem_gb = get_memory_peak()
        if mem_gb > MAX_MEMORY_GB:
            logger.critical(f"Memory limit exceeded: {mem_gb:.2f} GB > {MAX_MEMORY_GB} GB. Exiting.")
            sys.exit(1)

    avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
    return avg_loss


def evaluate(model: nn.Module, loader: DataLoader, device: str) -> Tuple[float, Dict[str, float]]:
    """Evaluate model and return loss and metrics."""
    model.eval()
    total_loss = 0.0
    total_samples = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch)
            loss = nn.MSELoss()(out, batch.y)
            total_loss += loss.item()
            all_preds.extend(out.cpu().numpy().flatten())
            all_targets.extend(batch.y.cpu().numpy().flatten())
    
    avg_loss = total_loss / len(loader)
    
    # Calculate metrics
    preds = np.array(all_preds)
    targets = np.array(all_targets)
    
    # MAPE
    non_zero_mask = targets != 0
    if np.any(non_zero_mask):
        mape = np.mean(np.abs((targets[non_zero_mask] - preds[non_zero_mask]) / targets[non_zero_mask])) * 100
    else:
        mape = 0.0
    
    # RMSE
    rmse = np.sqrt(np.mean((preds - targets) ** 2))
    
    # R2
    ss_res = np.sum((targets - preds) ** 2)
    ss_tot = np.sum((targets - np.mean(targets)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    metrics = {"mape": float(mape), "rmse": float(rmse), "r2": float(r2)}
    return avg_loss, metrics

def main():
    parser = argparse.ArgumentParser(description="Train Lightweight GNN for 2D Material Elastic Moduli")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--data_path", type=str, required=True, help="Path to graphs_v1.parquet")
    parser.add_argument("--split_path", type=str, required=True, help="Path to split_indices.json")
    parser.add_argument("--output_log", type=str, default="data/results/training_logs.json", help="Path to output training log")
    parser.add_argument("--output_test_indices", type=str, default="data/results/test_indices.json", help="Path to output test indices")
    
    args = parser.parse_args()
    
    # Set global config for reproducibility
    set_global_config(seed=42)
    
    # Load config
    config = load_config_from_args(args)
    
    # Setup logging
    log_operation("training_start", epochs=args.epochs, patience=args.patience, data_path=args.data_path)
    
    # Check memory limit at start
    current_mem = get_memory_peak()
    if current_mem > MAX_MEMORY_GB:
        logger.error(f"Memory usage {current_mem:.2f}GB exceeds limit {MAX_MEMORY_GB}GB. Aborting.")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading graphs from {args.data_path}")
    graphs = load_graphs_from_parquet(Path(args.data_path))
    
    logger.info(f"Loading split indices from {args.split_path}")
    split_indices = load_split_indices(Path(args.split_path))
    
    # Filter data
    train_graphs = filter_graphs_by_split(graphs, split_indices, "train")
    test_graphs = filter_graphs_by_split(graphs, split_indices, "test")
    
    if not train_graphs:
        logger.error("No training data found. Aborting.")
        sys.exit(1)
    
    logger.info(f"Train size: {len(train_graphs)}, Test size: {len(test_graphs)}")
    
    # Create datasets and loaders
    train_dataset = GraphDataset(train_graphs, device=DEVICE)
    test_dataset = GraphDataset(test_graphs, device=DEVICE)
    
    train_loader = PyGDataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    test_loader = PyGDataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    
    # Initialize model
    # Infer input dim from first graph (simplified)
    if len(train_graphs) > 0:
        input_dim = len(train_graphs[0]["node_features"][0]) if train_graphs[0]["node_features"] else 0
    else:
        input_dim = 0
    
    model = create_model(input_dim=input_dim, hidden_dim=64, num_layers=3).to(DEVICE)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    
    # Training loop
    best_loss = float('inf')
    patience_counter = 0
    training_logs = []
    predictions = []
    
    logger.info("Starting training loop...")
    
    for epoch in range(args.epochs):
        start_time = time.time()
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, DEVICE)
        
        # Evaluate
        val_loss, val_metrics = evaluate(model, test_loader, DEVICE)
        
        # Log memory
        mem_peak = get_memory_peak()

        # Check memory limit
        if mem_peak > MAX_MEMORY_GB:
            logger.error(f"Memory usage {mem_peak:.2f}GB exceeds limit {MAX_MEMORY_GB}GB at epoch {epoch}. Aborting.")
            sys.exit(1)
        
        # Log epoch
        epoch_log = {
            "epoch": epoch + 1,
            "loss": float(train_loss),
            "val_loss": float(val_loss),
            "metrics": val_metrics,
            "memory_peak": float(mem_peak),
            "time_elapsed": time.time() - start_time
        }
        training_logs.append(epoch_log)
        
        logger.info(f"Epoch {epoch+1}/{args.epochs} - Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, MAPE: {val_metrics['mape']:.2f}%, Mem: {mem_peak:.2f}GB")
        
        # Save best model
        if val_loss < best_loss:
            best_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), "data/processed/model_v1.pt")
            logger.info(f"Saved best model at epoch {epoch+1}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        scheduler.step(val_loss)
        
        # Cleanup
        gc.collect()
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
    
    # Generate predictions on test set
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(DEVICE)
            out = model(batch)
            all_preds.extend(out.cpu().numpy().flatten())
            all_targets.extend(batch.y.cpu().numpy().flatten())
    
    predictions = {
        "predictions": all_preds,
        "targets": all_targets,
        "metrics": val_metrics,
        "disclaimer": "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation."
    }
    
    # Save outputs
    with open(args.output_log, "w") as f:
        json.dump(training_logs, f, indent=2)
    
    with open("data/results/predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    # Save test indices for reference
    with open(args.output_test_indices, "w") as f:
        json.dump({"test_indices": split_indices.get("test", [])}, f, indent=2)
    
    log_operation("training_complete", epochs_trained=len(training_logs), best_val_loss=best_loss)
    logger.info("Training completed successfully.")
    log_operation("training_end", final_val_loss=best_val_loss, final_test_loss=test_loss)


if __name__ == "__main__":
    main()