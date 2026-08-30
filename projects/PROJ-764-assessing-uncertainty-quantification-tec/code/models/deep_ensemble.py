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
    df = pd.read_csv(path)
    X = torch.tensor(df[[f'pca_{i}' for i in range(20)]].values, dtype=torch.float32)
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
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            mean, var = model(X_batch)
            loss = 0.5 * torch.mean(torch.log(var) + ((y_batch - mean) ** 2) / var)
            loss.backward()
            optimizer.step()
    return model

def train_ensemble(input_dim: int, n_models: int = 5, seed: int = 42):
    models = []
    for i in range(n_models):
        logger.info(f"Training model {i+1}/{n_models}")
        model = train_single_model(input_dim, seed + i, epochs=50)
        models.append(model)
    return models

class DeepEnsemble:
    def __init__(self, models: list):
        self.models = models

    def predict(self, X: torch.Tensor):
        means = []
        vars = []
        for model in self.models:
            model.eval()
            with torch.no_grad():
                mean, var = model(X)
                means.append(mean)
                vars.append(var)
        means = torch.stack(means, dim=1)  # (N, n_models)
        vars = torch.stack(vars, dim=1)
        return means, vars

def main(seed: int = 42):
    input_dim = 20
    models = train_ensemble(input_dim, n_models=5, seed=seed)
    
    out_dir = Path("results/models/ensemble_models")
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, model in enumerate(models):
        torch.save(model.state_dict(), out_dir / f"model_{i}.pt")
    logger.info("Ensemble models saved")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
