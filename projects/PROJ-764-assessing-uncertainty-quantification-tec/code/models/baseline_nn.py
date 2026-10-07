import os
import sys
import json
import logging
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np

# Configure logging for this module
logger = logging.getLogger(__name__)

# Ensure results directory exists
RESULTS_DIR = Path("results/models")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data():
    """
    Load PCA-transformed training data from data/processed/features_train_20pca.csv.
    Returns X (features) and y (target).
    """
    data_path = Path("data/processed/features_train_20pca.csv")
    if not data_path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {data_path}. "
            "Ensure T006d (PCA Transform) has completed."
        )
    
    df = pd.read_csv(data_path)
    
    # Identify target column (assuming 'formation_energy' or similar)
    # Based on T006d output, we expect a target column.
    # If 'target' or 'formation_energy' exists, use it.
    target_col = None
    for col in ['formation_energy', 'target', 'energy_per_atom']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise ValueError("Could not identify target column in data. Columns: " + str(df.columns.tolist()))
    
    X = df.drop(columns=[target_col]).values.astype(np.float32)
    y = df[target_col].values.astype(np.float32)
    
    return X, y

class HeteroscedasticNN(nn.Module):
    """
    2-hidden layer FFNN with a heteroscedastic output head.
    Output head predicts both mean (mu) and log-variance (log_var).
    Total parameters must be <= 10000.
    """
    def __init__(self, input_dim, hidden_dims=(64, 32)):
        super(HeteroscedasticNN, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        
        # Build layers
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.1)) # Small dropout for stability
            prev_dim = h_dim
        
        self.feature_extractor = nn.Sequential(*layers)
        
        # Heteroscedastic head: outputs 2 values (mu, log_var)
        self.head = nn.Linear(prev_dim, 2)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)
    
    def forward(self, x):
        features = self.feature_extractor(x)
        out = self.head(features)
        mu = out[:, 0]
        log_var = out[:, 1]
        return mu, log_var

def count_parameters(model):
    """Count total trainable parameters in the model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def verify_parameter_count(model, max_params=10000):
    """Verify that the model has <= max_params parameters."""
    total = count_parameters(model)
    if total > max_params:
        raise ValueError(f"Model has {total} parameters, which exceeds the limit of {max_params}.")
    return total

def negative_log_likelihood_loss(mu, log_var, y_true):
    """
    Compute negative log likelihood for heteroscedastic regression.
    Loss = 0.5 * (log_var + (y_true - mu)^2 / exp(log_var))
    """
    # Stability: clamp log_var to prevent exp overflow/underflow
    log_var = torch.clamp(log_var, min=-10, max=10)
    variance = torch.exp(log_var)
    
    nll = 0.5 * (log_var + (y_true - mu) ** 2 / variance)
    return torch.mean(nll)

def train_model(X_train, y_train, epochs=100, lr=0.001, batch_size=64, seed=42):
    """
    Train the heteroscedastic NN model.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    # Convert to tensors
    X_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    
    dataset = TensorDataset(X_tensor, y_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    input_dim = X_train.shape[1]
    model = HeteroscedasticNN(input_dim, hidden_dims=(64, 32))
    
    # Verify parameter count
    total_params = verify_parameter_count(model)
    logger.info(f"Model total parameters: {total_params}")
    
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_X, batch_y in loader:
            optimizer.zero_grad()
            mu, log_var = model(batch_X)
            loss = negative_log_likelihood_loss(mu, log_var.squeeze(1), batch_y.squeeze(1))
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        if (epoch + 1) % 20 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss/len(loader):.4f}")
    
    return model, total_params

def main():
    """
    Main entry point for T012: Define architecture, verify params, and save artifact.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting T012: Baseline NN Architecture Definition & Verification")
    
    try:
        # 1. Load config
        config = load_config()
        logger.info("Configuration loaded.")
        
        # 2. Load processed data to determine input dimension
        X, y = load_processed_data()
        input_dim = X.shape[1]
        logger.info(f"Loaded training data. Input dimension: {input_dim}, Samples: {len(X)}")
        
        # 3. Instantiate model (no training required for T012, just definition & verification)
        model = HeteroscedasticNN(input_dim, hidden_dims=(64, 32))
        
        # 4. Verify parameter count
        total_params = verify_parameter_count(model)
        logger.info(f"Verification passed: Model has {total_params} parameters (<= 10000).")
        
        # 5. Save architecture definition to results/models/baseline_nn_arch.pt
        # We save the state_dict and the config to reconstruct the model later.
        output_path = RESULTS_DIR / "baseline_nn_arch.pt"
        torch.save({
            'model_state_dict': model.state_dict(),
            'input_dim': input_dim,
            'hidden_dims': [64, 32],
            'total_parameters': total_params
        }, output_path)
        
        logger.info(f"Architecture saved to: {output_path}")
        
        # 6. Log entry confirming parameter count
        log_entry = {
            "task": "T012",
            "model": "HeteroscedasticNN",
            "total_parameters": total_params,
            "max_allowed": 10000,
            "status": "passed"
        }
        
        log_path = Path("logs/architecture_verification.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to log file or overwrite? Task says "a log entry".
        # We'll write a dedicated JSON log for this verification.
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        logger.info(f"Verification log saved to: {log_path}")
        logger.info("T012 completed successfully.")
        
    except Exception as e:
        logger.error(f"T012 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()