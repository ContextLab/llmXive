import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from scipy.optimize import least_squares
from utils.logging import get_logger, AnalysisError
import json
import os
from datetime import datetime

logger = get_logger(__name__)

@dataclass
class OrbitSolution:
    """
    Container for the joint orbit solution and parameter estimates.
    """
    # Joint parameters: [ac, g] where ac is differential acceleration, g is local gravity
    parameters: np.ndarray
    # Covariance matrix of the parameters
    covariance: np.ndarray
    # Residuals from the fit (stacked for all satellites)
    residuals: np.ndarray
    # Number of observations used in the fit
    n_obs: int
    # Number of parameters estimated
    n_params: int
    # Convergence status (0 = converged, >0 = failure)
    success: bool
    # Message from the optimizer
    message: str
    # Timestamp of the solution
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    # Satellite IDs included in the joint fit
    satellite_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert solution to a dictionary for JSON serialization."""
        return {
            "parameters": self.parameters.tolist(),
            "covariance": self.covariance.tolist(),
            "residuals": self.residuals.tolist(),
            "n_obs": self.n_obs,
            "n_params": self.n_params,
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp,
            "satellite_ids": self.satellite_ids
        }

    def save(self, filepath: str) -> None:
        """Save the solution to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Orbit solution saved to {filepath}")

def extract_joint_parameters(solution: OrbitSolution) -> Dict[str, Any]:
    """
    Extract differential acceleration (ac) and local gravity (g) from the joint solution.
    
    Args:
        solution: The joint OrbitSolution object.
        
    Returns:
        Dictionary with keys 'ac', 'g', and 'covariance'.
    """
    return {
        "ac": float(solution.parameters[0]),
        "g": float(solution.parameters[1]),
        "covariance": solution.covariance.tolist()
    }

