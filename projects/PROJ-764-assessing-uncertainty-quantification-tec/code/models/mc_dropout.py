import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import logging
import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

class MCDropoutModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list = [64, 32], dropout_p: float = 0.2):
        super().__init__()
        self.dropout_p = dropout_p
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_p))
            prev_dim = h
        self.fc = nn.Sequential(*layers)
        self.mean_head = nn.Linear(prev_dim, 1)
        self.var_head = nn.Linear(prev_dim, 1)

    def forward(self, x):
        h = self.fc(x)
        mean = self.mean_head(h)
        var = torch.exp(self.var_head(h))
        return mean, var

    def enable_dropout(self):
        self.train()

    def disable_dropout(self):
        self.eval()

def load_config(config_path: str = "code/config.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)

def load_data(split: str = "train"):
    path = Path(f"data/processed/features_{split}_20pca.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}. Run T006b first.")
    df = pd.read_csv(path)
    feature_cols = [f'pca_{i}' for i in range(20)]
    # Ensure columns exist
    if not all(col in df.columns for col in feature_cols):
        raise ValueError(f"Expected PCA columns {feature_cols} not found in {path}")
    
    X = torch.tensor(df[feature_cols].values, dtype=torch.float32)
    y = torch.tensor(df['formation_energy'].values, dtype=torch.float32).unsqueeze(1)
    return X, y

def train_mc_dropout(input_dim: int, seed: int, epochs: int = 50, lr: float = 1e-3):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = MCDropoutModel(input_dim, dropout_p=0.2)
    X, y = load_data("train")
    train_dataset = torch.utils.data.TensorDataset(X, y)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)

    optimizer = optim.Adam(model.parameters(), lr=lr)

    logger.info(f"Starting MC Dropout training with seed {seed}, epochs {epochs}")
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            mean, var = model(X_batch)
            # Heteroscedastic loss: 0.5 * (log(var) + (y - mean)^2 / var)
            loss = 0.5 * torch.mean(torch.log(var) + ((y_batch - mean) ** 2) / var)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.6f}")

    return model

def run_mc_dropout_inference(model: MCDropoutModel, X: torch.Tensor, n_samples: int = 30):
    """
    Runs multiple stochastic forward passes with dropout enabled.
    
    Args:
        model: The trained MCDropoutModel
        X: Input tensor (N, input_dim)
        n_samples: Number of stochastic forward passes
        
    Returns:
        means: Tensor of shape (N, n_samples)
        vars_list: Tensor of shape (N, n_samples)
    """
    model.enable_dropout()
    means = []
    vars_list = []
    
    with torch.no_grad():
        for _ in range(n_samples):
            mean, var = model(X)
            means.append(mean)
            vars_list.append(var)
    
    means = torch.stack(means, dim=1) # (N, n_samples)
    vars_list = torch.stack(vars_list, dim=1) # (N, n_samples)
    
    return means, vars_list

def main(seed: int = 42):
    """
    Main entry point for T014.
    Trains the MC Dropout model and saves it to results/models/mc_dropout/mc_dropout_seed_<seed>.pt.
    """
    config = load_config()
    input_dim = 20
    epochs = config.get('epochs', 50)
    
    logger.info("Loading training data...")
    try:
        X, y = load_data("train")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Training MC Dropout model (seed={seed})...")
    model = train_mc_dropout(input_dim, seed, epochs=epochs)
    
    # Save the model
    out_dir = Path("results/models/mc_dropout")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"mc_dropout_seed_{seed}.pt"
    
    torch.save({
        'model_state_dict': model.state_dict(),
        'seed': seed,
        'dropout_p': 0.2
    }, output_path)
    
    logger.info(f"MC Dropout model saved to {output_path}")
    
    # Verify inference works
    logger.info("Verifying inference with 30 stochastic passes...")
    model.load_state_dict(torch.load(output_path, weights_only=True)['model_state_dict'])
    test_means, test_vars = run_mc_dropout_inference(model, X[:10], n_samples=30)
    logger.info(f"Inference successful. Mean shape: {test_means.shape}, Var shape: {test_vars.shape}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()