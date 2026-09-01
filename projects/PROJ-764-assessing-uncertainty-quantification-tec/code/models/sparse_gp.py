import os
import sys
import json
import torch
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import yaml
import joblib

try:
    import gpytorch
    from gpytorch.models import SparseVariational
    from gpytorch.kernels import RBFKernel, ScaleKernel
    from gpytorch.means import ConstantMean
    from gpytorch.mlls import VariationalELBO
    from gpytorch.likelihoods import GaussianLikelihood
    from gpytorch.variational import VariationalStrategy, CholeskyVariationalDistribution
except ImportError:
    logging.error("gpytorch not installed. Cannot run SparseGP.")
    sys.exit(1)

logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)

def load_processed_data(split: str = "test"):
    """
    Loads the pre-processed PCA features and target for the specified split.
    Explicitly checks for the existence of the required input files as per T015.
    """
    # T015 Requirement: Explicit Check for existence of input files
    features_path = Path(f"data/processed/features_{split}_20pca.csv")
    pca_transformer_path = Path("data/processed/pca_transformer.pkl")

    if not features_path.exists():
        raise FileNotFoundError(
            f"Required input file missing: {features_path}. "
            "Ensure T006b3 (preprocess PCA) has completed successfully."
        )
    
    # We verify the transformer exists to ensure the pipeline state is consistent,
    # even though we don't re-fit it.
    if not pca_transformer_path.exists():
        raise FileNotFoundError(
            f"Required PCA transformer missing: {pca_transformer_path}. "
            "Ensure T006b3 has completed successfully."
        )

    df = pd.read_csv(features_path)
    
    # Ensure columns exist
    expected_pca_cols = [f'pca_{i}' for i in range(20)]
    if not all(col in df.columns for col in expected_pca_cols):
        raise ValueError(f"Input CSV missing expected PCA columns. Found: {df.columns.tolist()}")
    
    if 'formation_energy' not in df.columns:
        raise ValueError("Input CSV missing 'formation_energy' target column.")

    X = torch.tensor(df[expected_pca_cols].values, dtype=torch.float32)
    y = torch.tensor(df['formation_energy'].values, dtype=torch.float32)
    return X, y

class SparseGPModel(SparseVariational):
    """
    A Sparse Variational Gaussian Process model using GPyTorch.
    """
    def __init__(self, train_x, train_y, inducing_points):
        # Use CholeskyVariationalDistribution for stability
        variational_distribution = CholeskyVariationalDistribution(inducing_points.size(0))
        variational_strategy = VariationalStrategy(
            None,  # Will be set after super init if needed, but passing self here
            inducing_points,
            variational_distribution,
            learn_inducing_locations=True
        )
        
        # Correct initialization for SparseVariational
        # We need to pass the strategy to the parent
        super().__init__(variational_strategy)
        
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(RBFKernel())

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

def train_sparse_gp(input_dim: int, seed: int, n_inducing: int = 100, n_epochs: int = 200):
    """
    Trains the Sparse GP model on the training set.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Load training data
    train_path = Path("data/processed/features_train_20pca.csv")
    if not train_path.exists():
        raise FileNotFoundError(f"Training data missing: {train_path}. Run T006b3 first.")
    
    train_df = pd.read_csv(train_path)
    train_X = torch.tensor(train_df[[f'pca_{i}' for i in range(20)]].values, dtype=torch.float32)
    train_y = torch.tensor(train_df['formation_energy'].values, dtype=torch.float32)

    # Select inducing points
    inducing_idx = np.random.choice(train_X.shape[0], n_inducing, replace=False)
    inducing_points = train_X[inducing_idx]

    # Initialize model
    # Note: The parent class expects the strategy. We construct it inline.
    variational_distribution = CholeskyVariationalDistribution(inducing_points.size(0))
    variational_strategy = VariationalStrategy(
        None, # Placeholder, we will re-assign the strategy in __init__ logic if needed, 
              # but SparseVariational usually takes strategy in __init__. 
              # Let's use the standard pattern:
        inducing_points,
        variational_distribution,
        learn_inducing_locations=True
    )
    
    # Re-initialize properly
    model = SparseGPModel.__new__(SparseGPModel)
    gpytorch.models.AbstractGP.__init__(model)
    
    model.variational_strategy = VariationalStrategy(
        model,
        inducing_points,
        CholeskyVariationalDistribution(inducing_points.size(0)),
        learn_inducing_locations=True
    )
    
    model.mean_module = ConstantMean()
    model.covar_module = ScaleKernel(RBFKernel())

    likelihood = GaussianLikelihood()

    model.train()
    likelihood.train()

    optimizer = torch.optim.Adam([
        {'params': model.parameters()},
        {'params': likelihood.parameters()}
    ], lr=0.01)

    mll = VariationalELBO(likelihood, model, num_data=train_y.size(0))

    logger.info(f"Training Sparse GP with {n_inducing} inducing points for {n_epochs} epochs...")
    
    for i in range(n_epochs):
        optimizer.zero_grad()
        output = model(train_X)
        loss = -mll(output, train_y)
        loss.backward()
        if i % 20 == 0:
            logger.info(f"Iter {i}, Loss: {loss.item():.4f}")
        optimizer.step()

    return model, likelihood

def save_model(model, likelihood, path: str):
    """
    Saves the model and likelihood states to a .pt file.
    """
    torch.save({
        'model_state_dict': model.state_dict(),
        'likelihood_state_dict': likelihood.state_dict(),
        'inducing_points': model.variational_strategy.inducing_points,
        'mean_module': model.mean_module.state_dict(),
        'covar_module': model.covar_module.state_dict()
    }, path)
    logger.info(f"Model saved to {path}")

def main(seed: int = 42):
    """
    Main entry point for T015.
    1. Verifies input artifacts (T006b3 outputs).
    2. Trains the Sparse GP model.
    3. Saves the output artifact.
    """
    # Verify inputs exist before proceeding
    try:
        # We call load_processed_data with 'test' just to trigger the existence checks
        # as per task requirement, though we train on 'train'.
        load_processed_data("test") 
        if not Path("data/processed/features_train_20pca.csv").exists():
             raise FileNotFoundError("Training data missing for training phase.")
    except FileNotFoundError as e:
        logger.error(f"Pre-requisite check failed: {e}")
        sys.exit(1)

    input_dim = 20
    model, likelihood = train_sparse_gp(input_dim, seed)
    
    out_dir = Path("results/models")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sparse_gp_model.pt"
    
    save_model(model, likelihood, str(out_path))
    logger.info("Sparse GP training complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()