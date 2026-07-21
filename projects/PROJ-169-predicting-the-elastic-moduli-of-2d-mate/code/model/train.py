"""Training loop for the lightweight GNN on 2D material elastic moduli.

This script trains the GNN defined in `model.gnn` on the dataset generated
by the ingestion pipeline. It enforces CPU-only execution, monitors memory
usage to ensure it stays under 7GB, and saves the trained model and
predictions.

**Disclaimer**: These results are derived from a machine learning surrogate
model interpolating pre-computed DFT data. They do not represent first-principles
calculations or solutions to the Schrödinger equation.
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
from torch.utils.data import DataLoader
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader as PyGDataLoader

# Project imports
from model.gnn import LightweightGNN, create_model
from model.train_config import TrainingConfig, load_config_from_args
from utils.config import enforce_reproducibility, get_config
from utils.logger import get_logger, log_operation, log_training_metrics
from utils.memory_utils import get_memory_profile, enforce_memory_limit

# Constants
MAX_MEMORY_GB = 7.0
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Ensure output directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROCESSED_DIR / "training.log"),
    ],
)
logger = logging.getLogger(__name__)
reproducibility_logger = get_logger("training")

def load_graphs_from_parquet(parquet_path: Path) -> List[Dict[str, Any]]:
    """Load graphs from a parquet file.
    
    Note: This assumes the parquet file was created by the ingestion pipeline
    and contains the necessary columns: node_features, edge_features, target_moduli, family_id.
    """
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        # Convert rows to dictionaries for processing
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Failed to load parquet file {parquet_path}: {e}")
        raise

def load_split_indices(split_path: Path) -> Dict[str, List[int]]:
    """Load train/test/validation indices from a JSON file."""
    try:
        with open(split_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load split indices from {split_path}: {e}")
        raise

def filter_graphs_by_split(
    graphs: List[Dict[str, Any]], 
    indices: List[int]
) -> List[Dict[str, Any]]:
    """Filter graphs to only include those in the specified indices."""
    return [graphs[i] for i in indices if i < len(graphs)]

def convert_to_pyg_graph(data_dict: Dict[str, Any]) -> Data:
    """Convert a dictionary representation of a graph to a PyG Data object."""
    # Extract features
    node_features = torch.tensor(data_dict['node_features'], dtype=torch.float32)
    edge_index = torch.tensor(data_dict['edge_features']['edge_index'], dtype=torch.long)
    edge_attr = torch.tensor(data_dict['edge_features']['edge_attr'], dtype=torch.float32)
    target = torch.tensor(data_dict['target_moduli'], dtype=torch.float32)
    
    # Create PyG Data object
    # Ensure edge_index is 2x num_edges
    if edge_index.dim() == 1:
        # Handle case where edge_index might be flattened incorrectly
        # Assuming standard format: [src, dst, src, dst, ...] -> reshape
        edge_index = edge_index.view(2, -1)
    
    return Data(
        x=node_features,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=target
    )

class GraphDataset(torch.utils.data.Dataset):
    """Dataset wrapper for PyTorch Geometric graphs."""
    
    def __init__(self, graphs: List[Dict[str, Any]]):
        self.graphs = [convert_to_pyg_graph(g) for g in graphs]
    
    def __len__(self):
        return len(self.graphs)
    
    def __getitem__(self, idx):
        return self.graphs[idx]

def collate_fn(batch):
    """Custom collate function for DataLoader."""
    return torch_geometric.data.Batch.from_data_list(batch)

def get_memory_peak() -> float:
    """Get the peak memory usage in GB."""
    import tracemalloc
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 ** 3)

def train_epoch(
    model: nn.Module, 
    loader: DataLoader, 
    optimizer: torch.optim.Optimizer, 
    device: torch.device
) -> Tuple[float, float]:
    """Train the model for one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        try:
            output = model(batch.x, batch.edge_index, batch.edge_attr)
            # Flatten output and target for loss calculation
            loss = nn.functional.mse_loss(output.squeeze(), batch.y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            # Check memory after each batch
            mem_peak = get_memory_peak()
            if mem_peak > MAX_MEMORY_GB:
                logger.error(f"Memory peak {mem_peak:.2f}GB exceeds limit {MAX_MEMORY_GB}GB. Stopping training.")
                sys.exit(1)
            
        except Exception as e:
            logger.error(f"Error during training batch: {e}")
            raise
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss, get_memory_peak()

def evaluate(
    model: nn.Module, 
    loader: DataLoader, 
    device: torch.device
) -> Tuple[float, float, List[float], List[float]]:
    """Evaluate the model on a dataset."""
    model.eval()
    total_loss = 0.0
    num_batches = 0
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            try:
                output = model(batch.x, batch.edge_index, batch.edge_attr)
                loss = nn.functional.mse_loss(output.squeeze(), batch.y)
                
                total_loss += loss.item()
                num_batches += 1
                
                # Collect predictions and targets
                all_predictions.extend(output.squeeze().cpu().numpy().tolist())
                all_targets.extend(batch.y.cpu().numpy().tolist())
                
            except Exception as e:
                logger.error(f"Error during evaluation batch: {e}")
                raise
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    return avg_loss, get_memory_peak(), all_predictions, all_targets

def main():
    """Main training loop."""
    parser = argparse.ArgumentParser(description="Train the GNN model.")
    parser.add_argument("--config", type=str, default=None, help="Path to config file.")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs.")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience.")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size.")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate.")
    parser.add_argument("--data_path", type=str, default=str(PROCESSED_DIR / "graphs_v1.parquet"), help="Path to parquet file.")
    parser.add_argument("--split_path", type=str, default=str(PROCESSED_DIR / "split_indices.json"), help="Path to split indices.")
    parser.add_argument("--output_log", type=str, default=str(RESULTS_DIR / "training_logs.json"), help="Path to output log.")
    parser.add_argument("--output_test_indices", type=str, default=None, help="Path to save test indices.")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config_from_args(args)
    
    # Enforce reproducibility
    enforce_reproducibility(config.seed)
    
    logger.info(f"Starting training with config: {config}")
    
    # Load data
    logger.info(f"Loading graphs from {args.data_path}")
    graphs = load_graphs_from_parquet(Path(args.data_path))
    logger.info(f"Loaded {len(graphs)} graphs.")
    
    # Load split indices
    logger.info(f"Loading split indices from {args.split_path}")
    split_indices = load_split_indices(Path(args.split_path))
    train_indices = split_indices.get('train', [])
    test_indices = split_indices.get('test', [])
    
    logger.info(f"Train size: {len(train_indices)}, Test size: {len(test_indices)}")
    
    # Filter graphs by split
    train_graphs = filter_graphs_by_split(graphs, train_indices)
    test_graphs = filter_graphs_by_split(graphs, test_indices)
    
    # Create datasets and loaders
    train_dataset = GraphDataset(train_graphs)
    test_dataset = GraphDataset(test_graphs)
    
    train_loader = PyGDataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    test_loader = PyGDataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)
    
    # Create model
    device = torch.device("cpu")  # Enforce CPU-only
    logger.info(f"Using device: {device}")
    
    model = create_model(config).to(device)
    logger.info(f"Model created: {model}")
    
    # Optimizer and loss function
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # Training loop
    best_loss = float('inf')
    patience_counter = 0
    training_logs = []
    
    start_time = time.time()
    
    for epoch in range(config.epochs):
        epoch_start = time.time()
        
        # Train
        train_loss, train_mem_peak = train_epoch(model, train_loader, optimizer, device)
        
        # Evaluate
        test_loss, test_mem_peak, predictions, targets = evaluate(model, test_loader, device)
        
        # Calculate metrics
        predictions = np.array(predictions)
        targets = np.array(targets)
        mape = np.mean(np.abs((targets - predictions) / (targets + 1e-8))) * 100
        rmse = np.sqrt(np.mean((targets - predictions) ** 2))
        
        # Log metrics
        log_entry = {
            "epoch": epoch + 1,
            "loss": float(train_loss),
            "metrics": {
                "mape": float(mape),
                "rmse": float(rmse)
            },
            "memory_peak": float(max(train_mem_peak, test_mem_peak)),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        training_logs.append(log_entry)
        
        # Log to file
        log_training_metrics(log_entry)
        
        logger.info(f"Epoch {epoch+1}: Loss={train_loss:.4f}, MAPE={mape:.2f}%, RMSE={rmse:.4f}, Mem={max(train_mem_peak, test_mem_peak):.2f}GB")
        
        # Early stopping
        if test_loss < best_loss:
            best_loss = test_loss
            patience_counter = 0
            # Save model
            model_path = PROCESSED_DIR / "model_v1.pt"
            torch.save(model.state_dict(), model_path)
            logger.info(f"Saved best model to {model_path}")
        else:
            patience_counter += 1
            if patience_counter >= config.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # Update scheduler
        scheduler.step(test_loss)
        
        epoch_time = time.time() - epoch_start
        logger.info(f"Epoch {epoch+1} took {epoch_time:.2f}s")
    
    total_time = time.time() - start_time
    logger.info(f"Training completed in {total_time:.2f}s")
    
    # Save final predictions
    predictions_file = RESULTS_DIR / "predictions.json"
    with open(predictions_file, 'w') as f:
        json.dump({
            "predictions": predictions.tolist(),
            "targets": targets.tolist(),
            "metrics": {
                "mape": float(mape),
                "rmse": float(rmse)
            },
            "disclaimer": "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation."
        }, f, indent=2)
    logger.info(f"Saved predictions to {predictions_file}")
    
    # Save training logs
    with open(args.output_log, 'w') as f:
        json.dump({
            "logs": training_logs,
            "config": vars(config),
            "disclaimer": "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation."
        }, f, indent=2)
    logger.info(f"Saved training logs to {args.output_log}")
    
    # Save test indices if requested
    if args.output_test_indices:
        with open(args.output_test_indices, 'w') as f:
            json.dump(test_indices, f)
        logger.info(f"Saved test indices to {args.output_test_indices}")
    
    logger.info("Training finished successfully.")

if __name__ == "__main__":
    main()