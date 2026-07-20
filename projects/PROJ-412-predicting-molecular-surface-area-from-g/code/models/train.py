import os
import sys
import json
import logging
import argparse
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn.functional as F
from torch_geometric.data import Data, DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

# Local imports
from models.gcn import GCNModel, create_model_from_processed_data
from models.evaluation import EvaluationResult
from utils.seed import set_seed
from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir, get_results_dir

logger = get_logger(__name__)

# Configuration constants
MEMORY_THRESHOLD_MB = 1024.0  # Default 1GB threshold, adjustable via env
MAX_EPOCHS = 50
PATIENCE = 5
BATCH_SIZE = 32

def load_processed_graphs(
    data_path: Path,
    device: torch.device
) -> Tuple[List[Data], List[Data]]:
    """
    Load processed graphs from parquet file and convert to PyTorch Geometric Data objects.
    Returns train and test splits based on indices in data/splits.
    """
    logger.info(f"Loading processed data from {data_path}")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")

    df = pd.read_parquet(data_path)
    
    # Load split indices
    split_dir = get_data_dir() / "splits"
    train_indices_path = split_dir / "train_indices.csv"
    test_indices_path = split_dir / "test_indices.csv"

    if not train_indices_path.exists() or not test_indices_path.exists():
        raise FileNotFoundError("Split indices not found. Run data splitting first.")

    train_indices = pd.read_csv(train_indices_path)['index'].tolist()
    test_indices = pd.read_csv(test_indices_path)['index'].tolist()

    # Filter dataframe
    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)

    logger.info(f"Loaded {len(train_df)} train and {len(test_df)} test samples")

    def df_to_graphs(df: pd.DataFrame) -> List[Data]:
        graphs = []
        for _, row in df.iterrows():
            # Extract node and edge features
            node_features = np.array(row['node_features'])
            edge_index = np.array(row['edge_features']).T  # Assuming [2, E] format
            edge_attr = None  # Simplified: no edge attributes for now
            
            # Create PyTorch Geometric Data object
            data = Data(
                x=torch.tensor(node_features, dtype=torch.float),
                edge_index=torch.tensor(edge_index, dtype=torch.long),
                y=torch.tensor([row['surface_area']], dtype=torch.float)
            )
            graphs.append(data)
        return graphs

    train_graphs = df_to_graphs(train_df)
    test_graphs = df_to_graphs(test_df)

    return train_graphs, test_graphs

