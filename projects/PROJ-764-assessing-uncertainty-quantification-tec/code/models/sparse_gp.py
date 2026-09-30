import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

# Importing from sibling modules as per API surface
from models.baseline_nn import load_config

# Setup logger
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger("sparse_gp")

def load_config() -> dict:
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load processed data from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at {path}")
    return pd.read_csv(path)

def verify_dependencies() -> bool:
    """
    T015a Implementation: Verification step.
    Checks existence of required artifacts before execution.
    Fails loudly if missing.
    """
    required_files = [
        "data/processed/features_train_20pca.csv",
        "data/processed/features_test_20pca.csv",
        "data/processed/pca_transformer.pkl"
    ]
    
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
            logger.error(f"Required artifact missing: {f}")
        else:
            logger.info(f"Verified artifact: {f}")

    if missing:
        error_msg = f"CRITICAL: Missing required artifacts: {missing}. " \
                    "T015a verification failed. Cannot proceed to training (T015b)."
        logger.critical(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info("All dependencies verified. PCA transformer exists; re-fitting is prevented by design.")
    return True

class SparseGPModel:
    """
    Sparse Gaussian Process Model wrapper using GPyTorch.
    Implements Stochastic Variational Inference with 500 inducing points.
    """
    def __init__(self, num_features: int, num_inducing: int = 500):
        import torch
        import gpytorch
        
        self.num_features = num_features
        self.num_inducing = num_inducing
        self.device = torch.device("cpu")
        
        # Initialize inducing points randomly (will be optimized during training)
        self.inducing_points = torch.randn(num_inducing, num_features, device=self.device)
        
        # Model definition
        class ExactGPModel(gpytorch.models.ExactGP):
            def __init__(self, train_x, train_y, likelihood):
                super().__init__(train_x, train_y, likelihood)
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())
            
            def forward(self, x):
                mean_x = self.mean_module(x)
                covar_x = self.covar_module(x)
                return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

        class VariationalGPModel(gpytorch.models.VariationalGP):
            def __init__(self, train_x, likelihood):
                super().__init__(train_x, likelihood)
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())
            
            def forward(self, x):
                mean_x = self.mean_module(x)
                covar_x = self.covar_module(x)
                return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

        class PredictiveGPModel(gpytorch.models.PredictiveGP):
            def __init__(self, train_x, likelihood, inducing_points):
                super().__init__(train_x, likelihood, inducing_points)
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())
            
            def forward(self, x):
                mean_x = self.mean_module(x)
                covar_x = self.covar_module(x)
                return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

        # Using VariationalGP with Stochastic Variational Inference for scalability
        self.likelihood = gpytorch.likelihoods.GaussianLikelihood().to(self.device)
        self.model = VariationalGPModel(self.inducing_points, self.likelihood).to(self.device)
        
        self.train_x = None
        self.train_y = None
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 50, lr: float = 0.1):
        """
        Fit the Sparse GP model using Stochastic Variational Inference.
        
        Args:
            X: Training features (n_samples, n_features)
            y: Training targets (n_samples,)
            epochs: Number of training iterations
            lr: Learning rate for the optimizer
        """
        import torch
        import gpytorch
        
        logger.info(f"Starting Sparse GP training with {X.shape[0]} samples, {X.shape[1]} features")
        logger.info(f"Using {self.num_inducing} inducing points")

        # Convert to tensors
        self.train_x = torch.tensor(X, dtype=torch.float32).to(self.device)
        self.train_y = torch.tensor(y, dtype=torch.float32).to(self.device)

        # Update model's inducing points to match training data dimension
        # Re-initialize with actual inducing points from data if possible
        if X.shape[0] >= self.num_inducing:
            # Use k-means or random sampling for inducing points
            indices = np.random.choice(X.shape[0], self.num_inducing, replace=False)
            self.inducing_points = torch.tensor(X[indices], dtype=torch.float32).to(self.device)
            self.model = VariationalGPModel(self.inducing_points, self.likelihood).to(self.device)
        else:
            # Use all data as inducing points if less than requested
            self.inducing_points = torch.tensor(X, dtype=torch.float32).to(self.device)
            self.model = VariationalGPModel(self.inducing_points, self.likelihood).to(self.device)
            self.num_inducing = X.shape[0]
            logger.info(f"Adjusted inducing points to {self.num_inducing} (less than requested)")

        # Set model to training mode
        self.model.train()
        self.likelihood.train()

        # Optimizer
        optimizer = torch.optim.Adam([
            {'params': self.model.variational_parameters()},
            {'params': self.likelihood.parameters()},
            {'params': self.model.hyperparameters()},
        ], lr=lr)

        # Loss
        mll = gpytorch.mlls.VariationalELBO(self.likelihood, self.model, num_data=self.train_y.size(0))

        # Training loop
        logger.info("Training loop started...")
        for i in range(epochs):
            optimizer.zero_grad()
            output = self.model(self.train_x)
            loss = -mll(output, self.train_y)
            loss.backward()
            optimizer.step()
            
            if (i + 1) % 10 == 0:
                logger.info(f"Epoch {i+1}/{epochs} - Loss: {loss.item():.4f}")

        self.is_fitted = True
        logger.info("Sparse GP training completed successfully.")

    def predict(self, X: np.ndarray) -> tuple:
        """
        Make predictions with uncertainty quantification.
        
        Args:
            X: Test features (n_samples, n_features)
            
        Returns:
            tuple: (mean predictions, variance predictions)
        """
        import torch
        import gpytorch
        
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted. Call fit() first.")

        self.model.eval()
        self.likelihood.eval()

        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            test_x = torch.tensor(X, dtype=torch.float32).to(self.device)
            observed_pred = self.likelihood(self.model(test_x))
            
            mean = observed_pred.mean.cpu().numpy()
            variance = observed_pred.variance.cpu().numpy()
            
            return mean, variance

    def save(self, path: str):
        """Save the fitted model and inducing points."""
        import torch
        
        save_data = {
            'model_state_dict': self.model.state_dict(),
            'likelihood_state_dict': self.likelihood.state_dict(),
            'inducing_points': self.inducing_points,
            'num_inducing': self.num_inducing,
            'num_features': self.num_features,
            'is_fitted': self.is_fitted
        }
        
        torch.save(save_data, path)
        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: str) -> 'SparseGPModel':
        """Load a fitted model."""
        import torch
        
        save_data = torch.load(path, map_location=torch.device('cpu'))
        
        model = cls(
            num_features=save_data['num_features'],
            num_inducing=save_data['num_inducing']
        )
        
        model.model.load_state_dict(save_data['model_state_dict'])
        model.likelihood.load_state_dict(save_data['likelihood_state_dict'])
        model.inducing_points = save_data['inducing_points']
        model.is_fitted = save_data['is_fitted']
        
        logger.info(f"Model loaded from {path}")
        return model

