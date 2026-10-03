"""
MC Dropout Inference Module.

Implements Monte Carlo Dropout for uncertainty quantification.
Enables dropout during inference to generate stochastic predictions.
"""
import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/mc_dropout.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure results directories exist
Path('results/models/mc_dropout').mkdir(parents=True, exist_ok=True)
Path('results').mkdir(parents=True, exist_ok=True)

class MCDropoutModel(nn.Module):
    """
    Heteroscedastic Neural Network with MC Dropout enabled.
    Same architecture as baseline but with configurable dropout for inference.
    """
    def __init__(self, input_dim, hidden_dims=[64, 32], dropout_rate=0.2):
        super(MCDropoutModel, self).__init__()
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate

        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(p=dropout_rate))
            prev_dim = hidden_dim

        self.feature_extractor = nn.Sequential(*layers)

        # Heteroscedastic head: predicts mean and log variance
        self.mean_head = nn.Linear(prev_dim, 1)
        self.variance_head = nn.Linear(prev_dim, 1)

    def forward(self, x):
        features = self.feature_extractor(x)
        mean = self.mean_head(features)
        log_var = self.variance_head(features)
        # Ensure variance is positive
        variance = torch.exp(log_var)
        return mean, variance

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters())


def load_config():
    """Load configuration from code/config.yaml"""
    config_path = 'code/config.yaml'
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_data(split='test'):
    """
    Load processed PCA-reduced data.
    Expects files: data/processed/features_test_20pca.csv, etc.
    """
    file_map = {
        'train': 'data/processed/features_train_20pca.csv',
        'val': 'data/processed/features_val_20pca.csv',
        'test': 'data/processed/features_test_20pca.csv'
    }

    if split not in file_map:
        raise ValueError(f"Unknown split: {split}")

    path = file_map[split]
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required data file not found: {path}. "
            "Ensure T006b (preprocess.py) has completed successfully."
        )

    df = pd.read_csv(path)

    # Identify feature columns (exclude target and target_bin if present)
    feature_cols = [col for col in df.columns if col not in ['target', 'target_bin', 'sample_id']]
    target_col = 'target' if 'target' in df.columns else df.columns[-1]

    X = df[feature_cols].values.astype(np.float32)
    y = df[target_col].values.astype(np.float32)

    # Convert to PyTorch tensors
    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32).unsqueeze(1)

    return X_tensor, y_tensor


def train_mc_dropout(config, seed=42):
    """
    Train a single MC Dropout model.
    Uses the same training loop as baseline but ensures dropout is active.
    """
    logger.info(f"Training MC Dropout model with seed {seed}")

    # Set seeds for reproducibility
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Load training data
    X_train, y_train = load_data('train')
    X_val, y_val = load_data('val')

    # Create data loaders
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)

    batch_size = config.get('training', {}).get('batch_size', 64)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Initialize model
    input_dim = X_train.shape[1]
    hidden_dims = config.get('model', {}).get('hidden_dims', [64, 32])
    dropout_rate = config.get('model', {}).get('dropout_rate', 0.2)

    model = MCDropoutModel(input_dim, hidden_dims, dropout_rate)
    logger.info(f"Model architecture: {model}")
    logger.info(f"Total parameters: {model.count_parameters()}")

    # Training hyperparameters
    epochs = config.get('training', {}).get('epochs', 100)
    lr = config.get('training', {}).get('lr', 0.001)

    # Optimizer and loss
    optimizer = optim.Adam(model.parameters(), lr=lr)

    def negative_log_likelihood_loss(mean, variance, y_true):
        """
        Negative log-likelihood for heteroscedastic regression.
        Loss = 0.5 * (log(var) + (y_true - mean)^2 / var)
        """
        return torch.mean(0.5 * (torch.log(variance) + (y_true - mean) ** 2 / variance))

    # Training loop
    best_val_loss = float('inf')
    patience = 10
    patience_counter = 0

    for epoch in range(epochs):
        model.train()  # Ensure dropout is active during training
        train_loss = 0.0

        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            mean, variance = model(batch_X)
            loss = negative_log_likelihood_loss(mean, variance, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                mean, variance = model(batch_X)
                loss = negative_log_likelihood_loss(mean, variance, batch_y)
                val_loss += loss.item()

        val_loss /= len(val_loader)

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), 'results/models/mc_dropout/mc_dropout_seed_42.pt')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

    logger.info(f"Training completed. Best validation loss: {best_val_loss:.6f}")
    return model


