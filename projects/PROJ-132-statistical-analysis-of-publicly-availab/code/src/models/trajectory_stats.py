"""
Compute Manifold-Based Trajectory Statistics using geomstats.

This module implements Riemannian statistics for bird migration trajectories,
including Fréchet variance, geodesic regression, and parallel transport.
"""
import json
import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Mandatory import as per task requirement
import geomstats
from geomstats.geometry.sphere import Sphere
from geomstats.learning.frechet_mean import FrechetMean

from src.config import setup_logging
from src.models.trajectory import load_centroid_data, group_centroids_by_period

logger = setup_logging(__name__)


def _ensure_sphere_metric() -> Sphere:
    """
    Initialize the intrinsic Sphere geometry (dim=2) as required by the spec.
    Raises ModuleNotFoundError if geomstats is unavailable.
    """
    try:
        sphere = Sphere(dim=2, metric='intrinsic')
        return sphere
    except Exception as e:
        raise ModuleNotFoundError(f"geomstats is required but failed to initialize Sphere: {e}") from e


def compute_frechet_variance(
    points: np.ndarray,
    sphere: Sphere,
    max_iter: int = 100,
    tol: float = 1e-6
) -> float:
    """
    Compute the Fréchet variance of a set of points on the sphere.

    The Fréchet variance is defined as the mean squared geodesic distance
    from the Fréchet mean.

    Args:
        points: Array of shape (n_samples, dim) representing points on the sphere.
        sphere: The Sphere geometry instance.
        max_iter: Maximum iterations for mean estimation.
        tol: Convergence tolerance.

    Returns:
        float: The computed Fréchet variance.
    """
    if points.size == 0:
        return 0.0

    # Compute Fréchet mean
    mean_estimator = FrechetMean(
        metric=sphere.metric,
        max_iter=max_iter,
        tol=tol
    )
    mean_estimator.fit(points)
    mean_point = mean_estimator.estimate_

    # Compute squared geodesic distances from the mean
    squared_distances = sphere.metric.squared_dist(points, mean_point)

    # Fréchet variance is the average of these squared distances
    variance = np.mean(squared_distances)
    return float(variance)


def geodesic_regression(
    points: np.ndarray,
    time_coords: np.ndarray,
    sphere: Sphere,
    max_iter: int = 100,
    tol: float = 1e-6
) -> Dict[str, Any]:
    """
    Perform geodesic regression on points over time.

    This fits a geodesic curve (the Riemannian analogue of a line) to the data
    by minimizing the sum of squared geodesic distances.

    Args:
        points: Array of shape (n_samples, dim) representing points on the sphere.
        time_coords: Array of shape (n_samples,) representing time (e.g., week index).
        sphere: The Sphere geometry instance.
        max_iter: Maximum iterations for optimization.
        tol: Convergence tolerance.

    Returns:
        Dictionary containing:
            - 'intercept': The starting point of the geodesic (on the manifold).
            - 'velocity': The tangent vector (velocity) at the intercept.
            - 'residual_variance': The residual sum of squares normalized.
    """
    if points.size == 0 or time_coords.size == 0:
        return {
            'intercept': [0.0, 0.0, 0.0],
            'velocity': [0.0, 0.0, 0.0],
            'residual_variance': 0.0
        }

    # Initial guess: Fréchet mean of points as intercept, zero velocity
    mean_estimator = FrechetMean(metric=sphere.metric, max_iter=50, tol=1e-5)
    mean_estimator.fit(points)
    intercept = mean_estimator.estimate_

    # Simple iterative optimization for geodesic regression
    # We minimize: sum_i d^2(exp_intercept(t_i * velocity), point_i)
    # Using a simple gradient descent approach on the tangent space at intercept

    velocity = np.zeros(3)  # Tangent space at a point on S^2 is R^3 (with constraint)
    # Initialize velocity based on linear regression in tangent space at mean
    # Project points to tangent space at intercept
    log_map_points = sphere.metric.log(points, intercept)

    # Linear regression: log_map_points ~ time_coords * velocity
    # Solve for velocity using least squares
    # log_map_points = velocity * time_coords (approx)
    # velocity = (X^T X)^-1 X^T Y
    X = time_coords.reshape(-1, 1)
    Y = log_map_points

    # Handle case where X is empty or singular
    if X.shape[0] < 2:
        velocity = np.zeros(3)
    else:
        try:
            # Simple least squares
            velocity = np.linalg.lstsq(X, Y, rcond=None)[0].flatten()
        except np.linalg.LinAlgError:
            velocity = np.zeros(3)

    # Compute residual variance
    # Reconstruct geodesic points
    exp_map_points = sphere.metric.exp(time_coords.reshape(-1, 1) * velocity, intercept)
    squared_residuals = sphere.metric.squared_dist(exp_map_points, points)
    residual_variance = float(np.mean(squared_residuals))

    return {
        'intercept': intercept.tolist(),
        'velocity': velocity.tolist(),
        'residual_variance': residual_variance
    }


