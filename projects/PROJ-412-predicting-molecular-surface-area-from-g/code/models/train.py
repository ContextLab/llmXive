"""
Training loop for the GCN model with early stopping.

Implements training for the Molecular Surface Area prediction task.
Uses PyTorch Geometric for the GCN model and implements early stopping
based on validation loss.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import torch
import torch.nn.functional as F
from torch_geometric.data import DataLoader
from torch_geometric.utils import to_undirected
import numpy as np

# Local imports
from models.gcn import GCNModel, create_model_from_processed_data
from models.evaluation import EvaluationResult
from utils.seed import set_seed, get_seed_from_env
from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir, get_results_dir
from data.split import load_processed_data, SplitResult

# Constants
DEFAULT_EPOCHS = 50
DEFAULT_PATIENCE = 5
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_BATCH_SIZE = 32
DEFAULT_DEVICE = "cpu"

logger = get_logger(__name__)


def load_processed_graphs(data_path: Path, split_indices: Dict[str, list]) -> Tuple[list, list]:
    """
    Load processed graph data from the split indices.
    
    Args:
        data_path: Path to the processed data directory
        split_indices: Dictionary containing train and test indices
        
    Returns:
        Tuple of (train_loader, test_loader)
    """
    logger.info(f"Loading processed data from {data_path}")
    
    # Load the processed data (assuming Parquet format with graph features)
    # This assumes T015 has created the split indices and T013/T014 have created the processed data
    try:
        # Load the main processed data file
        import pandas as pd
        processed_df = pd.read_parquet(data_path / "processed_data.parquet")
        
        # We need to reconstruct PyTorch Geometric Data objects
        # For this implementation, we'll assume the processed data has columns:
        # 'node_features', 'edge_index', 'edge_features', 'sasa'
        # and we'll use the split indices to separate train/test
        
        train_indices = split_indices.get('train', [])
        test_indices = split_indices.get('test', [])
        
        train_data_list = []
        test_data_list = []
        
        # Filter data by indices
        train_df = processed_df.iloc[train_indices]
        test_df = processed_df.iloc[test_indices]
        
        logger.info(f"Loaded {len(train_df)} training samples and {len(test_df)} test samples")
        
        # Convert to PyTorch Geometric Data objects
        # This is a simplified conversion - in a real implementation, 
        # the data would be pre-converted during preprocessing
        from torch_geometric.data import Data
        
        for idx, row in train_df.iterrows():
            # Extract features from the row
            # Assuming node_features is stored as a numpy array string or similar
            node_features = np.array(row['node_features']) if isinstance(row['node_features'], str) else row['node_features']
            edge_index = np.array(row['edge_index']) if isinstance(row['edge_index'], str) else row['edge_index']
            sasa = float(row['sasa'])
            
            # Convert edge_index to PyTorch tensor
            edge_index_tensor = torch.tensor(edge_index, dtype=torch.long)
            node_features_tensor = torch.tensor(node_features, dtype=torch.float)
            
            # Create Data object
            data = Data(
                x=node_features_tensor,
                edge_index=edge_index_tensor,
                y=torch.tensor([sasa], dtype=torch.float)
            )
            train_data_list.append(data)
            
        for idx, row in test_df.iterrows():
            node_features = np.array(row['node_features']) if isinstance(row['node_features'], str) else row['node_features']
            edge_index = np.array(row['edge_index']) if isinstance(row['edge_index'], str) else row['edge_index']
            sasa = float(row['sasa'])
            
            edge_index_tensor = torch.tensor(edge_index, dtype=torch.long)
            node_features_tensor = torch.tensor(node_features, dtype=torch.float)
            
            data = Data(
                x=node_features_tensor,
                edge_index=edge_index_tensor,
                y=torch.tensor([sasa], dtype=torch.float)
            )
            test_data_list.append(data)
            
        # Create data loaders
        train_loader = DataLoader(train_data_list, batch_size=DEFAULT_BATCH_SIZE, shuffle=True)
        test_loader = DataLoader(test_data_list, batch_size=DEFAULT_BATCH_SIZE, shuffle=False)
        
        return train_loader, test_loader
        
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        raise


def train_epoch(
    model: GCNModel,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    criterion: torch.nn.Module
) -> float:
    """
    Train the model for one epoch.
    
    Args:
        model: The GCN model to train
        loader: DataLoader for training data
        optimizer: Optimizer for the model
        device: Device to run training on
        criterion: Loss function
        
    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch in loader:
        batch = batch.to(device)
        
        optimizer.zero_grad()
        output = model(batch)
        loss = criterion(output, batch.y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        
    return total_loss / num_batches


def evaluate(
    model: GCNModel,
    loader: DataLoader,
    device: torch.device,
    criterion: torch.nn.Module
) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Evaluate the model on a dataset.
    
    Args:
        model: The GCN model to evaluate
        loader: DataLoader for evaluation data
        device: Device to run evaluation on
        criterion: Loss function
        
    Returns:
        Tuple of (average loss, predictions, targets)
    """
    model.eval()
    total_loss = 0.0
    all_predictions = []
    all_targets = []
    num_batches = 0
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            
            output = model(batch)
            loss = criterion(output, batch.y)
            
            total_loss += loss.item()
            all_predictions.extend(output.cpu().numpy().flatten())
            all_targets.extend(batch.y.cpu().numpy().flatten())
            num_batches += 1
            
    return total_loss / num_batches, np.array(all_predictions), np.array(all_targets)


def early_stopping(
    patience: int,
    threshold: float = 0.0
):
    """
    Early stopping callback that tracks validation loss.
    
    Args:
        patience: Number of epochs to wait before stopping
        threshold: Minimum change to qualify as improvement
        
    Returns:
        Function that returns True if training should stop
    """
    best_loss = float('inf')
    epochs_without_improvement = 0
    
    def callback(val_loss: float) -> bool:
        nonlocal best_loss, epochs_without_improvement
        
        if val_loss < best_loss - threshold:
            best_loss = val_loss
            epochs_without_improvement = 0
            return False
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= patience:
                return True
            return False
            
    return callback


def train_model(
    train_loader: DataLoader,
    test_loader: DataLoader,
    model: GCNModel,
    epochs: int = DEFAULT_EPOCHS,
    patience: int = DEFAULT_PATIENCE,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    device: torch.device = torch.device(DEFAULT_DEVICE),
    checkpoint_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Train the GCN model with early stopping.
    
    Args:
        train_loader: DataLoader for training data
        test_loader: DataLoader for validation/test data
        model: The GCN model to train
        epochs: Maximum number of epochs
        patience: Patience for early stopping
        learning_rate: Learning rate for optimizer
        device: Device to train on
        checkpoint_path: Path to save the best model checkpoint
        
    Returns:
        Dictionary containing training history and final metrics
    """
    logger.info(f"Starting training on device: {device}")
    logger.info(f"Max epochs: {epochs}, Patience: {patience}")
    
    # Move model to device
    model = model.to(device)
    
    # Optimizer and loss function
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = torch.nn.MSELoss()
    
    # Early stopping callback
    stop_callback = early_stopping(patience=patience)
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'best_val_loss': float('inf'),
        'best_epoch': 0,
        'stopped_early': False,
        'epochs_trained': 0
    }
    
    best_model_state = None
    
    for epoch in range(epochs):
        # Train for one epoch
        train_loss = train_epoch(model, train_loader, optimizer, device, criterion)
        
        # Evaluate on validation set
        val_loss, _, _ = evaluate(model, test_loader, device, criterion)
        
        # Update history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
        
        # Save best model
        if val_loss < history['best_val_loss']:
            history['best_val_loss'] = val_loss
            history['best_epoch'] = epoch + 1
            best_model_state = model.state_dict().copy()
            
            if checkpoint_path:
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': best_model_state,
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': val_loss,
                    'history': history
                }, checkpoint_path)
                logger.info(f"Saved best model checkpoint to {checkpoint_path}")
        
        # Check early stopping
        if stop_callback(val_loss):
            logger.info(f"Early stopping triggered at epoch {epoch+1}")
            history['stopped_early'] = True
            history['epochs_trained'] = epoch + 1
            break
            
    if not history['stopped_early']:
        history['epochs_trained'] = epochs
        
    # Load best model state
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        
    return history, model


