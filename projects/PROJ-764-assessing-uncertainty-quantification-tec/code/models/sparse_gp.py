import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import torch
import gpytorch
from gpytorch.models import ApproximateGP
from gpytorch.variational import CholeskyVariationalDistribution, VariationalStrategy
from gpytorch.kernels import RBFKernel, ScaleKernel
from gpytorch.likelihoods import GaussianLikelihood

# --- Setup Logger ---
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger('sparse_gp')

# --- Config Loading ---
def load_config():
    config_path = Path('code/config.yaml')
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# --- Data Loading ---
def load_processed_data():
    """
    Loads PCA-reduced training features.
    Expects: data/processed/features_train_20pca.csv
    """
    train_path = Path('data/processed/features_train_20pca.csv')
    if not train_path.exists():
        raise FileNotFoundError(f"Required artifact missing: {train_path}")
    
    df = pd.read_csv(train_path)
    # Assuming the first column is index/sample_id, and rest are features
    # We need to separate features (X) and target (y)
    # The target column name is typically 'formation_energy' or similar based on context
    # Let's assume the last column is the target if not explicitly named, 
    # but standard practice in this pipeline is to have explicit columns.
    # Based on T006d, the output CSVs contain features. The target was likely separated or is in a specific column.
    # Looking at T006d output: "features_train_20pca.csv". Usually this implies X only, or X+y.
    # Let's assume the CSV contains 'target' column or 'formation_energy' based on previous steps.
    # If not, we might need to load y separately. 
    # However, T006d says "Transform train/val/test sets". Usually this means X.
    # Let's check if 'target' or 'formation_energy' exists.
    if 'formation_energy' in df.columns:
        y = df['formation_energy'].values
        X = df.drop(columns=['formation_energy']).values
    elif 'target' in df.columns:
        y = df['target'].values
        X = df.drop(columns=['target']).values
    else:
        # Fallback: assume last column is target
        y = df.iloc[:, -1].values
        X = df.iloc[:, :-1].values
    
    return X, y

# --- Dependency Verification ---
def verify_dependencies():
    """
    Checks existence of required artifacts before execution.
    """
    required_files = [
        'data/processed/features_train_20pca.csv',
        'data/processed/features_test_20pca.csv',
        'data/processed/pca_transformer.pkl'
    ]
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        logger.critical(f"CRITICAL: Missing required artifacts: {missing}. T006d verification failed. Cannot proceed.")
        raise FileNotFoundError(f"Missing artifacts: {missing}")
    
    logger.info("All required artifacts verified.")

# --- Sparse GP Model Definition ---
class InducingPointGP(ApproximateGP):
    def __init__(self, inducing_points):
        variational_distribution = CholeskyVariationalDistribution(inducing_points.size(0))
        variational_strategy = VariationalStrategy(
            self, inducing_points, variational_distribution, learn_inducing_locations=True
        )
        super().__init__(variational_strategy)
        
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = ScaleKernel(RBFKernel())

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