def parallel_transport_velocity(
    velocity: np.ndarray,
    start_point: np.ndarray,
    end_point: np.ndarray,
    sphere: Sphere
) -> np.ndarray:
    """
    Parallel transport a velocity vector from start_point to end_point along the geodesic.

    Args:
        velocity: Tangent vector at start_point.
        start_point: Point on the manifold where the vector originates.
        end_point: Point on the manifold where the vector is transported to.
        sphere: The Sphere geometry instance.

    Returns:
        Transported tangent vector at end_point.
    """
    # Use the built-in parallel transport if available, otherwise approximate
    try:
        transported = sphere.metric.parallel_transport(start_point, velocity, end_point)
        return transported
    except AttributeError:
        # Fallback: approximate using rotation on the sphere
        # This is a simplified approximation; for S^2, parallel transport
        # can be computed via rotation around the cross product of start and end
        logger.warning("Using fallback parallel transport approximation.")
        # Compute the geodesic direction
        log_vec = sphere.metric.log(end_point, start_point)
        angle = np.linalg.norm(log_vec)
        if angle < 1e-10:
            return velocity

        # Axis of rotation
        axis = np.cross(start_point, end_point)
        axis = axis / np.linalg.norm(axis)

        # Rotate the velocity vector around this axis by the angle
        # Rodrigues' rotation formula
        k = axis
        v_rot = (
            velocity * np.cos(angle) +
            np.cross(k, velocity) * np.sin(angle) +
            k * np.dot(k, velocity) * (1 - np.cos(angle))
        )
        # Project back to tangent space at end_point
        # Subtract component along end_point
        v_tangent = v_rot - np.dot(v_rot, end_point) * end_point
        return v_tangent


def compute_trajectory_statistics(
    species: str,
    year: int,
    centroids: np.ndarray,
    weeks: np.ndarray
) -> Dict[str, Any]:
    """
    Compute trajectory-level statistics for a single species-year.

    Args:
        species: Species name.
        year: Year of observation.
        centroids: Array of shape (n_weeks, 3) representing weekly centroids on S^2.
        weeks: Array of shape (n_weeks,) representing week indices.

    Returns:
        Dictionary containing:
            - 'fréchet_variance': Variance of the trajectory points.
            - 'geodesic_regression_coefficients': Dict with 'intercept', 'velocity', 'residual_variance'.
            - 'parallel_transport_vectors': List of transported velocity vectors (if applicable).
    """
    sphere = _ensure_sphere_metric()

    # 1. Compute Fréchet Variance
    frechet_var = compute_frechet_variance(centroids, sphere)

    # 2. Perform Geodesic Regression
    reg_results = geodesic_regression(centroids, weeks, sphere)

    # 3. Compute Parallel Transport (example: transport velocity from first to last week)
    # We transport the initial velocity vector along the geodesic from start to end
    transport_vectors = []
    if len(centroids) > 1 and np.linalg.norm(reg_results['velocity']) > 1e-10:
        start_pt = centroids[0]
        end_pt = centroids[-1]
        initial_vel = np.array(reg_results['velocity'])

        # Transport the velocity from start to end
        transported_vel = parallel_transport_velocity(initial_vel, start_pt, end_pt, sphere)
        transport_vectors.append({
            'from_week': int(weeks[0]),
            'to_week': int(weeks[-1]),
            'transported_velocity': transported_vel.tolist()
        })

    return {
        'species': species,
        'year': year,
        'fréchet_variance': frechet_var,
        'geodesic_regression_coefficients': reg_results,
        'parallel_transport_vectors': transport_vectors
    }


def run_trajectory_statistics_pipeline(
    input_path: str = "data/interim/weekly_centroids.parquet",
    output_path: str = "data/interim/trajectory_statistics.json"
) -> None:
    """
    Main pipeline to compute trajectory statistics for all species-years.

    Reads weekly centroids, groups by species-year, computes statistics,
    and writes the results to a JSON file.
    """
    logger.info(f"Starting trajectory statistics pipeline for {input_path}")

    # Load and group data
    grouped_data = group_centroids_by_period(input_path)

    all_statistics = []

    for (species, year), data in grouped_data.items():
        try:
            centroids = np.array(data['centroids'])
            weeks = np.array(data['weeks'])

            if len(centroids) < 2:
                logger.warning(f"Skipping {species}-{year}: insufficient centroids ({len(centroids)})")
                continue

            stats = compute_trajectory_statistics(species, year, centroids, weeks)
            all_statistics.append(stats)
            logger.info(f"Computed statistics for {species}-{year}: variance={stats['fréchet_variance']:.6f}")

        except Exception as e:
            logger.error(f"Failed to compute statistics for {species}-{year}: {e}", exc_info=True)
            continue

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_statistics, f, indent=2)

    logger.info(f"Trajectory statistics written to {output_path}")


def main():
    """Entry point for the script."""
    run_trajectory_statistics_pipeline()


if __name__ == "__main__":
    main()
