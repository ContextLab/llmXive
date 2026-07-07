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
MODEL_OUTPUT_PATH = "results/models/mc_dropout_model.pt"
NUM_SAMPLES = 30

os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)

logger = logging.getLogger(__name__)

class MCDropoutModel(nn.Module):
    def __init__(self, input_dim, hidden_dims=[64, 32], dropout_p=0.2):
        super().__init__()
        self.dropout_p = dropout_p
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_p))
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

def train_mc_dropout(X, y, config):
    seed = config.get('seed', 42)
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X.shape[1]
    model = MCDropoutModel(input_dim)
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

def run_mc_dropout_inference(model, X):
    model.train() # Enable dropout
    predictions = []
    variances = []

    with torch.no_grad():
        for _ in range(NUM_SAMPLES):
            mean, log_var = model(X)
            predictions.append(mean)
            variances.append(torch.exp(log_var))

    predictions = torch.stack(predictions, dim=0)
    variances = torch.stack(variances, dim=0)

    mean_pred = predictions.mean(dim=0)
    # Epistemic uncertainty from MC dropout samples
    epistemic_var = predictions.var(dim=0)
    # Aleatoric from average predicted variance
    aleatoric_var = variances.mean(dim=0)
    
    total_var = epistemic_var + aleatoric_var

    return mean_pred, total_var

def main():
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    X, y = load_data()

    timing_logger.start("mc_dropout_training")
    model = train_mc_dropout(X, y, config)
    timing_logger.stop("mc_dropout_training")

    torch.save(model.state_dict(), MODEL_OUTPUT_PATH)
    logger.info(f"MC Dropout model saved to {MODEL_OUTPUT_PATH}")

    # Run inference to verify and log timing
    timing_logger.start("mc_dropout_inference")
    mean, var = run_mc_dropout_inference(model, X[:10]) # Small sample for logging
    timing_logger.stop("mc_dropout_inference")
    
    timing_logger.save_report()

if __name__ == "__main__":
    main()
