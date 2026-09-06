import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data(
    train_path: str = "data/processed/features_train_20pca.csv",
    val_path: str = "data/processed/features_val_20pca.csv",
    test_path: str = "data/processed/features_test_20pca.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load preprocessed train/val/test datasets."""
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Training data not found: {train_path}")
    if not os.path.exists(val_path):
        raise FileNotFoundError(f"Validation data not found: {val_path}")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test data not found: {test_path}")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    logger.info(f"Loaded train: {len(train_df)}, val: {len(val_df)}, test: {len(test_df)}")
    return train_df, val_df, test_df

class HeteroscedasticNN(nn.Module):
    """
    Heteroscedastic Neural Network for regression.
    Architecture: 2 hidden layers, outputting mean and log-variance.
    Designed to stay under 10k parameters.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super(HeteroscedasticNN, self).__init__()
        self.hidden_dim = hidden_dim
        
        # Layer definitions
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.relu2 = nn.ReLU()
        
        # Output heads: one for mean, one for log-variance
        self.mean_head = nn.Linear(hidden_dim, 1)
        self.var_head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        Returns: (mean, log_variance)
        """
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        
        mean = self.mean_head(x)
        # Softplus ensures positive variance
        log_var = self.var_head(x)
        
        return mean, log_var

    def count_parameters(self) -> int:
        """Calculate total number of parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

def negative_log_likelihood_loss(mean: torch.Tensor, log_var: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """
    Negative Log Likelihood loss for heteroscedastic regression.
    Assumes y ~ N(mean, exp(log_var))
    """
    # NLL = 0.5 * (log_var + (y - mean)^2 / exp(log_var))
    # We work in log space for stability
    precision = torch.exp(-log_var)
    loss = 0.5 * (log_var + precision * (y - mean) ** 2)
    return loss.mean()

def train_model(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    epochs: int = 100,
    lr: float = 1e-3,
    patience: int = 10,
    device: str = "cpu"
) -> nn.Module:
    """
    Train the heteroscedastic model with early stopping.
    """
    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_state_dict = None

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            mean, log_var = model(batch_x)
            loss = negative_log_likelihood_loss(mean, log_var, batch_y)
            
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                mean, log_var = model(batch_x)
                loss = negative_log_likelihood_loss(mean, log_var, batch_y)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        scheduler.step(val_loss)
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_state_dict = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)
    
    return model

def main():
    """
    Main entry point for training the baseline model.
    - Loads config and processed data.
    - Trains HeteroscedasticNN.
    - Verifies parameter count <= 10,000.
    - Saves model to results/models/baseline_seed42.pt.
    """
    args = argparse.ArgumentParser()
    args.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    args.add_argument('--seed', type=int, default=42, help='Random seed')
    args.add_argument('--output', type=str, default='results/models/baseline_seed42.pt', help='Output path')
    args = args.parse_args()

    # Set seed
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    # Load config
    config = load_config(args.config)
    seed = config.get('seed', args.seed)
    epochs = config.get('epochs', 100)
    lr = config.get('lr', 1e-3)
    hidden_dim = config.get('hidden_dim', 32)
    batch_size = config.get('batch_size', 64)

    logger.info(f"Starting baseline training with seed {seed}")

    # Load data
    train_df, val_df, _ = load_processed_data()
    
    # Prepare tensors
    # Assume feature columns are all except 'target', 'target_bin', 'sample_id'
    feature_cols = [c for c in train_df.columns if c not in ['target', 'target_bin', 'sample_id']]
    target_col = 'target'

    X_train = torch.tensor(train_df[feature_cols].values, dtype=torch.float32)
    y_train = torch.tensor(train_df[target_col].values, dtype=torch.float32).unsqueeze(1)
    X_val = torch.tensor(val_df[feature_cols].values, dtype=torch.float32)
    y_val = torch.tensor(val_df[target_col].values, dtype=torch.float32).unsqueeze(1)

    # Create datasets and loaders
    train_dataset = torch.utils.data.TensorDataset(X_train, y_train)
    val_dataset = torch.utils.data.TensorDataset(X_val, y_val)
    
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Initialize model
    input_dim = X_train.shape[1]
    model = HeteroscedasticNN(input_dim=input_dim, hidden_dim=hidden_dim)
    
    param_count = model.count_parameters()
    logger.info(f"Model parameter count: {param_count}")

    # Verification: Assert parameter count <= 10,000
    if param_count > 10000:
        raise ValueError(f"Model parameter count ({param_count}) exceeds limit of 10,000. Aborting save.")

    # Train
    trained_model = train_model(
        model, 
        train_loader, 
        val_loader, 
        epochs=epochs, 
        lr=lr,
        device='cpu'
    )

    # Save model
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    torch.save({
        'model_state_dict': trained_model.state_dict(),
        'input_dim': input_dim,
        'hidden_dim': hidden_dim,
        'seed': seed,
        'param_count': param_count
    }, args.output)
    
    logger.info(f"Model saved to {args.output} with {param_count} parameters")

if __name__ == "__main__":
    main()
