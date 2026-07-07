import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import yaml
import pandas as pd
import time
import logging

from utils.timing_logger import timing_logger

CONFIG_PATH = "code/config.yaml"
PROCESSED_DATA_PATH = "data/processed/features_20pca.csv"
ENSEMBLE_DIR = "results/models/ensemble_models"
NUM_MODELS = 5

os.makedirs(ENSEMBLE_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

class HeteroscedasticNN(nn.Module):
    def __init__(self, input_dim, hidden_dims=[64, 32]):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            prev_dim = h_dim
        self.backbone = nn.Sequential(*layers)
        self.mean_head = nn.Linear(prev_dim, 1)
        self.log_var_head = nn.Linear(prev_dim, 1)

    def forward(self, x):
        h = self.backbone(x)
        mean = self.mean_head(h)
        log_var = self.log_var_head(h)
        return mean, log_var

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_data():
    df = pd.read_csv(PROCESSED_DATA_PATH)
    feature_cols = [col for col in df.columns if col.startswith('feature_')]
    X = df[feature_cols].values
    y = df['target'].values
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def train_single_model(model_idx, X, y, config):
    seed = config.get('seed', 42)
    torch.manual_seed(seed + model_idx)
    np.random.seed(seed + model_idx)

    input_dim = X.shape[1]
    model = HeteroscedasticNN(input_dim)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    model.train()
    epochs = 100
    batch_size = 64
    n_samples = X.shape[0]

    for epoch in range(epochs):
        indices = torch.randperm(n_samples)
        X_shuffled = X[indices]
        y_shuffled = y[indices]

        for i in range(0, n_samples, batch_size):
            batch_X = X_shuffled[i:i+batch_size]
            batch_y = y_shuffled[i:i+batch_size]

            optimizer.zero_grad()
            mean, log_var = model(batch_X)
            precision = torch.exp(-log_var)
            loss = precision * (batch_y.unsqueeze(1) - mean) ** 2 + log_var
            loss = loss.mean()
            loss.backward()
            optimizer.step()

    return model

def train_ensemble():
    config = load_config()
    X, y = load_data()

    timing_logger.start("deep_ensemble_training")

    models = []
    for i in range(NUM_MODELS):
        logger.info(f"Training ensemble member {i+1}/{NUM_MODELS}")
        model = train_single_model(i, X, y, config)
        path = os.path.join(ENSEMBLE_DIR, f"model_{i}.pt")
        torch.save(model.state_dict(), path)
        models.append(model)

    timing_logger.stop("deep_ensemble_training")
    timing_logger.save_report()
    logger.info(f"Ensemble trained and saved to {ENSEMBLE_DIR}")

class DeepEnsemble:
    def __init__(self, models):
        self.models = models

    def predict(self, X):
        means = []
        log_vars = []
        for model in self.models:
            model.eval()
            with torch.no_grad():
                m, lv = model(X)
                means.append(m)
                log_vars.append(lv)
        
        means = torch.stack(means, dim=0) # [N_models, N_samples, 1]
        log_vars = torch.stack(log_vars, dim=0)

        # Epistemic: variance of means
        mean_of_means = means.mean(dim=0)
        epistemic_var = means.var(dim=0)
        
        # Aleatoric: mean of variances
        aleatoric_var = torch.exp(log_vars).mean(dim=0)
        
        total_var = epistemic_var + aleatoric_var

        return mean_of_means, total_var

def main():
    logging.basicConfig(level=logging.INFO)
    train_ensemble()

if __name__ == "__main__":
    main()