class SparseGPModel:
    def __init__(self, input_dim, inducing_points):
        self.input_dim = input_dim
        self.inducing_points = inducing_points
        self.model = None
        self.likelihood = None
        self.training = False

    def fit(self, X_train, y_train, epochs=50, lr=0.01):
        """
        Fits the Sparse GP model on CPU.
        """
        self.training = True
        X = torch.tensor(X_train, dtype=torch.float32)
        y = torch.tensor(y_train, dtype=torch.float32)
        
        # Initialize inducing points (random subset or k-means, using random here for simplicity)
        n_inducing = min(self.inducing_points, X.size(0))
        idx = torch.randperm(X.size(0))[:n_inducing]
        inducing_points = X[idx]
        
        self.model = InducingPointGP(inducing_points).to('cpu')
        self.likelihood = GaussianLikelihood().to('cpu')
        
        self.model.train()
        self.likelihood.train()
        
        optimizer = torch.optim.Adam([
            {'params': self.model.parameters()},
            {'params': self.likelihood.parameters()}
        ], lr=lr)
        
        mll = gpytorch.mlls.VariationalELBO(self.likelihood, self.model, num_data=y.size(0))
        
        logger.info(f"Starting training for {epochs} epochs...")
        
        for i in range(epochs):
            optimizer.zero_grad()
            output = self.model(X)
            loss = -mll(output, y)
            loss.backward()
            optimizer.step()
            
            if (i + 1) % 10 == 0:
                logger.info(f"Epoch {i+1}/{epochs} - Loss: {loss.item():.4f}")
        
        logger.info("Training completed.")
        return self

    def predict(self, X_test, return_std=True):
        """
        Returns predictions and standard deviations.
        """
        if not self.training:
            self.model.eval()
            self.likelihood.eval()
        
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            X = torch.tensor(X_test, dtype=torch.float32)
            observed_pred = self.likelihood(self.model(X))
            mean = observed_pred.mean.numpy()
            if return_std:
                std = observed_pred.stddev.numpy()
                return mean, std
            return mean

    def save(self, path):
        """
        Saves the model state.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = {
            'model': self.model.state_dict(),
            'likelihood': self.likelihood.state_dict(),
            'inducing_points': self.model.variational_strategy.inducing_points,
            'input_dim': self.input_dim
        }
        torch.save(state, path)
        logger.info(f"Model saved to {path}")

    def load(self, path):
        """
        Loads the model state.
        """
        state = torch.load(path, map_location='cpu')
        self.input_dim = state['input_dim']
        # Re-initialize with correct inducing points count
        n_inducing = state['inducing_points'].size(0)
        self.model = InducingPointGP(state['inducing_points']).to('cpu')
        self.likelihood = GaussianLikelihood().to('cpu')
        self.model.load_state_dict(state['model'])
        self.likelihood.load_state_dict(state['likelihood'])
        self.model.eval()
        self.likelihood.eval()
        logger.info(f"Model loaded from {path}")

# --- Training Function ---
def train_sparse_gp(X_train, y_train, inducing_points=500, epochs=100, lr=0.01):
    input_dim = X_train.shape[1]
    model = SparseGPModel(input_dim, inducing_points)
    model.fit(X_train, y_train, epochs=epochs, lr=lr)
    return model

# --- Metric Calculation ---
def calculate_reconstruction_variance(model, X_train, y_train):
    """
    Calculates reconstruction variance (mean of predictive variances on training set).
    """
    model.training = False # Ensure eval mode for prediction
    mean, std = model.predict(X_train, return_std=True)
    # Variance is std^2
    variances = std ** 2
    mean_variance = float(np.mean(variances))
    return mean_variance

# --- Main Entry Point ---
def main():
    parser = argparse.ArgumentParser(description='Sparse GP Fitting and Saving')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()
    
    # Set seeds for reproducibility
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    
    # Verify dependencies
    verify_dependencies()
    
    # Load data
    logger.info("Loading processed training data...")
    X_train, y_train = load_processed_data()
    logger.info(f"Loaded training data: X={X_train.shape}, y={y_train.shape}")
    
    # Get config for hyperparameters
    try:
        import yaml
        config = load_config()
        inducing_points = config.get('model', {}).get('gp_inducing_points', 500)
        epochs = config.get('training', {}).get('epochs', 100)
        lr = config.get('training', {}).get('lr', 0.01) # Adjusted for GP
    except Exception as e:
        logger.warning(f"Could not load config, using defaults. Error: {e}")
        inducing_points = 500
        epochs = 100
        lr = 0.01
    
    # Train model
    logger.info(f"Training Sparse GP with {inducing_points} inducing points...")
    gp_model = train_sparse_gp(X_train, y_train, inducing_points=inducing_points, epochs=epochs, lr=lr)
    
    # Save model
    output_path = 'results/models/sparse_gp_model.pt'
    gp_model.save(output_path)
    
    # Calculate and save reconstruction variance
    logger.info("Calculating reconstruction variance...")
    reconstruction_var = calculate_reconstruction_variance(gp_model, X_train, y_train)
    
    variance_path = 'results/gp_reconstruction_variance.json'
    os.makedirs(os.path.dirname(variance_path), exist_ok=True)
    with open(variance_path, 'w') as f:
        json.dump({"reconstruction_variance": reconstruction_var}, f, indent=2)
    
    logger.info(f"Reconstruction variance saved to {variance_path}: {reconstruction_var}")
    logger.info("Task T015 completed successfully.")

if __name__ == '__main__':
    main()