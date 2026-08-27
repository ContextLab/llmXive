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

from utils.timing_logger import TimingLogger

CONFIG_PATH = "code/config.yaml"
PROCESSED_DATA_PATH = "data/processed/features_20pca.csv"
MODEL_OUTPUT_PATH = "results/models/mc_dropout_model.pt"
NUM_SAMPLES = 30

# Ensure output directory exists
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
    if not os.path.exists(PROCESSED_DATA_PATH):
        raise FileNotFoundError(f"Required processed data file not found: {PROCESSED_DATA_PATH}. "
                                "Please run code/data/preprocess.py first.")
    df = pd.read_csv(PROCESSED_DATA_PATH)
    feature_cols = [col for col in df.columns if col.startswith('feature_')]
    if not feature_cols:
        raise ValueError("No feature columns found in processed data.")
    X = df[feature_cols].values
    if 'target' not in df.columns:
        raise ValueError("Target column 'target' not found in processed data.")
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

    logger.info(f"Training MC Dropout model on {n_samples} samples, {input_dim} features.")
    
    for epoch in range(epochs):
        indices = torch.randperm(n_samples)
        X_shuffled = X[indices]
        y_shuffled = y[indices]

        epoch_loss = 0.0
        for i in range(0, n_samples, batch_size):
            batch_X = X_shuffled[i:i+batch_size]
            batch_y = y_shuffled[i:i+batch_size]

            optimizer.zero_grad()
            mean, log_var = model(batch_X)
            # Heteroscedastic loss: NLL for Gaussian
            precision = torch.exp(-log_var)
            loss = precision * (batch_y.unsqueeze(1) - mean) ** 2 + log_var
            loss = loss.mean()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        if (epoch + 1) % 20 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / (n_samples/batch_size):.4f}")

    return model

def run_mc_dropout_inference(model, X):
    """
    Runs NUM_SAMPLES stochastic forward passes with dropout enabled.
    Returns mean prediction, total variance (epistemic + aleatoric).
    """
    model.train() # Crucial: Enable dropout for stochastic inference
    predictions = []
    variances = []

    with torch.no_grad():
        for _ in range(NUM_SAMPLES):
            mean, log_var = model(X)
            predictions.append(mean)
            variances.append(torch.exp(log_var))

    predictions = torch.stack(predictions, dim=0) # (num_samples, batch_size, 1)
    variances = torch.stack(variances, dim=0)     # (num_samples, batch_size, 1)

    # Aggregate results
    mean_pred = predictions.mean(dim=0)
    
    # Epistemic uncertainty: variance of the predictions across samples
    epistemic_var = predictions.var(dim=0)
    
    # Aleatoric uncertainty: mean of the predicted variances
    aleatoric_var = variances.mean(dim=0)
    
    # Total uncertainty
    total_var = epistemic_var + aleatoric_var

    return mean_pred, total_var, epistemic_var, aleatoric_var

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    timing_logger = TimingLogger()
    
    try:
        config = load_config()
        X, y = load_data()

        timing_logger.start("mc_dropout_training")
        model = train_mc_dropout(X, y, config)
        timing_logger.stop("mc_dropout_training")

        # Save the trained model state dict to the required artifact path
        torch.save(model.state_dict(), MODEL_OUTPUT_PATH)
        logger.info(f"MC Dropout model saved to {MODEL_OUTPUT_PATH}")

        # Run inference on a small sample to verify functionality and log timing
        timing_logger.start("mc_dropout_inference")
        # Use a small subset for inference check to keep it fast
        sample_size = min(100, X.shape[0])
        X_sample = X[:sample_size]
        mean, total_var, epistemic_var, aleatoric_var = run_mc_dropout_inference(model, X_sample)
        timing_logger.stop("mc_dropout_inference")
        
        logger.info(f"Inference completed on {sample_size} samples.")
        logger.info(f"Sample prediction stats - Mean: {mean.mean().item():.4f}, Std: {mean.std().item():.4f}")
        logger.info(f"Sample variance stats - Total: {total_var.mean().item():.4f}, Epistemic: {epistemic_var.mean().item():.4f}, Aleatoric: {aleatoric_var.mean().item():.4f}")

        timing_logger.save_report()

    except Exception as e:
        logger.error(f"Error during MC Dropout execution: {e}")
        raise

if __name__ == "__main__":
    main()