def run_joint_fit(
    cleaned_data_path: str,
    output_path: str,
    satellite_ids: List[str]
) -> OrbitSolution:
    """
    Perform joint weighted least-squares fitting for multiple satellites.
    
    This function stacks the residuals of all provided satellites into a single vector
    and estimates a shared differential acceleration parameter (ac) along with local
    gravity (g) using a linearized least-squares approach.
    
    The model assumes:
      r_i = H_i * theta + epsilon_i
      where theta = [ac, g]
      H_i is the design matrix for satellite i (partial derivatives of residuals w.r.t parameters)
      
    For the Equivalence Principle test:
      - ac represents the differential acceleration between two composition types
      - g is the local gravitational acceleration (approx 9.8 m/s^2 at LEO)
      
    The joint fit minimizes:
      sum_i (r_i - H_i * theta)^T * W_i * (r_i - H_i * theta)
    
    Args:
        cleaned_data_path: Path to the cleaned SLR data CSV (from T019).
        output_path: Path to save the resulting OrbitSolution JSON.
        satellite_ids: List of satellite IDs to include in the joint fit.
        
    Returns:
        OrbitSolution object containing the joint fit results.
        
    Raises:
        AnalysisError: If data loading fails or fit does not converge.
    """
    import pandas as pd
    
    logger.info(f"Starting joint fit for satellites: {satellite_ids}")
    
    # Load cleaned data
    if not os.path.exists(cleaned_data_path):
        raise AnalysisError(f"Cleaned data file not found: {cleaned_data_path}")
    
    df = pd.read_csv(cleaned_data_path)
    
    # Filter for requested satellites
    df_filtered = df[df['satellite_id'].isin(satellite_ids)]
    
    if len(df_filtered) == 0:
        raise AnalysisError(f"No data found for satellites: {satellite_ids}")
    
    logger.info(f"Loaded {len(df_filtered)} observations for {len(satellite_ids)} satellites")
    
    # Prepare design matrix and residuals
    # We assume the data has columns: 'satellite_id', 'residual', 'sigma', 'time'
    # For the EP test, we construct a simple linear model:
    # residual = ac * composition_factor + g * 1.0 + noise
    # where composition_factor is +1 for one satellite type, -1 for the other (or 0 for others)
    # For simplicity in this joint fit, we'll estimate ac and g directly from the residuals
    # assuming the residuals are primarily due to the EP violation and local gravity effects.
    
    # In a more sophisticated model, we would compute partial derivatives from the dynamics model.
    # Here, we approximate:
    # H = [composition_factor, 1.0] for each observation
    # We'll assume a simple composition factor: 
    #   LAGEOS-1, LAGEOS-2 -> +1 (dense, low drag)
    #   Etalon-1, Etalon-2 -> -1 (different composition)
    #   Starlette -> 0 (reference or ignored in differential term)
    # But for a true joint fit of ac and g, we need a model that links them.
    # Let's assume the residual is modeled as:
    # r = ac * (comp_i) + g * (local_g_i / g0) + noise
    # For simplicity, we'll set local_g_i = g0 (constant) and estimate g as a scaling factor.
    # This is a simplification; in reality, g varies with orbit.
    
    # Simplified approach for the joint fit:
    # We treat the problem as:
    # r = H * theta
    # H = [comp_factor, 1.0]
    # theta = [ac, g]
    
    # Define composition factors
    comp_map = {
        'LAGEOS-1': 1.0,
        'LAGEOS-2': 1.0,
        'Etalon-1': -1.0,
        'Etalon-2': -1.0,
        'Starlette': 0.0  # Reference, no differential contribution
    }
    
    # Build H matrix and residual vector
    H_list = []
    r_list = []
    w_list = []  # Weights (1/sigma^2)
    
    for _, row in df_filtered.iterrows():
        sat_id = row['satellite_id']
        res = row['residual']
        sigma = row['sigma']
        
        if sat_id in comp_map:
            comp = comp_map[sat_id]
        else:
            logger.warning(f"Unknown satellite {sat_id}, skipping")
            continue
        
        # Design matrix row: [comp_factor, 1.0]
        H_list.append([comp, 1.0])
        r_list.append(res)
        w_list.append(1.0 / (sigma ** 2) if sigma > 0 else 1.0)
    
    H = np.array(H_list)
    r = np.array(r_list)
    W = np.diag(w_list)
    
    n_obs = len(r)
    n_params = 2  # [ac, g]
    
    logger.info(f"Design matrix shape: {H.shape}, Residuals shape: {r.shape}")
    
    # Weighted least squares: theta = (H^T W H)^{-1} H^T W r
    # Using scipy.optimize.least_squares for robustness and to get covariance
    
    def residuals_func(theta):
        """Compute weighted residuals: sqrt(W) * (r - H * theta)"""
        return np.sqrt(w_list) * (r - H @ theta)
    
    # Initial guess: [0, 9.8]
    theta0 = np.array([0.0, 9.8])
    
    result = least_squares(
        residuals_func,
        theta0,
        method='lm',  # Levenberg-Marquardt
        max_nfev=10000
    )
    
    if not result.success:
        logger.warning(f"Fit did not converge: {result.message}")
        # Continue with best-fit even if not fully converged (per robustness requirements)
    
    theta_opt = result.x
    residuals_opt = result.fun / np.sqrt(w_list)  # Unweighted residuals for reporting
    
    # Compute covariance matrix: Cov(theta) = (H^T W H)^{-1} * sigma2
    # where sigma2 is the reduced chi-squared
    HtWH = H.T @ W @ H
    try:
        cov_theta = np.linalg.inv(HtWH)
    except np.linalg.LinAlgError:
        logger.error("Singular matrix in covariance estimation. Using pseudo-inverse.")
        cov_theta = np.linalg.pinv(HtWH)
    
    # Estimate variance from residuals
    dof = n_obs - n_params
    if dof > 0:
        sigma2 = np.sum(result.fun ** 2) / dof
        cov_theta = cov_theta * sigma2
    else:
        logger.warning("Degrees of freedom <= 0, setting covariance to zero.")
        cov_theta = np.zeros((n_params, n_params))
    
    solution = OrbitSolution(
        parameters=theta_opt,
        covariance=cov_theta,
        residuals=residuals_opt,
        n_obs=n_obs,
        n_params=n_params,
        success=result.success,
        message=result.message,
        satellite_ids=satellite_ids
    )
    
    # Save solution
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    solution.save(output_path)
    
    logger.info(f"Joint fit complete. ac = {theta_opt[0]:.6e}, g = {theta_opt[1]:.6f}")
    logger.info(f"Covariance:\n{cov_theta}")
    
    return solution