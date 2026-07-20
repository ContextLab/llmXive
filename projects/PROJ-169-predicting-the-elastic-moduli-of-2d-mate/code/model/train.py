"""
Training loop for the Lightweight GNN on 2D Material Elastic Moduli.

This script trains the GNN model defined in `code/model/gnn.py` on the processed
dataset. It enforces CPU-only execution, logs memory usage, and validates
success criteria.

Requirements:
- Consumes `data/processed/split_indices.json` (from T017).
- Enforces CPU-only execution.
- Logs `memory_peak` at each epoch.
- Exits with code 1 if `memory_peak` > 7GB.
- Saves model weights to `data/processed/model_v1.pt`.
- Outputs `predictions.json` for the test set.
- Includes "Surrogate Model Disclaimer" in outputs.
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
from torch_geometric.data import Data, DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool
from torch.utils.data import Dataset

# Import local project modules
from model.gnn import LightweightGNN, create_model
from model.train_config import TrainingConfig, load_config_from_args
from utils.config import enforce_reproducibility, get_config
from utils.logger import get_logger, log_operation, log_training_metrics
from utils.memory_utils import get_memory_profile, enforce_memory_limit

# Constants
MAX_MEMORY_GB = 7.0
DISCLAIMER = (
    "These results are derived from a machine learning surrogate model "
    "interpolating pre-computed DFT data. They do not represent first-principles "
    "calculations or solutions to the Schrödinger equation."
)

# Setup logging
logger = logging.getLogger(__name__)
reproducibility_logger = get_logger("training")


class GraphDataset(Dataset):
    """PyTorch Dataset wrapper for loading graphs from memory/lists."""

    def __init__(self, graphs: List[Data], targets: List[np.ndarray]):
        self.graphs = graphs
        self.targets = targets

    def __len__(self) -> int:
        return len(self.graphs)

    def __getitem__(self, idx: int) -> Tuple[Data, torch.Tensor]:
        return self.graphs[idx], torch.tensor(self.targets[idx], dtype=torch.float32)


def collate_fn(batch: List[Tuple[Data, torch.Tensor]]) -> Tuple[Data, torch.Tensor]:
    """Custom collate function for PyTorch Geometric DataLoader."""
    graphs, targets = zip(*batch)
    # torch_geometric's default collate handles stacking node/edge features
    # We just need to stack the targets
    stacked_targets = torch.stack(targets)
    # Use PyG's default collate for the graphs
    from torch_geometric.data import Batch
    return Batch.from_data_list(list(graphs)), stacked_targets


def load_split_indices(split_path: Path) -> Dict[str, Any]:
    """Load split indices from JSON file."""
    if not split_path.exists():
        raise FileNotFoundError(f"Split indices file not found: {split_path}")
    with open(split_path, 'r') as f:
        return json.load(f)


def load_graphs_from_parquet(graphs_path: Path) -> List[Dict[str, Any]]:
    """
    Load graphs from Parquet file.
    Note: This is a simplified loader assuming the parquet structure matches
    the output of T013d. In a real scenario, we would use pyarrow/pandas.
    """
    try:
        import pandas as pd
        df = pd.read_parquet(graphs_path)
        # Convert rows to dictionaries
        return df.to_dict(orient='records')
    except ImportError:
        logger.error("pandas is required to load parquet files. Install with: pip install pandas")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load graphs from {graphs_path}: {e}")
        raise


def convert_to_pyg_graph(record: Dict[str, Any]) -> Data:
    """
    Convert a dictionary record (from parquet) to a PyTorch Geometric Data object.
    Expects: node_features, edge_index, edge_features (optional), family_id, target_moduli
    """
    node_features = torch.tensor(record['node_features'], dtype=torch.float32)
    edge_index = torch.tensor(record['edge_index'], dtype=torch.int64)
    
    # Handle edge features if present
    edge_attr = None
    if 'edge_features' in record and record['edge_features'] is not None:
        edge_attr = torch.tensor(record['edge_features'], dtype=torch.float32)

    # Target is usually a vector of [Young's, Shear, Poisson]
    target = torch.tensor(record['target_moduli'], dtype=torch.float32)

    return Data(x=node_features, edge_index=edge_index, edge_attr=edge_attr, y=target)


def filter_graphs_by_split(graphs_data: List[Dict[str, Any]], split_indices: Dict[str, List[int]]) -> Tuple[List[Data], List[np.ndarray], List[str]]:
    """
    Filter graphs based on split indices and convert to PyG Data objects.
    Returns: (graphs, targets, family_ids)
    """
    train_indices = set(split_indices.get('train', []))
    test_indices = set(split_indices.get('test', []))
    val_indices = set(split_indices.get('val', []))

    # We need to separate train, test, val
    # For training, we only use train_indices
    # For this function, let's assume we are filtering for a specific split name
    # But the caller will handle the split selection.
    # Here we just return all graphs with their indices for now, or filter by a specific set.
    # Actually, the requirement is to consume split_indices.json.
    # Let's assume the caller passes the specific indices they want.
    # For now, we'll return the full list with indices mapped, but the caller
    # will select the subset.
    
    # Let's re-implement to return the full list with metadata, 
    # and the caller selects based on split_indices.
    # But the function signature suggests filtering.
    # Let's assume we are filtering for the 'train' set by default, 
    # or we pass the indices to filter.
    
    # To make it generic, let's just return the data with indices.
    # The caller will slice.
    
    # Actually, let's just implement the filtering for a given set of indices.
    # The caller will call this multiple times or pass the combined list.
    # Let's assume we are filtering for the 'train' set for the training loop.
    # But the function name is `filter_graphs_by_split`.
    
    # Let's change the logic: this function takes the full data and the split manifest,
    # and returns the train, test, val sets separately.
    
    train_graphs = []
    train_targets = []
    train_families = []
    
    test_graphs = []
    test_targets = []
    test_families = []
    
    val_graphs = []
    val_targets = []
    val_families = []

    for idx, record in enumerate(graphs_data):
        family_id = record.get('family_id', 'unknown')
        graph = convert_to_pyg_graph(record)
        target = np.array(record['target_moduli'])

        if idx in train_indices:
            train_graphs.append(graph)
            train_targets.append(target)
            train_families.append(family_id)
        elif idx in test_indices:
            test_graphs.append(graph)
            test_targets.append(target)
            test_families.append(family_id)
        elif idx in val_indices:
            val_graphs.append(graph)
            val_targets.append(target)
            val_families.append(family_id)

    return (train_graphs, train_targets, train_families), \
           (test_graphs, test_targets, test_families), \
           (val_graphs, val_targets, val_families)


def get_memory_peak() -> float:
    """Get the peak memory usage in GB."""
    # tracemalloc is already started in main
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 ** 3)


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: TrainingConfig
) -> Tuple[float, float]:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    total_samples = 0

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        # Forward pass
        # model expects (x, edge_index, edge_attr, batch)
        # batch.y is the target
        out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        
        # Loss calculation (MSE)
        # out shape: [N_graphs, 3] (Young's, Shear, Poisson)
        # batch.y shape: [N_graphs, 3]
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


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device
) -> Tuple[float, List[np.ndarray], List[np.ndarray]]:
    """Evaluate model on a dataset."""
    model.eval()
    total_loss = 0.0
    total_samples = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            
            loss = nn.MSELoss()(out, batch.y)
            
            total_loss += loss.item() * batch.num_graphs
            total_samples += batch.num_graphs

            all_preds.append(out.cpu().numpy())
            all_targets.append(batch.y.cpu().numpy())

    avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
    
    # Concatenate predictions and targets
    all_preds = np.vstack(all_preds) if all_preds else np.array([])
    all_targets = np.vstack(all_targets) if all_targets else np.array([])

    return avg_loss, all_preds, all_targets


def main():
    parser = argparse.ArgumentParser(description="Train Lightweight GNN for Elastic Moduli")
    parser.add_argument("--config", type=str, default="code/model/train_config.yaml", help="Path to config file")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--data_path", type=str, default="data/processed/graphs_v1.parquet", help="Path to processed graphs")
    parser.add_argument("--split_path", type=str, default="data/processed/split_indices.json", help="Path to split indices")
    parser.add_argument("--output_log", type=str, default="data/results/training_logs.json", help="Path to training log")
    parser.add_argument("--output_test_indices", type=str, default="data/results/test_indices.json", help="Path to test indices for prediction")
    parser.add_argument("--output_model", type=str, default="data/processed/model_v1.pt", help="Path to save model weights")
    parser.add_argument("--output_predictions", type=str, default="data/results/predictions.json", help="Path to save predictions")

    args = parser.parse_args()

    # Enforce reproducibility
    enforce_reproducibility()

    # Setup logging
    log_operation("training_start", config_path=args.config)

    # Load configuration
    config = load_config_from_args(args)
    
    # Set device (CPU only)
    device = torch.device("cpu")
    logger.info(f"Using device: {device}")

    # Start memory tracing
    tracemalloc.start()

    # Load data
    logger.info(f"Loading graphs from {args.data_path}")
    graphs_data = load_graphs_from_parquet(Path(args.data_path))
    
    logger.info(f"Loading split indices from {args.split_path}")
    split_indices = load_split_indices(Path(args.split_path))

    # Filter and convert graphs
    (train_graphs, train_targets, train_families), \
    (test_graphs, test_targets, test_families), \
    (val_graphs, val_targets, val_families) = filter_graphs_by_split(graphs_data, split_indices)

    logger.info(f"Train size: {len(train_graphs)}, Test size: {len(test_graphs)}, Val size: {len(val_graphs)}")

    if len(train_graphs) == 0:
        logger.error("No training data found. Exiting.")
        sys.exit(1)

    # Create datasets and loaders
    train_dataset = GraphDataset(train_graphs, train_targets)
    test_dataset = GraphDataset(test_graphs, test_targets)
    val_dataset = GraphDataset(val_graphs, val_targets)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    # Initialize model
    # Determine input dimension from first graph
    input_dim = train_graphs[0].x.shape[1]
    model = LightweightGNN(input_dim=input_dim, hidden_dim=config.hidden_dim, num_layers=config.num_layers)
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    training_logs = []

    logger.info("Starting training...")
    for epoch in range(args.epochs):
        start_time = time.time()
        
        train_loss = train_epoch(model, train_loader, optimizer, device, config)
        val_loss, _, _ = evaluate(model, val_loader, device)
        
        end_time = time.time()
        epoch_time = end_time - start_time
        mem_peak = get_memory_peak()

        # Check memory limit
        if mem_peak > MAX_MEMORY_GB:
            logger.critical(f"Memory limit exceeded at epoch {epoch}: {mem_peak:.2f} GB > {MAX_MEMORY_GB} GB. Exiting.")
            sys.exit(1)

        # Log metrics
        log_entry = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "learning_rate": optimizer.param_groups[0]['lr'],
            "time_seconds": epoch_time,
            "memory_peak_gb": mem_peak,
            "disclaimer": DISCLAIMER
        }
        training_logs.append(log_entry)
        
        # Log to reproducibility logger
        log_training_metrics(epoch + 1, train_loss, val_loss, mem_peak)

        logger.info(f"Epoch {epoch+1}/{args.epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Time: {epoch_time:.2f}s, Mem: {mem_peak:.2f}GB")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), args.output_model)
            logger.info(f"Saved best model to {args.output_model}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break

        scheduler.step(val_loss)

    # Final evaluation on test set
    logger.info("Evaluating on test set...")
    test_loss, test_preds, test_targets = evaluate(model, test_loader, device)
    
    # Save predictions
    predictions_data = {
        "predictions": test_preds.tolist(),
        "targets": test_targets.tolist(),
        "test_loss": test_loss,
        "disclaimer": DISCLAIMER
    }
    with open(args.output_predictions, 'w') as f:
        json.dump(predictions_data, f, indent=2)
    logger.info(f"Predictions saved to {args.output_predictions}")

    # Save training logs
    with open(args.output_log, 'w') as f:
        json.dump(training_logs, f, indent=2)
    logger.info(f"Training logs saved to {args.output_log}")

    # Save test indices (for reference)
    test_indices = split_indices.get('test', [])
    with open(args.output_test_indices, 'w') as f:
        json.dump({"test_indices": test_indices, "disclaimer": DISCLAIMER}, f, indent=2)
    logger.info(f"Test indices saved to {args.output_test_indices}")

    logger.info("Training completed successfully.")
    log_operation("training_end", final_val_loss=best_val_loss, final_test_loss=test_loss)


if __name__ == "__main__":
    main()