from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
import numpy as np
from numpy.typing import ArrayLike
import json
import os
import logging

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DatasetInstance:
    """
    Container for a single simulated dataset instance.
    
    Attributes:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        beta_true: True coefficients used to generate y (n_features,)
        metadata: Dictionary containing generation parameters and diagnostics (N, rho, seed, vif_max, etc.)
    """
    X: np.ndarray
    y: np.ndarray
    beta_true: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary suitable for JSON serialization."""
        return {
            "X": self.X.tolist(),
            "y": self.y.tolist(),
            "beta_true": self.beta_true.tolist(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetInstance':
        """Reconstruct a DatasetInstance from a dictionary."""
        return cls(
            X=np.array(data["X"]),
            y=np.array(data["y"]),
            beta_true=np.array(data["beta_true"]),
            metadata=data.get("metadata", {})
        )


def calculate_vif(X: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Calculate Variance Inflation Factors (VIF) for each predictor.
    
    Args:
        X: Feature matrix (n_samples, n_features). Should NOT include intercept.
    
    Returns:
        Tuple of (vif_array, max_vif)
    """
    n_features = X.shape[1]
    vifs = np.zeros(n_features)
    
    # Add intercept column for the regression
    X_with_intercept = np.column_stack((np.ones(X.shape[0]), X))
    
    for i in range(n_features):
        # Predictor to test
        y_test = X_with_intercept[:, i+1] # Skip intercept column
        # Predictors to regress against (all other columns including intercept)
        X_test = np.delete(X_with_intercept, i+1, axis=1)
        
        # Simple OLS: beta = (X'X)^-1 X'y
        try:
            # Using least squares to avoid matrix inversion issues directly
            coeffs, _, _, _ = np.linalg.lstsq(X_test, y_test, rcond=None)
            y_pred = X_test @ coeffs
            residuals = y_test - y_pred
            
            # R-squared
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_test - np.mean(y_test))**2)
            
            if ss_tot == 0:
                vifs[i] = np.inf
            else:
                r_squared = 1 - (ss_res / ss_tot)
                if r_squared >= 1.0:
                    vifs[i] = np.inf
                else:
                    vifs[i] = 1.0 / (1.0 - r_squared)
        except np.linalg.LinAlgError:
            vifs[i] = np.inf
    
    return vifs, np.max(vifs)


def generate_dataset(
    N: int,
    n_features: int,
    rho: float,
    beta_true: np.ndarray,
    sigma: float,
    seed: Optional[int] = None
) -> DatasetInstance:
    """
    Generate a synthetic dataset with controlled correlation structure.
    
    Args:
        N: Sample size
        n_features: Number of predictors
        rho: Target correlation between predictors (assumes equicorrelation structure)
        beta_true: True coefficients
        sigma: Noise standard deviation
        seed: Random seed for reproducibility
    
    Returns:
        DatasetInstance containing X, y, beta_true, and metadata
    """
    if seed is not None:
        np.random.seed(seed)
    
    # 1. Generate Correlation Matrix (Equicorrelation)
    # Ensure positive semi-definite
    # Condition for PSD: rho >= -1/(n_features-1) and rho <= 1
    min_rho = -1.0 / (n_features - 1) if n_features > 1 else -1.0
    if rho < min_rho or rho > 1.0:
        raise ValueError(f"rho={rho} is outside the valid range [{min_rho}, 1.0] for {n_features} features.")
    
    Sigma = np.full((n_features, n_features), rho)
    np.fill_diagonal(Sigma, 1.0)
    
    # Check PSD explicitly
    eigvals = np.linalg.eigvalsh(Sigma)
    if np.min(eigvals) < -1e-10:
        raise ValueError(f"Generated correlation matrix is not positive semi-definite (min eigval: {np.min(eigvals)})")
    
    # 2. Generate X using Cholesky decomposition
    try:
        L = np.linalg.cholesky(Sigma)
    except np.linalg.LinAlgError:
        # Fallback for numerical instability: adjust rho slightly if needed
        logger.warning("Cholesky failed, attempting to adjust rho slightly for numerical stability.")
        Sigma_adjusted = Sigma * 0.999 + np.eye(n_features) * 0.001
        L = np.linalg.cholesky(Sigma_adjusted)
    
    Z = np.random.normal(0, 1, size=(N, n_features))
    X = Z @ L.T
    
    # 3. Generate y
    noise = np.random.normal(0, sigma, size=N)
    y = X @ beta_true + noise
    
    # 4. Calculate VIF
    vifs, max_vif = calculate_vif(X)
    
    metadata = {
        "N": N,
        "n_features": n_features,
        "rho": rho,
        "sigma": sigma,
        "seed": seed,
        "vif_max": float(max_vif),
        "vif_list": vifs.tolist(),
        "generated_at": str(np.datetime64('now'))
    }
    
    return DatasetInstance(X=X, y=y, beta_true=beta_true, metadata=metadata)


def save_dataset_instance(
    instance: DatasetInstance,
    output_dir: str,
    filename_prefix: str = "dataset"
) -> str:
    """
    Save a DatasetInstance to disk as a JSON file.
    
    Args:
        instance: The DatasetInstance to save.
        output_dir: Directory to save the file (e.g., 'data/simulated').
        filename_prefix: Prefix for the filename.
    
    Returns:
        The absolute path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename based on seed and N if available, otherwise timestamp
    seed = instance.metadata.get("seed", "none")
    n = instance.metadata.get("N", "unknown")
    timestamp = instance.metadata.get("generated_at", "now").replace(":", "-").replace(" ", "_")
    
    filename = f"{filename_prefix}_N{n}_seed{seed}.json"
    filepath = os.path.join(output_dir, filename)
    
    data = instance.to_dict()
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved dataset instance to {filepath}")
    return filepath


def load_dataset_instance(filepath: str) -> DatasetInstance:
    """
    Load a DatasetInstance from a JSON file.
    
    Args:
        filepath: Path to the JSON file.
    
    Returns:
        DatasetInstance object.
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    return DatasetInstance.from_dict(data)