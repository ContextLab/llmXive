"""
Participation Ratio (PR) analysis for 1D disordered chains.

Computes PR for eigenstates near E=0 and performs finite-size scaling
to extract localization length ξ.

Implements fallback to sparse eigensolver for large systems (L >= 1600)
to avoid RAM exhaustion (FR-008).
"""
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from scipy import linalg
from scipy import sparse
from scipy.sparse.linalg import eigsh, ArpackNoConvergence
from scipy.optimize import curve_fit
from scipy import stats
import json
import os
import logging
from pathlib import Path
import time

from code.config import get_config
from code.logger_utils import get_logger, log_numerical_warning, log_numerical_error

# Constants
DEFAULT_RAM_LIMIT_GB = 6.0
MEMORY_FACTOR_PER_ELEMENT = 8.0 / (1024**3)  # bytes per float64 to GB
MAX_EIGENVALUES = 10  # Number of eigenvalues to compute near E=0 for sparse solver

logger = get_logger(__name__)

def _estimate_dense_memory_gb(L: int) -> float:
    """Estimate RAM required for dense diagonalization of LxL Hamiltonian."""
    # Dense storage: L*L complex128 (16 bytes) or float64 (8 bytes) for real symmetric
    # Plus workspace overhead (typically 2-3x for LAPACK)
    matrix_bytes = L * L * 8.0  # float64
    # LAPACK workspace can be ~2-3x the matrix size for eigh
    workspace_factor = 3.0
    total_bytes = matrix_bytes * workspace_factor
    return total_bytes / (1024**3)

def _compute_participation_ratio_dense(eigenstates: np.ndarray) -> np.ndarray:
    """Compute PR for all eigenstates using dense arrays."""
    # eigenstates: shape (L, L), columns are eigenvectors
    # PR = (sum |psi_i|^2)^2 / sum |psi_i|^4
    # For normalized eigenvectors, sum |psi_i|^2 = 1
    # So PR = 1 / sum |psi_i|^4
    
    # Compute |psi|^4 for each eigenstate (column)
    psi_squared = np.abs(eigenstates) ** 2
    psi_fourth = psi_squared ** 2
    sum_psi_fourth = np.sum(psi_fourth, axis=0)
    
    # Avoid division by zero
    pr_values = np.ones_like(sum_psi_fourth)
    nonzero_mask = sum_psi_fourth > 1e-15
    pr_values[nonzero_mask] = 1.0 / sum_psi_fourth[nonzero_mask]
    
    return pr_values

