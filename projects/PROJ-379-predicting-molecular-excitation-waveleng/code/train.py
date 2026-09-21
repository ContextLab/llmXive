"""
Training module for the molecular excitation wavelength prediction model.

This module implements the training loop for the MPNN GNN and baseline models.
It handles data loading, model training with early stopping, and artifact generation.

Key features:
- CPU-only execution
- Fixed random seed (42) for reproducibility
- Early stopping with patience=5 based on validation loss
- Generates model.pt and seeds.json artifacts
"""

import os
import sys
import json
import logging
import random
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import pandas as pd

# Import from local modules
from utils import setup_logging, get_logger, get_device
from model import MPNN, RidgeBaseline, prepare_gnn_data, smiles_to_ecfp
from split import scaffold_split

# Setup logging
logger = setup_logging()

# Constants
DEFAULT_SEED = 42
DEFAULT_EPOCHS = 100
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_PATIENCE = 5
EARLY_STOP_THRESHOLD = 1e-4


class MolecularDataset(Dataset):
    """PyTorch Dataset for molecular graphs."""
    
    def __init__(self, data: pd.DataFrame, device: str = 'cpu'):
        """
        Initialize the dataset.
        
        Args:
            data: DataFrame with columns [smi, lambda_max, scaffold_id, split]
            device: Device to store tensors on
        """
        self.data = data
        self.device = device
        self.graphs = []
        self.targets = []
        
        logger.info(f"Converting {len(data)} molecules to graphs...")
        for idx, row in data.iterrows():
            try:
                mol_graph, features = prepare_gnn_data(row['smi'])
                if mol_graph is not None:
                    self.graphs.append({
                        'x': mol_graph.x,
                        'edge_index': mol_graph.edge_index,
                        'edge_attr': mol_graph.edge_attr if hasattr(mol_graph, 'edge_attr') else None
                    })
                    self.targets.append(row['lambda_max'])
                else:
                    logger.warning(f"Failed to convert SMILES at index {idx}: {row['smi']}")
            except Exception as e:
                logger.error(f"Error processing molecule {idx}: {e}")
        
        logger.info(f"Successfully converted {len(self.graphs)} molecules to graphs")
        
    def __len__(self):
        return len(self.graphs)
    
    def __getitem__(self, idx):
        graph = self.graphs[idx]
        target = self.targets[idx]
        
        # Move to device
        x = graph['x'].to(self.device)
        edge_index = graph['edge_index'].to(self.device)
        edge_attr = graph['edge_attr'].to(self.device) if graph['edge_attr'] is not None else None
        
        return {
            'x': x,
            'edge_index': edge_index,
            'edge_attr': edge_attr,
            'y': torch.tensor(target, dtype=torch.float32).to(self.device)
        }

