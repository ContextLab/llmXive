"""
Training script for Molecular Excitation Wavelength Prediction.
Implements GNN training with explicit seed logging and early stopping.
"""
import os
import sys
import json
import logging
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch_geometric.data import Data

# Import from local modules
from model import MPNN, RidgeBaseline, build_gnn_model, build_baseline_model, prepare_gnn_data
from utils import get_device, get_logger, setup_logging
from hash_artifacts import compute_file_hash, update_state_file

# Configure logging
logger = get_logger(__name__)

# Constants
DEFAULT_SEEDS = {
    "split_seed": 42,
    "model_seed": 123,
    "training_seed": 456
}

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility across all libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # Ensure deterministic behavior where possible
    torch.use_deterministic_algorithms(True)
    os.environ['PYTHONHASHSEED'] = str(seed)

def load_data_splits(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train, validation, and test splits from CSV files."""
    train_path = data_dir / "train_val_test.csv"
    if not train_path.exists():
        raise FileNotFoundError(f"Data file not found: {train_path}")
    
    df = pd.read_csv(train_path)
    
    # Assuming the split column exists or we need to reconstruct based on previous tasks
    # For T010.5 output, we expect a 'split' column or similar indicator
    # If the file is just the merged data, we need to rely on the split_indices.json
    split_indices_path = data_dir / "split_indices.json"
    if split_indices_path.exists():
        with open(split_indices_path, 'r') as f:
            split_data = json.load(f)
        
        train_idx = split_data.get('train', [])
        val_idx = split_data.get('val', [])
        test_idx = split_data.get('test', [])
        
        train_df = df.iloc[train_idx].reset_index(drop=True)
        val_df = df.iloc[val_idx].reset_index(drop=True)
        test_df = df.iloc[test_idx].reset_index(drop=True)
    else:
        # Fallback if split_indices.json is missing but split column exists
        if 'split' in df.columns:
            train_df = df[df['split'] == 'train'].reset_index(drop=True)
            val_df = df[df['split'] == 'val'].reset_index(drop=True)
            test_df = df[df['split'] == 'test'].reset_index(drop=True)
        else:
            raise FileNotFoundError("Could not determine data splits. Missing split_indices.json or 'split' column.")
    
    return train_df, val_df, test_df

def preprocess_df(df: pd.DataFrame, device: torch.device) -> List[Data]:
    """Convert pandas DataFrame to list of PyTorch Geometric Data objects."""
    data_list = []
    for _, row in df.iterrows():
        smi = row['smi']
        y = row['lambda_max']
        
        # Prepare graph data (assuming prepare_gnn_data handles SMILES to graph)
        # This function is imported from model.py
        try:
            graph_data = prepare_gnn_data(smi, y)
            if graph_data is not None:
                data_list.append(graph_data)
        except Exception as e:
            logger.warning(f"Failed to process molecule {smi}: {e}")
            continue
    
    return data_list

def train_model(
    train_loader: DataLoader,
    val_loader: DataLoader,
    model: nn.Module,
    device: torch.device,
    epochs: int = 100,
    lr: float = 1e-3,
    patience: int = 10,
    seed: int = 456
) -> Tuple[nn.Module, List[float], List[float]]:
    """
    Train the model with early stopping.
    Returns trained model, training losses, and validation losses.
    """
    set_seed(seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    model.to(device)
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        epoch_train_loss = 0.0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(batch)
            loss = criterion(outputs, batch.y)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss.item()
        
        avg_train_loss = epoch_train_loss / len(train_loader)
        train_losses.append(avg_train_loss)
        
        # Validation phase
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                outputs = model(batch)
                loss = criterion(outputs, batch.y)
                epoch_val_loss += loss.item()
        
        avg_val_loss = epoch_val_loss / len(val_loader)
        val_losses.append(avg_val_loss)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
        
        # Early stopping check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break
    
    # Restore best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    return model, train_losses, val_losses

def save_seeds(seeds: Dict[str, int], output_path: Path) -> None:
    """
    Save random seeds to a JSON file for reproducibility documentation.
    Schema: {"split_seed": int, "model_seed": int, "training_seed": int}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(seeds, f, indent=2)
    logger.info(f"Seeds saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train GNN for molecular excitation prediction")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Path to processed data")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Path to save model and logs")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--split_seed", type=int, default=42, help="Seed for data splitting")
    parser.add_argument("--model_seed", type=int, default=123, help="Seed for model initialization")
    parser.add_argument("--training_seed", type=int, default=456, help="Seed for training loop")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    # Collect seeds
    seeds = {
        "split_seed": args.split_seed,
        "model_seed": args.model_seed,
        "training_seed": args.training_seed
    }
    
    # Save seeds immediately for reproducibility documentation
    seeds_path = output_dir / "seeds.json"
    save_seeds(seeds, seeds_path)
    
    # Set global seed for data loading consistency if needed
    set_seed(seeds["split_seed"])
    
    device = get_device()
    logger.info(f"Using device: {device}")
    
    try:
        # Load data
        train_df, val_df, test_df = load_data_splits(data_dir)
        logger.info(f"Loaded {len(train_df)} train, {len(val_df)} val, {len(test_df)} test samples")
        
        # Preprocess data
        train_data = preprocess_df(train_df, device)
        val_data = preprocess_df(val_df, device)
        test_data = preprocess_df(test_df, device)
        
        # Create data loaders
        train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_data, batch_size=32, shuffle=False)
        test_loader = DataLoader(test_data, batch_size=32, shuffle=False)
        
        # Build model
        set_seed(seeds["model_seed"])
        model = build_gnn_model()
        logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
        
        # Train model
        set_seed(seeds["training_seed"])
        model, train_losses, val_losses = train_model(
            train_loader, val_loader, model, device,
            epochs=args.epochs, lr=args.lr, patience=args.patience,
            seed=seeds["training_seed"]
        )
        
        # Save model
        model_path = output_dir / "model.pt"
        torch.save({
            "model_state_dict": model.state_dict(),
            "seeds": seeds,
            "train_losses": train_losses,
            "val_losses": val_losses
        }, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Update state file with model hash
        update_state_file(model_path)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
