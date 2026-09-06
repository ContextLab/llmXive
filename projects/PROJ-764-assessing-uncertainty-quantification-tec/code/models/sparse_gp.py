import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Ensure parent directory is in path for imports if running as script
# But since we are inside code/models, we assume standard project structure
# where 'code' is the root or PYTHONPATH is set.
# We rely on the API surface provided:
# from models.sparse_gp import ...

# Import configuration and data loading helpers if they exist in the project
# Since the API surface lists load_config and load_processed_data, we assume they are defined
# in this file or imported. Given the "extend" constraint and the provided API surface,
# we will implement the missing logic here.

import torch
import gpytorch
from gpytorch.mlls import ExactMarginalLogLikelihood
from gpytorch.likelihoods import GaussianLikelihood
from gpytorch.models import ExactGP
from gpytorch.kernels import ScaleKernel, RBFKernel
from gpytorch.means import ConstantMean
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np
import joblib

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SparseGPModel(ExactGP):
    """
    A simple Exact GP model using RBF kernel and Constant mean.
    Designed to run on CPU.
    """
    def __init__(self, train_x, train_y, likelihood):
        super(SparseGPModel, self).__init__(train_x, train_y, likelihood)
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(RBFKernel())
        self.n_features = train_x.shape[1]

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

def load_config():
    """
    Loads configuration from code/config.yaml.
    Returns a dict with config values.
    """
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults.")
        return {"seed": 42, "num_inducing": 100}
    
    with open(config_path, 'r') as f:
        import yaml
        return yaml.safe_load(f)

def load_processed_data():
    """
    Loads the pre-processed test data and PCA transformer.
    Returns X_test, y_test, pca_transformer.
    """
    # Paths as defined in T006b3
    features_path = Path(__file__).parent.parent.parent / "data" / "processed" / "features_test_20pca.csv"
    pca_path = Path(__file__).parent.parent.parent / "data" / "processed" / "pca_transformer.pkl"

    if not features_path.exists():
        raise FileNotFoundError(f"Required file not found: {features_path}. "
                                "Please ensure T006b3 (PCA Fit/Transform) has been completed successfully.")
    
    if not pca_path.exists():
        raise FileNotFoundError(f"Required file not found: {pca_path}. "
                                "Please ensure T006b3 (PCA Fit/Transform) has been completed successfully.")

    logger.info(f"Loading features from {features_path}")
    df = pd.read_csv(features_path)
    
    # Assuming the target column is 'formation_energy' or similar, based on context
    # We need to identify the target column. The spec mentions 'formation energy'.
    # Let's assume the column name is 'formation_energy' or 'target'.
    # If not present, we might need to infer.
    target_col = None
    for col in ['formation_energy', 'target', 'y']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise ValueError("Could not identify target column in features file.")

    X = df.drop(columns=[target_col]).values
    y = df[target_col].values

    logger.info(f"Loading PCA transformer from {pca_path}")
    pca = joblib.load(pca_path)

    return X, y, pca

def train_sparse_gp(X_train, y_train, num_inducing_points=100, seed=42):
    """
    Trains a Sparse GP model on the provided data.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Convert to tensors
    train_x = torch.tensor(X_train, dtype=torch.float32)
    train_y = torch.tensor(y_train, dtype=torch.float32)

    likelihood = GaussianLikelihood()
    model = SparseGPModel(train_x, train_y, likelihood)

    model.train()
    likelihood.train()

    optimizer = torch.optim.Adam([
        {'params': model.parameters()},
    ], lr=0.1)

    mll = ExactMarginalLogLikelihood(likelihood, model)

    training_iter = 50
    for i in range(training_iter):
        optimizer.zero_grad()
        output = model(train_x)
        loss = -mll(output, train_y)
        loss.backward()
        if (i + 1) % 10 == 0:
            logger.info(f"Iter {i+1}/{training_iter} - Loss: {loss.item():.4f}")
        optimizer.step()

    model.eval()
    likelihood.eval()

    return model, likelihood

def save_model(model, likelihood, output_path):
    """
    Saves the trained GP model and likelihood.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    state_dict = {
        'model': model.state_dict(),
        'likelihood': likelihood.state_dict()
    }
    torch.save(state_dict, output_path)
    logger.info(f"Model saved to {output_path}")

def main():
    """
    Main entry point for T015a (Verification) and subsequent fitting (T015b).
    
    T015a Requirement:
    - Check existence of data/processed/features_test_20pca.csv and data/processed/pca_transformer.pkl
    - Fail loudly if missing.
    - Do not re-fit PCA.
    
    This function performs the verification and then proceeds to load data 
    (assuming T015b fitting logic is also part of this flow or called subsequently).
    For this task, we focus on the verification and preparation.
    """
    logger.info("Starting Sparse GP Verification (T015a)...")

    # 1. Verification: Check existence of required files
    features_path = Path(__file__).parent.parent.parent / "data" / "processed" / "features_test_20pca.csv"
    pca_path = Path(__file__).parent.parent.parent / "data" / "processed" / "pca_transformer.pkl"

    if not features_path.exists():
        logger.error(f"CRITICAL: Required file not found: {features_path}")
        logger.error("Task T006b3 (PCA Fit/Transform) must be completed before running this task.")
        sys.exit(1)

    if not pca_path.exists():
        logger.error(f"CRITICAL: Required file not found: {pca_path}")
        logger.error("Task T006b3 (PCA Fit/Transform) must be completed before running this task.")
        sys.exit(1)

    logger.info("Verification passed: Required data files exist.")

    # 2. Load data (Preparation for T015b)
    # We load the data to ensure it's valid, but we don't train yet in this specific 
    # verification step unless we combine them. The task T015a is verification.
    # However, to make the script useful and runnable as a unit, we will load the data
    # and print a success message confirming readiness.
    try:
        X, y, pca = load_processed_data()
        logger.info(f"Successfully loaded {X.shape[0]} samples with {X.shape[1]} features.")
        logger.info(f"PCA transformer loaded. Components: {pca.n_components_}")
        
        # Optional: Verify PCA transform consistency if we had training data
        # But for T015a, existence check is the primary goal.
        
        logger.info("T015a Verification: PASSED. Ready for T015b (Fitting).")
        
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        sys.exit(1)

    # If the task implies running the full flow (T015a + T015b + T015c) in one go
    # based on the "Implement ... (Verification)" description, we might need to 
    # actually fit the model if the user intends to run the full pipeline step.
    # Given the task description says "Implement ... (Verification)", strictly speaking,
    # it's just the check. But to be helpful and "complete" as an implementer, 
    # we can check if a flag is passed to train.
    # However, T015b is a separate task. So we stop here for T015a.
    
    # To ensure the script is "runnable" and produces an artifact if requested by the pipeline
    # (though T015a doesn't produce an artifact, T015b does), we just exit successfully.
    sys.exit(0)

if __name__ == "__main__":
    main()