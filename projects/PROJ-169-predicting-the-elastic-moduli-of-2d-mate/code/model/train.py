"""Training script for Structure-Only Surrogate Model.

WARNING: This model is a SURROGATE for DFT calculations. It does NOT solve
the Schrödinger equation. It interpolates elastic properties from existing
DFT data found in public repositories.
"""
import os
import json
import logging
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import DataLoader
import numpy as np

from model.gnn import create_model, LightweightGNN
from model.splitter import split_by_family, save_split_manifest
from utils.config import Config
from utils.logger import get_logger

logger = get_logger("train")

def load_graphs_from_parquet(path: Path):
    """Load graphs from parquet file."""
    import pyarrow.parquet as pq
    table = pq.read_table(path)
    # Convert to list of dicts
    return [row.as_py() for row in table.to_pydict()]

def graph_to_pyg(graph_dict: Dict[str, Any]):
    """Convert material graph dict to PyTorch Geometric Data."""
    import torch
    from torch_geometric.data import Data
    import numpy as np

    # Create node features (simplified: atomic number)
    nodes = graph_dict.get('nodes', [])
    x = torch.tensor([[n['atomic_number']] for n in nodes], dtype=torch.float)
    
    # Edge index
    edge_index = graph_dict.get('edge_index', np.zeros((2, 0), dtype=int))
    if isinstance(edge_index, list):
        edge_index = np.array(edge_index)
    edge_index = torch.tensor(edge_index, dtype=torch.long)
    
    # Batch
    batch = torch.zeros(len(nodes), dtype=torch.long)
    
    # Target
    target = graph_dict.get('target_tensor')
    y = torch.tensor(target, dtype=torch.float) if target is not None else torch.zeros(6)
    
    return Data(x=x, edge_index=edge_index, y=y, batch=batch)

def train_epoch(model: LightweightGNN, loader: DataLoader, optimizer: optim.Optimizer, device: str):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch.x, batch.edge_index, batch.batch)
        loss = nn.MSELoss()(out, batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)

def evaluate(model: LightweightGNN, loader: DataLoader, device: str) -> Dict[str, float]:
    """Evaluate model."""
    model.eval()
    total_loss = 0
    preds, targets = [], []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = nn.MSELoss()(out, batch.y)
            total_loss += loss.item()
            preds.extend(out.cpu().numpy())
            targets.extend(batch.y.cpu().numpy())
    
    preds = np.array(preds)
    targets = np.array(targets)
    
    mape = np.mean(np.abs((preds - targets) / (targets + 1e-8))) * 100
    rmse = np.sqrt(np.mean((preds - targets) ** 2))
    r2 = 1 - np.sum((preds - targets) ** 2) / np.sum((targets - np.mean(targets)) ** 2)
    
    return {'loss': total_loss / len(loader), 'mape': mape, 'rmse': rmse, 'r2': r2}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='data/processed/graphs_v1.parquet')
    parser.add_argument('--output', default='data/results/training_logs.json')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--patience', type=int, default=3)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--batch_size', type=int, default=32)
    args = parser.parse_args()

    # Setup
    config = Config()
    device = config.device
    logger.info(f"Using device: {device}")
    logger.warning("WARNING: This model is a SURROGATE for DFT calculations. It does NOT solve the Schrödinger equation.")

    # Load data
    graphs = load_graphs_from_parquet(Path(args.data))
    logger.info(f"Loaded {len(graphs)} graphs")

    # Split by family
    split_manifest = split_by_family(graphs)
    save_split_manifest(split_manifest, Path('data/splits/split_manifest.json'))

    # Convert to PyG
    train_graphs = [g for g in graphs if g['material_id'] in split_manifest.train_ids]
    val_graphs = [g for g in graphs if g['material_id'] in split_manifest.val_ids]
    test_graphs = [g for g in graphs if g['material_id'] in split_manifest.test_ids]

    train_loader = DataLoader([graph_to_pyg(g) for g in train_graphs], batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader([graph_to_pyg(g) for g in val_graphs], batch_size=args.batch_size)
    test_loader = DataLoader([graph_to_pyg(g) for g in test_graphs], batch_size=args.batch_size)

    # Model
    model = create_model(node_dim=1, hidden_dim=64, num_layers=2).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=2, factor=0.5)

    # Training loop with early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    training_log = []

    for epoch in range(args.epochs):
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_metrics = evaluate(model, val_loader, device)
        scheduler.step(val_metrics['loss'])

        log_entry = {
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_metrics['loss'],
            'val_mape': val_metrics['mape'],
            'val_rmse': val_metrics['rmse'],
            'val_r2': val_metrics['r2']
        }
        training_log.append(log_entry)
        logger.info(f"Epoch {epoch+1}: train_loss={train_loss:.4f}, val_mape={val_metrics['mape']:.2f}%")

        # Early stopping
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            patience_counter = 0
            torch.save(model.state_dict(), 'data/results/best_model.pt')
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

    # Final evaluation on test set
    test_metrics = evaluate(model, test_loader, device)
    logger.info(f"Test MAPE: {test_metrics['mape']:.2f}%, RMSE: {test_metrics['rmse']:.4f}, R2: {test_metrics['r2']:.4f}")

    # Save logs
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'training_log': training_log,
            'test_metrics': test_metrics,
            'config': vars(args)
        }, f, indent=2)
    logger.info(f"Training logs saved to {output_path}")

if __name__ == '__main__':
    main()