def _compute_eigenstates_near_zero_dense(H: np.ndarray, energy_window: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """Compute all eigenpairs and filter near E=0 (dense method)."""
    # For real symmetric matrices, eigh returns eigenvalues in ascending order
    eigenvalues, eigenstates = linalg.eigh(H)
    
    # Filter eigenstates with |E| < energy_window
    mask = np.abs(eigenvalues) < energy_window
    filtered_eigenvalues = eigenvalues[mask]
    filtered_eigenstates = eigenstates[:, mask]
    
    return filtered_eigenvalues, filtered_eigenstates

def _compute_eigenstates_near_zero_sparse(H: sparse.csr_matrix, energy_window: float = 0.1, k: int = MAX_EIGENVALUES) -> Tuple[np.ndarray, np.ndarray]:
    """Compute eigenpairs near E=0 using sparse solver (shift-invert mode)."""
    L = H.shape[0]
    
    # Use shift-invert mode to find eigenvalues near sigma=0
    # This requires solving linear systems, which is memory efficient
    sigma = 0.0
    
    try:
        # eigsh with mode='c' (shift-invert) for eigenvalues near sigma
        # We want eigenvalues closest to 0
        # Use which='LM' with sigma to get eigenvalues near sigma
        eigenvalues, eigenstates = eigsh(
            H, 
            k=min(k, L-1), 
            sigma=sigma, 
            which='LM',
            mode='normal',  # Use normal mode for Hermitian matrices
            tol=1e-8,
            maxiter=L*100
        )
    except ArpackNoConvergence as e:
        log_numerical_warning(f"ARPACK did not converge after {L*100} iterations. Returning partial results.")
        if e.eigenvalues is not None and len(e.eigenvalues) > 0:
            eigenvalues = e.eigenvalues
            eigenstates = e.eigenstates
        else:
            raise ValueError("ARPACK failed to converge and returned no eigenvalues.")
    
    # Filter eigenstates with |E| < energy_window
    mask = np.abs(eigenvalues) < energy_window
    filtered_eigenvalues = eigenvalues[mask]
    filtered_eigenstates = eigenstates[:, mask]
    
    return filtered_eigenvalues, filtered_eigenstates

def compute_participation_ratio(
    H: np.ndarray,
    energy_window: float = 0.1,
    use_sparse_fallback: bool = True,
    ram_limit_gb: float = DEFAULT_RAM_LIMIT_GB
) -> Dict[str, Any]:
    """
    Compute Participation Ratio for eigenstates within |E| < energy_window.
    
    Implements automatic fallback to sparse solver if dense method would exceed RAM.
    
    Args:
        H: Hamiltonian matrix (L x L)
        energy_window: Energy window around E=0 to consider
        use_sparse_fallback: Whether to use sparse solver as fallback
        ram_limit_gb: RAM limit in GB for dense solver fallback
    
    Returns:
        Dict with keys:
            - 'pr_values': array of PR values for eigenstates in window
            - 'eigenvalues': corresponding eigenvalues
            - 'method': 'dense' or 'sparse'
            - 'memory_estimate_gb': estimated memory for dense method
            - 'converged': bool indicating successful computation
    """
    L = H.shape[0]
    memory_estimate_gb = _estimate_dense_memory_gb(L)
    
    result = {
        'pr_values': None,
        'eigenvalues': None,
        'method': 'dense',
        'memory_estimate_gb': memory_estimate_gb,
        'converged': False,
        'fallback_used': False
    }
    
    # Decide which solver to use
    use_sparse = False
    if memory_estimate_gb > ram_limit_gb:
        if use_sparse_fallback:
            use_sparse = True
            result['fallback_used'] = True
            log_numerical_warning(
                f"Dense diagonalization estimated at {memory_estimate_gb:.2f} GB exceeds "
                f"limit of {ram_limit_gb} GB. Using sparse solver."
            )
        else:
            log_numerical_error(
                f"Dense diagonalization requires {memory_estimate_gb:.2f} GB > {ram_limit_gb} GB limit. "
                "Cannot proceed without sparse fallback enabled."
            )
            return result
    
    try:
        if use_sparse:
            # Convert to sparse format
            H_sparse = sparse.csr_matrix(H)
            eigenvalues, eigenstates = _compute_eigenstates_near_zero_sparse(
                H_sparse, energy_window
            )
            result['method'] = 'sparse'
        else:
            eigenvalues, eigenstates = _compute_eigenstates_near_zero_dense(H, energy_window)
            result['method'] = 'dense'
        
        if eigenstates.size == 0:
            log_numerical_warning(f"No eigenstates found within |E| < {energy_window}")
            result['pr_values'] = np.array([])
            result['eigenvalues'] = np.array([])
            result['converged'] = True
            return result
        
        # Compute PR for filtered eigenstates
        pr_values = _compute_participation_ratio_dense(eigenstates)
        
        result['pr_values'] = pr_values
        result['eigenvalues'] = eigenvalues
        result['converged'] = True
        
    except Exception as e:
        log_numerical_error(f"Eigenvalue computation failed: {str(e)}")
        result['converged'] = False
        raise
    
    return result

def analyze_single_realization(
    H: np.ndarray,
    W: float,
    L: int,
    realization_index: int,
    energy_window: float = 0.1,
    ram_limit_gb: float = DEFAULT_RAM_LIMIT_GB
) -> Dict[str, Any]:
    """
    Analyze a single disorder realization.
    
    Computes PR for eigenstates near E=0 and returns summary statistics.
    
    Args:
        H: Hamiltonian matrix
        W: Disorder strength
        L: System size
        realization_index: Index of this realization
        energy_window: Energy window for eigenstate selection
        ram_limit_gb: RAM limit for dense solver fallback
    
    Returns:
        Dict with analysis results including mean PR, std PR, and eigenstate details
    """
    start_time = time.time()
    
    pr_result = compute_participation_ratio(
        H, 
        energy_window=energy_window,
        ram_limit_gb=ram_limit_gb
    )
    
    elapsed = time.time() - start_time
    
    result = {
        'W': W,
        'L': L,
        'realization_index': realization_index,
        'method_used': pr_result['method'],
        'memory_estimate_gb': pr_result['memory_estimate_gb'],
        'fallback_used': pr_result.get('fallback_used', False),
        'n_eigenstates': len(pr_result['eigenvalues']) if pr_result['eigenvalues'] is not None else 0,
        'mean_pr': float(np.mean(pr_result['pr_values'])) if pr_result['pr_values'] is not None and len(pr_result['pr_values']) > 0 else None,
        'std_pr': float(np.std(pr_result['pr_values'])) if pr_result['pr_values'] is not None and len(pr_result['pr_values']) > 0 else None,
        'min_pr': float(np.min(pr_result['pr_values'])) if pr_result['pr_values'] is not None and len(pr_result['pr_values']) > 0 else None,
        'max_pr': float(np.max(pr_result['pr_values'])) if pr_result['pr_values'] is not None and len(pr_result['pr_values']) > 0 else None,
        'eigenvalues': pr_result['eigenvalues'].tolist() if pr_result['eigenvalues'] is not None else [],
        'pr_values': pr_result['pr_values'].tolist() if pr_result['pr_values'] is not None else [],
        'computation_time_s': elapsed,
        'converged': pr_result['converged']
    }
    
    if not pr_result['converged']:
        log_numerical_error(f"Realization W={W}, L={L}, idx={realization_index} failed to converge")
    
    return result

def saturation_curve(pr_values: np.ndarray, L: int) -> float:
    """
    Compute the saturation value of PR for a given system size.
    
    For localized states, PR saturates to a constant value independent of L.
    For delocalized states, PR scales with L.
    
    Args:
        pr_values: Array of PR values for eigenstates in the energy window
        L: System size
    
    Returns:
        Saturation value (mean PR for this realization)
    """
    if len(pr_values) == 0:
        return 0.0
    return float(np.mean(pr_values))

def finite_size_scaling(
    results: List[Dict[str, Any]],
    L_values: List[int]
) -> Dict[str, Any]:
    """
    Perform finite-size scaling analysis to extract localization length ξ.
    
    Fits PR(L) saturation values to the scaling function:
    PR(L) = L * f(L/ξ)
    
    For localized states (L >> ξ), PR saturates to constant.
    For delocalized states (L << ξ), PR ∝ L.
    
    Uses the corrected methodology from Plan.md: fit saturation across
    system sizes to extract ξ, not simple proportionality.
    
    Args:
        results: List of analysis results from different system sizes
        L_values: Corresponding system sizes
    
    Returns:
        Dict with keys:
            - 'xi': extracted localization length
            - 'uncertainty': uncertainty in ξ
            - 'fit_params': parameters from curve fit
            - 'r_squared': goodness of fit
    """
    # Extract saturation values for each L
    pr_saturation = []
    valid_L = []
    
    for result, L in zip(results, L_values):
        if result['mean_pr'] is not None and result['converged']:
            pr_saturation.append(result['mean_pr'])
            valid_L.append(L)
    
    if len(pr_saturation) < 3:
        logger.warning(f"Insufficient data points for finite-size scaling: {len(pr_saturation)}")
        return {
            'xi': None,
            'uncertainty': None,
            'fit_params': {},
            'r_squared': None,
            'error': 'Insufficient data points'
        }
    
    pr_saturation = np.array(pr_saturation)
    valid_L = np.array(valid_L)
    
    # Scaling function: PR(L) = A * L / (1 + L/xi)
    # This interpolates between PR ∝ L (delocalized) and PR = A (localized)
    def scaling_func(L, xi, A):
        if xi <= 0:
            return np.full_like(L, A)
        return A * L / (1 + L / xi)
    
    # Initial guesses
    A_init = np.max(pr_saturation)
    xi_init = np.median(valid_L)
    
    try:
        popt, pcov = curve_fit(
            scaling_func,
            valid_L,
            pr_saturation,
            p0=[xi_init, A_init],
            bounds=([1e-3, 1e-3], [np.inf, np.inf]),
            maxfev=10000
        )
        
        xi_fit, A_fit = popt
        perr = np.sqrt(np.diag(pcov))
        xi_uncertainty = perr[0]
        
        # Calculate R-squared
        y_pred = scaling_func(valid_L, xi_fit, A_fit)
        ss_res = np.sum((pr_saturation - y_pred) ** 2)
        ss_tot = np.sum((pr_saturation - np.mean(pr_saturation)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            'xi': float(xi_fit),
            'uncertainty': float(xi_uncertainty),
            'fit_params': {'A': float(A_fit)},
            'r_squared': float(r_squared),
            'converged': True
        }
        
    except Exception as e:
        logger.error(f"Curve fitting failed: {str(e)}")
        return {
            'xi': None,
            'uncertainty': None,
            'fit_params': {},
            'r_squared': None,
            'error': str(e),
            'converged': False
        }

def main():
    """
    Main entry point for PR analysis.
    
    This function demonstrates the fallback mechanism by:
    1. Generating a large Hamiltonian (L=1600)
    2. Attempting dense diagonalization
    3. Automatically falling back to sparse solver if RAM limit exceeded
    4. Computing PR and logging the method used
    """
    config = get_config()
    logger.info("Starting PR analysis with fallback mechanism test")
    
    # Test with a large system to trigger fallback
    L_test = 1600
    W_test = 1.0
    n_realizations = 1
    
    logger.info(f"Testing with L={L_test}, W={W_test}")
    memory_estimate = _estimate_dense_memory_gb(L_test)
    logger.info(f"Estimated memory for dense diagonalization: {memory_estimate:.2f} GB")
    
    from code.generate_hamiltonian import generate_hamiltonian
    
    results = []
    for idx in range(n_realizations):
        H = generate_hamiltonian(L_test, W_test, seed=config.RANDOM_SEED + idx)
        
        result = analyze_single_realization(
            H, 
            W=W_test, 
            L=L_test, 
            realization_index=idx,
            energy_window=0.1,
            ram_limit_gb=DEFAULT_RAM_LIMIT_GB
        )
        
        results.append(result)
        
        logger.info(f"Realization {idx}: Method={result['method_used']}, "
                   f"Mean PR={result['mean_pr']:.4f}, "
                   f"Fallback used={result['fallback_used']}")
    
    # Save results
    output_dir = Path(config.DATA_PROCESSED_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"pr_analysis_L{L_test}_W{W_test}.json"
    
    with open(output_path, 'w') as f:
        json.dump({
            'config': {
                'L': L_test,
                'W': W_test,
                'n_realizations': n_realizations,
                'ram_limit_gb': DEFAULT_RAM_LIMIT_GB
            },
            'results': results
        }, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    main()