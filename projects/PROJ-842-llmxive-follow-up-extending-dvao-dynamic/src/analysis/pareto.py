import numpy as np
from typing import List, Tuple, Optional
import warnings

def calculate_pareto_frontier(
    objectives: np.ndarray,
    maximize: bool = True
) -> np.ndarray:
    """
    Calculate the Pareto frontier for a set of objective vectors.

    Parameters
    ----------
    objectives : np.ndarray
        Array of shape (n_samples, n_objectives) containing the objective values
        for each sample/policy.
    maximize : bool, default=True
        If True, we look for Pareto optimal solutions in the maximization sense.
        If False, we look for minimization sense.

    Returns
    -------
    np.ndarray
        Boolean array of shape (n_samples,) indicating which samples are on the
        Pareto frontier (True) and which are dominated (False).
    """
    if objectives.ndim != 2:
        raise ValueError("Objectives must be a 2D array of shape (n_samples, n_objectives)")

    n_samples, n_objectives = objectives.shape

    if n_samples == 0:
        return np.array([], dtype=bool)

    # Normalize sign based on maximization/minimization
    # For maximization: A dominates B if A >= B and A != B
    # For minimization: A dominates B if A <= B and A != B
    # We can standardize by flipping signs for minimization to treat as maximization
    data = objectives if maximize else -objectives

    frontier_mask = np.ones(n_samples, dtype=bool)

    for i in range(n_samples):
        if not frontier_mask[i]:
            continue

        # Check if i is dominated by any other j
        for j in range(n_samples):
            if i == j or not frontier_mask[j]:
                continue

            # Check if j dominates i
            # j dominates i if data[j] >= data[i] and data[j] != data[i]
            # (element-wise)
            if np.all(data[j] >= data[i]) and np.any(data[j] > data[i]):
                frontier_mask[i] = False
                break

    return frontier_mask

def distance_to_frontier(
    point: np.ndarray,
    frontier_points: np.ndarray,
    metric: str = 'euclidean'
) -> float:
    """
    Calculate the distance from a point to the Pareto frontier.

    Parameters
    ----------
    point : np.ndarray
        A single point (1D array) of shape (n_objectives,).
    frontier_points : np.ndarray
        Array of shape (n_frontier_points, n_objectives) representing the
        Pareto frontier.
    metric : str, default='euclidean'
        Distance metric to use. Supported: 'euclidean'.

    Returns
    -------
    float
        The minimum distance from the point to any point on the frontier.
    """
    if point.ndim != 1:
        raise ValueError("point must be a 1D array")

    if frontier_points.ndim != 2:
        raise ValueError("frontier_points must be a 2D array")

    if point.shape[0] != frontier_points.shape[1]:
        raise ValueError("Dimension mismatch between point and frontier_points")

    if frontier_points.shape[0] == 0:
        return np.inf

    if metric == 'euclidean':
        # Calculate Euclidean distance to all frontier points
        distances = np.linalg.norm(frontier_points - point, axis=1)
        return float(np.min(distances))
    else:
        raise ValueError(f"Unsupported metric: {metric}. Only 'euclidean' is supported.")

def compute_pareto_metrics(
    objectives: np.ndarray,
    policy_values: np.ndarray,
    maximize: bool = True
) -> dict:
    """
    Compute comprehensive Pareto metrics for a set of policies.

    Parameters
    ----------
    objectives : np.ndarray
        Array of shape (n_policies, n_objectives) containing objective values.
    policy_values : np.ndarray
        Array of shape (n_policies,) containing a scalar value (e.g., total reward)
        for each policy to correlate with Pareto distance.
    maximize : bool, default=True
        Whether to treat objectives as maximization problems.

    Returns
    -------
    dict
        Dictionary containing:
        - 'frontier_indices': indices of policies on the Pareto frontier
        - 'frontier_size': number of policies on the frontier
        - 'distances': array of distances to frontier for each policy
        - 'mean_distance': mean distance to frontier
        - 'max_distance': maximum distance to frontier
        - 'frontier_values': objective values of policies on the frontier
        - 'correlation_reward_distance': correlation between policy value and distance
  """
    if objectives.shape[0] != policy_values.shape[0]:
        raise ValueError("objectives and policy_values must have the same number of policies")

    # Calculate frontier mask
    frontier_mask = calculate_pareto_frontier(objectives, maximize=maximize)
    frontier_indices = np.where(frontier_mask)[0]
    frontier_points = objectives[frontier_mask]

    # Calculate distances for all policies
    distances = np.array([
        distance_to_frontier(objectives[i], frontier_points)
        for i in range(objectives.shape[0])
    ])

    # Calculate correlation between policy value and distance to frontier
    if len(np.unique(policy_values)) > 1:
        correlation, _ = np.corrcoef(policy_values, distances)
        correlation = correlation[0, 1]
    else:
        correlation = 0.0

    metrics = {
        'frontier_indices': frontier_indices.tolist(),
        'frontier_size': int(frontier_mask.sum()),
        'distances': distances.tolist(),
        'mean_distance': float(np.mean(distances)),
        'max_distance': float(np.max(distances)),
        'frontier_values': frontier_points.tolist(),
        'correlation_reward_distance': float(correlation)
    }

    return metrics
