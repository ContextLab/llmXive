import os
import torch
import torch.nn as nn
import numpy as np
import yaml
import pandas as pd
import time
import logging

# Import timing logger from the new utility
from utils.timing_logger import timing_logger

# Ensure paths are relative to project root
CONFIG_PATH = "code/config.yaml"
PROCESSED_DATA_PATH = "data/processed/features_20pca.csv"
MODEL_OUTPUT_DIR = "results/models"
MODEL_OUTPUT_PATH = os.path.join(MODEL_OUTPUT_DIR, "baseline_seed42.pt")

os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data():
    """Load the preprocessed features and target."""
    df = pd.read_csv(PROCESSED_DATA_PATH)
    # Assuming standard columns 'feature_0'...'feature_19' and 'target'
    feature_cols = [col for col in df.columns if col.startswith('feature_')]
    X = df[feature_cols].values
    y = df['target'].values
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

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
        
        # Output head: mean and log_variance (for heteroscedasticity)
        self.mean_head = nn.Linear(prev_dim, 1)
        self.log_var_head = nn.Linear(prev_dim, 1)

    def forward(self, x):
        h = self.backbone(x)
        mean = self.mean_head(h)
        log_var = self.log_var_head(h)
        return mean, log_var

def negative_log_likelihood_loss(mean, log_var, y):
    """
    Negative Log Likelihood loss for heteroscedastic regression.
    Assumes y ~ N(mean, exp(log_var)).
    """
    precision = torch.exp(-log_var)
    loss = precision * (y - mean) ** 2 + log_var
    return loss.mean()

def train_model():
    config = load_config()
    seed = config.get('seed', 42)
    torch.manual_seed(seed)
    np.random.seed(seed)

    X, y = load_processed_data()
    input_dim = X.shape[1]

    model = HeteroscedasticNN(input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    # Start timing
    timing_logger.start("baseline_nn_training")
    
    epochs = 100
    batch_size = 64
    n_samples = X.shape[0]
    
    model.train()
    for epoch in range(epochs):
        # Simple shuffling
        indices = torch.randperm(n_samples)
        X_shuffled = X[indices]
        y_shuffled = y[indices]

        epoch_loss = 0.0
        for i in range(0, n_samples, batch_size):
            batch_X = X_shuffled[i:i+batch_size]
            batch_y = y_shuffled[i:i+batch_size]

            optimizer.zero_grad()
            mean, log_var = model(batch_X)
            loss = negative_log_likelihood_loss(mean, log_var, batch_y.unsqueeze(1))
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        if (epoch + 1) % 20 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / (n_samples/batch_size):.4f}")

    # Stop timing
    timing_logger.stop("baseline_nn_training")

    # Save model
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config
    }, MODEL_OUTPUT_PATH)
    logger.info(f"Model saved to {MODEL_OUTPUT_PATH}")

    return model

def main():
    setup_logging = None # Placeholder if not imported from main
    logging.basicConfig(level=logging.INFO)
    train_model()
    timing_logger.save_report()

if __name__ == "__main__":
    main()
