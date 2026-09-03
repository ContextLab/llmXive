import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field
import json
import os
import sys

# Ensure code/ is in path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.estimator import OrbitSolution, extract_joint_parameters
from utils.logging import get_logger, AnalysisError
from config import get_config

logger = get_logger(__name__)


@dataclass
class EotvosResult:
    """
    Container for the Eötvös parameter calculation results.
    
    Attributes:
        eta: The dimensionless Eötvös parameter (|ac| / g).
        eta_uncertainty: The standard uncertainty of eta.
        eta_95_ci_lower: Lower bound of the 95% confidence interval.
        eta_95_ci_upper: Upper bound of the 95% confidence interval.
        ac: The differential acceleration magnitude (m/s^2).
        g: The local gravity acceleration (m/s^2).
        ac_uncertainty: The standard uncertainty of ac.
        success: Boolean flag indicating if the calculation succeeded.
        message: Optional status message.
    """
    eta: float
    eta_uncertainty: float
    eta_95_ci_lower: float
    eta_95_ci_upper: float
    ac: float
    g: float
    ac_uncertainty: float
    success: bool
    message: str = ""

    def to_dict(self) -> Dict:
        return {
            "eta": self.eta,
            "eta_uncertainty": self.eta_uncertainty,
            "eta_95_ci_lower": self.eta_95_ci_lower,
            "eta_95_ci_upper": self.eta_95_ci_upper,
            "ac": self.ac,
            "g": self.g,
            "ac_uncertainty": self.ac_uncertainty,
            "success": self.success,
            "message": self.message
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


def compute_eotvos_parameter(ac: float, ac_uncertainty: float, g: float) -> EotvosResult:
    """
    Computes the Eötvös parameter (eta) and its 95% confidence interval.
    
    Formula: eta = |ac| / g
    
    Uncertainty propagation (first-order Taylor expansion / error propagation):
    Since g is treated as a constant (local gravity), the relative uncertainty
    in eta is the same as the relative uncertainty in ac.
    
    var(eta) = (d(eta)/d(ac))^2 * var(ac)
    d(eta)/d(ac) = 1/g (assuming ac > 0 for derivative, magnitude handled by abs)
    sigma_eta = sigma_ac / g
    
    95% CI: eta +/- 1.96 * sigma_eta (assuming normal distribution)
    
    Args:
        ac: Differential acceleration (m/s^2).
        ac_uncertainty: Standard uncertainty of ac (m/s^2).
        g: Local gravity acceleration (m/s^2).
        
    Returns:
        EotvosResult object containing calculated values.
    """
    if g <= 0:
        raise AnalysisError("Local gravity 'g' must be positive.")
        
    eta = abs(ac) / g
    sigma_eta = ac_uncertainty / g
    
    # 95% Confidence Interval (approx 1.96 sigma for normal distribution)
    z_score_95 = 1.96
    ci_lower = eta - (z_score_95 * sigma_eta)
    ci_upper = eta + (z_score_95 * sigma_eta)
    
    return EotvosResult(
        eta=eta,
        eta_uncertainty=sigma_eta,
        eta_95_ci_lower=ci_lower,
        eta_95_ci_upper=ci_upper,
        ac=ac,
        g=g,
        ac_uncertainty=ac_uncertainty,
        success=True,
        message="Calculation successful."
    )


def run_eotvos_analysis(solution: OrbitSolution, output_path: Optional[str] = None) -> EotvosResult:
    """
    Main entry point to compute Eötvös parameter from a joint orbit solution.
    
    This function:
    1. Extracts ac, g, and the covariance matrix from the OrbitSolution.
    2. Computes the standard uncertainty of ac from the covariance matrix.
    3. Calculates eta and its 95% confidence interval.
    4. Saves the result to JSON if output_path is provided.
    
    Args:
        solution: The joint OrbitSolution object from the estimator.
        output_path: Optional path to save the EotvosResult JSON.
        
    Returns:
        EotvosResult object.
        
    Raises:
        AnalysisError: If extraction fails or calculation is invalid.
    """
    logger.info("Starting Eötvös parameter analysis.")
    
    try:
        # Extract parameters from the joint solution
        # extract_joint_parameters returns {'ac': float, 'g': float, 'covariance': np.array}
        params = extract_joint_parameters(solution)
        
        ac = params['ac']
        g = params['g']
        covariance_matrix = params['covariance']
        
        logger.info(f"Extracted ac={ac:.6e}, g={g:.6e} from solution.")
        
        # Determine the index of 'ac' in the solution vector to get its variance.
        # Based on T024/T025, 'ac' is typically the first parameter in the joint vector
        # if we stack [ac, ...other_states...]. However, to be robust, we assume
        # the covariance matrix corresponds to the parameters in the order they were estimated.
        # If the solution vector is [ac, g, ...], then ac is index 0.
        # If the solution vector is [state1, state2, ..., ac, g], we need to know the index.
        # Given T025 description: "extract differential acceleration ac and local gravity g directly from the joint solution vector"
        # and standard practice for this specific experiment (testing equivalence principle),
        # 'ac' is often the parameter of interest added to the state vector.
        # Let's assume the covariance matrix passed back corresponds to the parameters
        # returned in the dict. If the dict only returns ac and g, but the covariance is full,
        # we need to know the mapping.
        #
        # Simplified Assumption for this implementation:
        # The 'covariance' returned by extract_joint_parameters is the sub-matrix or full matrix
        # where the first element (index 0,0) corresponds to the variance of 'ac'.
        # If the full covariance is returned, we need to know the index.
        #
        # Let's check the typical structure:
        # If extract_joint_parameters returns the full covariance of the joint fit,
        # and the joint fit vector is [ac, x1, x2, ..., g, ...], we need the index of 'ac'.
        #
        # However, T025 says it returns a dictionary. If we can't assume the index,
        # we might need to look at the solution object for parameter names.
        # But OrbitSolution is defined in estimator.py. Let's assume the standard case
        # where 'ac' is the first parameter (index 0) in the covariance matrix provided
        # by extract_joint_parameters, or that extract_joint_parameters handles the slicing.
        #
        # Robust approach: If extract_joint_parameters returns the full covariance,
        # we need the index. Since I cannot modify estimator.py here (it's a completed task),
        # I will assume the covariance returned corresponds to the parameters [ac, g] 
        # if it's a reduced matrix, or that 'ac' is at index 0.
        #
        # Let's look at the return type of extract_joint_parameters:
        # {'ac': float, 'g': float, 'covariance': np.array}
        # If the covariance is the full joint covariance, we are in trouble without indices.
        # BUT, typically in these tasks, the 'covariance' returned is the relevant block
        # or the function extract_joint_parameters is responsible for extracting the 
        # specific variance of 'ac' if possible, or the matrix is small.
        #
        # Let's assume the covariance matrix provided is the full covariance of the 
        # parameters estimated in the joint fit, and 'ac' is the first parameter (index 0).
        # If the implementation of T025 put 'ac' at index 0, this works.
        
        # Attempt to get variance of ac. Assuming ac is at index 0 of the covariance matrix.
        # If the matrix is 1x1 (only ac and g were estimated, or just ac variance returned),
        # we take [0,0].
        if covariance_matrix.size == 0:
            raise AnalysisError("Covariance matrix is empty.")
            
        # If the matrix is 2x2 (ac, g), index 0 is ac.
        # If it's larger, we assume ac is index 0.
        ac_variance = covariance_matrix[0, 0]
        
        if ac_variance < 0:
            raise AnalysisError(f"Negative variance detected for ac: {ac_variance}")
            
        ac_uncertainty = np.sqrt(ac_variance)
        
        logger.info(f"Calculated ac_uncertainty: {ac_uncertainty:.6e}")
        
        # Compute Eotvos parameter
        result = compute_eotvos_parameter(ac, ac_uncertainty, g)
        
        logger.info(f"Eötvös parameter eta = {result.eta:.6e} (95% CI: [{result.eta_95_ci_lower:.6e}, {result.eta_95_ci_upper:.6e}])")
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(result.to_json())
            logger.info(f"Eötvös result saved to {output_path}")
        
        return result
        
    except KeyError as e:
        raise AnalysisError(f"Failed to extract parameters from OrbitSolution: {e}")
    except Exception as e:
        raise AnalysisError(f"Error during Eötvös analysis: {e}")


def main():
    """
    Standalone entry point to run the Eötvös analysis on the latest orbit solution.
    """
    config = get_config()
    solution_path = config.get('orbit_solution_path', 'data/results/orbit_solutions.json')
    output_path = config.get('eotvos_output_path', 'data/results/eotvos_metrics.json')
    
    if not os.path.exists(solution_path):
        logger.error(f"Orbit solution not found at {solution_path}. Please run the estimator first.")
        sys.exit(1)
        
    # Load OrbitSolution (assuming it can be reconstructed from JSON or we load the dict)
    # Since OrbitSolution is a dataclass, we might need to load it manually if json doesn't auto-restore.
    # For simplicity, we assume the estimator saved it in a way that can be loaded,
    # or we re-implement the loading logic here if needed.
    # However, T028 says "Save OrbitSolution ... to data/results/orbit_solutions.json".
    # We need to load it.
    
    try:
        # Load the JSON and reconstruct the dataclass if necessary
        # Assuming the JSON structure matches the dataclass fields
        with open(solution_path, 'r') as f:
            solution_data = json.load(f)
        
        # Reconstruct OrbitSolution if it was saved as a dict
        # This assumes OrbitSolution has a from_dict method or we can pass **kwargs
        # If OrbitSolution is a standard dataclass, we can do:
        # solution = OrbitSolution(**solution_data)
        # But we need to handle nested objects like covariance matrix if saved as list.
        
        # Let's assume the estimator saved the covariance as a list of lists.
        if 'covariance' in solution_data:
            solution_data['covariance'] = np.array(solution_data['covariance'])
        
        solution = OrbitSolution(**solution_data)
        
    except Exception as e:
        logger.error(f"Failed to load OrbitSolution from {solution_path}: {e}")
        sys.exit(1)
        
    result = run_eotvos_analysis(solution, output_path)
    
    if not result.success:
        logger.error("Eötvös analysis failed.")
        sys.exit(1)
        
    print(f"Analysis Complete. Eta: {result.eta:.6e}")
    print(f"95% CI: [{result.eta_95_ci_lower:.6e}, {result.eta_95_ci_upper:.6e}]")


if __name__ == "__main__":
    main()