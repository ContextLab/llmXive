"""
Outlier detection logic for perturbed random matrix eigenvalues.

This module implements the logic to distinguish between eigenvalues belonging
to the bulk (semicircle law support [-2, 2]) and outliers predicted by the
BBP (Baik-Ben Arous-Péché) phase transition theory.

The detection relies on comparing the computed eigenvalues against the
theoretical bulk edge (2.0) and the predicted BBP threshold (theta + 1/theta).
"""
from typing import List, Dict, Tuple, Optional
import numpy as np

from data_models import PerturbationConfig, SimulationRun
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues

# Constants
BULK_EDGE_THEORETICAL = 2.0
TOLERANCE_FRACTION = 1e-6  # Fraction of matrix size for tolerance scaling

class OutlierResult:
    """
    Container for outlier detection results.
    """
    def __init__(
        self,
        eigenvalues: np.ndarray,
        outlier_indices: List[int],
        outlier_values: np.ndarray,
        bulk_indices: List[int],
        bulk_values: np.ndarray,
        bbp_threshold: float,
        is_outlier_present: bool
    ):
        self.eigenvalues = eigenvalues
        self.outlier_indices = outlier_indices
        self.outlier_values = outlier_values
        self.bulk_indices = bulk_indices
        self.bulk_values = bulk_values
        self.bbp_threshold = bbp_threshold
        self.is_outlier_present = is_outlier_present

    def to_dict(self) -> Dict:
        return {
            "eigenvalues": self.eigenvalues.tolist(),
            "outlier_indices": self.outlier_indices,
            "outlier_values": self.outlier_values.tolist(),
            "bulk_indices": self.bulk_indices,
            "bulk_values": self.bulk_values.tolist(),
            "bbp_threshold": self.bbp_threshold,
            "bulk_edge_theoretical": BULK_EDGE_THEORETICAL,
            "is_outlier_present": self.is_outlier_present
        }

def calculate_bbp_threshold(theta: float) -> float:
    """
    Calculate the theoretical BBP threshold for outlier emergence.

    According to BBP theory, for a perturbation of norm theta > 1,
    the outlier eigenvalue emerges at approximately:
        lambda_outlier = theta + 1/theta

    For theta <= 1, no outlier exists above the bulk edge (2.0).

    Args:
        theta: The norm of the rank-k perturbation.

    Returns:
        The predicted eigenvalue position for the outlier.
    """
    if theta <= 1.0:
        # No theoretical outlier for sub-critical perturbations
        return BULK_EDGE_THEORETICAL
    return theta + (1.0 / theta)

def detect_outliers(
    eigenvalues: np.ndarray,
    perturbation_config: PerturbationConfig,
    matrix_size: int,
    strict_validation: bool = True
) -> OutlierResult:
    """
    Detect outliers in the eigenvalue spectrum based on BBP theory.

    This function:
    1. Calculates the theoretical BBP threshold based on the perturbation norm.
    2. Compares the computed eigenvalues against the bulk edge (2.0) and the BBP threshold.
    3. Classifies eigenvalues as 'bulk' or 'outlier'.

    Args:
        eigenvalues: Array of computed eigenvalues (sorted descending).
        perturbation_config: Configuration containing the perturbation norm (theta).
        matrix_size: Dimension N of the matrix.
        strict_validation: If True, strictly validate against the theoretical bulk edge (2.0)
                           to ensure outliers are not artifacts, as per T007 requirements.

    Returns:
        OutlierResult containing classification details.
    """
    if len(eigenvalues) == 0:
        return OutlierResult(
            eigenvalues=np.array([]),
            outlier_indices=[],
            outlier_values=np.array([]),
            bulk_indices=[],
            bulk_values=np.array([]),
            bbp_threshold=BULK_EDGE_THEORETICAL,
            is_outlier_present=False
        )

    theta = perturbation_config.norm
    bbp_threshold = calculate_bbp_threshold(theta)

    # Determine tolerance for numerical stability
    # Scale tolerance with matrix size to account for finite-N fluctuations
    tolerance = max(1e-8, BULK_EDGE_THEORETICAL * TOLERANCE_FRACTION * np.sqrt(matrix_size))

    outlier_indices = []
    outlier_values = []
    bulk_indices = []
    bulk_values = []

    # Sort eigenvalues descending (should already be, but ensure)
    sorted_indices = np.argsort(eigenvalues)[::-1]
    sorted_eigenvalues = eigenvalues[sorted_indices]

    for i, val in enumerate(sorted_eigenvalues):
        # Strict validation: An outlier must be strictly greater than the bulk edge (2.0)
        # and ideally close to the BBP prediction if theta > 1.
        # We use a slightly relaxed check against the bulk edge to account for finite-N
        # fluctuations, but strictly greater than 2.0 + tolerance.
        if strict_validation:
            is_outlier = val > (BULK_EDGE_THEORETICAL + tolerance)
        else:
            # Fallback: use BBP threshold directly if not in strict mode
            is_outlier = val > bbp_threshold

        if is_outlier:
            outlier_indices.append(int(sorted_indices[i]))
            outlier_values.append(float(val))
        else:
            bulk_indices.append(int(sorted_indices[i]))
            bulk_values.append(float(val))

    # Convert lists to numpy arrays for consistency
    outlier_vals_arr = np.array(outlier_values)
    bulk_vals_arr = np.array(bulk_values)

    is_outlier_present = len(outlier_vals_arr) > 0

    return OutlierResult(
        eigenvalues=sorted_eigenvalues,
        outlier_indices=outlier_indices,
        outlier_values=outlier_vals_arr,
        bulk_indices=bulk_indices,
        bulk_values=bulk_vals_arr,
        bbp_threshold=bbp_threshold,
        is_outlier_present=is_outlier_present
    )

def run_outlier_analysis(
    simulation_run: SimulationRun,
    perturbation_config: PerturbationConfig,
    eigenvalues: Optional[np.ndarray] = None
) -> OutlierResult:
    """
    Perform a complete outlier analysis on a simulation run.

    If eigenvalues are not provided, they are computed using the iterative solver.

    Args:
        simulation_run: The simulation run object containing matrix info.
        perturbation_config: The perturbation configuration.
        eigenvalues: Optional pre-computed eigenvalues.

    Returns:
        OutlierResult with classification and metrics.
    """
    if eigenvalues is None:
        # Compute top eigenvalues if not provided
        # We need enough eigenvalues to detect outliers; usually top 10 is sufficient
        num_eigs = max(10, perturbation_config.rank + 5)
        eigenvalues = compute_top_eigenvalues(
            matrix_size=simulation_run.matrix_size,
            perturbation_config=perturbation_config,
            num_eigenvalues=num_eigs
        )

    # Validate eigenvalues against the theoretical semicircle edge
    # This ensures we are not misidentifying bulk fluctuations as outliers
    validate_eigenvalues(eigenvalues, simulation_run.matrix_size)

    return detect_outliers(
        eigenvalues=eigenvalues,
        perturbation_config=perturbation_config,
        matrix_size=simulation_run.matrix_size
    )
