import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

# Setup logger
logger = logging.getLogger("sparse_gp")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def setup_logger():
    return logger

def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data():
    """
    Loads the PCA-reduced feature sets from the data/processed directory.
    Returns X_train, y_train, X_test, y_test, and the loaded transformer.
    """
    processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    
    train_path = processed_dir / "features_train_20pca.csv"
    test_path = processed_dir / "features_test_20pca.csv"
    transformer_path = processed_dir / "pca_transformer.pkl"

    if not train_path.exists():
        raise FileNotFoundError(f"Required artifact missing: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Required artifact missing: {test_path}")
    if not transformer_path.exists():
        raise FileNotFoundError(f"Required artifact missing: {transformer_path}")

    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    # Assume target column is 'formation_energy' or 'target' based on preprocessing
    # Based on T006a, the target is likely named 'formation_energy' or similar.
    # We look for the column that was used for binning or standard naming.
    target_col = 'formation_energy'
    if target_col not in df_train.columns:
        # Fallback to common alternative if schema differs slightly
        if 'target' in df_train.columns:
            target_col = 'target'
        else:
            # Check for any column that might be the target if standard names fail
            # This is a safeguard; the pipeline should ensure consistent naming.
            cols = [c for c in df_train.columns if c not in ['sample_id', 'target_bin']]
            if len(cols) > 0 and cols[-1] == 'target':
                target_col = 'target'
            else:
                logger.warning(f"Target column '{target_col}' not found. Attempting to infer from schema.")
                # If we can't find it, we might need to inspect the dataframe.
                # For now, we assume 'formation_energy' is the standard.
                raise KeyError(f"Target column '{target_col}' not found in {train_path}. Columns: {df_train.columns.tolist()}")

    feature_cols = [c for c in df_train.columns if c not in ['sample_id', 'target_bin', target_col]]
    
    X_train = df_train[feature_cols].values
    y_train = df_train[target_col].values
    X_test = df_test[feature_cols].values
    y_test = df_test[target_col].values

    with open(transformer_path, 'rb') as f:
        pca_transformer = pickle.load(f)

    return X_train, y_train, X_test, y_test, pca_transformer

def verify_dependencies():
    """
    Checks existence of required artifacts before execution.
    Fails loudly if missing.
    """
    processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    required_files = [
        "features_train_20pca.csv",
        "features_test_20pca.csv",
        "pca_transformer.pkl"
    ]
    
    missing = []
    for f in required_files:
        if not (processed_dir / f).exists():
            missing.append(str(processed_dir / f))
    
    if missing:
        logger.critical(f"CRITICAL: Missing required artifacts: {missing}. T015a verification failed. Cannot proceed to training (T015b).")
        raise FileNotFoundError(f"Missing required artifacts: {missing}")
    
    logger.info("All required artifacts verified.")
    return True