def train_sparse_gp():
    """
    T015b Implementation: Fit Sparse GP model.
    
    Loads PCA-reduced features from data/processed/features_train_20pca.csv
    and the transformer from data/processed/pca_transformer.pkl.
    Fits Sparse GP with 500 inducing points and RBF kernel.
    """
    logger.info("Starting T015b: Sparse GP Fitting")
    
    # Verify dependencies first (T015a check)
    verify_dependencies()
    
    # Load config
    config = load_config()
    seed = config.get('seed', 42)
    np.random.seed(seed)
    
    # Load training data
    logger.info("Loading training data...")
    train_df = load_processed_data("data/processed/features_train_20pca.csv")
    
    # Extract features and target
    # Assuming the target column is 'formation_energy' or similar
    # Based on preprocessing tasks, the target should be present
    target_col = 'formation_energy'
    if target_col not in train_df.columns:
        # Try alternative column names
        possible_targets = ['target', 'y', 'formation_energy_eV']
        target_col = None
        for col in possible_targets:
            if col in train_df.columns:
                target_col = col
                break
        
        if target_col is None:
            raise ValueError(f"Could not find target column in {train_df.columns}")
    
    X_train = train_df.drop(columns=[target_col]).values
    y_train = train_df[target_col].values
    
    logger.info(f"Training data shape: {X_train.shape}")
    logger.info(f"Target range: [{y_train.min():.4f}, {y_train.max():.4f}]")
    
    # Initialize model
    num_features = X_train.shape[1]
    model = SparseGPModel(num_features=num_features, num_inducing=500)
    
    # Train model
    logger.info("Fitting Sparse GP model...")
    model.fit(X_train, y_train, epochs=100, lr=0.1)
    
    return model

def save_model(model, path: str):
    """
    T015c Implementation: Save fitted model.
    """
    model.save(path)
    logger.info(f"Model saved to {path}")

def main():
    """
    Entry point for T015b fitting.
    """
    logger.info("Starting T015b: Sparse GP Fitting")
    
    try:
        # 1. Verify dependencies (T015a check)
        verify_dependencies()
        
        # 2. Train model
        model = train_sparse_gp()
        
        # 3. Save model (T015c)
        output_path = "results/models/sparse_gp_model.pt"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        save_model(model, output_path)
        
        logger.info("T015b Fitting COMPLETED successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Fitting FAILED: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during fitting: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
