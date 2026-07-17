"""
Training script for the Lightweight GNN surrogate model.

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
from typing import List, Dict, Any, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch_geometric.data import Data
import numpy as np

# Import project utilities
from utils.config import Config
from utils.logger import get_logger, log_training_metrics
from utils.memory_utils import get_memory_profile
from data_models.material_graph import MaterialGraph
from model.gnn import LightweightGNN, create_model
from model.splitter import load_graphs_from_parquet

# Configure logging
logger = get_logger(__name__)

# Explicit Surrogate Model Warning
SURROGATE_WARNING = (
    "WARNING: This model is a surrogate interpolating pre-computed DFT results. "
    "It does NOT solve the Schrödinger equation or perform first-principles calculations. "
    "All predictions are statistical interpolations within the chemical space of the training data."
)

class GraphDataset(Dataset):
    """PyTorch Dataset wrapper for MaterialGraphs."""

    def __init__(self, graphs: List[MaterialGraph], transform=None):
        self.graphs = graphs
        self.transform = transform

    def __len__(self):
        return len(self.graphs)

    def __getitem__(self, idx):
        graph = self.graphs[idx]
        if self.transform:
            graph = self.transform(graph)
        return graph

def collate_fn(batch):
    """Custom collate function to convert list of MaterialGraphs to PyG Data."""
    # We expect the batch to contain MaterialGraph objects or dicts that need conversion
    pyg_batch = []
    for item in batch:
        if isinstance(item, MaterialGraph):
            pyg_batch.append(graph_to_pyg(item))
        else:
            # Assume it's already a dict or Data object if passed differently
            pyg_batch.append(item)
    # PyG collate handles the rest
    return torch.utils.data.default_collate(pyg_batch)

def graph_to_pyg(graph: MaterialGraph) -> Data:
    """Convert MaterialGraph dataclass to PyTorch Geometric Data object."""
    # Ensure features are tensors
    x = torch.tensor(graph.node_features, dtype=torch.float32)
    edge_index = torch.tensor(graph.edge_index, dtype=torch.long)
    edge_attr = torch.tensor(graph.edge_features, dtype=torch.float32) if graph.edge_features is not None else None
    
    # Target: Elastic moduli (Young's, Shear, Poisson)
    # Assuming target_moduli is a list or array of 3 values
    y = torch.tensor(graph.target_moduli, dtype=torch.float32).view(1, -1)

    data = Data(x=x, edge_index=edge_index, y=y)
    if edge_attr is not None:
        data.edge_attr = edge_attr
    
    return data

def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, device: str) -> float:
    """Train the model for one epoch."""
    model.train()
    total_loss = 0.0
    criterion = nn.MSELoss()

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        out = model(batch)
        # Handle output shape if necessary (model might return 1D or 2D)
        if out.dim() == 1:
            out = out.unsqueeze(1)
        
        loss = criterion(out, batch.y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()

    return total_loss / len(loader)

def evaluate(model: nn.Module, loader: DataLoader, device: str) -> Dict[str, float]:
    """Evaluate the model on a dataset."""
    model.eval()
    total_loss = 0.0
    criterion = nn.MSELoss()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch)
            if out.dim() == 1:
                out = out.unsqueeze(1)
            
            loss = criterion(out, batch.y)
            total_loss += loss.item()
            
            all_preds.append(out.cpu().numpy())
            all_targets.append(batch.y.cpu().numpy())

    all_preds = np.vstack(all_preds) if all_preds else np.array([])
    all_targets = np.vstack(all_targets) if all_targets else np.array([])

    # Calculate metrics
    mse = total_loss / len(loader)
    rmse = np.sqrt(mse)
    
    # MAPE calculation (handle zeros)
    if np.any(all_targets != 0):
        mape = np.mean(np.abs((all_targets - all_preds) / (all_targets + 1e-8))) * 100
    else:
        mape = 0.0

    return {
        "loss": mse,
        "rmse": float(rmse),
        "mape": float(mape)
    }

def main():
    """Main training loop with early stopping and logging."""
    print(SURROGATE_WARNING)
    logger.warning(SURROGATE_WARNING)

    parser = argparse.ArgumentParser(description="Train Lightweight GNN Surrogate Model")
    parser.add_argument("--data_path", type=str, default="data/processed/graphs_v1.parquet",
                        help="Path to processed graphs parquet file")
    parser.add_argument("--split_manifest", type=str, default="data/results/split_manifest.json",
                        help="Path to split manifest file")
    parser.add_argument("--output_dir", type=str, default="data/results",
                        help="Directory to save logs and checkpoints")
    parser.add_argument("--epochs", type=int, default=100, help="Maximum epochs")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--hidden_dim", type=int, default=64, help="Hidden dimension")
    parser.add_argument("--num_layers", type=int, default=3, help="Number of GNN layers")
    args = parser.parse_args()

    # Setup
    config = Config()
    config.seed_everything()
    
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    log_file = output_path / "training_logs.json"
    log_entries = []

    device = torch.device("cpu")  # CPU execution as required
    logger.info(f"Using device: {device}")

    # Load Data
    logger.info(f"Loading graphs from {args.data_path}")
    graphs = load_graphs_from_parquet(args.data_path)
    logger.info(f"Loaded {len(graphs)} graphs")

    # Load Split Manifest
    logger.info(f"Loading split manifest from {args.split_manifest}")
    with open(args.split_manifest, 'r') as f:
        split_data = json.load(f)
    
    train_indices = split_data.get("train_indices", [])
    val_indices = split_data.get("val_indices", [])

    train_graphs = [graphs[i] for i in train_indices]
    val_graphs = [graphs[i] for i in val_indices]

    logger.info(f"Train size: {len(train_graphs)}, Val size: {len(val_graphs)}")

    # Create Datasets and Loaders
    train_dataset = GraphDataset(train_graphs)
    val_dataset = GraphDataset(val_graphs)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    # Initialize Model
    model = create_model(hidden_dim=args.hidden_dim, num_layers=args.num_layers)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

    # Training Loop
    best_val_loss = float('inf')
    patience_counter = 0
    
    logger.info("Starting training loop...")
    tracemalloc.start()

    for epoch in range(args.epochs):
        start_time = time.time()
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, device)
        
        # Evaluate
        val_metrics = evaluate(model, val_loader, device)
        val_loss = val_metrics["loss"]
        
        scheduler.step(val_loss)

        # Memory Profile
        current_mem, peak_mem = get_memory_profile()
        memory_peak_gb = peak_mem / (1024 ** 3)

        # Log Entry
        log_entry = {
            "epoch": epoch + 1,
            "loss": float(train_loss),
            "metrics": {
                "mape": val_metrics["mape"],
                "rmse": val_metrics["rmse"]
            },
            "memory_peak": memory_peak_gb,
            "val_loss": float(val_loss),
            "lr": optimizer.param_groups[0]['lr'],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        log_entries.append(log_entry)

        # Log to file and console
        log_training_metrics(log_entry)
        logger.info(f"Epoch {epoch+1}: Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, "
                    f"MAPE={val_metrics['mape']:.2f}%, RMSE={val_metrics['rmse']:.4f}, "
                    f"Peak Mem={memory_peak_gb:.2f}GB")

        # Early Stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save checkpoint
            checkpoint_path = output_path / "best_model.pth"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': best_val_loss,
            }, checkpoint_path)
            logger.info(f"Checkpoint saved to {checkpoint_path}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break

        # Cleanup
        gc.collect()
        if device.type == 'cuda':
            torch.cuda.empty_cache()

    tracemalloc.stop()

    # Final Save
    with open(log_file, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    logger.info(f"Training logs saved to {log_file}")
    logger.info("Training completed.")

if __name__ == "__main__":
    main()