def set_seed(seed: int = DEFAULT_SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    # Log seed for reproducibility
    logger.info(f"Random seed set to: {seed}")
    return seed

def load_data_splits(data_path: str = "data/processed/train_val_test.csv") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and split the processed data.
    
    Args:
        data_path: Path to the processed CSV file
        
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    df = pd.read_csv(data_path)
    
    train_df = df[df['split'] == 'train']
    val_df = df[df['split'] == 'val']
    test_df = df[df['split'] == 'test']
    
    logger.info(f"Loaded data splits: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
    
    return train_df, val_df, test_df

def preprocess_df(df: pd.DataFrame, device: str = 'cpu') -> MolecularDataset:
    """
    Convert DataFrame to PyTorch Dataset.
    
    Args:
        df: DataFrame with molecular data
        device: Device to store tensors on
        
    Returns:
        MolecularDataset instance
    """
    return MolecularDataset(df, device)

def train_epoch(model: nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer, criterion: nn.Module, device: str):
    """
    Train for one epoch.
    
    Args:
        model: Model to train
        dataloader: Training data loader
        optimizer: Optimizer
        criterion: Loss function
        device: Device to use
        
    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch in dataloader:
        optimizer.zero_grad()
        
        # Extract batch data
        x = batch['x']
        edge_index = batch['edge_index']
        edge_attr = batch['edge_attr']
        y = batch['y']
        
        # Forward pass
        if edge_attr is not None:
            output = model(x, edge_index, edge_attr)
        else:
            output = model(x, edge_index)
        
        # Calculate loss
        loss = criterion(output.squeeze(), y)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / num_batches

def validate_epoch(model: nn.Module, dataloader: DataLoader, criterion: nn.Module, device: str) -> float:
    """
    Validate for one epoch.
    
    Args:
        model: Model to validate
        dataloader: Validation data loader
        criterion: Loss function
        device: Device to use
        
    Returns:
        Average validation loss
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch in dataloader:
            x = batch['x']
            edge_index = batch['edge_index']
            edge_attr = batch['edge_attr']
            y = batch['y']
            
            if edge_attr is not None:
                output = model(x, edge_index, edge_attr)
            else:
                output = model(x, edge_index)
            
            loss = criterion(output.squeeze(), y)
            total_loss += loss.item()
            num_batches += 1
    
    return total_loss / num_batches

def train_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    epochs: int = DEFAULT_EPOCHS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    patience: int = DEFAULT_PATIENCE,
    device: str = 'cpu',
    seed: int = DEFAULT_SEED
) -> Tuple[nn.Module, Dict[str, Any]]:
    """
    Train the model with early stopping.
    
    Args:
        train_df: Training data
        val_df: Validation data
        epochs: Maximum number of epochs
        batch_size: Batch size for training
        learning_rate: Learning rate
        patience: Patience for early stopping
        device: Device to use
        seed: Random seed
        
    Returns:
        Tuple of (trained_model, training_history)
    """
    set_seed(seed)
    
    # Prepare datasets
    train_dataset = preprocess_df(train_df, device)
    val_dataset = preprocess_df(val_df, device)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    model = MPNN().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # Early stopping variables
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    history = {
        'train_loss': [],
        'val_loss': [],
        'best_val_loss': best_val_loss,
        'early_stop_epoch': None
    }
    
    logger.info(f"Starting training for {epochs} epochs...")
    logger.info(f"Device: {device}, Batch size: {batch_size}, Learning rate: {learning_rate}")
    
    start_time = time.time()
    
    for epoch in range(epochs):
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = validate_epoch(model, val_loader, criterion, device)
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Early stopping check
        if val_loss < best_val_loss - EARLY_STOP_THRESHOLD:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
            logger.info(f"  -> New best model saved (Val Loss: {best_val_loss:.4f})")
        else:
            patience_counter += 1
            logger.info(f"  -> Patience: {patience_counter}/{patience}")
        
        if patience_counter >= patience:
            logger.info(f"Early stopping triggered at epoch {epoch+1}")
            history['early_stop_epoch'] = epoch + 1
            break
    
    training_time = time.time() - start_time
    logger.info(f"Training completed in {training_time:.2f} seconds")
    
    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    history['training_time'] = training_time
    history['final_train_loss'] = history['train_loss'][-1] if history['train_loss'] else None
    history['final_val_loss'] = history['val_loss'][-1] if history['val_loss'] else None
    
    return model, history

def save_seeds(seeds: Dict[str, int], output_path: str = "data/processed/seeds.json"):
    """
    Save random seeds to a JSON file for reproducibility.
    
    Args:
        seeds: Dictionary of seed values
        output_path: Path to save the seeds file
    """
    with open(output_path, 'w') as f:
        json.dump(seeds, f, indent=2)
    logger.info(f"Seeds saved to {output_path}")

def main():
    """Main training entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train molecular excitation wavelength model")
    parser.add_argument('--epochs', type=int, default=DEFAULT_EPOCHS, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=DEFAULT_LEARNING_RATE, help='Learning rate')
    parser.add_argument('--patience', type=int, default=DEFAULT_PATIENCE, help='Early stopping patience')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help='Random seed')
    parser.add_argument('--device', type=str, default='cpu', help='Device to use (cpu only)')
    parser.add_argument('--data_path', type=str, default='data/processed/train_val_test.csv', help='Path to processed data')
    parser.add_argument('--output_dir', type=str, default='data/processed', help='Output directory for artifacts')
    
    args = parser.parse_args()
    
    # Setup logging
    log_dir = Path(args.output_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / 'training.log'
    setup_logging(log_file=log_file)
    
    logger.info("=" * 60)
    logger.info("Starting Training Pipeline")
    logger.info("=" * 60)
    logger.info(f"Arguments: epochs={args.epochs}, batch_size={args.batch_size}, lr={args.learning_rate}")
    logger.info(f"Seed: {args.seed}, Device: {args.device}")
    
    # Set seed
    set_seed(args.seed)
    
    # Load data
    try:
        train_df, val_df, test_df = load_data_splits(args.data_path)
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    
    # Train model
    model, history = train_model(
        train_df=train_df,
        val_df=val_df,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        patience=args.patience,
        device=args.device,
        seed=args.seed
    )
    
    # Save model
    model_path = Path(args.output_dir) / 'model.pt'
    torch.save({
        'model_state_dict': model.state_dict(),
        'history': history,
        'seed': args.seed
    }, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Save seeds
    seeds = {
        'random': args.seed,
        'numpy': args.seed,
        'torch': args.seed
    }
    save_seeds(seeds)
    
    # Save training history
    history_path = Path(args.output_dir) / 'training_history.json'
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    logger.info(f"Training history saved to {history_path}")
    
    logger.info("=" * 60)
    logger.info("Training Pipeline Completed Successfully")
    logger.info("=" * 60)
    
    return model, history

if __name__ == "__main__":
    main()