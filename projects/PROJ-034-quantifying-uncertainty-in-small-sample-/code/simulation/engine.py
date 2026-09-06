from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from numpy.typing import ArrayLike
import json
import os
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

@dataclass
class DatasetInstance:
    X: np.ndarray
    y: np.ndarray
    beta_true: np.ndarray
    vif_scores: Dict[str, float]
    seed: int
    regeneration_attempts: int = 0
    regeneration_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

def calculate_vif(X: np.ndarray) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each predictor.
    Returns a dictionary mapping feature index to VIF score.
    """
    n_samples, n_features = X.shape
    if n_features == 0:
        return {}
    
    # Add intercept column for VIF calculation if not present
    # VIF is typically calculated on standardized predictors
    # We use the correlation matrix approach
    
    try:
        # Calculate correlation matrix of predictors
        corr_matrix = np.corrcoef(X, rowvar=False)
        
        # Invert correlation matrix
        # Add small epsilon for numerical stability if needed
        corr_inv = np.linalg.inv(corr_matrix)
        
        vif_scores = {}
        for i in range(n_features):
            # VIF[i] = 1 / (1 - R_i^2) = diagonal element of inverse correlation matrix
            vif_scores[f"feature_{i}"] = float(corr_inv[i, i])
        
        return vif_scores
    except np.linalg.LinAlgError:
        logger.warning("Correlation matrix is singular, cannot calculate VIF")
        return {f"feature_{i}": np.inf for i in range(n_features)}

def check_positive_semidefinite(matrix: np.ndarray, tol: float = 1e-10) -> Tuple[bool, Optional[np.ndarray]]:
    """
    Check if a matrix is positive semi-definite.
    Returns (is_psd, eigenvalues) or (False, None) if not PSD.
    """
    try:
        eigenvalues = np.linalg.eigvalsh(matrix)
        is_psd = bool(np.all(eigenvalues >= -tol))
        return is_psd, eigenvalues
    except np.linalg.LinAlgError:
        return False, None

def generate_correlation_matrix(n_features: int, rho: float, seed: int) -> np.ndarray:
    """
    Generate a correlation matrix with a specific correlation structure.
    Uses an equicorrelation structure where off-diagonal elements are rho.
    """
    if not (-1/(n_features-1) <= rho <= 1):
        raise ValueError(f"rho must be in range [{-1/(n_features-1)}, 1] for {n_features} features")
    
    # Create equicorrelation matrix
    corr_matrix = np.full((n_features, n_features), rho)
    np.fill_diagonal(corr_matrix, 1.0)
    
    return corr_matrix

def generate_synthetic_data(config: 'SimulationConfig', seed: int) -> DatasetInstance:
    """
    Generate synthetic dataset with controlled correlation structure.
    Implements auto-regeneration logic for non-PSD matrices.
    """
    from simulation.config import SimulationConfig
    
    max_attempts = config.max_attempts if hasattr(config, 'max_attempts') else 10
    n_features = len(config.predictors) if hasattr(config, 'predictors') else config.n_predictors
    rho = config.rho
    
    rng = np.random.default_rng(seed)
    
    for attempt in range(max_attempts):
        try:
            # Generate correlation matrix
            corr_matrix = generate_correlation_matrix(n_features, rho, seed + attempt)
            
            # Check if positive semi-definite
            is_psd, eigenvalues = check_positive_semidefinite(corr_matrix)
            
            if not is_psd:
                logger.warning(f"Attempt {attempt + 1}: Generated correlation matrix is not PSD. "
                             f"Min eigenvalue: {np.min(eigenvalues) if eigenvalues is not None else 'N/A'}")
                if attempt < max_attempts - 1:
                    # Slightly adjust rho and retry
                    # This is a simple heuristic; in practice, one might use more sophisticated methods
                    rho = rho * 0.95 if rho > 0 else rho * 1.05
                    continue
                else:
                    raise ValueError(f"Failed to generate PSD matrix after {max_attempts} attempts")
            
            # Generate X using Cholesky decomposition
            L = np.linalg.cholesky(corr_matrix)
            Z = rng.standard_normal((config.n, n_features))
            X = Z @ L.T
            
            # Generate true coefficients
            beta_true = rng.standard_normal(n_features) * config.coefficient_scale
            
            # Generate noise
            noise = rng.standard_normal(config.n) * config.noise_std
            
            # Generate y
            y = X @ beta_true + noise
            
            # Calculate VIF
            vif_scores = calculate_vif(X)
            
            return DatasetInstance(
                X=X,
                y=y,
                beta_true=beta_true,
                vif_scores=vif_scores,
                seed=seed,
                regeneration_attempts=attempt,
                regeneration_reason="PSD check passed on first attempt" if attempt == 0 else f"Regenerated {attempt} times due to non-PSD matrix",
                metadata={
                    'n': config.n,
                    'n_features': n_features,
                    'rho': rho,
                    'seed': seed,
                    'vif_max': max(vif_scores.values()) if vif_scores else 0,
                    'is_psd': True
                }
            )
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
            if attempt < max_attempts - 1:
                continue
            else:
                raise ValueError(f"Failed to generate synthetic data after {max_attempts} attempts: {str(e)}")
    
    # This should not be reached due to the raise in the loop
    raise RuntimeError("Unexpected termination in synthetic data generation")

def generate_dataset(config: 'SimulationConfig', seed: int) -> DatasetInstance:
    """
    Wrapper for generate_synthetic_data to maintain API compatibility.
    """
    return generate_synthetic_data(config, seed)

def save_dataset_instance(instance: DatasetInstance, output_path: str) -> None:
    """
    Save a DatasetInstance to a JSON file.
    Converts numpy arrays to lists for JSON serialization.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    data = {
        'X': instance.X.tolist(),
        'y': instance.y.tolist(),
        'beta_true': instance.beta_true.tolist(),
        'vif_scores': instance.vif_scores,
        'seed': instance.seed,
        'regeneration_attempts': instance.regeneration_attempts,
        'regeneration_reason': instance.regeneration_reason,
        'metadata': instance.metadata
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved dataset instance to {output_path}")

def load_dataset_instance(input_path: str) -> DatasetInstance:
    """
    Load a DatasetInstance from a JSON file.
    Converts lists back to numpy arrays.
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    return DatasetInstance(
        X=np.array(data['X']),
        y=np.array(data['y']),
        beta_true=np.array(data['beta_true']),
        vif_scores=data['vif_scores'],
        seed=data['seed'],
        regeneration_attempts=data.get('regeneration_attempts', 0),
        regeneration_reason=data.get('regeneration_reason', ''),
        metadata=data.get('metadata', {})
    )