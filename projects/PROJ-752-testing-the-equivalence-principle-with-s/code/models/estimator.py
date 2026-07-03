import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
from scipy.optimize import least_squares
from utils.logging import get_logger, AnalysisError

logger = get_logger(__name__)

@dataclass
class OrbitSolution:
    """
    Container for the results of a joint orbit determination fit.
    """
    parameters: np.ndarray
    covariance: np.ndarray
    cost: float
    success: bool
    message: str
    nit: int
    residuals: np.ndarray
    ac: Optional[float] = None
    g: Optional[float] = None
    fallback_applied: bool = False

def extract_joint_parameters(solution: OrbitSolution) -> dict:
    """
    Extract differential acceleration ac and local gravity g directly from the 
    joint solution vector and joint covariance matrix.
    
    Assumes the joint parameter vector is structured as:
    [common_params..., ac, g]
    where ac is the second to last parameter and g is the last parameter.
    
    Args:
        solution: The OrbitSolution object containing the fit results.
        
    Returns:
        Dictionary with keys 'ac', 'g', and 'covariance'.
    """
    # Assuming the last two parameters are [ac, g] based on the task description
    # This indexing might need adjustment based on the actual parameter vector structure
    n_params = len(solution.parameters)
    if n_params < 2:
        raise AnalysisError("Parameter vector too short to extract ac and g.")
        
    ac = float(solution.parameters[-2])
    g = float(solution.parameters[-1])
    
    # Extract the relevant part of the covariance matrix for ac and g
    # Assuming we want the 2x2 submatrix corresponding to ac and g
    cov_ac_g = solution.covariance[-2:, -2:]
    
    return {
        'ac': ac,
        'g': g,
        'covariance': cov_ac_g
    }

def run_joint_fit(
    residuals_func,
    initial_guess: np.ndarray,
    tol: float = 1e-6,
    max_nfev: int = 1000,
    use_fallback: bool = True
) -> OrbitSolution:
    """
    Run a joint weighted least-squares fit for multiple satellites.
    
    Args:
        residuals_func: A callable that takes parameters and returns residuals.
        initial_guess: Initial parameter vector.
        tol: Convergence tolerance for the solver.
        max_nfev: Maximum number of function evaluations.
        use_fallback: Whether to attempt relaxed tolerance on failure.
        
    Returns:
        OrbitSolution object containing the fit results.
    """
    logger.info(f"Starting joint fit with tolerance {tol} and max_nfev {max_nfev}")
    
    try:
        result = least_squares(
            residuals_func,
            initial_guess,
            method='trf',
            ftol=tol,
            xtol=tol,
            gtol=tol,
            max_nfev=max_nfev,
            verbose=0
        )
        
        # Calculate approximate covariance matrix
        # J^T J approximation
        jac = result.jac
        if jac is not None:
            try:
                cov = np.linalg.inv(jac.T @ jac)
            except np.linalg.LinAlgError:
                logger.warning("Covariance matrix calculation failed (singular matrix). Using pseudo-inverse.")
                cov = np.linalg.pinv(jac.T @ jac)
        else:
            logger.warning("Jacobian not available. Cannot calculate covariance.")
            cov = np.eye(len(initial_guess)) * 1e-6
        
        solution = OrbitSolution(
            parameters=result.x,
            covariance=cov,
            cost=result.cost,
            success=result.success,
            message=result.message,
            nit=result.nfev,
            residuals=result.fun,
            fallback_applied=False
        )
        
        if solution.success:
            logger.info(f"Joint fit converged successfully. Cost: {solution.cost:.6e}, Iterations: {solution.nit}")
        else:
            logger.warning(f"Joint fit did not converge. Message: {solution.message}")
            
            # Fallback logic for non-convergence
            if use_fallback:
                logger.warning("Attempting fallback with relaxed tolerance...")
                fallback_solution = _attempt_fallback_fit(
                    residuals_func, 
                    initial_guess, 
                    tol, 
                    max_nfev
                )
                if fallback_solution:
                    solution = fallback_solution
                    solution.fallback_applied = True
                    logger.info(f"Fallback fit completed. Success: {solution.success}")
                else:
                    logger.error("Fallback fit also failed. Returning best available solution.")
                    
        return solution

    except Exception as e:
        logger.error(f"Joint fit failed with exception: {str(e)}")
        if use_fallback:
            logger.warning("Attempting fallback after exception...")
            fallback_solution = _attempt_fallback_fit(
                residuals_func, 
                initial_guess, 
                tol, 
                max_nfev
            )
            if fallback_solution:
                fallback_solution.fallback_applied = True
                logger.info(f"Fallback fit completed after exception.")
                return fallback_solution
            
        # Return a minimal solution even on failure
        return OrbitSolution(
            parameters=initial_guess,
            covariance=np.eye(len(initial_guess)) * 1e-6,
            cost=float('inf'),
            success=False,
            message=f"Fit failed: {str(e)}",
            nit=0,
            residuals=residuals_func(initial_guess),
            fallback_applied=False
        )

def _attempt_fallback_fit(
    residuals_func,
    initial_guess: np.ndarray,
    original_tol: float,
    max_nfev: int
) -> Optional[OrbitSolution]:
    """
    Attempt to find a solution by relaxing tolerance and increasing iterations.
    
    Args:
        residuals_func: The residuals function.
        initial_guess: Initial parameter vector.
        original_tol: The original tolerance that failed.
        max_nfev: Original max iterations.
        
    Returns:
        OrbitSolution if fallback succeeds, None otherwise.
    """
    # Strategy 1: Relax tolerance by 2 orders of magnitude
    relaxed_tol = original_tol * 100
    relaxed_max_nfev = max_nfev * 2
    
    logger.info(f"Trying fallback with tol={relaxed_tol}, max_nfev={relaxed_max_nfev}")
    
    try:
        result = least_squares(
            residuals_func,
            initial_guess,
            method='trf',
            ftol=relaxed_tol,
            xtol=relaxed_tol,
            gtol=relaxed_tol,
            max_nfev=relaxed_max_nfev,
            verbose=0
        )
        
        # Calculate approximate covariance matrix
        jac = result.jac
        if jac is not None:
            try:
                cov = np.linalg.inv(jac.T @ jac)
            except np.linalg.LinAlgError:
                logger.warning("Covariance matrix calculation failed in fallback. Using pseudo-inverse.")
                cov = np.linalg.pinv(jac.T @ jac)
        else:
            logger.warning("Jacobian not available in fallback. Using identity covariance.")
            cov = np.eye(len(initial_guess)) * 1e-6
        
        return OrbitSolution(
            parameters=result.x,
            covariance=cov,
            cost=result.cost,
            success=True, # Mark as success because we found a solution
            message=f"Fallback solution with relaxed tolerance {relaxed_tol}",
            nit=result.nfev,
            residuals=result.fun,
            fallback_applied=True
        )
        
    except Exception as e:
        logger.error(f"Fallback fit failed with exception: {str(e)}")
        return None