def run_mc_dropout_inference(model, X_test, n_passes=30):
    """
    Run MC Dropout inference with stochastic forward passes.

    Args:
        model: Trained MC Dropout model
        X_test: Test features tensor
        n_passes: Number of stochastic forward passes

    Returns:
        predictions: Mean predictions across passes
        variances: Total variance (epistemic + aleatoric)
    """
    logger.info(f"Running MC Dropout inference with {n_passes} passes")

    model.train()  # CRITICAL: Enable dropout during inference

    all_predictions = []
    all_variances = []

    with torch.no_grad():
        for i in range(n_passes):
            mean, variance = model(X_test)
            all_predictions.append(mean.numpy().flatten())
            all_variances.append(variance.numpy().flatten())

    # Stack predictions and variances
    predictions_stack = np.stack(all_predictions, axis=1)  # (n_samples, n_passes)
    variances_stack = np.stack(all_variances, axis=1)

    # Calculate mean prediction
    mean_predictions = np.mean(predictions_stack, axis=1)

    # Calculate total variance:
    # Epistemic variance = variance of predictions across passes
    # Aleatoric variance = mean of predicted variances
    epistemic_variance = np.var(predictions_stack, axis=1)
    aleatoric_variance = np.mean(variances_stack, axis=1)

    # Total variance
    total_variance = epistemic_variance + aleatoric_variance

    return mean_predictions, total_variance, epistemic_variance, aleatoric_variance


def main():
    """Main entry point for MC Dropout training and inference."""
    import yaml

    logger.info("Starting MC Dropout Inference Pipeline")

    # Load configuration
    config = load_config()

    # Get seed from config or use default
    seed = config.get('seed', 42)

    # Train the model
    model = train_mc_dropout(config, seed=seed)

    # Load test data
    X_test, y_test = load_data('test')
    logger.info(f"Test set size: {X_test.shape[0]}")

    # Run MC Dropout inference
    n_passes = config.get('uq', {}).get('mc_dropout_passes', 30)
    mean_preds, total_var, epistemic_var, aleatoric_var = run_mc_dropout_inference(
        model, X_test, n_passes=n_passes
    )

    # Calculate bounds using Gaussian assumption (z-scores)
    # 50% CI: z = 0.674
    # 90% CI: z = 1.645
    z_50 = 0.674
    z_90 = 1.645

    std_dev = np.sqrt(total_var)
    lower_50 = mean_preds - z_50 * std_dev
    upper_50 = mean_preds + z_50 * std_dev
    lower_90 = mean_preds - z_90 * std_dev
    upper_90 = mean_preds + z_90 * std_dev

    # Create results DataFrame
    results_df = pd.DataFrame({
        'sample_id': range(len(mean_preds)),
        'method': 'mc_dropout',
        'prediction': mean_preds,
        'variance': total_var,
        'lower_50': lower_50,
        'upper_50': upper_50,
        'lower_90': lower_90,
        'upper_90': upper_90
    })

    # Save predictions to CSV
    output_path = 'results/uq_predictions_mc_dropout.csv'
    results_df.to_csv(output_path, index=False)
    logger.info(f"MC Dropout predictions saved to {output_path}")

    # Verify the model file exists (it should have been saved during training)
    model_path = 'results/models/mc_dropout/mc_dropout_seed_42.pt'
    if os.path.exists(model_path):
        logger.info(f"Model saved to {model_path}")
    else:
        logger.warning(f"Model file not found at {model_path}")

    logger.info("MC Dropout Inference Pipeline completed successfully")


if __name__ == '__main__':
    main()
