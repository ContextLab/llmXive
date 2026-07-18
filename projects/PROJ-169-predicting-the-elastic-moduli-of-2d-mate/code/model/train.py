"""
Training loop for the Structure-Only Surrogate Model.

WARNING: This model is a surrogate interpolating pre-computed DFT results.
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""

import os
import json
import logging
import argparse
import time
import gc
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
from torch_geometric.data import DataLoader, Data
from torch_geometric.nn import GCNConv, global_mean_pool

# Local imports
from utils.config import Config
from utils.logger import get_logger, log_training_metrics, configure_log_file
from model.gnn import LightweightGNN, create_model
from model.splitter import load_graphs_from_parquet

# Disable GPU to enforce CPU-only constraint
os.environ["CUDA_VISIBLE_DEVICES"] = ""

logger = get_logger(__name__)


class GraphDataset(torch.utils.data.Dataset):
    """Dataset wrapper for PyTorch Geometric Data objects."""

    def __init__(self, graphs: List[Data]):
        self.graphs = graphs

    def __len__(self):
        return len(self.graphs)

    def __getitem__(self, idx):
        return self.graphs[idx]


def collate_fn(batch: List[Data]) -> Data:
    """Custom collate function if specific handling is needed, otherwise use default."""
    # PyG default collate is usually sufficient for simple Data objects
    return torch.utils.data._utils.collate.default_collate(batch)


def graph_to_pyg(graph_dict: Dict[str, Any]) -> Data:
    """
    Convert a dictionary representation of a MaterialGraph to a PyG Data object.
    Expects keys: 'node_features', 'edge_index', 'edge_features', 'target_moduli'.
    """
    # Convert numpy arrays/tensors to torch tensors
    x = torch.tensor(graph_dict['node_features'], dtype=torch.float)
    edge_index = torch.tensor(graph_dict['edge_index'], dtype=torch.long)
    
    # Handle edge features if present
    edge_attr = None
    if 'edge_features' in graph_dict and graph_dict['edge_features'] is not None:
        edge_attr = torch.tensor(graph_dict['edge_features'], dtype=torch.float)

    y = torch.tensor(graph_dict['target_moduli'], dtype=torch.float)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    return data


def train_epoch(
    model: nn.Module, 
    loader: DataLoader, 
    optimizer: torch.optim.Optimizer, 
    device: torch.device
) -> Tuple[float, int]:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        # Forward pass
        # model expects (x, edge_index, edge_attr) or similar depending on implementation
        # Assuming model.forward handles the batched Data object or unpacks it
        if hasattr(model, 'forward_batch'):
            out = model.forward_batch(batch)
        else:
            # Fallback for standard GNN expecting x, edge_index
            out = model(batch.x, batch.edge_index, batch.edge_attr)

        loss = out.mean() # Simple MSE-like loss if out is scalar per node, or adapt
        # If out is graph-level prediction (y_hat) and batch.y is target:
        # Assuming out shape matches batch.y for regression
        if out.shape != batch.y.shape:
             # If out is node-level and we need graph-level, pool
             # But typically for this task, model should output graph-level
             pass 
        
        # Correct loss calculation for graph-level regression
        # Assuming 'out' is the prediction for the whole graph
        criterion = nn.MSELoss()
        # Ensure shapes match. If model outputs per-node, we need global_mean_pool here too
        # Let's assume the model in gnn.py returns graph-level predictions
        loss = criterion(out, batch.y)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

        # Memory safety check
        if num_batches % 10 == 0:
            gc.collect()

    return total_loss / max(num_batches, 1), num_batches


def evaluate(
    model: nn.Module, 
    loader: DataLoader, 
    device: torch.device
) -> Tuple[float, Dict[str, float]]:
    """Evaluate model on a dataset."""
    model.eval()
    total_loss = 0.0
    num_batches = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            
            if hasattr(model, 'forward_batch'):
                out = model.forward_batch(batch)
            else:
                out = model(batch.x, batch.edge_index, batch.edge_attr)

            criterion = nn.MSELoss()
            loss = criterion(out, batch.y)

            total_loss += loss.item()
            num_batches += 1

            all_preds.extend(out.cpu().numpy().flatten())
            all_targets.extend(batch.y.cpu().numpy().flatten())

    avg_loss = total_loss / max(num_batches, 1)

    # Calculate metrics
    import numpy as np
    preds = np.array(all_preds)
    targets = np.array(all_targets)

    # Avoid division by zero
    abs_targets = np.abs(targets)
    abs_targets[abs_targets == 0] = 1e-8

    mape = np.mean(np.abs((preds - targets) / abs_targets)) * 100
    rmse = np.sqrt(np.mean((preds - targets) ** 2))

    return avg_loss, {"mape": float(mape), "rmse": float(rmse)}


def main():
    parser = argparse.ArgumentParser(description="Train the Surrogate GNN Model")
    parser.add_argument("--config", type=str, default="code/utils/config.yaml", help="Path to config file")
    parser.add_argument("--epochs", type=int, default=100, help="Max epochs")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--data_path", type=str, default="data/processed/graphs_v1.parquet", help="Path to processed graphs")
    parser.add_argument("--split_path", type=str, default="data/processed/split_indices.json", help="Path to split indices")
    parser.add_argument("--output_log", type=str, default="data/results/training_logs.json", help="Path to training log")
    parser.add_argument("--output_test_indices", type=str, default="data/processed/test_indices.json", help="Path to save test indices")
    args = parser.parse_args()

    # Initialize config and logging
    config = Config.load(args.config)
    log_path = Path(args.output_log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    configure_log_file(log_path)
    
    logger.info("Starting Training Loop for Surrogate Model")
    logger.warning("WARNING: This model is a surrogate interpolating pre-computed DFT results. It does NOT solve the Schrödinger equation.")

    # Load data
    logger.info(f"Loading graphs from {args.data_path}")
    all_graphs = load_graphs_from_parquet(args.data_path)
    
    # Load split indices
    logger.info(f"Loading split indices from {args.split_path}")
    with open(args.split_path, 'r') as f:
        split_data = json.load(f)
    
    train_indices = split_data['train_indices']
    val_indices = split_data['val_indices']
    test_indices = split_data['test_indices']

    # Save test indices as required
    with open(args.output_test_indices, 'w') as f:
        json.dump({"test_indices": test_indices}, f, indent=2)
    logger.info(f"Saved test indices to {args.output_test_indices}")

    # Create datasets
    train_graphs = [all_graphs[i] for i in train_indices]
    val_graphs = [all_graphs[i] for i in val_indices]
    # Test graphs are not used in training loop, only for final eval if needed later

    train_dataset = GraphDataset(train_graphs)
    val_dataset = GraphDataset(val_graphs)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    # Initialize model
    device = torch.device("cpu") # Enforce CPU
    model = create_model() # Uses default args from gnn.py
    model = model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

    # Training state
    best_val_loss = float('inf')
    patience_counter = 0
    training_log = []

    # Metadata for log
    metadata = {
        "disclaimer": "These results are ML interpolations of DFT data, not first-principles solutions.",
        "config": {
            "epochs": args.epochs,
            "patience": args.patience,
            "batch_size": args.batch_size,
            "lr": args.lr
        }
    }

    logger.info(f"Model initialized. Parameters: {sum(p.numel() for p in model.parameters())}")

    # Start memory tracking
    tracemalloc.start()

    for epoch in range(args.epochs):
        start_time = time.time()
        
        # Train
        train_loss, _ = train_epoch(model, train_loader, optimizer, device)
        
        # Validate
        val_loss, val_metrics = evaluate(model, val_loader, device)
        
        # Update LR
        scheduler.step(val_loss)

        # Memory check
        current, peak = tracemalloc.get_traced_memory()
        memory_peak_gb = peak / 1024**3
        
        # Log entry
        log_entry = {
            "epoch": epoch + 1,
            "loss": float(train_loss),
            "metrics": {
                "mape": val_metrics["mape"],
                "rmse": val_metrics["rmse"]
            },
            "memory_peak": float(memory_peak_gb)
        }
        training_log.append(log_entry)
        
        logger.info(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, Val MAPE={val_metrics['mape']:.2f}%, Val RMSE={val_metrics['rmse']:.4f}, Mem={memory_peak_gb:.2f}GB")
        log_training_metrics(log_entry)

        # Early stopping logic
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model state (optional but good practice)
            # torch.save(model.state_dict(), "best_model.pth")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break

        gc.collect()

    tracemalloc.stop()

    # Final log save
    final_report = {
        "metadata": metadata,
        "training_history": training_log,
        "best_val_loss": best_val_loss,
        "final_epoch": epoch + 1
    }

    with open(args.output_log, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Training complete. Logs saved to {args.output_log}")
    logger.info(f"Best Validation Loss: {best_val_loss}")

if __name__ == "__main__":
    main()
