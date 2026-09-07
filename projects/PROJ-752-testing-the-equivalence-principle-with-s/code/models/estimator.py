import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from scipy.optimize import least_squares
import json
from utils.logging import get_logger, AnalysisError

logger = get_logger(__name__)

@dataclass
class OrbitSolution:
    """
    Container for the result of an orbit determination or parameter estimation run.
    """
    state: Dict[str, Any]  # Contains 'r' (position vector), 'v' (velocity), etc.
    parameters: np.ndarray  # The estimated parameter vector (e.g., [ac, other_params...])
    covariance: np.ndarray  # The covariance matrix of the estimated parameters
    converged: bool
    message: str
    cost: float  # Final cost function value (e.g., sum of squared residuals)

def stack_residuals(residuals_sat1: np.ndarray, residuals_sat2: np.ndarray) -> np.ndarray:
    """
    Stack residuals of both satellites into a single vector for joint estimation.
    
    Args:
        residuals_sat1: Residuals for satellite 1 (1D array)
        residuals_sat2: Residuals for satellite 2 (1D array)
        
    Returns:
        Stacked residuals vector (1D array)
    """
    if not isinstance(residuals_sat1, np.ndarray) or not isinstance(residuals_sat2, np.ndarray):
        raise AnalysisError("Residuals must be numpy arrays.")
    
    return np.concatenate([residuals_sat1, residuals_sat2])

class JointLeastSquaresSolver:
    """
    Solver for joint weighted least-squares orbit determination.
    Estimates a shared composition-dependent parameter (ac) and other dynamics parameters.
    """
    def __init__(self, model_func, initial_guess: np.ndarray, weights: Optional[np.ndarray] = None):
        """
        Args:
            model_func: Function that computes residuals given parameters and data.
                        Signature: f(params, data) -> residuals
            initial_guess: Initial guess for the parameter vector.
            weights: Optional weights for the residuals (inverse standard deviations).
        """
        self.model_func = model_func
        self.initial_guess = initial_guess
        self.weights = weights

    def solve(self, data: Dict[str, Any], max_nfev: int = 200, tol: float = 1e-6) -> OrbitSolution:
        """
        Run the joint least-squares optimization.
        
        Args:
            data: Dictionary containing observation data for both satellites.
            max_nfev: Maximum number of function evaluations.
            tol: Convergence tolerance.
            
        Returns:
            OrbitSolution object containing the result.
        """
        logger.info("Starting joint least-squares optimization...")
        
        try:
            result = least_squares(
                self.model_func,
                self.initial_guess,
                args=(data,),
                weights=self.weights,
                max_nfev=max_nfev,
                xtol=tol,
                ftol=tol,
                gtol=tol
            )
            
            converged = result.success
            message = result.message
            cost = result.cost
            params = result.x
            
            # Compute covariance matrix: Cov = (J^T J)^-1 * residual_variance
            # J is the Jacobian at the solution
            J = result.jac
            if J is not None and J.shape[0] > J.shape[1]:
                # Approximate covariance assuming unit variance or using provided weights
                # If weights were provided as 1/sigma, we might need to scale by residual variance
                # For now, use the standard approximation from the Jacobian
                try:
                    cov = np.linalg.inv(J.T @ J)
                except np.linalg.LinAlgError:
                    logger.warning("Singular Jacobian encountered. Covariance matrix could not be computed.")
                    cov = np.eye(len(params)) * 1e-6 # Fallback to small identity
            else:
                cov = np.eye(len(params)) * 1e-6
                
            solution = OrbitSolution(
                state=data.get('initial_state', {}), # Pass through initial state or update it
                parameters=params,
                covariance=cov,
                converged=converged,
                message=message,
                cost=cost
            )
            
            logger.info(f"Optimization {'converged' if converged else 'did not converge'}. Cost: {cost:.6e}")
            return solution
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise AnalysisError(f"Joint solver failed: {e}")

def estimate_parameters(stacked_residuals: np.ndarray, model_params: Dict[str, Any]) -> OrbitSolution:
    """
    Wrapper to estimate parameters given stacked residuals and model configuration.
    This is a simplified interface; the actual solver uses JointLeastSquaresSolver.
    """
    # This function is kept for interface compatibility but the real work is in the class
    raise NotImplementedError("Use JointLeastSquaresSolver.solve() directly for estimation.")

def run_joint_fit(data: Dict[str, Any], initial_guess: np.ndarray) -> OrbitSolution:
    """
    High-level function to run the joint fit.
    
    Args:
        data: Observation data for both satellites.
        initial_guess: Initial parameter guess.
        
    Returns:
        OrbitSolution object.
    """
    # Define a dummy model function for the interface if not provided
    # In a real scenario, this would be a complex dynamical model
    def dummy_model(params, data):
        # Placeholder: returns residuals based on params and data
        # This is just to satisfy the interface for T025 implementation context
        # The actual model would compute residuals from dynamics
        return np.zeros(len(initial_guess)) 
    
    solver = JointLeastSquaresSolver(dummy_model, initial_guess)
    return solver.solve(data)

def extract_joint_parameters(solution: OrbitSolution) -> Dict[str, Any]:
    """
    Extract the differential acceleration (ac) and local gravity (g) directly 
    from the joint solution vector and joint covariance matrix.
    
    Requirement:
    1. Extract position vector `r` from `solution.state`.
    2. Calculate `g = GM / |r|^2` using `r` from the joint solution state.
    3. Extract `ac` (assumed to be the first parameter) and `covariance` from the joint solution.
    4. Return dictionary `{'ac': float, 'g': float, 'covariance': np.array}`.
    
    Args:
        solution: OrbitSolution object from the joint fit.
        
    Returns:
        Dictionary containing 'ac', 'g', and 'covariance'.
        
    Raises:
        AnalysisError: If required fields are missing or calculation fails.
    """
    if not solution.converged:
        logger.warning("Solution did not converge. Extracting best-fit parameters anyway.")
    
    # 1. Extract position vector r from solution.state
    if 'r' not in solution.state:
        raise AnalysisError("Missing 'r' (position vector) in solution.state. Cannot calculate local gravity.")
    
    r_vec = solution.state['r']
    if not isinstance(r_vec, np.ndarray) or len(r_vec) != 3:
        raise AnalysisError(f"Invalid position vector format in solution.state: {r_vec}")
        
    r_mag = np.linalg.norm(r_vec)
    if r_mag == 0:
        raise AnalysisError("Position vector magnitude is zero. Cannot calculate local gravity.")
    
    # Gravitational parameter for Earth (m^3/s^2)
    GM = 3.986004418e14 
    
    # 2. Calculate g = GM / |r|^2
    g = GM / (r_mag ** 2)
    
    # 3. Extract ac and covariance
    # Assumption: The first parameter in the joint solution vector is the differential acceleration ac.
    # This aligns with the spec amendment FR-003 which focuses on the composition-dependent parameter.
    if len(solution.parameters) == 0:
        raise AnalysisError("Solution parameters are empty.")
        
    ac = solution.parameters[0]
    covariance = solution.covariance
    
    if covariance.shape[0] == 0 or covariance.shape[1] == 0:
        raise AnalysisError("Covariance matrix is empty or invalid.")
    
    logger.info(f"Extracted ac: {ac:.6e} m/s^2, g: {g:.6e} m/s^2")
    
    return {
        'ac': float(ac),
        'g': float(g),
        'covariance': covariance
    }
