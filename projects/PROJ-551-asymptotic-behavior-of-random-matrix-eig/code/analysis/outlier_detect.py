"""
Outlier detection logic for perturbed random matrices.

This module implements the detection of outliers (eigenvalues outside the bulk)
based on the BBP (Baik-Ben Arous-Péché) phase transition prediction.

The theoretical bulk edge for a standard Wigner matrix is at +/- 2.0.
Outliers are eigenvalues that exceed this edge by a significant margin,
predicted by the BBP transition when the perturbation strength theta > 1.
"""

from typing import List, Dict, Tuple, Optional, NamedTuple
import numpy as np

from data_models import PerturbationConfig, SimulationRun
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from utils.config import get_outlier_tolerance


class OutlierResult(NamedTuple):
    """Result of outlier detection analysis."""
    run_id: str
    N: int
    theta: float
    bulk_edge: float
    top_eigenvalue: float
    is_outlier: bool
    deviation: float
    bbp_predicted_outlier: bool
    theoretical_outlier_pos: Optional[float]
    perturbation_type: str


def calculate_bbp_threshold(
    theta: float,
    perturbation_rank: int = 1,
    bulk_edge: float = 2.0
) -> Tuple[bool, Optional[float]]:
    """
    Calculate the BBP prediction for outlier emergence.

    According to the BBP transition theorem, for a rank-k perturbation
    with strength theta added to a Wigner matrix:
    - If theta <= 1 (critical threshold), no outlier emerges from the bulk.
    - If theta > 1, an outlier emerges at position:
      lambda_outlier = theta + 1/theta (for standard Wigner scaling)

    Args:
        theta: Perturbation strength parameter.
        perturbation_rank: Rank of the perturbation (default 1).
        bulk_edge: Theoretical edge of the Wigner semicircle (default 2.0).

    Returns:
        Tuple of (bbp_predicts_outlier, theoretical_outlier_position).
        If no outlier is predicted, theoretical_outlier_position is None.
    """
    # Critical threshold for BBP transition is theta = 1
    # For theta > 1, an outlier emerges
    critical_threshold = 1.0

    if theta > critical_threshold:
        # BBP prediction: lambda = theta + 1/theta
        # This assumes the Wigner matrix is scaled by 1/sqrt(N)
        # and the perturbation is added directly.
        theoretical_pos = theta + 1.0 / theta
        return True, theoretical_pos
    else:
        return False, None


def detect_outliers(
    eigenvalues: List[float],
    theta: float,
    perturbation_config: PerturbationConfig,
    bulk_edge: float = 2.0,
    tolerance: Optional[float] = None
) -> OutlierResult:
    """
    Detect outliers in the eigenvalue spectrum.

    This function compares the top eigenvalue against:
    1. The theoretical bulk edge (2.0 for Wigner)
    2. The BBP prediction for the given theta

    Args:
        eigenvalues: List of computed eigenvalues (sorted descending).
        theta: Perturbation strength.
        perturbation_config: Configuration of the perturbation.
        bulk_edge: Theoretical edge of the bulk spectrum.
        tolerance: Optional tolerance for outlier detection.
                  If None, uses config default.

    Returns:
        OutlierResult with detection details.
    """
    if tolerance is None:
        tolerance = get_outlier_tolerance()

    if not eigenvalues:
        raise ValueError("Eigenvalues list cannot be empty")

    top_eigenvalue = max(eigenvalues)
    deviation = top_eigenvalue - bulk_edge

    # Check if top eigenvalue is outside the bulk
    # Using strict tolerance as per T007b
    is_outlier = deviation > tolerance

    # BBP prediction
    bbp_predicts_outlier, theoretical_pos = calculate_bbp_threshold(
        theta,
        perturbation_config.rank,
        bulk_edge
    )

    return OutlierResult(
        run_id="",  # Will be set by caller
        N=0,  # Will be set by caller
        theta=theta,
        bulk_edge=bulk_edge,
        top_eigenvalue=top_eigenvalue,
        is_outlier=is_outlier,
        deviation=deviation,
        bbp_predicted_outlier=bbp_predicts_outlier,
        theoretical_outlier_pos=theoretical_pos,
        perturbation_type=perturbation_config.type
    )


def run_outlier_analysis(
    simulation_run: SimulationRun,
    perturbation_config: PerturbationConfig,
    bulk_edge: float = 2.0
) -> OutlierResult:
    """
    Run full outlier analysis on a simulation run.

    This function:
    1. Computes top eigenvalues if not already present
    2. Validates eigenvalues against the bulk edge
    3. Detects outliers using BBP prediction
    4. Returns detailed analysis result

    Args:
        simulation_run: The simulation run with eigenvalues.
        perturbation_config: Configuration of the perturbation.
        bulk_edge: Theoretical edge of the bulk spectrum.

    Returns:
        OutlierResult with complete analysis.
    """
    eigenvalues = simulation_run.eigenvalues

    if not eigenvalues:
        raise ValueError("Simulation run has no eigenvalues")

    # Validate eigenvalues (T007b)
    validation_result = validate_eigenvalues(eigenvalues, bulk_edge)

    # Detect outliers
    result = detect_outliers(
        eigenvalues,
        simulation_run.theta,
        perturbation_config,
        bulk_edge
    )

    # Fill in run metadata
    result = OutlierResult(
        run_id=simulation_run.run_id,
        N=simulation_run.N,
        theta=simulation_run.theta,
        bulk_edge=result.bulk_edge,
        top_eigenvalue=result.top_eigenvalue,
        is_outlier=result.is_outlier,
        deviation=result.deviation,
        bbp_predicted_outlier=result.bbp_predicted_outlier,
        theoretical_outlier_pos=result.theoretical_outlier_pos,
        perturbation_type=result.perturbation_type
    )

    return result