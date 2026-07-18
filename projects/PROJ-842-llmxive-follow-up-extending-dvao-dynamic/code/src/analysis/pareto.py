"""
Pareto Frontier Analysis Module.

Implements calculation of distance to the theoretical Pareto frontier
for a given set of policy returns across multiple objectives.

This module assumes the theoretical Pareto frontier for the synthetic MDP
corresponds to the set of achievable returns where the sum of normalized
objectives is maximized (or simply the convex hull of achievable extreme points).
In the context of the linear scalarization used in `synthetic_mdp.py`,
the theoretical frontier is defined by the maximum possible return vector
achievable by any deterministic policy.

For a set of achieved returns R = {r_1, r_2, ..., r_N}, the distance to the
Pareto frontier is calculated as the Euclidean distance from the point R
to the closest point on the theoretical frontier.
"""
import numpy as np
from typing import List, Tuple, Optional
import warnings

def calculate_pareto_frontier(
    returns_matrix: np.ndarray,
    epsilon: float = 1e-9
) -> np.ndarray:
    """
    Compute the non-dominated points (Pareto frontier) from a set of return vectors.

    Args:
        returns_matrix: Array of shape (num_policies, num_objectives).
        epsilon: Threshold for strict dominance comparison.

    Returns:
        Array of shape (num_frontier_points, num_objectives) containing
        the non-dominated points.
    """
    if returns_matrix.size == 0:
        return np.empty((0, returns_matrix.shape[1] if returns_matrix.ndim > 1 else 0))

    # Normalize to 2D
    if returns_matrix.ndim == 1:
        returns_matrix = returns_matrix.reshape(1, -1)

    n_policies, n_objectives = returns_matrix.shape
    is_dominated = np.zeros(n_policies, dtype=bool)

    # Simple O(N^2) dominance check (sufficient for typical simulation sizes)
    for i in range(n_policies):
        if is_dominated[i]:
            continue
        for j in range(n_policies):
            if i == j or is_dominated[j]:
                continue
            
            # Check if i dominates j (i is better or equal in all, strictly better in at least one)
            # Since we are maximizing returns:
            dominates = np.all(returns_matrix[i] >= returns_matrix[j] - epsilon)
            strictly_better = np.any(returns_matrix[i] > returns_matrix[j] + epsilon)
            
            if dominates and strictly_better:
                is_dominated[j] = True

    return returns_matrix[~is_dominated]


def distance_to_frontier(
    achieved_returns: np.ndarray,
    frontier_points: Optional[np.ndarray] = None,
    returns_matrix: Optional[np.ndarray] = None,
    epsilon: float = 1e-9
) -> float:
    """
    Calculate the Euclidean distance from a set of achieved returns to the theoretical Pareto frontier.

    If `frontier_points` is not provided, it is computed from `returns_matrix`.
    If `returns_matrix` is also not provided, the `achieved_returns` are assumed
    to be a single point, and the frontier is computed from the provided `frontier_points`.

    Args:
        achieved_returns: The return vector(s) achieved by the policy. Shape (num_objectives,) or (num_policies, num_objectives).
        frontier_points: Optional pre-computed Pareto frontier.
        returns_matrix: Full set of policy returns to compute the frontier from if not provided.
        epsilon: Tolerance for numerical stability.

    Returns:
        The minimum Euclidean distance to any point on the Pareto frontier.
    """
    # Normalize achieved_returns to 2D
    if achieved_returns.ndim == 1:
        achieved_returns = achieved_returns.reshape(1, -1)
    
    if frontier_points is None:
        if returns_matrix is None:
            raise ValueError("Either 'frontier_points' or 'returns_matrix' must be provided.")
        frontier_points = calculate_pareto_frontier(returns_matrix, epsilon)

    if frontier_points.size == 0:
        # If frontier is empty, distance is undefined or infinite. 
        # Returning infinity to indicate failure to find a frontier.
        return float('inf')

    # Compute distances from each achieved point to all frontier points
    # achieved_returns: (P, N)
    # frontier_points: (F, N)
    # We want min distance for each achieved point to any frontier point.
    
    # Expand dimensions for broadcasting
    # A: (P, 1, N), B: (1, F, N) -> Diff: (P, F, N)
    diff = achieved_returns[:, np.newaxis, :] - frontier_points[np.newaxis, :, :]
    distances = np.linalg.norm(diff, axis=2) # (P, F)
    
    # Return the minimum distance found across all achieved points
    min_dist = np.min(distances)
    
    return float(min_dist)


def compute_pareto_metrics(
    returns_matrix: np.ndarray,
    policy_returns: np.ndarray
) -> dict:
    """
    Compute comprehensive metrics regarding Pareto optimality.

    Args:
        returns_matrix: Full set of returns from all policies (N x M).
        policy_returns: Specific returns to evaluate (K x M or M).

    Returns:
        Dictionary containing:
            - 'frontier_size': Number of points on the frontier.
            - 'min_distance': Minimum distance to the frontier.
            - 'mean_distance': Mean distance of evaluated policies to the frontier.
            - 'is_pareto_optimal': Boolean indicating if policy_returns are on the frontier.
    """
    if policy_returns.ndim == 1:
        policy_returns = policy_returns.reshape(1, -1)

    frontier = calculate_pareto_frontier(returns_matrix)
    
    # Check if the specific policy returns are on the frontier
    # A point is on the frontier if it is in the set of non-dominated points
    # (with floating point tolerance)
    is_optimal = False
    for point in frontier:
        if np.allclose(point, policy_returns[0], atol=1e-5):
            is_optimal = True
            break

    # Calculate distances
    distances = []
    for pr in policy_returns:
        d = distance_to_frontier(pr, frontier_points=frontier)
        distances.append(d)

    return {
        "frontier_size": len(frontier),
        "min_distance": float(np.min(distances)),
        "mean_distance": float(np.mean(distances)),
        "is_pareto_optimal": is_optimal,
        "frontier_points": frontier.tolist()
    }