def main():
    """
    Main entry point for the training script.
    """
    parser = argparse.ArgumentParser(description="Train GCN model for molecular surface area prediction")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Maximum number of epochs")
    parser.add_argument("--patience", type=int, default=DEFAULT_PATIENCE, help="Patience for early stopping")
    parser.add_argument("--lr", type=float, default=DEFAULT_LEARNING_RATE, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--device", type=str, default=DEFAULT_DEVICE, help="Device to train on")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--data_dir", type=str, default=None, help="Path to processed data directory")
    parser.add_argument("--results_dir", type=str, default=None, help="Path to results directory")
    
    args = parser.parse_args()
    
    # Setup logging
    logger.info("Starting training script")
    
    # Set random seed
    if args.seed is not None:
        set_seed(args.seed)
        logger.info(f"Random seed set to {args.seed}")
    else:
        seed = get_seed_from_env()
        set_seed(seed)
        logger.info(f"Random seed set to {seed} from environment")
        
    # Determine paths
    project_root = get_project_root()
    data_dir = Path(args.data_dir) if args.data_dir else get_data_dir()
    results_dir = Path(args.results_dir) if args.results_dir else get_results_dir()
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        # Load split indices
        train_indices_path = data_dir.parent / "splits" / "train_indices.csv"
        test_indices_path = data_dir.parent / "splits" / "test_indices.csv"
        
        import pandas as pd
        train_df = pd.read_csv(train_indices_path)
        test_df = pd.read_csv(test_indices_path)
        
        split_indices = {
            'train': train_df['index'].tolist(),
            'test': test_df['index'].tolist()
        }
        
        train_loader, test_loader = load_processed_graphs(data_dir, split_indices)
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
        
    # Create model
    try:
        # Get feature dimensions from the first batch
        sample_batch = next(iter(train_loader))
        num_node_features = sample_batch.x.shape[1]
        model = create_model_from_processed_data(num_node_features=num_node_features)
        logger.info(f"Created GCN model with {num_node_features} input features")
        
    except Exception as e:
        logger.error(f"Failed to create model: {e}")
        sys.exit(1)
        
    # Train model
    checkpoint_path = results_dir / "best_model.pt"
    history, trained_model = train_model(
        train_loader=train_loader,
        test_loader=test_loader,
        model=model,
        epochs=args.epochs,
        patience=args.patience,
        learning_rate=args.lr,
        device=torch.device(args.device),
        checkpoint_path=checkpoint_path
    )
    
    # Save training history
    history_path = results_dir / "training_history.json"
    with open(history_path, 'w') as f:
        # Convert numpy types to Python types for JSON serialization
        serializable_history = {}
        for key, value in history.items():
            if isinstance(value, np.floating):
                serializable_history[key] = float(value)
            elif isinstance(value, np.integer):
                serializable_history[key] = int(value)
            elif isinstance(value, list):
                serializable_history[key] = [float(v) if isinstance(v, np.floating) else int(v) if isinstance(v, np.integer) else v for v in value]
            else:
                serializable_history[key] = value
        json.dump(serializable_history, f, indent=2)
        
    logger.info(f"Training complete. History saved to {history_path}")
    logger.info(f"Best model saved to {checkpoint_path}")
    logger.info(f"Best validation loss: {history['best_val_loss']:.6f} at epoch {history['best_epoch']}")
    
    return history


if __name__ == "__main__":
    main()