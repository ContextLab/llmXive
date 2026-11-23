"""
Training script for the DelTA MLP model.

This script implements the training loop (FR-004) using:
- Extracted static features (from T020: data/processed/static_features.parquet)
- Ground truth coefficients (from T015: data/processed/delta_coefficients.json)
- The MLP model defined in code/models/mlp.py

Constraints:
- CPU-only execution (no CUDA/GPU calls)
- Saves model to data/processed/mlp_model.pt
"""
import os
import sys
import json
import logging
import argparse
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

# Import project modules
from config import get_config_summary
from models.mlp import create_model

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/train.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StaticFeatureDataset(Dataset):
    """
    PyTorch Dataset for loading static features and ground truth coefficients.
    
    Loads data from:
    - data/processed/static_features.parquet (features)
    - data/processed/delta_coefficients.json (targets)
    """
    
    def __init__(self, features_path: str, coefficients_path: str, split: str = 'train'):
        """
        Initialize the dataset.
        
        Args:
            features_path: Path to the static features parquet file
            coefficients_path: Path to the delta coefficients JSON file
            split: 'train' or 'test' (used for stratified sampling if needed)
        """
        logger.info(f"Loading features from {features_path}")
        if not os.path.exists(features_path):
            raise FileNotFoundError(f"Features file not found: {features_path}")
        
        # Load features
        self.features_df = pd.read_parquet(features_path)
        
        logger.info(f"Loading coefficients from {coefficients_path}")
        if not os.path.exists(coefficients_path):
            raise FileNotFoundError(f"Coefficients file not found: {coefficients_path}")
        
        with open(coefficients_path, 'r') as f:
            self.coefficients_data = json.load(f)
        
        # Convert coefficients to a lookup dict: (example_id, token_id) -> coefficient
        self.coefficient_map = {}
        for example in self.coefficients_data.get('coefficients', []):
            key = (example['example_id'], example['token_id'])
            self.coefficient_map[key] = example['coefficient']
        
        # Filter features to only include those with valid coefficients
        valid_indices = []
        for idx, row in self.features_df.iterrows():
            key = (row['example_id'], row['token_id'])
            if key in self.coefficient_map:
                valid_indices.append(idx)
        
        self.features_df = self.features_df.iloc[valid_indices].reset_index(drop=True)
        
        logger.info(f"Loaded {len(self.features_df)} valid feature-target pairs")
        
        if len(self.features_df) == 0:
            raise ValueError("No valid feature-target pairs found. Check data integrity.")
        
        # Convert to numpy arrays
        self.feature_vectors = np.vstack(self.features_df['feature_vector'].values)
        self.targets = np.array([
            self.coefficient_map[(row['example_id'], row['token_id'])]
            for _, row in self.features_df.iterrows()
        ], dtype=np.float32)
        
        logger.info(f"Feature shape: {self.feature_vectors.shape}, Target shape: {self.targets.shape}")

    def __len__(self):
        return len(self.feature_vectors)

    def __getitem__(self, idx):
        return (
            torch.FloatTensor(self.feature_vectors[idx]),
            torch.FloatTensor([self.targets[idx]])
        )

def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: Optional[DataLoader] = None,
    epochs: int = 100,
    learning_rate: float = 1e-3,
    device: str = 'cpu'
) -> Tuple[nn.Module, Dict[str, Any]]:
    """
    Train the MLP model on CPU.
    
    Args:
        model: The MLP model to train
        train_loader: DataLoader for training data
        val_loader: Optional DataLoader for validation data
        epochs: Number of training epochs
        learning_rate: Learning rate for optimizer
        device: Device to train on (must be 'cpu' per constraints)
    
    Returns:
        Tuple of (trained_model, training_history)
    """
    if device != 'cpu':
        raise ValueError("GPU/CUDA is not allowed. Must use CPU-only execution.")
    
    model = model.to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=10, factor=0.5)
    
    history = {
        'train_loss': [],
        'val_loss': [],
        'lr': []
    }
    
    logger.info(f"Starting training for {epochs} epochs on {device}")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        for batch_features, batch_targets in train_loader:
            batch_features = batch_features.to(device)
            batch_targets = batch_targets.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_features)
            loss = criterion(outputs, batch_targets)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        history['train_loss'].append(avg_train_loss)
        history['lr'].append(optimizer.param_groups[0]['lr'])
        
        # Validation
        if val_loader is not None:
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_features, batch_targets in val_loader:
                    batch_features = batch_features.to(device)
                    batch_targets = batch_targets.to(device)
                    outputs = model(batch_features)
                    loss = criterion(outputs, batch_targets)
                    val_loss += loss.item()
            
            avg_val_loss = val_loss / len(val_loader)
            history['val_loss'].append(avg_val_loss)
            scheduler.step(avg_val_loss)
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}")
        else:
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.6f}")
        
        # Early stopping check (optional: could add logic here)
        if avg_train_loss < 1e-6:
            logger.info("Converged early, stopping training.")
            break
    
    return model, history

def main():
    """
    Main entry point for the training script.
    
    Loads configuration, prepares data, trains the model, and saves the checkpoint.
    """
    parser = argparse.ArgumentParser(description='Train DelTA MLP model')
    parser.add_argument('--features', type=str, default='data/processed/static_features.parquet',
                      help='Path to static features parquet file')
    parser.add_argument('--coefficients', type=str, default='data/processed/delta_coefficients.json',
                      help='Path to delta coefficients JSON file')
    parser.add_argument('--output', type=str, default='data/processed/mlp_model.pt',
                      help='Path to save the trained model')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    args = parser.parse_args()
    
    try:
        # Load config
        config = get_config_summary()
        logger.info(f"Configuration: {config}")
        
        # Ensure CPU-only
        device = 'cpu'
        logger.info(f"Using device: {device}")
        
        # Create output directory if it doesn't exist
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load dataset
        dataset = StaticFeatureDataset(
            features_path=args.features,
            coefficients_path=args.coefficients
        )
        
        # Split into train/val (80/20)
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(42)
        )
        
        train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
        
        logger.info(f"Train size: {len(train_dataset)}, Val size: {len(val_dataset)}")
        
        # Create model
        input_dim = len(dataset.feature_vectors[0])
        model = create_model(input_dim=input_dim, hidden_dim=64, output_dim=1)
        logger.info(f"Model architecture:\n{model}")
        
        # Train model
        trained_model, history = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            epochs=args.epochs,
            learning_rate=args.lr,
            device=device
        )
        
        # Save model
        torch.save({
            'model_state_dict': trained_model.state_dict(),
            'input_dim': input_dim,
            'hidden_dim': 64,
            'output_dim': 1,
            'training_history': history
        }, args.output)
        
        logger.info(f"Model saved to {args.output}")
        
        # Save training metrics
        metrics_path = output_path.parent / 'training_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(history, f, indent=2)
        logger.info(f"Training metrics saved to {metrics_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()