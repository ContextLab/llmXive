import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field
import json
import os
import sys
import logging

# Add project root to path to ensure imports work when running as script
if "code" not in sys.path:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from utils.logging import get_logger, log_progress, log_error, AnalysisError
from config import get_config

logger = get_logger(__name__)

@dataclass
class EotvosResult:
    """
    Container for the calculated Eötvös parameter and associated statistics.
    """
    eta: float
    eta_std: float
    eta_95_ci_lower: float
    eta_95_ci_upper: float
    ac: float
    g: float
    ac_std: float
    covariance_matrix: np.ndarray
    source_file: str
    timestamp: str = field(default_factory=lambda: "N/A")

    def to_dict(self) -> Dict:
        return {
            "eta": self.eta,
            "eta_std": self.eta_std,
            "eta_95_ci_lower": self.eta_95_ci_lower,
            "eta_95_ci_upper": self.eta_95_ci_upper,
            "ac": self.ac,
            "g": self.g,
            "ac_std": self.ac_std,
            "covariance_matrix": self.covariance_matrix.tolist(),
            "source_file": self.source_file,
            "timestamp": self.timestamp
        }

def compute_eotvos_parameter(params: Dict) -> EotvosResult:
    """
    Compute the Eötvös parameter ($\eta$) and its 95% Confidence Interval.
    
    This function consumes the output dictionary from T025 (extract_joint_parameters).
    
    Formula: $\eta = |a_c| / g$
    
    Error Propagation (First-order Taylor approximation):
    $\sigma_\eta \approx \frac{1}{g} \sigma_{a_c}$
    (Assuming $g$ is a deterministic constant derived from the state vector, 
    and $a_c$ is the stochastic parameter from the covariance matrix).
    
    Args:
        params (Dict): Dictionary containing 'ac', 'g', and 'covariance' (2D numpy array).
                       Expected keys: 'ac', 'g', 'covariance'.
                       'ac' is the differential acceleration parameter.
                       'g' is the local gravity magnitude.
                       'covariance' is the joint covariance matrix where the first element
                       (index 0,0) corresponds to the variance of 'ac'.
    
    Returns:
        EotvosResult: Object containing the calculated eta, standard deviation, and CI.
    
    Raises:
        AnalysisError: If input parameters are missing, invalid, or non-converged.
    """
    log_progress(logger, "Computing Eötvös parameter from joint solution...")
    
    required_keys = ['ac', 'g', 'covariance']
    for key in required_keys:
        if key not in params:
            raise AnalysisError(f"Missing required key '{key}' in input parameters. "
                                f"Ensure T025 (extract_joint_parameters) has populated the dictionary correctly.")
    
    ac = params['ac']
    g = params['g']
    cov_matrix = params['covariance']
    
    if not isinstance(cov_matrix, np.ndarray):
        cov_matrix = np.array(cov_matrix)
    
    if cov_matrix.ndim != 2 or cov_matrix.shape[0] != cov_matrix.shape[1]:
        raise AnalysisError(f"Covariance matrix must be a square 2D array. Got shape: {cov_matrix.shape}")
    
    if g <= 0:
        raise AnalysisError(f"Local gravity 'g' must be positive. Got: {g}")
    
    # Extract variance of ac (assumed to be the first parameter in the joint vector)
    # If the joint solution has more parameters, ac is at index 0 based on T025 logic
    ac_variance = cov_matrix[0, 0]
    
    if ac_variance < 0:
        raise AnalysisError(f"Negative variance detected for ac: {ac_variance}. "
                            "This indicates a non-positive-definite covariance matrix or numerical instability.")
    
    ac_std = np.sqrt(ac_variance)
    
    # Calculate eta = |ac| / g
    eta = abs(ac) / g
    
    # Calculate standard deviation of eta using error propagation
    # sigma_eta = (1/g) * sigma_ac
    eta_std = ac_std / g
    
    # Calculate 95% Confidence Interval
    # For a normal distribution, 95% CI is approx mean +/- 1.96 * std
    z_score_95 = 1.96
    eta_95_ci_lower = eta - (z_score_95 * eta_std)
    eta_95_ci_upper = eta + (z_score_95 * eta_std)
    
    result = EotvosResult(
        eta=eta,
        eta_std=eta_std,
        eta_95_ci_lower=eta_95_ci_lower,
        eta_95_ci_upper=eta_95_ci_upper,
        ac=ac,
        g=g,
        ac_std=ac_std,
        covariance_matrix=cov_matrix,
        source_file=params.get('source_file', 'unknown')
    )
    
    log_progress(logger, f"Calculated eta: {eta:.4e} +/- {eta_std:.4e} (95% CI: [{eta_95_ci_lower:.4e}, {eta_95_ci_upper:.4e}])")
    
    return result

def run_eotvos_analysis(input_file: str, output_file: str) -> EotvosResult:
    """
    Main entry point to run the Eötvös analysis on a saved joint solution.
    
    Args:
        input_file (str): Path to the JSON file containing the output of T025 
                          (extract_joint_parameters).
        output_file (str): Path where the EotvosResult JSON will be saved.
    
    Returns:
        EotvosResult: The computed result object.
    
    Raises:
        FileNotFoundError: If input_file does not exist.
        json.JSONDecodeError: If input_file is not valid JSON.
        AnalysisError: If computation fails.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Loading joint parameters from {input_file}")
    with open(input_file, 'r') as f:
        params = json.load(f)
    
    # Ensure covariance is loaded as numpy array
    if 'covariance' in params and isinstance(params['covariance'], list):
        params['covariance'] = np.array(params['covariance'])
    
    result = compute_eotvos_parameter(params)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    logger.info(f"Saving Eötvös result to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    return result

def main():
    """
    CLI entry point for T026.
    Expects paths to the joint solution parameters and output file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute Eötvös parameter from joint orbit solution.")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to the JSON file with joint parameters (from T025).")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to save the Eötvös result JSON.")
    
    args = parser.parse_args()
    
    try:
        result = run_eotvos_analysis(args.input, args.output)
        print(f"Analysis complete. Result saved to: {args.output}")
        print(f"Eötvös Parameter (η): {result.eta:.6e}")
        print(f"95% CI: [{result.eta_95_ci_lower:.6e}, {result.eta_95_ci_upper:.6e}]")
    except Exception as e:
        log_error(logger, f"Failed to compute Eötvös parameter: {e}")
        raise

if __name__ == "__main__":
    main()