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
from torch.utils.data import DataLoader, Dataset
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from model.gnn import LightweightGNN, create_model
from model.train_config import TrainingConfig, load_config_from_args
from utils.config import Config
from utils.logger import get_logger, log_training_metrics, log_model_checkpoint
from utils.memory_utils import enforce_memory_limit
from data_models.material_graph import MaterialGraph

# --- Constants ---
MEMORY_LIMIT_GB = 7.0
DEVICE = "cpu"  # Enforce CPU-only as per requirement

# --- Data Loading Utilities ---
def load_split_indices(split_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load split_indices.json containing list of objects with 'id' and 'family_id'."""
    if not split_path.exists():
        raise FileNotFoundError(f"Split indices file not found: {split_path}")
    with open(split_path, 'r') as f:
        return json.load(f)

def load_graphs_from_parquet(graphs_path: Path) -> pd.DataFrame:
    """Load the processed graphs parquet file."""
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs parquet file not found: {graphs_path}")
    return pq.read_table(graphs_path).to_pandas()

def filter_graphs_by_split(graphs_df: pd.DataFrame, split_indices: Dict[str, List[Dict[str, Any]]]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Filter the full dataframe into train, val, test sets based on split_indices."""
    train_ids = set(item['id'] for item in split_indices['train'])
    val_ids = set(item['id'] for item in split_indices['val'])
    test_ids = set(item['id'] for item in split_indices['test'])

    train_df = graphs_df[graphs_df['material_id'].isin(train_ids)].reset_index(drop=True)
    val_df = graphs_df[graphs_df['material_id'].isin(val_ids)].reset_index(drop=True)
    test_df = graphs_df[graphs_df['material_id'].isin(test_ids)].reset_index(drop=True)

    return train_df, val_df, test_df

# --- PyTorch Dataset ---
class GraphDataset(Dataset):
    def __init__(self, df: pd.DataFrame, device: str = DEVICE):
        self.df = df
        self.device = device

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # Reconstruct MaterialGraph-like structure for the model
        # Assuming columns 'node_features', 'edge_features', 'edge_index', 'target_moduli' exist in parquet
        # If edge_index is stored as a list of lists, we need to convert it to tensor
        
        node_features = torch.tensor(row['node_features'], dtype=torch.float32)
        edge_features = torch.tensor(row['edge_features'], dtype=torch.float32)
        edge_index = torch.tensor(row['edge_index'], dtype=torch.long)
        target = torch.tensor(row['target_moduli'], dtype=torch.float32)
        
        # Create a simple dict or object to pass to model, or unpack directly
        # For simplicity, we return a tuple (node_features, edge_features, edge_index, target)
        # The model's forward method must accept these or we wrap them in a Data object
        return node_features, edge_features, edge_index, target

def collate_fn(batch):
    """Collate function for DataLoader."""
    node_features_list, edge_features_list, edge_index_list, target_list = zip(*batch)
    # Stack node features (assuming variable graph sizes, we might need padding or batching differently)
    # For a simple GNN that processes one graph at a time, we can return a list of tensors
    # However, standard PyTorch Geometric expects a Batch object. 
    # Given the constraints, we will process one graph at a time in the training loop or use a custom collate
    # that creates a list of Data objects.
    
    # Let's assume the model takes a list of (node, edge, edge_index, target) and handles batching internally
    # or we use a batch size of 1 for simplicity if the model isn't designed for batching variable graphs.
    # But to be robust, we'll return the list.
    return list(zip(node_features_list, edge_features_list, edge_index_list, target_list))

# --- Training Loop ---
def train_epoch(model: nn.Module, train_loader: DataLoader, optimizer: torch.optim.Optimizer, criterion: nn.Module, device: str):
    model.train()
    total_loss = 0.0
    for batch in train_loader:
        # batch is a list of tuples (nodes, edges, edge_index, target)
        # We process one graph at a time if batch_size=1, or iterate if collate returns list
        # Assuming collate_fn returns a list of (nodes, edges, edge_index, target) for the batch
        batch_loss = 0.0
        count = 0
        for nodes, edges, edge_index, target in batch:
            nodes = nodes.to(device)
            edges = edges.to(device)
            edge_index = edge_index.to(device)
            target = target.to(device)

            optimizer.zero_grad()
            # Assuming model signature: model(node_features, edge_features, edge_index)
            # We need to ensure the model can handle the input format. 
            # LightweightGNN likely expects a Data object or separate tensors.
            # Let's assume it takes (x, edge_attr, edge_index)
            output = model(nodes, edges, edge_index)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            batch_loss += loss.item()
            count += 1
        
        total_loss += batch_loss
    
    return total_loss / max(len(train_loader), 1)

def evaluate(model: nn.Module, val_loader: DataLoader, criterion: nn.Module, device: str) -> Dict[str, float]:
    model.eval()
    total_loss = 0.0
    predictions = []
    targets = []
    
    with torch.no_grad():
        for batch in val_loader:
            for nodes, edges, edge_index, target in batch:
                nodes = nodes.to(device)
                edges = edges.to(device)
                edge_index = edge_index.to(device)
                target = target.to(device)

                output = model(nodes, edges, edge_index)
                loss = criterion(output, target)
                
                total_loss += loss.item()
                predictions.extend(output.cpu().numpy().flatten())
                targets.extend(target.cpu().numpy().flatten())
    
    predictions = np.array(predictions)
    targets = np.array(targets)
    
    mse = np.mean((predictions - targets) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(predictions - targets))
    
    return {
        "loss": total_loss / max(len(val_loader), 1),
        "rmse": rmse,
        "mae": mae
    }

def main():
    parser = argparse.ArgumentParser(description="Train GNN for elastic moduli prediction")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--data_path", type=str, required=True, help="Path to graphs_v1.parquet")
    parser.add_argument("--split_path", type=str, required=True, help="Path to split_indices.json")
    parser.add_argument("--output_log", type=str, default="data/results/training_logs.json", help="Path to output log")
    parser.add_argument("--output_test_indices", type=str, default="data/processed/test_indices.json", help="Path to output test indices")
    parser.add_argument("--output_model", type=str, default="data/processed/model_v1.pt", help="Path to save model")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger("train")
    logger.info(f"Starting training with args: {args}")
    
    # Load configuration
    if args.config:
        config = load_config_from_args(args.config)
    else:
        config = TrainingConfig(
            epochs=args.epochs,
            patience=args.patience,
            batch_size=args.batch_size,
            lr=args.lr
        )
    
    # Load data
    logger.info(f"Loading data from {args.data_path}")
    graphs_df = load_graphs_from_parquet(Path(args.data_path))
    
    logger.info(f"Loading split indices from {args.split_path}")
    split_indices = load_split_indices(Path(args.split_path))
    
    # Filter data
    train_df, val_df, test_df = filter_graphs_by_split(graphs_df, split_indices)
    logger.info(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    # Create datasets and loaders
    train_dataset = GraphDataset(train_df)
    val_dataset = GraphDataset(val_df)
    test_dataset = GraphDataset(test_df)
    
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=False, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False, collate_fn=collate_fn)
    
    # Initialize model
    logger.info("Initializing model")
    # Assuming input dim is inferred from data or set in config
    # For now, we'll use a fixed input dim or infer from first batch
    # Let's assume node_features dim is 100 and edge_features dim is 50 (example)
    # We need to get this from the data or config
    # For robustness, we'll get it from the first batch
    sample_nodes, sample_edges, _, _ = next(iter(train_loader))[0]
    node_dim = sample_nodes.shape[-1]
    edge_dim = sample_edges.shape[-1]
    
    model = create_model(node_dim=node_dim, edge_dim=edge_dim)
    model = model.to(DEVICE)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    training_logs = []
    
    # Start memory tracking
    tracemalloc.start()
    
    for epoch in range(config.epochs):
        start_time = time.time()
        
        # Check memory before epoch
        current, peak = tracemalloc.get_traced_memory()
        peak_gb = peak / 1024 ** 3
        
        if peak_gb > MEMORY_LIMIT_GB:
            logger.error(f"Memory limit exceeded: {peak_gb:.2f}GB > {MEMORY_LIMIT_GB}GB")
            sys.exit(1)
        
        train_loss = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        val_metrics = evaluate(model, val_loader, criterion, DEVICE)
        
        scheduler.step(val_metrics['loss'])
        
        end_time = time.time()
        epoch_time = end_time - start_time
        
        log_entry = {
            "epoch": epoch + 1,
            "loss": train_loss,
            "metrics": {
                "val_loss": val_metrics['loss'],
                "val_rmse": val_metrics['rmse'],
                "val_mae": val_metrics['mae']
            },
            "memory_peak": peak_gb,
            "time": epoch_time
        }
        
        training_logs.append(log_entry)
        logger.info(f"Epoch {epoch+1}/{config.epochs} - Loss: {train_loss:.4f} - Val Loss: {val_metrics['loss']:.4f} - Val RMSE: {val_metrics['rmse']:.4f} - Mem: {peak_gb:.2f}GB")
        
        # Early stopping check
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), args.output_model)
            logger.info(f"Saved best model to {args.output_model}")
        else:
            patience_counter += 1
            if patience_counter >= config.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
    
    # Stop memory tracking
    tracemalloc.stop()
    
    # Save training logs
    log_dir = Path(args.output_log).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output_log, 'w') as f:
        json.dump(training_logs, f, indent=2)
    logger.info(f"Saved training logs to {args.output_log}")
    
    # Save test indices (from split_indices)
    test_indices_path = Path(args.output_test_indices)
    test_indices_path.parent.mkdir(parents=True, exist_ok=True)
    with open(test_indices_path, 'w') as f:
        # Write only the test part of split_indices
        json.dump(split_indices['test'], f, indent=2)
    logger.info(f"Saved test indices to {test_indices_path}")
    
    # Evaluate on test set
    logger.info("Evaluating on test set")
    test_metrics = evaluate(model, test_loader, criterion, DEVICE)
    logger.info(f"Test RMSE: {test_metrics['rmse']:.4f}, Test MAE: {test_metrics['mae']:.4f}")
    
    # Save predictions
    model.eval()
    predictions = []
    targets = []
    with torch.no_grad():
        for batch in test_loader:
            for nodes, edges, edge_index, target in batch:
                nodes = nodes.to(DEVICE)
                edges = edges.to(DEVICE)
                edge_index = edge_index.to(DEVICE)
                target = target.to(DEVICE)
                
                output = model(nodes, edges, edge_index)
                predictions.extend(output.cpu().numpy().flatten())
                targets.extend(target.cpu().numpy().flatten())
    
    predictions_path = Path("data/results/predictions.json")
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    with open(predictions_path, 'w') as f:
        json.dump({
            "predictions": predictions,
            "targets": targets
        }, f, indent=2)
    logger.info(f"Saved predictions to {predictions_path}")
    
    logger.info("Training completed successfully")

if __name__ == "__main__":
    main()
