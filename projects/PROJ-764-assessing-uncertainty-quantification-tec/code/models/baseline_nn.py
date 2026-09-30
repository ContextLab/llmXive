import os
import sys
import json
import logging
import argparse
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = 'code/config.yaml') -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data(
    train_path: str = 'data/processed/features_train_20pca.csv',
    val_path: str = 'data/processed/features_val_20pca.csv',
    test_path: str = 'data/processed/features_test_20pca.csv'
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Load pre-processed data from CSV files.
    Returns: (X_train, y_train, X_val, y_val, X_test, y_test)
    """
    import pandas as pd
    import numpy as np

    def load_csv(path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}. Ensure T006b1 and T006b3 are complete.")
        df = pd.read_csv(path)
        # Assume first columns are features, last column is target
        feature_cols = [c for c in df.columns if c != 'formation_energy' and c != 'target_bin']
        target_col = 'formation_energy'
        if target_col not in df.columns:
            # Fallback: if 'formation_energy' is missing, try to find the numeric target
            numeric_cols = df.select_dtypes(include=[np.float64, np.int64]).columns
            if len(numeric_cols) > 0:
                target_col = numeric_cols[-1]
            else:
                raise ValueError("Could not identify target column in data.")
        
        X = df[feature_cols].values.astype(np.float32)
        y = df[target_col].values.astype(np.float32)
        return torch.from_numpy(X), torch.from_numpy(y)

    X_train, y_train = load_csv(train_path)
    X_val, y_val = load_csv(val_path)
    X_test, y_test = load_csv(test_path)

    logger.info(f"Loaded data: Train={X_train.shape}, Val={X_val.shape}, Test={X_test.shape}")
    return X_train, y_train, X_val, y_val, X_test, y_test

class HeteroscedasticNN(nn.Module):
    """
    A 2-hidden-layer Feed-Forward Neural Network with a heteroscedastic output head.
    Outputs: (mean, log_var) for regression with learned noise variance.
    Total parameters must be <= 10,000.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 32, output_dim: int = 1):
        super().__init__()
        # Layer 1
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu1 = nn.ReLU()
        # Layer 2
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.relu2 = nn.ReLU()
        # Output Head: predicts mean and log_variance
        self.mean_head = nn.Linear(hidden_dim, output_dim)
        self.log_var_head = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        mean = self.mean_head(x)
        # Ensure log_var is not too large/small for numerical stability
        log_var = self.log_var_head(x)
        log_var = torch.clamp(log_var, -10, 10)
        return mean, log_var

def count_parameters(model: nn.Module) -> int:
    """Calculate total number of parameters in the model."""
    return sum(p.numel() for p in model.parameters())

def negative_log_likelihood_loss(mean: torch.Tensor, log_var: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """
    Calculate Negative Log Likelihood (NLL) loss for heteroscedastic regression.
    L = 0.5 * (log(var) + (y - mean)^2 / var)
    """
    var = torch.exp(log_var)
    nll = torch.mean(0.5 * (log_var + ((y - mean) ** 2) / var))
    return nll

def train_model(
    model: nn.Module,
    X_train: torch.Tensor,
    y_train: torch.Tensor,
    X_val: torch.Tensor,
    y_val: torch.Tensor,
    epochs: int = 100,
    lr: float = 0.001,
    batch_size: int = 64,
    device: str = 'cpu'
) -> nn.Module:
    """
    Train the heteroscedastic model using NLL loss.
    """
    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = negative_log_likelihood_loss

    train_loader = torch.utils.data.DataLoader(
        torch.utils.data.Dataset(torch.cat([X_train.unsqueeze(1), y_train.unsqueeze(1)], dim=1)),
        batch_size=batch_size,
        shuffle=True
    )
    # Simplified loader for demonstration: using indices
    n_samples = X_train.size(0)
    indices = torch.arange(n_samples)

    logger.info(f"Training model for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        # Mini-batch training
        for i in range(0, n_samples, batch_size):
            batch_idx = indices[i:i+batch_size]
            batch_x = X_train[batch_idx].to(device)
            batch_y = y_train[batch_idx].to(device)

            optimizer.zero_grad()
            mean, log_var = model(batch_x)
            loss = criterion(mean, log_var, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / (n_samples // batch_size + 1)

        # Validation
        model.eval()
        with torch.no_grad():
            val_mean, val_log_var = model(X_val.to(device))
            val_loss = criterion(val_mean, val_log_var, y_val.to(device)).item()

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_loss:.4f} | Val Loss: {val_loss:.4f}")

    return model

def verify_parameter_count(model: nn.Module, max_params: int = 10000) -> bool:
    """
    Verify that the model has <= 10,000 parameters.
    Raises AssertionError if limit is exceeded.
    """
    total_params = count_parameters(model)
    logger.info(f"Total parameters in model: {total_params}")
    assert total_params <= max_params, f"Model has {total_params} parameters, exceeds limit of {max_params}."
    return True

def main():
    """
    Main execution: Load data, define model, verify parameters, and optionally train.
    This script serves as the definition and verification unit for T012.
    """
    config = load_config()
    seed = config.get('seed', 42)
    torch.manual_seed(seed)

    # Load data
    X_train, y_train, X_val, y_val, X_test, y_test = load_processed_data()

    input_dim = X_train.size(1)
    logger.info(f"Input dimension: {input_dim}")

    # Define model with hidden dim 32 to ensure < 10k params
    # Params = (in*32 + 32) + (32*32 + 32) + (32*2 + 2) approx 1000-2000
    model = HeteroscedasticNN(input_dim=input_dim, hidden_dim=32)
    
    # Verify parameter count
    verify_parameter_count(model, max_params=10000)
    
    logger.info("Model architecture defined and verified successfully.")
    
    # Save architecture definition (weights not saved here, just the class definition)
    # The actual weights are saved during training in T013/T016a
    model_path = 'results/models/baseline_architecture.pt'
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    torch.save({'model_state': model.state_dict(), 'config': {'input_dim': input_dim, 'hidden_dim': 32}}, model_path)
    logger.info(f"Saved model architecture to {model_path}")

    return model

if __name__ == '__main__':
    main()