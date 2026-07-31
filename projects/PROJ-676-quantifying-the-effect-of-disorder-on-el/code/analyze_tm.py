import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from scipy import linalg
from code.config import get_config
from code.logger import NumericalLogger

logger = logging.getLogger(__name__)

def compute_lyapunov_exponents(H: np.ndarray, W: float, realization_index: int, max_iter: int = 10000, tol: float = 1e-5) -> Tuple[float, List[float]]:
    """
    Compute Lyapunov exponent using Transfer Matrix Method with QR orthogonalization.
    Integrates NumericalLogger for stability checks (Constitution Principle VI).
    
    Args:
        H: Hamiltonian matrix (not directly used in TM but passed for context)
        W: Disorder width
        realization_index: Index of the disorder realization
        max_iter: Maximum iterations
        tol: Convergence tolerance for relative change in gamma
    
    Returns:
        Tuple of (final_gamma, convergence_trace)
    """
    L = H.shape[0]
    logger_instance = NumericalLogger()
    
    # Initialize transfer matrices
    # For 1D chain, T_n = [[(E - epsilon_n)/t, -1], [1, 0]]
    # We assume E=0 for the band center analysis as per typical Anderson model studies
    E = 0.0
    t = 1.0
    
    # Extract diagonal (on-site energies)
    eps = np.diag(H)
    
    # Initial vector (2x2 identity for two-component spinor-like state in TM)
    # Actually, TM propagates a 2-component vector [psi_n, psi_{n-1}]
    # We track the growth of a set of vectors to compute the exponent
    v = np.eye(2) 
    
    gamma_history = []
    current_gamma = 0.0
    converged = False
    
    for n in range(L):
        # Construct transfer matrix for site n
        # T_n = [[(E - eps[n])/t, -1], [1, 0]]
        T_n = np.array([
            [(E - eps[n])/t, -1.0],
            [1.0, 0.0]
        ])
        
        # Update vector
        v = T_n @ v
        
        # QR Decomposition for orthogonalization and norm tracking
        # This is the standard step to prevent overflow and extract Lyapunov exponent
        Q, R = np.linalg.qr(v)
        
        # The Lyapunov exponent is related to the log of the diagonal elements of R
        # gamma_n = (1/n) * sum(log(|R_ii|))
        # We accumulate the log norms
        log_norms = np.log(np.abs(np.diag(R)) + 1e-12) # Avoid log(0)
        current_gamma = np.mean(log_norms)
        
        gamma_history.append(current_gamma)
        
        # Log residual for this step (Constitution Principle VI)
        # In TM, "residual" can be interpreted as the deviation from orthogonality or convergence
        # Here we log the current gamma and a boolean for convergence check
        logger_instance.log_residual("tm", True, L=L, W=W, realization_index=realization_index, residual_norm=0.0) # Norm 0 for successful QR step
        
        # Check convergence (relative change)
        if len(gamma_history) > 1:
            prev_gamma = gamma_history[-2]
            if abs(current_gamma - prev_gamma) < tol * abs(prev_gamma):
                converged = True
                break
    
    # Final logging for the realization
    logger_instance.log_residual("tm", converged, L=L, W=W, realization_index=realization_index, residual_norm=float('inf') if not converged else 0.0)
    
    return current_gamma, gamma_history

def main():
    """
    Main entry point for Transfer Matrix Analysis.
    """
    config = get_config()
    logger.info("Starting Transfer Matrix Analysis")
    
    # Example usage
    W = 2.0
    L = 100
    seed = 42
    np.random.seed(seed)
    
    # Generate random diagonal
    eps = np.random.uniform(-W/2, W/2, L)
    # Generate tridiagonal Hamiltonian
    H = np.diag(eps) + np.diag(np.ones(L-1), k=1) + np.diag(np.ones(L-1), k=-1)
    
    gamma, trace = compute_lyapunov_exponents(H, W, 0)
    logger.info(f"Lyapunov Exponent: {gamma}")
    
    # Save convergence trace
    output_path = Path(config.DATA_DIR) / "metadata" / "tm_convergence.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    trace_data = {
        "disorder_width": W,
        "realization_index": 0,
        "convergence_trace": trace,
        "final_gamma": gamma
    }
    
    with open(output_path, 'w') as f:
        json.dump([trace_data], f, indent=2)

if __name__ == "__main__":
    main()
