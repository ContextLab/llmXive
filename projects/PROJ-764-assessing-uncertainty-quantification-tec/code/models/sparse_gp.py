"""
Sparse Gaussian Process implementation for uncertainty quantification.

This module implements a Sparse Variational Gaussian Process using GPyTorch
for scalable uncertainty estimation on material property predictions.

Dependencies:
  - GPyTorch (for GP implementation)
  - PyTorch (for tensor operations)
  - scikit-learn (for preprocessing utilities)
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import gpytorch
from gpytorch.models import ApproximateGP
from gpytorch.variational import CholeskyVariationalDistribution, VariationalStrategy
from gpytorch.mlls import VariationalELBO
from gpytorch.likelihoods import GaussianLikelihood
from gpytorch.kernels import RBFKernel, ScaleKernel
from gpytorch.means import ConstantMean

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEVICE = torch.device('cpu')
RANDOM_SEED = 42

# Set random seeds for reproducibility
torch.manual_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)

class SparseGPModel(ApproximateGP):
    """
    Sparse Variational Gaussian Process Model.
    
    Uses inducing points to approximate the full GP for scalability.
    """
    
    def __init__(self, num_features: int, num_inducing_points: int = 500):
        """
        Initialize the Sparse GP model.
        
        Args:
            num_features: Number of input features
            num_inducing_points: Number of inducing points for the sparse approximation
        """
        # Initialize variational distribution and strategy
        variational_distribution = CholeskyVariationalDistribution(
            num_inducing_points, batch_shape=torch.Size([])
        )
        variational_strategy = VariationalStrategy(
            self,
            torch.randn(num_inducing_points, num_features, device=DEVICE),
            variational_distribution,
            learn_inducing_locations=True
        )
        
        super(SparseGPModel, self).__init__(variational_strategy)
        
        # Mean function
        self.mean_module = ConstantMean()
        
        # Covariance function (RBF kernel with automatic relevance determination)
        self.covar_module = ScaleKernel(
            RBFKernel(ard_num_dims=num_features),
            batch_shape=torch.Size([])
        )
        
        # Likelihood for heteroscedastic noise (optional, using homoscedastic for now)
        self.likelihood = GaussianLikelihood()
        
        logger.info(f"Initialized SparseGPModel with {num_features} features and {num_inducing_points} inducing points")
    
    def forward(self, x):
        """Forward pass through the GP model."""
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)
    
    def predict(self, test_x):
        """
        Make predictions on test data.
        
        Args:
            test_x: Test input features (tensor)
            
        Returns:
            Tuple of (mean predictions, variance predictions)
        """
        self.eval()
        self.likelihood.eval()
        
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            observed_pred = self.likelihood(self(test_x))
            mean = observed_pred.mean
            variance = observed_pred.variance
            
        return mean.cpu().numpy(), variance.cpu().numpy()

def load_config(config_path: str = "code/config.yaml") -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration parameters
    """
    import yaml
    
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return {
            'seed': RANDOM_SEED,
            'num_inducing_points': 500,
            'max_epochs': 100,
            'learning_rate': 0.01
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def load_processed_data(
    features_path: str = "data/processed/features_test_20pca.csv",
    target_path: str = "data/processed/raw_test.csv"
):
    """
    Load preprocessed training and test data.
    
    Args:
        features_path: Path to PCA-reduced features file
        target_path: Path to target values file
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test) as numpy arrays
    """
    logger.info(f"Loading features from {features_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    features_df = pd.read_csv(features_path)
    
    # Separate features and target
    # Assuming target column is named 'target' or 'formation_energy'
    target_col = None
    for col in ['target', 'formation_energy', 'y']:
        if col in features_df.columns:
            target_col = col
            break
    
    if target_col is None:
        # Try to load from separate target file
        if os.path.exists(target_path):
            target_df = pd.read_csv(target_path)
            if 'target' in target_df.columns:
                y = target_df['target'].values
            elif 'formation_energy' in target_df.columns:
                y = target_df['formation_energy'].values
            else:
                raise ValueError("No target column found in data files")
            X = features_df.drop(columns=[col for col in features_df.columns if col in ['sample_id', 'target_bin']]).values
        else:
            raise ValueError("Target column not found and separate target file not available")
    else:
        y = features_df[target_col].values
        X = features_df.drop(columns=[target_col, 'target_bin', 'sample_id'] if 'sample_id' in features_df.columns 
                             else [target_col, 'target_bin']).values
    
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")
    return X, y

def train_sparse_gp(
    X_train: np.ndarray,
    y_train: np.ndarray,
    num_inducing_points: int = 500,
    max_epochs: int = 100,
    learning_rate: float = 0.01
):
    """
    Train the Sparse Gaussian Process model.
    
    Args:
        X_train: Training features (numpy array)
        y_train: Training targets (numpy array)
        num_inducing_points: Number of inducing points
        max_epochs: Maximum training epochs
        learning_rate: Learning rate for optimization
        
    Returns:
        Trained SparseGPModel instance
    """
    logger.info(f"Training Sparse GP with {num_inducing_points} inducing points")
    
    # Convert to tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32).to(DEVICE)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32).to(DEVICE)
    
    # Initialize model
    model = SparseGPModel(
        num_features=X_train.shape[1],
        num_inducing_points=num_inducing_points
    ).to(DEVICE)
    
    # Initialize likelihood
    likelihood = GaussianLikelihood().to(DEVICE)
    
    # Training setup
    model.train()
    likelihood.train()
    
    optimizer = torch.optim.Adam([
        {'params': model.variational_parameters()},
        {'params': likelihood.parameters()},
        {'params': model.parameters()},
    ], lr=learning_rate)
    
    mll = VariationalELBO(likelihood, model, num_data=len(y_train_tensor))
    
    # Training loop
    logger.info("Starting training loop...")
    for epoch in range(max_epochs):
        optimizer.zero_grad()
        
        output = model(X_train_tensor)
        loss = -mll(output, y_train_tensor)
        
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch + 1}/{max_epochs} - Loss: {loss.item():.4f}")
    
    logger.info("Training completed")
    return model, likelihood

def save_model(model, likelihood, output_path: str):
    """
    Save the trained GP model and likelihood to disk.
    
    Args:
        model: Trained SparseGPModel instance
        likelihood: Trained GaussianLikelihood instance
        output_path: Path to save the model checkpoint
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Save model state
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'likelihood_state_dict': likelihood.state_dict(),
        'num_features': model.variational_strategy.inducing_points.shape[1],
        'num_inducing_points': model.variational_strategy.inducing_points.shape[0]
    }
    
    torch.save(checkpoint, output_path)
    logger.info(f"Model saved to {output_path}")

def main():
    """Main entry point for training and saving the Sparse GP model."""
    parser = argparse.ArgumentParser(description='Train and save Sparse GP model')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--features', type=str, default='data/processed/features_test_20pca.csv', help='Path to features file')
    parser.add_argument('--target', type=str, default='data/processed/raw_test.csv', help='Path to target file')
    parser.add_argument('--output', type=str, default='results/models/sparse_gp_model.pt', help='Path to save model')
    parser.add_argument('--inducing-points', type=int, default=500, help='Number of inducing points')
    parser.add_argument('--epochs', type=int, default=100, help='Maximum training epochs')
    parser.add_argument('--lr', type=float, default=0.01, help='Learning rate')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command line arguments if provided
    num_inducing_points = args.inducing_points if args.inducing_points != 500 else config.get('num_inducing_points', 500)
    max_epochs = args.epochs if args.epochs != 100 else config.get('max_epochs', 100)
    learning_rate = args.lr if args.lr != 0.01 else config.get('learning_rate', 0.01)
    
    # Load data
    try:
        X_train, y_train = load_processed_data(args.features, args.target)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Train model
    model, likelihood = train_sparse_gp(
        X_train, y_train,
        num_inducing_points=num_inducing_points,
        max_epochs=max_epochs,
        learning_rate=learning_rate
    )
    
    # Save model
    save_model(model, likelihood, args.output)
    
    logger.info("Sparse GP training and saving completed successfully")

if __name__ == '__main__':
    main()
