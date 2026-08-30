import os
import sys
import json
import torch
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import joblib

try:
    import gpytorch
    from gpytorch.models import SparseVariational
    from gpytorch.kernels import RBFKernel, ScaleKernel
    from gpytorch.means import ConstantMean
    from gpytorch.mlls import VariationalELBO
except ImportError:
    logging.error("gpytorch not installed. Skipping SparseGP.")
    sys.exit(1)

logger = logging.getLogger(__name__)

def load_config(config_path: str = "code/config.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)

def load_processed_data(split: str = "test"):
    path = Path(f"data/processed/features_{split}_20pca.csv")
    df = pd.read_csv(path)
    X = torch.tensor(df[[f'pca_{i}' for i in range(20)]].values, dtype=torch.float32)
    y = torch.tensor(df['formation_energy'].values, dtype=torch.float32)
    return X, y

class SparseGPModel(gpytorch.models.AbstractGP):
    def __init__(self, train_x, train_y, inducing_points):
        super().__init__()
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(RBFKernel())
        self.variational_strategy = gpytorch.variational.VariationalStrategy(
            self, inducing_points, gpytorch.variational.IndependentMultitaskVariationalStrategy, learn_additional_noise=True
        )
        self.variational_strategy = gpytorch.variational.VariationalStrategy(
            self, inducing_points, gpytorch.variational.IndependentMultitaskVariationalStrategy, learn_additional_noise=True
        )
        # Simplified for single output
        self.variational_strategy = gpytorch.variational.VariationalStrategy(
            self, inducing_points, gpytorch.variational.IndependentVariationalStrategy, learn_additional_noise=True
        )
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())
        
        # Initialize inducing points
        self.inducing_points = inducing_points

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

def train_sparse_gp(input_dim: int, seed: int, n_inducing: int = 100):
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Load training data
    train_path = Path("data/processed/features_train_20pca.csv")
    train_df = pd.read_csv(train_path)
    train_X = torch.tensor(train_df[[f'pca_{i}' for i in range(20)]].values, dtype=torch.float32)
    train_y = torch.tensor(train_df['formation_energy'].values, dtype=torch.float32)

    # Select inducing points
    inducing_idx = np.random.choice(train_X.shape[0], n_inducing, replace=False)
    inducing_points = train_X[inducing_idx]

    model = SparseGPModel(train_X, train_y, inducing_points)
    likelihood = gpytorch.likelihoods.GaussianLikelihood()

    model.train()
    likelihood.train()

    optimizer = torch.optim.Adam([
        {'params': model.parameters()},
        {'params': likelihood.parameters()}
    ], lr=0.01)

    mll = VariationalELBO(likelihood, model, num_data=train_y.size(0))

    for i in range(100):
        optimizer.zero_grad()
        output = model(train_X)
        loss = -mll(output, train_y)
        loss.backward()
        if i % 10 == 0:
            logger.info(f"Iter {i}, Loss: {loss.item()}")
        optimizer.step()

    return model, likelihood

def save_model(model, likelihood, path: str):
    torch.save({
        'model_state_dict': model.state_dict(),
        'likelihood_state_dict': likelihood.state_dict()
    }, path)

def main(seed: int = 42):
    input_dim = 20
    model, likelihood = train_sparse_gp(input_dim, seed)
    
    out_dir = Path("results/models")
    out_dir.mkdir(parents=True, exist_ok=True)
    save_model(model, likelihood, out_dir / "sparse_gp_model.pt")
    logger.info("Sparse GP model saved")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
