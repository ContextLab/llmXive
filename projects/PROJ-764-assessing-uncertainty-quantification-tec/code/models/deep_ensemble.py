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

class HeteroscedasticNN(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list = [64, 32]):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.ReLU())
            prev_dim = h
        self.fc = nn.Sequential(*layers)
        self.mean_head = nn.Linear(prev_dim, 1)
        self.var_head = nn.Linear(prev_dim, 1)

    def forward(self, x):
        h = self.fc(x)
        mean = self.mean_head(h)
        var = torch.exp(self.var_head(h))
        return mean, var

def load_config(config_path: str = "code/config.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)

def load_data(split: str = "train"):
    path = Path(f"data/processed/features_{split}_20pca.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}. Ensure T006b3 has completed.")
    df = pd.read_csv(path)
    # Ensure we select exactly 20 PCA columns
    pca_cols = [f'pca_{i}' for i in range(20)]
    if not all(col in df.columns for col in pca_cols):
        missing = set(pca_cols) - set(df.columns)
        raise ValueError(f"Missing PCA columns in {path}: {missing}")
    
    X = torch.tensor(df[pca_cols].values, dtype=torch.float32)
    y = torch.tensor(df['formation_energy'].values, dtype=torch.float32).unsqueeze(1)
    return X, y

def train_single_model(input_dim: int, seed: int, epochs: int = 50):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = HeteroscedasticNN(input_dim)
    X, y = load_data("train")
    train_dataset = torch.utils.data.TensorDataset(X, y)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)

    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            mean, var = model(X_batch)
            # Heteroscedastic loss: 0.5 * (log(var) + (y - mean)^2 / var)
            loss = 0.5 * torch.mean(torch.log(var) + ((y_batch - mean) ** 2) / var)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Seed {seed}, Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")
    
    return model

def train_ensemble(input_dim: int, n_models: int = 5, seed: int = 42):
    models = []
    for i in range(n_models):
        logger.info(f"Training ensemble model {i+1}/{n_models} with seed {seed + i}")
        model = train_single_model(input_dim, seed + i, epochs=50)
        models.append(model)
    return models

class DeepEnsemble:
    def __init__(self, models: list):
        self.models = models

    def predict(self, X: torch.Tensor):
        means = []
        vars_list = []
        for model in self.models:
            model.eval()
            with torch.no_grad():
                mean, var = model(X)
                means.append(mean)
                vars_list.append(var)
        
        means = torch.stack(means, dim=1)  # (N, n_models)
        vars_list = torch.stack(vars_list, dim=1)
        
        # Aggregate: Mean of means, Mean of variances + Variance of means (Total Uncertainty)
        # However, for storage in ensemble, we often store the individual predictions
        # or the aggregated statistics. The task asks to "aggregate mean/variance".
        # We return the stack of predictions for later aggregation by the runner.
        return means, vars_list

def main(seed: int = 42):
    config = load_config()
    input_dim = 20
    n_models = config.get('ensemble_size', 5)
    
    logger.info(f"Starting Deep Ensemble training with {n_models} models, base seed {seed}")
    models = train_ensemble(input_dim, n_models=n_models, seed=seed)
    
    out_dir = Path("results/models/ensemble")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for i, model in enumerate(models):
        save_path = out_dir / f"ensemble_seed_{seed + i}.pt"
        torch.save({
            'model_state_dict': model.state_dict(),
            'seed': seed + i,
            'input_dim': input_dim
        }, save_path)
        logger.info(f"Saved model {i+1} to {save_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()