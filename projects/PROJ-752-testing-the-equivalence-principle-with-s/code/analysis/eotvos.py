"""
Eotvos Parameter Estimation Module

Computes the Eotvos parameter (η) and its 95% confidence interval
from the joint orbit solution covariance matrix.
"""
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field

from models.estimator import OrbitSolution, extract_joint_parameters
from utils.logging import get_logger, AnalysisError

logger = get_logger(__name__)


@dataclass
class EotvosResult:
    """Container for the Eotvos parameter estimation results."""
    eta: float
    eta_std: float
    eta_ci_95_lower: float
    eta_ci_95_upper: float
    ac: float
    g: float
    covariance_ac_g: np.ndarray
    success: bool
    message: str = field(default="")

    def to_dict(self) -> Dict:
        """Convert result to a JSON-serializable dictionary."""
        return {
            "eta": self.eta,
            "eta_std": self.eta_std,
            "eta_ci_95_lower": self.eta_ci_95_lower,
            "eta_ci_95_upper": self.eta_ci_95_upper,
            "ac": self.ac,
            "g": self.g,
            "covariance_ac_g": self.covariance_ac_g.tolist(),
            "success": self.success,
            "message": self.message
        }


def compute_eotvos_parameter(solution: OrbitSolution) -> EotvosResult:
    """
    Compute the Eotvos parameter η = |a_c| / g and its 95% confidence interval.

    This function extracts the differential acceleration (a_c) and local gravity (g)
    from the joint orbit solution, then calculates η and propagates the uncertainty
    from the joint covariance matrix.

    Args:
        solution: The joint orbit solution object containing parameters and covariance.

    Returns:
        EotvosResult object containing η, its uncertainty, 95% CI, and diagnostic info.

    Raises:
        AnalysisError: If the solution is invalid or covariance extraction fails.
    """
    logger.info("Computing Eotvos parameter from joint solution...")

    try:
        # Extract parameters and covariance from the joint solution
        params = extract_joint_parameters(solution)
        ac = params['ac']
        g = params['g']
        cov_matrix = params['covariance']

        # Validate inputs
        if not isinstance(cov_matrix, np.ndarray):
            raise AnalysisError("Covariance matrix must be a numpy array.")

        if cov_matrix.shape != (2, 2):
            raise AnalysisError(
                f"Expected 2x2 covariance matrix for [ac, g], got shape {cov_matrix.shape}"
            )

        if g == 0:
            raise AnalysisError("Local gravity g is zero, cannot compute η.")

        # Compute η
        eta = abs(ac) / g
        logger.info(f"Computed η = {eta:.6e}")

        # Uncertainty propagation using the delta method
        # η = |ac| / g
        # For small uncertainties, the variance is approximated by:
        # Var(η) ≈ (∂η/∂ac)^2 * Var(ac) + (∂η/∂g)^2 * Var(g) + 2*(∂η/∂ac)*(∂η/∂g)*Cov(ac,g)

        # Partial derivatives evaluated at the solution
        # dη/dac = sign(ac) / g  (using sign to handle the absolute value)
        # dη/dg = -|ac| / g^2 = -η / g

        sign_ac = 1.0 if ac >= 0 else -1.0
        d_eta_d_ac = sign_ac / g
        d_eta_d_g = -eta / g

        # Extract variances and covariance from the matrix
        # Assuming cov_matrix[0,0] is Var(ac), cov_matrix[1,1] is Var(g), cov_matrix[0,1] is Cov(ac,g)
        var_ac = cov_matrix[0, 0]
        var_g = cov_matrix[1, 1]
        cov_ac_g = cov_matrix[0, 1]

        # Compute variance of η
        var_eta = (
            (d_eta_d_ac ** 2) * var_ac +
            (d_eta_d_g ** 2) * var_g +
            2 * d_eta_d_ac * d_eta_d_g * cov_ac_g
        )

        if var_eta < 0:
            # Numerical issue: clamp to zero if slightly negative
            logger.warning(f"Computed negative variance for η ({var_eta}), clamping to 0.")
            var_eta = 0.0

        std_eta = np.sqrt(var_eta)

        # Compute 95% Confidence Interval (using normal approximation, z=1.96)
        z_score = 1.96
        eta_ci_lower = eta - z_score * std_eta
        eta_ci_upper = eta + z_score * std_eta

        logger.info(f"η = {eta:.6e} ± {std_eta:.6e} (95% CI: [{eta_ci_lower:.6e}, {eta_ci_upper:.6e}])")

        return EotvosResult(
            eta=eta,
            eta_std=std_eta,
            eta_ci_95_lower=eta_ci_lower,
            eta_ci_95_upper=eta_ci_upper,
            ac=ac,
            g=g,
            covariance_ac_g=cov_matrix,
            success=True,
            message="Computation successful."
        )

    except KeyError as e:
        msg = f"Failed to extract required parameters from solution: {e}"
        logger.error(msg)
        raise AnalysisError(msg) from e
    except Exception as e:
        msg = f"Unexpected error during Eotvos computation: {e}"
        logger.error(msg)
        raise AnalysisError(msg) from e


def run_eotvos_analysis(solution: OrbitSolution, output_path: Optional[str] = None) -> EotvosResult:
    """
    Run the full Eotvos analysis pipeline.

    This is a convenience wrapper that computes the parameter and optionally
    saves the result to a file.

    Args:
        solution: The joint orbit solution.
        output_path: Optional path to save the result as JSON.

    Returns:
        EotvosResult object.
    """
    result = compute_eotvos_parameter(solution)

    if output_path:
        import json
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Eotvos result saved to {output_path}")

    return result
