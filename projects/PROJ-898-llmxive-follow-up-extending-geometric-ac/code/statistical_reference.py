"""
Statistical Reference Distribution Generator for T010b.

Computes mean and covariance statistics from generated physics states
and saves them to the reference stats file for use in latent drift detection.
"""

import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Import existing utilities from the project
try:
    from utils import setup_logging
except ImportError:
    # Fallback for direct execution if utils is not in path
    import utils
    setup_logging = utils.setup_logging

logger = logging.getLogger(__name__)


def load_physics_states(filepath: str) -> Dict[str, Any]:
    """Load physics states from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Physics states file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_state_vectors(states: Dict[str, Any]) -> np.ndarray:
    """
    Extract numeric state vectors from physics states for statistical analysis.
    
    Flattens all numeric state components (vertex positions, joint angles, etc.)
    into a single feature vector per timestep.
    
    Args:
        states: Dictionary containing physics states with structure:
               {
                 "topology_id": str,
                 "timesteps": [
                   {
                     "vertex_positions": [[x,y,z], ...],
                     "joint_angles": [angle1, angle2, ...],
                     "timestamp": float,
                     ...
                   },
                   ...
                 ]
               }
    
    Returns:
        np.ndarray of shape (n_timesteps, n_features)
    """
    all_vectors = []
    
    if "topology_id" in states:
        # Single topology structure
        timesteps = states.get("timesteps", [])
        vectors = _process_timesteps(timesteps)
        all_vectors.extend(vectors)
    elif "topologies" in states:
        # Multiple topologies structure
        for topology in states.get("topologies", []):
            timesteps = topology.get("timesteps", [])
            vectors = _process_timesteps(timesteps)
            all_vectors.extend(vectors)
    elif isinstance(states, list):
        # List of topology states
        for topology in states:
            timesteps = topology.get("timesteps", [])
            vectors = _process_timesteps(timesteps)
            all_vectors.extend(vectors)
    
    if len(all_vectors) == 0:
        raise ValueError("No valid state vectors found in physics states")
    
    return np.array(all_vectors, dtype=np.float64)


def _process_timesteps(timesteps: List[Dict]) -> List[np.ndarray]:
    """Process a list of timesteps into feature vectors."""
    vectors = []
    
    for timestep in timesteps:
        features = []
        
        # Extract vertex positions (flattened)
        if "vertex_positions" in timestep:
            positions = np.array(timestep["vertex_positions"], dtype=np.float64)
            features.extend(positions.flatten())
        
        # Extract joint angles
        if "joint_angles" in timestep:
            angles = np.array(timestep["joint_angles"], dtype=np.float64)
            features.extend(angles)
        
        # Extract other numeric state variables if present
        for key, value in timestep.items():
            if key not in ("vertex_positions", "joint_angles", "timestamp", "topology_id"):
                if isinstance(value, (int, float)):
                    features.append(float(value))
                elif isinstance(value, list) and all(isinstance(v, (int, float)) for v in value):
                    features.extend([float(v) for v in value])
        
        if features:
            vectors.append(np.array(features, dtype=np.float64))
    
    return vectors


def compute_statistics(vectors: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute mean and covariance matrix from state vectors.
    
    Args:
        vectors: np.ndarray of shape (n_samples, n_features)
    
    Returns:
        Tuple of (mean, covariance) where:
          - mean: np.ndarray of shape (n_features,)
          - covariance: np.ndarray of shape (n_features, n_features)
    """
    if vectors.shape[0] < 2:
        raise ValueError(f"Need at least 2 samples to compute covariance, got {vectors.shape[0]}")
    
    mean = np.mean(vectors, axis=0)
    covariance = np.cov(vectors, rowvar=False)
    
    # Ensure covariance is positive semi-definite (add small regularization if needed)
    min_eig = np.min(np.linalg.eigvalsh(covariance))
    if min_eig < 0:
        logger.warning(f"Covariance matrix has negative eigenvalue: {min_eig}. Adding regularization.")
        covariance += np.eye(covariance.shape[0]) * (-min_eig + 1e-8)
    
    return mean, covariance


def save_reference_stats(
    mean: np.ndarray,
    covariance: np.ndarray,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save reference statistics to JSON file.
    
    Args:
        mean: Mean vector
        covariance: Covariance matrix
        output_path: Path to save the JSON file
        metadata: Optional additional metadata to include
    """
    stats = {
        "mean": mean.tolist(),
        "covariance": covariance.tolist(),
        "n_features": len(mean),
        "n_samples": covariance.shape[0],
        "description": "Reference distribution for latent drift detection (Mahalanobis distance)",
        "created_at": metadata.get("created_at", "unknown") if metadata else "unknown"
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved reference statistics to {output_path}")


def compute_reference_stats_from_file(
    input_path: str,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main function to compute and save reference statistics from physics states.
    
    Args:
        input_path: Path to physics_states.json
        output_path: Path to save gam_reference_stats.json
        metadata: Optional metadata to include in output
    
    Returns:
        Dictionary with computation results
    """
    logger.info(f"Loading physics states from {input_path}")
    states = load_physics_states(input_path)
    
    logger.info("Extracting state vectors")
    vectors = extract_state_vectors(states)
    logger.info(f"Extracted {vectors.shape[0]} vectors with {vectors.shape[1]} features")
    
    logger.info("Computing statistics")
    mean, covariance = compute_statistics(vectors)
    
    logger.info(f"Saving reference statistics to {output_path}")
    save_reference_stats(mean, covariance, output_path, metadata)
    
    return {
        "n_samples": vectors.shape[0],
        "n_features": vectors.shape[1],
        "mean_shape": list(mean.shape),
        "covariance_shape": list(covariance.shape),
        "output_path": output_path
    }


def main() -> None:
    """Main entry point for T010b."""
    # Setup logging
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    setup_logging(level=log_level)
    
    # Define paths
    input_path = "data/generated/physics_states.json"
    output_path = "data/raw/gam_reference_stats.json"
    
    # Check input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T010a has completed and generated physics_states.json")
        sys.exit(1)
    
    # Compute and save statistics
    try:
        result = compute_reference_stats_from_file(input_path, output_path)
        logger.info(f"Successfully computed reference statistics: {result}")
    except Exception as e:
        logger.error(f"Failed to compute reference statistics: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