def train_epoch(
    model: GCNModel,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> Tuple[float, float]:
    """
    Train for one epoch and return loss and MAE.
    """
    model.train()
    total_loss = 0.0
    total_mae = 0.0
    count = 0

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        out = model(batch.x, batch.edge_index, batch.batch)
        loss = F.mse_loss(out, batch.y)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * batch.num_graphs
        
        # Calculate MAE for this batch
        mae = torch.mean(torch.abs(out - batch.y)).item()
        total_mae += mae * batch.num_graphs
        count += batch.num_graphs

    return total_loss / count, total_mae / count

def evaluate(
    model: GCNModel,
    loader: DataLoader,
    device: torch.device
) -> Dict[str, float]:
    """
    Evaluate model on loader and return metrics.
    """
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    total_rmse = 0.0
    total_r2_num = 0.0
    total_r2_den = 0.0
    count = 0

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            
            loss = F.mse_loss(out, batch.y)
            total_loss += loss.item() * batch.num_graphs
            
            mae = torch.mean(torch.abs(out - batch.y)).item()
            total_mae += mae * batch.num_graphs
            
            rmse = torch.sqrt(torch.mean((out - batch.y) ** 2)).item()
            total_rmse += rmse * batch.num_graphs
            
            # R2 calculation
            ss_res = torch.sum((batch.y - out) ** 2).item()
            ss_tot = torch.sum((batch.y - torch.mean(batch.y)) ** 2).item()
            total_r2_num += ss_res * batch.num_graphs
            total_r2_den += ss_tot * batch.num_graphs
            
            count += batch.num_graphs

    r2 = 1.0 - (total_r2_num / total_r2_den) if total_r2_den > 0 else 0.0

    return {
        'loss': total_loss / count,
        'mae': total_mae / count,
        'rmse': total_rmse / count,
        'r2': r2
    }

class EarlyStopping:
    def __init__(self, patience: int = 5, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
            return False
        
        if val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        
        return self.early_stop

def train_model(
    train_graphs: List[Data],
    test_graphs: List[Data],
    device: torch.device,
    epochs: int = MAX_EPOCHS,
    patience: int = PATIENCE,
    batch_size: int = BATCH_SIZE,
    memory_threshold_mb: float = MEMORY_THRESHOLD_MB
) -> Tuple[GCNModel, Dict[str, Any]]:
    """
    Train the GCN model with early stopping and memory profiling.
    
    Args:
        train_graphs: List of training graphs
        test_graphs: List of test graphs
        device: PyTorch device
        epochs: Maximum number of epochs
        patience: Early stopping patience
        batch_size: Batch size for training
        memory_threshold_mb: RAM threshold in MB to trigger early exit
        
    Returns:
        Trained model and training history with memory stats
    """
    logger.info(f"Starting training on device: {device}")
    logger.info(f"Memory threshold set to {memory_threshold_mb} MB")
    
    # Create model
    model = create_model_from_processed_data(train_graphs[0].x.shape[1])
    model = model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)
    
    # Create data loaders
    train_loader = DataLoader(train_graphs, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_graphs, batch_size=batch_size, shuffle=False)
    
    early_stopping = EarlyStopping(patience=patience)
    
    # Memory profiling
    tracemalloc.start()
    
    history = {
        'train_loss': [],
        'train_mae': [],
        'val_loss': [],
        'val_mae': [],
        'val_rmse': [],
        'val_r2': [],
        'peak_memory_mb': [],
        'epoch': []
    }
    
    best_model_state = None
    best_val_loss = float('inf')
    
    for epoch in range(epochs):
        # Train
        train_loss, train_mae = train_epoch(model, train_loader, optimizer, device)
        
        # Evaluate
        val_metrics = evaluate(model, test_loader, device)
        
        # Memory profiling
        current, peak = tracemalloc.get_traced_memory()
        peak_memory_mb = peak / (1024 * 1024)
        
        # Log memory stats
        logger.info(f"Epoch {epoch+1}/{epochs} | "
                    f"Train Loss: {train_loss:.4f}, Train MAE: {train_mae:.4f} | "
                    f"Val Loss: {val_metrics['loss']:.4f}, Val MAE: {val_metrics['mae']:.4f}, "
                    f"Val RMSE: {val_metrics['rmse']:.4f}, Val R2: {val_metrics['r2']:.4f} | "
                    f"Peak RAM: {peak_memory_mb:.2f} MB")
        
        # Record history
        history['train_loss'].append(train_loss)
        history['train_mae'].append(train_mae)
        history['val_loss'].append(val_metrics['loss'])
        history['val_mae'].append(val_metrics['mae'])
        history['val_rmse'].append(val_metrics['rmse'])
        history['val_r2'].append(val_metrics['r2'])
        history['peak_memory_mb'].append(peak_memory_mb)
        history['epoch'].append(epoch + 1)
        
        # Check memory threshold
        if peak_memory_mb > memory_threshold_mb:
            logger.warning(f"Memory threshold exceeded: {peak_memory_mb:.2f} MB > {memory_threshold_mb} MB")
            logger.warning("Triggering early exit with diagnostic report")
            
            # Save diagnostic report
            diag_report = {
                'status': 'memory_limit_exceeded',
                'peak_memory_mb': peak_memory_mb,
                'threshold_mb': memory_threshold_mb,
                'epoch': epoch + 1,
                'train_loss': train_loss,
                'val_loss': val_metrics['loss'],
                'val_mae': val_metrics['mae'],
                'val_rmse': val_metrics['rmse'],
                'val_r2': val_metrics['r2']
            }
            
            results_dir = get_results_dir()
            diag_path = results_dir / "memory_diagnostic.json"
            with open(diag_path, 'w') as f:
                json.dump(diag_report, f, indent=2)
            logger.info(f"Diagnostic report saved to {diag_path}")
            
            # Save partial model
            partial_model_path = get_data_dir() / "models" / "partial_model.pt"
            partial_model_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'history': history,
                'peak_memory_mb': peak_memory_mb,
                'reason': 'memory_limit_exceeded'
            }, partial_model_path)
            logger.info(f"Partial model saved to {partial_model_path}")
            
            tracemalloc.stop()
            return model, history
        
        # Update best model
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            best_model_state = model.state_dict().copy()
        
        # Learning rate scheduling
        scheduler.step(val_metrics['loss'])
        
        # Early stopping check
        if early_stopping(val_metrics['loss']):
            logger.info(f"Early stopping triggered at epoch {epoch+1}")
            break
    
    # Restore best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Save final model
    model_dir = get_data_dir() / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    torch.save({
        'epoch': len(history['epoch']),
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'history': history,
        'best_val_loss': best_val_loss
    }, model_dir / "gcn_model.pt")
    logger.info(f"Model saved to {model_dir / 'gcn_model.pt'}")
    
    tracemalloc.stop()
    return model, history

def main():
    parser = argparse.ArgumentParser(description="Train GCN model for molecular surface area prediction")
    parser.add_argument("--data_path", type=str, default=None, help="Path to processed data parquet file")
    parser.add_argument("--epochs", type=int, default=MAX_EPOCHS, help="Maximum number of epochs")
    parser.add_argument("--patience", type=int, default=PATIENCE, help="Early stopping patience")
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE, help="Batch size")
    parser.add_argument("--memory_threshold", type=float, default=MEMORY_THRESHOLD_MB, help="Memory threshold in MB")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    # Setup
    set_seed(args.seed)
    device = torch.device("cpu")  # CPU-only as per spec
    logger.info(f"Using device: {device}")
    
    # Load data
    if args.data_path is None:
        data_path = get_data_dir() / "processed" / "graphs_with_features.parquet"
    else:
        data_path = Path(args.data_path)
    
    try:
        train_graphs, test_graphs = load_processed_graphs(data_path, device)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if len(train_graphs) == 0 or len(test_graphs) == 0:
        logger.error("No data loaded. Check split indices and data file.")
        sys.exit(1)
    
    # Train model
    model, history = train_model(
        train_graphs,
        test_graphs,
        device,
        epochs=args.epochs,
        patience=args.patience,
        batch_size=args.batch_size,
        memory_threshold_mb=args.memory_threshold
    )
    
    # Save history
    history_path = get_results_dir() / "reports" / "training_history.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    logger.info(f"Training history saved to {history_path}")
    
    # Print summary
    logger.info("Training completed!")
    logger.info(f"Final Val MAE: {history['val_mae'][-1]:.4f}")
    logger.info(f"Final Val R2: {history['val_r2'][-1]:.4f}")
    logger.info(f"Peak Memory: {max(history['peak_memory_mb']):.2f} MB")

if __name__ == "__main__":
    main()