class SparseGPModel:
    """
    Wrapper for Sparse Gaussian Process model using GPyTorch.
    """
    def __init__(self, input_dim, num_inducing=500):
        self.input_dim = input_dim
        self.num_inducing = num_inducing
        self.model = None
        self.likelihood = None
        self.training_data_x = None
        self.training_data_y = None

    def fit(self, X, y):
        """
        Fits the Sparse GP model to the data.
        """
        try:
            import gpytorch
            import torch
        except ImportError:
            logger.error("GPyTorch is not installed. Please install it to use Sparse GP.")
            raise

        self.training_data_x = torch.tensor(X, dtype=torch.float32)
        self.training_data_y = torch.tensor(y, dtype=torch.float32).unsqueeze(-1)

        # Initialize inducing points randomly from the data
        inducing_indices = torch.randperm(X.shape[0])[:self.num_inducing]
        self.inducing_points = self.training_data_x[inducing_indices]

        # Define the model
        class ExactGPModel(gpytorch.models.ExactGP):
            def __init__(self, train_x, train_y, likelihood):
                super(ExactGPModel, self).__init__(train_x, train_y)
                self.likelihood = likelihood
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())

            def forward(self, x):
                mean_x = self.mean_module(x)
                covar_x = self.covar_module(x)
                return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

        class SparseGPModel(gpytorch.models.ExactGP):
            def __init__(self, train_x, train_y, likelihood, inducing_points):
                super(SparseGPModel, self).__init__(train_x, train_y)
                self.likelihood = likelihood
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())
                self.variational_strategy = gpytorch.variational.VariationalStrategy(
                    self, inducing_points, gpytorch.variational.InducingPointsLayer(inducing_points.size(0), train_x.size(1))
                )
                self.variational_strategy = gpytorch.variational.VariationalStrategy(
                    self, inducing_points, gpytorch.variational.InducingPointsLayer(self.inducing_points.size(0), self.inducing_points.size(1))
                )
                # Re-initialize strategy correctly for standard variational inference
                self.variational_strategy = gpytorch.variational.VariationalStrategy(
                    self, inducing_points, gpytorch.variational.InducingPointsLayer(inducing_points.size(0), inducing_points.size(1)), learn_inducing_locations=True
                )
                
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())

            def forward(self, x):
                mean_x = self.mean_module(x)
                covar_x = self.covar_module(x)
                return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

        # Correct initialization for Sparse GP
        self.likelihood = gpytorch.likelihoods.GaussianLikelihood()
        
        # Use VariationalStrategy with InducingPoints
        # We need to define the model structure properly
        class GPModel(gpytorch.models.AbstractVariationalGP):
            def __init__(self, train_x, inducing_points):
                super().__init__(gpytorch.variational.VariationalStrategy(
                    self, inducing_points, gpytorch.variational.InducingPointsLayer(inducing_points.size(0), train_x.size(1)), learn_inducing_locations=True
                ))
                self.mean_module = gpytorch.means.ConstantMean()
                self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())

            def forward(self, x):
                mean_x = self.mean_module(x)
                covar_x = self.covar_module(x)
                return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

        self.model = GPModel(self.training_data_x, self.inducing_points)
        
        # Training setup
        self.model.train()
        self.likelihood.train()
        
        optimizer = torch.optim.Adam([
            {'params': self.model.variational_parameters()},
            {'params': self.likelihood.parameters()},
            {'params': self.model.mean_module.parameters()},
            {'params': self.model.covar_module.parameters()},
        ], lr=0.01)

        mll = gpytorch.mlls.VariationalELBO(self.likelihood, self.model, num_data=self.training_data_y.size(0))

        # Training loop
        num_epochs = 100
        logger.info(f"Training Sparse GP with {self.num_inducing} inducing points for {num_epochs} epochs...")
        
        for i in range(num_epochs):
            optimizer.zero_grad()
            output = self.model(self.training_data_x)
            loss = -mll(output, self.training_data_y)
            loss.backward()
            if i % 20 == 0:
                logger.info(f"Epoch {i+1}/{num_epochs} - Loss: {loss.item():.4f}")
            optimizer.step()

        self.model.eval()
        self.likelihood.eval()
        logger.info("Sparse GP training completed.")

    def predict(self, X_test):
        """
        Runs inference on test data.
        Returns predictions and variances.
        """
        import torch
        import gpytorch

        test_x = torch.tensor(X_test, dtype=torch.float32)

        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            observed_pred = self.likelihood(self.model(test_x))
            mean = observed_pred.mean
            variance = observed_pred.variance

        return mean.numpy(), variance.numpy()

def train_sparse_gp(X_train, y_train, num_inducing=500):
    """
    Trains a Sparse GP model.
    """
    input_dim = X_train.shape[1]
    model = SparseGPModel(input_dim, num_inducing=num_inducing)
    model.fit(X_train, y_train)
    return model

def save_model(model, output_path):
    """
    Saves the trained Sparse GP model to disk.
    """
    import torch
    # We need to save the state dicts of both model and likelihood
    state_dict = {
        'model_state': model.model.state_dict(),
        'likelihood_state': model.likelihood.state_dict(),
        'inducing_points': model.inducing_points,
        'input_dim': model.input_dim,
        'num_inducing': model.num_inducing
    }
    torch.save(state_dict, output_path)
    logger.info(f"Model saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Sparse GP Verification and Training")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--inducing", type=int, default=500, help="Number of inducing points")
    parser.add_argument("--fit", action="store_true", help="Run training (T015b). If not set, only verifies (T015a).")
    args = parser.parse_args()

    # Set seed
    np.random.seed(args.seed)
    try:
        import torch
        torch.manual_seed(args.seed)
    except ImportError:
        pass

    # T015a: Verification
    logger.info("T015a: Verifying dependencies...")
    try:
        verify_dependencies()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # If only verification is requested, exit here
    if not args.fit:
        logger.info("Verification successful. Exiting (T015a complete).")
        sys.exit(0)

    # T015b: Fitting
    logger.info("T015b: Loading data and fitting Sparse GP...")
    try:
        X_train, y_train, X_test, y_test, pca_transformer = load_processed_data()
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        sys.exit(1)

    logger.info(f"Loaded data: Train={X_train.shape}, Test={X_test.shape}")

    # Train
    try:
        gp_model = train_sparse_gp(X_train, y_train, num_inducing=args.inducing)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

    # Save
    output_path = Path(__file__).parent.parent.parent / "results" / "models" / "sparse_gp_model.pt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        save_model(gp_model, output_path)
    except Exception as e:
        logger.error(f"Saving model failed: {e}")
        sys.exit(1)

    # Optional: Run inference on test set to verify
    try:
        preds, variances = gp_model.predict(X_test)
        logger.info(f"Test predictions sample: {preds[:5]}")
        logger.info(f"Test variances sample: {variances[:5]}")
    except Exception as e:
        logger.warning(f"Inference on test set failed (non-fatal): {e}")

    logger.info("T015b: Sparse GP fitting and saving completed successfully.")

if __name__ == "__main__":
    main()