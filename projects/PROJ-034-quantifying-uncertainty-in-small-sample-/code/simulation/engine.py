from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from numpy.typing import ArrayLike
import json
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatasetInstance:
    """
    Container for a generated synthetic dataset and its metadata.
    """
    X: np.ndarray
    y: np.ndarray
    beta_true: np.ndarray
    vif_scores: Dict[str, float] = field(default_factory=dict)
    config_params: Dict[str, Any] = field(default_factory=dict)
    seed: int = 0

def calculate_vif(X: np.ndarray) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors for each predictor in X.
    
    Args:
        X: Design matrix (n_samples, n_features)
        
    Returns:
        Dictionary mapping feature index to VIF score.
    """
    n_samples, n_features = X.shape
    if n_samples <= n_features:
        return {f"X{i}": float('inf') for i in range(n_features)}
    
    vif_scores = {}
    # Add intercept for OLS calculation if needed, but VIF is usually on centered X
    # We compute VIF for each column j by regressing X_j on all other columns
    for i in range(n_features):
        y_var = X[:, i]
        X_others = np.delete(X, i, axis=1)
        
        # OLS: beta = (X'X)^-1 X'y
        # Check rank
        if np.linalg.matrix_rank(X_others) < X_others.shape[1]:
            vif_scores[f"X{i}"] = float('inf')
            continue
        
        try:
            # Solve least squares
            _, residuals, rank, s = np.linalg.lstsq(X_others, y_var, rcond=None)
            
            # R-squared calculation
            # SSR = sum((y_hat - y_mean)^2)
            # SST = sum((y - y_mean)^2)
            # R2 = 1 - SSR/SST
            
            y_hat = X_others @ residuals
            y_mean = np.mean(y_var)
            
            ss_res = np.sum((y_var - y_hat) ** 2)
            ss_tot = np.sum((y_var - y_mean) ** 2)
            
            if ss_tot == 0:
                r_squared = 1.0
            else:
                r_squared = 1 - (ss_res / ss_tot)
            
            if r_squared >= 1.0:
                vif_scores[f"X{i}"] = float('inf')
            else:
                vif_scores[f"X{i}"] = 1.0 / (1.0 - r_squared)
        except np.linalg.LinAlgError:
            vif_scores[f"X{i}"] = float('inf')
    
    return vif_scores

def check_positive_semidefinite(matrix: np.ndarray, tol: float = 1e-8) -> bool:
    """
    Check if a matrix is positive semi-definite by checking eigenvalues.
    """
    eigenvalues = np.linalg.eigvalsh(matrix)
    return np.all(eigenvalues >= -tol)

def generate_correlation_matrix(n_features: int, rho: float, seed: int) -> np.ndarray:
    """
    Generate a correlation matrix with a specific off-diagonal correlation rho.
    
    Args:
        n_features: Number of features (p)
        rho: Target correlation between any pair of features
        seed: Random seed for reproducibility
        
    Returns:
        A valid correlation matrix.
        
    Raises:
        ValueError: If rho is out of valid range for the given dimension.
    """
    if not (-1.0 <= rho <= 1.0):
        raise ValueError("rho must be between -1 and 1")
    
    # For an equicorrelation matrix to be positive semi-definite:
    # rho >= -1/(n_features - 1)
    min_rho = -1.0 / (n_features - 1) if n_features > 1 else -1.0
    if rho < min_rho:
        raise ValueError(f"rho={rho} is too low for n_features={n_features}. Minimum allowed: {min_rho}")

    # Construct equicorrelation matrix
    R = np.full((n_features, n_features), rho)
    np.fill_diagonal(R, 1.0)
    
    if not check_positive_semidefinite(R):
        # Numerical stability adjustment if needed
        min_eig = np.min(np.linalg.eigvalsh(R))
        if min_eig < -1e-8:
            raise ValueError(f"Generated matrix is not positive semi-definite. Min eigenvalue: {min_eig}")
    
    return R

def generate_synthetic_data(config: 'SimulationConfig', seed: int) -> DatasetInstance:
    """
    Generate a synthetic dataset based on the configuration.
    
    Args:
        config: SimulationConfig object defining parameters.
        seed: Random seed for reproducibility.
        
    Returns:
        DatasetInstance containing X, y, beta_true, and metadata.
    """
    np.random.seed(seed)
    
    n = config.N
    p = len(config.predictors) if isinstance(config.predictors, list) else config.predictors
    
    # Generate correlation matrix
    try:
        R = generate_correlation_matrix(p, config.rho, seed)
    except ValueError as e:
        logger.error(f"Correlation matrix generation failed: {e}")
        raise
    
    # Cholesky decomposition to generate correlated X
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        # Fallback: add small jitter to diagonal if not PSD due to precision
        R_adj = R + np.eye(p) * 1e-6
        try:
            L = np.linalg.cholesky(R_adj)
        except np.linalg.LinAlgError:
            raise ValueError("Failed to generate valid correlation matrix even with jitter.")
    
    # Generate standard normal X
    Z = np.random.randn(n, p)
    X = Z @ L.T
    
    # Normalize X to mean 0, std 1 (optional but good for stability)
    # X = (X - X.mean(axis=0)) / X.std(axis=0)
    
    # Generate true coefficients
    # If config.coefficients is provided, use it; else generate random
    if isinstance(config.coefficients, list):
        beta_true = np.array(config.coefficients)
    else:
        # Default: generate random coefficients
        beta_true = np.random.randn(p)
    
    # Generate noise
    noise = np.random.randn(n) * config.noise_std
    
    # Generate y
    # Ensure beta_true is 1D and compatible
    if beta_true.ndim == 0:
        beta_true = np.full(p, beta_true)
        
    y = X @ beta_true + noise
    
    # Calculate VIF
    vif_scores = calculate_vif(X)
    
    # Check for high VIF
    max_vif = max(vif_scores.values()) if vif_scores else 0
    if max_vif > 10:
        logger.warning(f"High multicollinearity detected (Max VIF: {max_vif:.2f})")
    
    return DatasetInstance(
        X=X,
        y=y,
        beta_true=beta_true,
        vif_scores=vif_scores,
        config_params={
            "N": n,
            "rho": config.rho,
            "noise_std": config.noise_std,
            "predictors": config.predictors
        },
        seed=seed
    )

def generate_dataset(config: 'SimulationConfig', seed: int) -> DatasetInstance:
    """
    Wrapper to generate a dataset, ensuring PSD checks and regeneration logic.
    
    Args:
        config: SimulationConfig.
        seed: Random seed.
        
    Returns:
        DatasetInstance.
    """
    # T015: Auto-regeneration logic for invalid matrices
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            instance = generate_synthetic_data(config, seed + attempt)
            # Verify PSD of correlation matrix used (re-construct to check)
            p = len(config.predictors) if isinstance(config.predictors, list) else config.predictors
            R = generate_correlation_matrix(p, config.rho, seed + attempt)
            if check_positive_semidefinite(R):
                return instance
            else:
                logger.warning(f"Attempt {attempt}: Generated matrix not PSD. Retrying...")
        except (ValueError, np.linalg.LinAlgError) as e:
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying...")
    
    raise RuntimeError(f"Failed to generate a valid dataset after {max_attempts} attempts.")

def save_dataset_instance(instance: DatasetInstance, output_path: str) -> None:
    """
    Save a DatasetInstance to a JSON file.
    
    Explicitly serializes X, y, and beta_true as lists to satisfy FR-001.
    
    Args:
        instance: The DatasetInstance to save.
        output_path: Path to the output JSON file.
    """
    if not output_path.endswith('.json'):
        raise ValueError("Output path must be a .json file")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    data = {
        "X": instance.X.tolist(),
        "y": instance.y.tolist(),
        "beta_true": instance.beta_true.tolist(),
        "vif_scores": instance.vif_scores,
        "config_params": instance.config_params,
        "seed": instance.seed,
        "shape": {
            "n_samples": int(instance.X.shape[0]),
            "n_features": int(instance.X.shape[1])
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Dataset instance saved to {output_path}")

def load_dataset_instance(input_path: str) -> DatasetInstance:
    """
    Load a DatasetInstance from a JSON file.
    
    Args:
        input_path: Path to the input JSON file.
        
    Returns:
        DatasetInstance.
    """
    if not input_path.endswith('.json'):
        raise ValueError("Input path must be a .json file")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    X = np.array(data["X"])
    y = np.array(data["y"])
    beta_true = np.array(data["beta_true"])
    
    return DatasetInstance(
        X=X,
        y=y,
        beta_true=beta_true,
        vif_scores=data.get("vif_scores", {}),
        config_params=data.get("config_params", {}),
        seed=data.get("seed", 0)
    )

# Import SimulationConfig here to avoid circular import if defined in config.py
# We use a string type hint in the function signatures above to defer resolution
# but we need the actual class if we want to instantiate it here or use isinstance checks.
# Since the prompt says "extend code/simulation/engine.py", we assume config.py is available.
# However, to be safe and avoid import errors if this file is run standalone without config,
# we keep the type hints as strings or import inside functions if strictly necessary.
# For now, we rely on the fact that 'from simulation.config import SimulationConfig' exists in the project.

try:
    from simulation.config import SimulationConfig
except ImportError:
    # Fallback if imported in a context where config is not yet available
    SimulationConfig = None