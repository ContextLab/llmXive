"""
Data validation schema and checksumming logic.
"""
import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

# Physical bounds for robot joint configurations (normalized to [-1, 1])
# These are standard bounds for 7-DOF manipulators used in VLA datasets
DEFAULT_JOINT_LOWER_BOUNDS = np.array([-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0])
DEFAULT_JOINT_UPPER_BOUNDS = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

# Physical bounds for end-effector velocities (m/s)
DEFAULT_VELOCITY_LOWER_BOUNDS = np.array([-2.0, -2.0, -2.0])
DEFAULT_VELOCITY_UPPER_BOUNDS = np.array([2.0, 2.0, 2.0])

# Physical bounds for end-effector accelerations (m/s^2)
DEFAULT_ACCEL_LOWER_BOUNDS = np.array([-10.0, -10.0, -10.0])
DEFAULT_ACCEL_UPPER_BOUNDS = np.array([10.0, 10.0, 10.0])

def compute_file_checksum(filepath: str, algorithm: str = 'md5') -> str:
    """
    Compute checksum of a file for integrity verification.

    Args:
        filepath (str): Path to the file.
        algorithm (str): Hash algorithm to use ('md5', 'sha256', etc.).

    Returns:
        str: Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found for checksum: {filepath}")
    
    try:
        hash_func = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm '{algorithm}': {e}")
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_dataframe_schema(
    df: pd.DataFrame, 
    expected_columns: List[str], 
    required_types: Optional[Dict[str, type]] = None
) -> bool:
    """
    Validate that a DataFrame has the expected schema.

    Args:
        df (pd.DataFrame): DataFrame to validate.
        expected_columns (List[str]): List of required column names.
        required_types (Dict[str, type], optional): Dictionary mapping column names to expected types.

    Returns:
        bool: True if validation passes.

    Raises:
        ValueError: If validation fails.
    """
    if df.empty:
        raise ValueError("DataFrame is empty; cannot validate schema.")

    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    if required_types:
        for col, expected_type in required_types.items():
            if col in df.columns:
                # Check dtype compatibility for numpy/pandas types
                if np.issubdtype(expected_type, np.number):
                    if not np.issubdtype(df[col].dtype, np.number):
                        raise ValueError(
                            f"Column '{col}' has incorrect numeric type. "
                            f"Expected numeric, got {df[col].dtype}"
                        )
                elif not isinstance(df[col].iloc[0], expected_type):
                    raise ValueError(
                        f"Column '{col}' has incorrect type. "
                        f"Expected {expected_type}, got {type(df[col].iloc[0])}"
                    )
    
    return True

def validate_numeric_bounds(
    data: np.ndarray, 
    lower_bounds: np.ndarray, 
    upper_bounds: np.ndarray, 
    name: str = "data"
) -> bool:
    """
    Validate that numeric data is within physical bounds.

    Args:
        data (np.ndarray): Data array to validate.
        lower_bounds (np.ndarray): Lower bounds.
        upper_bounds (np.ndarray): Upper bounds.
        name (str): Name of the data for error messages.

    Returns:
        bool: True if all values are within bounds.

    Raises:
        ValueError: If any value is out of bounds or dimensions mismatch.
    """
    if data.ndim == 0:
        data = np.array([data])
        
    if lower_bounds.ndim == 0:
        lower_bounds = np.array([lower_bounds])
    if upper_bounds.ndim == 0:
        upper_bounds = np.array([upper_bounds])

    # Handle 2D data (samples x features) or 1D data (features)
    feature_dim = data.shape[-1] if data.ndim > 1 else data.shape[0]
    
    if lower_bounds.shape[0] != feature_dim or upper_bounds.shape[0] != feature_dim:
        raise ValueError(
            f"Dimension mismatch in {name}: data has {feature_dim} features, "
            f"but bounds have {lower_bounds.shape[0]} and {upper_bounds.shape[0]}"
        )

    # Broadcast bounds for multi-sample validation
    if data.ndim > 1:
        if data.shape[1] != feature_dim:
            raise ValueError(f"Dimension mismatch: data shape {data.shape}, expected last dim {feature_dim}")
        
        if np.any(data < lower_bounds) or np.any(data > upper_bounds):
            out_of_lower = np.sum(data < lower_bounds)
            out_of_upper = np.sum(data > upper_bounds)
            raise ValueError(
                f"{name} out of bounds: {out_of_lower} values below lower limit, "
                f"{out_of_upper} values above upper limit"
            )
    else:
        if np.any(data < lower_bounds) or np.any(data > upper_bounds):
            out_of_lower = np.sum(data < lower_bounds)
            out_of_upper = np.sum(data > upper_bounds)
            raise ValueError(
                f"{name} out of bounds: {out_of_lower} values below lower limit, "
                f"{out_of_upper} values above upper limit"
            )
    
    return True

def validate_cluster_assignments(
    assignments: np.ndarray, 
    n_clusters: int, 
    min_samples_per_cluster: int = 100
) -> bool:
    """
    Validate cluster assignments meet quality criteria.

    Args:
        assignments (np.ndarray): Array of cluster labels.
        n_clusters (int): Expected number of clusters.
        min_samples_per_cluster (int): Minimum samples required per cluster.

    Returns:
        bool: True if validation passes.

    Raises:
        ValueError: If validation fails.
    """
    if assignments.size == 0:
        raise ValueError("Assignments array is empty.")

    unique_labels, counts = np.unique(assignments, return_counts=True)
    
    if len(unique_labels) != n_clusters:
        raise ValueError(
            f"Expected {n_clusters} clusters, found {len(unique_labels)}. "
            f"Labels found: {unique_labels}"
        )
    
    if n_clusters > 1:
        for label, count in zip(unique_labels, counts):
            if count < min_samples_per_cluster:
                raise ValueError(
                    f"Cluster {label} has only {count} samples, "
                    f"minimum required is {min_samples_per_cluster}"
                )
    
    return True

def validate_trajectory_consistency(
    trajectory: np.ndarray, 
    expected_length: Optional[int] = None,
    joint_bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None
) -> bool:
    """
    Validate that a trajectory array is consistent with physical constraints.

    Args:
        trajectory (np.ndarray): Trajectory data (T x D or D).
        expected_length (int, optional): Expected number of time steps.
        joint_bounds (Tuple[np.ndarray, np.ndarray], optional): (lower, upper) bounds for joints.

    Returns:
        bool: True if validation passes.

    Raises:
        ValueError: If validation fails.
    """
    if trajectory.ndim == 1:
        trajectory = trajectory.reshape(1, -1)
    
    if trajectory.shape[1] != 7: # Assuming 7-DOF for Qwen-VLA tasks
        # Allow flexibility if bounds are provided
        if joint_bounds is None:
            raise ValueError(f"Expected 7 joints, got {trajectory.shape[1]}")
    
    if expected_length is not None and trajectory.shape[0] != expected_length:
        raise ValueError(
            f"Trajectory length mismatch: expected {expected_length}, got {trajectory.shape[0]}"
        )

    if joint_bounds:
        lower, upper = joint_bounds
        validate_numeric_bounds(trajectory, lower, upper, name="trajectory")
    
    return True

def generate_validation_report(
    results: Dict[str, bool],
    filepath: str
) -> None:
    """
    Generate a JSON validation report.

    Args:
        results (Dict[str, bool]): Dictionary of validation check names to results.
        filepath (str): Output path for the report.
    """
    report = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "checks": results,
        "summary": {
            "total": len(results),
            "passed": sum(results.values()),
            "failed": len(results) - sum(results.values())
        }
    }
    
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)