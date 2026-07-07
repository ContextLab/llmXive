import os
import sys
import json
import torch
import numpy as np
import pandas as pd
import yaml
import time
import logging

# GPyTorch might not be installed in all environments, but we implement the structure
# If GPyTorch is missing, this will fail loudly as per requirements.
try:
    import gpytorch
    from gpytorch.models import SparseVariational
    from gpytorch.kernels import RBFKernel, ScaleKernel
    from gpytorch.means import ConstantMean
    from gpytorch.mlls import VariationalELBO
    from gpytorch.distributions import MultivariateNormal
except ImportError:
    # Placeholder class to allow import if gpytorch is missing, 
    # but execution will fail if the real model is needed.
    class SparseGPModel:
        pass
    class SparseVariational:
        pass
    raise ImportError("GPyTorch is required for sparse_gp.py. Please install it.")

from utils.timing_logger import timing_logger

CONFIG_PATH = "code/config.yaml"
PROCESSED_DATA_PATH = "data/processed/features_20pca.csv"
MODEL_OUTPUT_PATH = "results/models/sparse_gp_model.pt"
NUM_INDUCING = 100

os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)

logger = logging.getLogger(__name__)

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data():
    df = pd.read_csv(PROCESSED_DATA_PATH)
    feature_cols = [col for col in df.columns if col.startswith('feature_')]
    X = df[feature_cols].values
    y = df['target'].values
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

class SparseGPModel(gpytorch.models.SparseVariational):
    def __init__(self, train_x, num_inducing_points):
        inducing_points = train_x[:num_inducing_points]
        strategy = gpytorch.variational.CholeskyVariationalStrategy(
            self, inducing_points, num_inducing_points=num_inducing_points
        )
        super(SparseGPModel, self).__init__(strategy)
        
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = gpytorch.kernels.ScaleKernel(
            gpytorch.kernels.RBFKernel()
        )

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

def train_sparse_gp(X, y, config):
    # Ensure CUDA is off for CPU mode as per spec
    device = torch.device("cpu")
    X = X.to(device)
    y = y.to(device)

    model = SparseGPModel(X, NUM_INDUCING)
    likelihood = gpytorch.likelihoods.GaussianLikelihood()

    model.train()
    likelihood.train()

    optimizer = torch.optim.Adam([
        {'params': model.parameters()},
        {'params': likelihood.parameters()}
    ], lr=0.1)

    mll = VariationalELBO(likelihood, model, num_data=y.size(0))

    epochs = 50
    for i in range(epochs):
        optimizer.zero_grad()
        output = model(X)
        loss = -mll(output, y)
        loss.backward()
        if i % 10 == 0:
            logger.info(f"Epoch {i}: Loss {loss.item()}")
        optimizer.step()

    return model, likelihood

def save_model(model, likelihood, path):
    torch.save({
        'model_state_dict': model.state_dict(),
        'likelihood_state_dict': likelihood.state_dict()
    }, path)

def main():
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    X, y = load_processed_data()

    timing_logger.start("sparse_gp_training")
    model, likelihood = train_sparse_gp(X, y, config)
    timing_logger.stop("sparse_gp_training")

    save_model(model, likelihood, MODEL_OUTPUT_PATH)
    logger.info(f"Sparse GP model saved to {MODEL_OUTPUT_PATH}")

    timing_logger.start("sparse_gp_inference")
    model.eval()
    likelihood.eval()
    with torch.no_grad():
        pred = likelihood(model(X[:10]))
    timing_logger.stop("sparse_gp_inference")

    timing_logger.save_report()

if __name__ == "__main__":
    main()
