import os
import json
import logging
import argparse
import time
import gc
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch_geometric.data import Data, DataLoader as PyGDataLoader
from torch_geometric.nn import GCNConv, global_mean_pool

from utils.config import get_config, set_global_config
from model.gnn import LightweightGNN
from model.train_config import TrainingConfig, load_config_from_args
from model.train_logger import TrainingLogger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_split_indices(split_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    if not split_path.exists():
        raise FileNotFoundError(f"Split indices file not found: {split_path}")
    with open(split_path, 'r') as f:
        return json.load(f)

def load_graphs_from_parquet(parquet_path: Path) -> pd.DataFrame:
    if not parquet_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {parquet_path}")
    return pd.read_parquet(parquet_path)

def filter_graphs_by_split(df: pd.DataFrame, split_list: List[Dict[str, Any]]) -> pd.DataFrame:
    ids = [item['id'] for item in split_list]
    return df[df['material_id'].isin(ids)]

class GraphDataset(torch.utils.data.Dataset):
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # Convert features to tensors
        x = torch.tensor(row['node_features'], dtype=torch.float)
        edge_index = torch.tensor(row['edge_features'], dtype=torch.long).t().contiguous()
        y = torch.tensor(row['target_moduli'], dtype=torch.float)
        
        # Handle scalar targets
        if y.dim() == 0:
            y = y.unsqueeze(0)
        
        return Data(x=x, edge_index=edge_index, y=y)

def collate_fn(batch):
    return batch # Already Data objects, PyG DataLoader handles collation

def train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch.x, batch.edge_index)
        loss = nn.functional.mse_loss(out, batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)

def evaluate(model, loader, device):
    model.eval()
    preds = []
    truths = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index)
            preds.append(out.cpu().numpy())
            truths.append(batch.y.cpu().numpy())
    return np.concatenate(preds), np.concatenate(truths)

def main():
    parser = argparse.ArgumentParser(description="Train the GNN model")
    parser.add_argument("--config", type=Path, default=None, help="Path to config file")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--data_path", type=Path, default=None, help="Path to graphs_v1.parquet")
    parser.add_argument("--split_path", type=Path, default=None, help="Path to split_indices.json")
    parser.add_argument("--output_log", type=Path, default=None, help="Path to training_logs.json")
    parser.add_argument("--output_test_indices", type=Path, default=None, help="Path to test_indices.json")
    
    args = parser.parse_args()
    
    config = set_global_config()
    
    data_path = args.data_path or config.paths['graphs_v1']
    split_path = args.split_path or config.paths['split_indices']
    output_log = args.output_log or config.paths['training_logs']
    output_test_indices = args.output_test_indices or config.paths['generalization_metrics'].parent / "test_indices.json"
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    df = load_graphs_from_parquet(data_path)
    splits = load_split_indices(split_path)
    
    train_df = filter_graphs_by_split(df, splits['train'])
    val_df = filter_graphs_by_split(df, splits['val'])
    test_df = filter_graphs_by_split(df, splits['test'])
    
    if len(train_df) == 0:
        raise RuntimeError("Training set is empty")
    
    # Save test indices for downstream tasks
    with open(output_test_indices, 'w') as f:
        json.dump(splits['test'], f, indent=2)
    logger.info(f"Saved test indices to {output_test_indices}")
    
    # Setup dataset and loader
    train_dataset = GraphDataset(train_df)
    val_dataset = GraphDataset(val_df)
    test_dataset = GraphDataset(test_df)
    
    train_loader = PyGDataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = PyGDataLoader(val_dataset, batch_size=args.batch_size)
    test_loader = PyGDataLoader(test_dataset, batch_size=args.batch_size)
    
    # Setup model
    device = torch.device('cpu') # CPU-only as per requirement
    input_dim = train_dataset[0].x.shape[1]
    model = LightweightGNN(input_dim=input_dim, hidden_dim=64, out_dim=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    
    # Training loop
    logger.info("Starting training...")
    tracemalloc.start()
    best_val_loss = float('inf')
    patience_counter = 0
    logs = []
    
    for epoch in range(args.epochs):
        start_time = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_preds, val_truths = evaluate(model, val_loader, device)
        val_loss = np.mean((val_preds - val_truths) ** 2)
        
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        peak_gb = peak_mem / 1024 ** 3
        
        if peak_gb > 7.0:
            logger.critical(f"Memory limit exceeded: {peak_gb:.2f}GB > 7GB")
            tracemalloc.stop()
            sys.exit(1)
        
        log_entry = {
            "epoch": epoch + 1,
            "loss": float(train_loss),
            "val_loss": float(val_loss),
            "memory_peak": float(peak_gb),
            "time": time.time() - start_time
        }
        logs.append(log_entry)
        
        logger.info(f"Epoch {epoch+1}: Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, Mem={peak_gb:.2f}GB")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save model
            model_path = config.paths['model_v1']
            torch.save(model.state_dict(), model_path)
            logger.info(f"Saved best model to {model_path}")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
    
    tracemalloc.stop()
    
    # Save logs
    output_log.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log, 'w') as f:
        json.dump(logs, f, indent=2)
    logger.info(f"Saved training logs to {output_log}")
    
    # Generate predictions for test set
    test_preds, test_truths = evaluate(model, test_loader, device)
    predictions = []
    for i, idx in enumerate(splits['test']):
        predictions.append({
            "id": idx['id'],
            "true": float(test_truths[i]),
            "pred": float(test_preds[i])
        })
    
    pred_path = config.data_processed / "predictions.json"
    with open(pred_path, 'w') as f:
        json.dump(predictions, f, indent=2)
    logger.info(f"Saved predictions to {pred_path}")

if __name__ == "__main__":
    main()