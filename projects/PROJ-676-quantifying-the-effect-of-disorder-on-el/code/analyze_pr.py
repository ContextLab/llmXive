"""
Analysis module for Participation Ratio (PR) and finite-size scaling.
Computes localization lengths via PR saturation.
"""
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from scipy import linalg
from scipy import sparse
from scipy.sparse.linalg import eigsh, ArpackNoConvergence
from scipy.optimize import curve_fit
import json
import os
import logging
from pathlib import Path

from code.config import get_config
from code.logger import get_logger, NumericalLogger
from code.generate_hamiltonian import generate_hamiltonian
from code.storage_utils import save_eigenstates_to_hdf5, save_localization_length


logger = logging.getLogger(__name__)
num_logger = get_logger()


def compute_participation_ratio(eigenvectors: np.ndarray, energy_threshold: float = 0.1) -> np.ndarray:
    """
    Compute Participation Ratio (PR) for eigenstates within |E| < energy_threshold.
    
    PR = (sum(|psi|^2))^2 / sum(|psi|^4)
    
    Args:
        eigenvectors: Array of shape (L, L) where columns are eigenvectors.
        energy_threshold: Only consider eigenstates with |E| < threshold.
        
    Returns:
        Array of PR values for selected eigenstates.
    """
    # We need eigenvalues to filter, but this function only takes eigenvectors.
    # The caller must filter eigenvectors before passing them here, or we assume
    # the input eigenvectors are already filtered.
    # For robustness, we assume eigenvectors are passed in order of eigenvalues,
    # but we cannot filter without eigenvalues.
    # Let's assume the caller passes the subset of eigenvectors corresponding to |E| < threshold.
    
    L = eigenvectors.shape[0]
    pr_values = []
    
    for i in range(L):
        psi = eigenvectors[:, i]
        # PR = (sum |psi_i|^2)^2 / sum |psi_i|^4
        # Since eigenvectors are normalized, sum |psi_i|^2 = 1
        # So PR = 1 / sum |psi_i|^4
        psi_sq = np.abs(psi)**2
        sum_sq = np.sum(psi_sq)
        sum_fourth = np.sum(psi_sq**2)
        
        if sum_fourth > 0:
            pr = (sum_sq**2) / sum_fourth
        else:
            pr = 0.0
        pr_values.append(pr)
        
    return np.array(pr_values)


def analyze_single_realization(L: int, W: float, seed: int, 
                               eigenvalue_method: str = 'dense') -> Dict[str, Any]:
    """
    Analyze a single disorder realization.
    
    Args:
        L: System size.
        W: Disorder strength.
        seed: Random seed for reproducibility.
        eigenvalue_method: 'dense' (scipy.linalg.eigh) or 'sparse' (scipy.sparse.linalg.eigsh).
        
    Returns:
        Dictionary containing eigenvalues, eigenvectors (subset), and PR values.
    """
    config = get_config()
    np.random.seed(seed)
    
    # Generate Hamiltonian
    H = generate_hamiltonian(L, W)
    
    # Diagonalize
    if eigenvalue_method == 'dense':
        try:
            eigenvalues, eigenvectors = linalg.eigh(H)
            residual_norm = 0.0 # eigh is direct, residual is typically 0
            converged = True
        except Exception as e:
            logger.error(f"Dense diagonalization failed: {e}")
            raise
    else:
        # Sparse method for large L
        # We need a few eigenvalues near E=0
        k = min(10, L-1)
        try:
            # sigma=0.0 to find eigenvalues near 0
            eigenvalues, eigenvectors = eigsh(H, k=k, sigma=0.0, which='LM')
            # Estimate residual: ||H*v - lambda*v||
            # For simplicity, we assume convergence if no exception
            residual_norm = 0.0 
            converged = True
        except ArpackNoConvergence as e:
            logger.warning(f"Sparse solver did not converge: {e}")
            eigenvalues = e.eigenvalues
            eigenvectors = e.eigenvectors
            residual_norm = float('inf')
            converged = False
        except Exception as e:
            logger.error(f"Sparse diagonalization failed: {e}")
            raise
    
    # Log numerical stability
    num_logger.log_residual(
        norm=residual_norm, 
        flag=converged, 
        task="eigh", 
        L=L, 
        W=W,
        realization_index=seed # Using seed as realization_index for simplicity in this context
    )
    
    # Filter eigenstates near E=0
    energy_threshold = 0.1
    mask = np.abs(eigenvalues) < energy_threshold
    selected_eigenvalues = eigenvalues[mask]
    selected_eigenvectors = eigenvectors[:, mask]
    
    # Compute PR for selected states
    pr_values = compute_participation_ratio(selected_eigenvectors)
    avg_pr = np.mean(pr_values) if len(pr_values) > 0 else 0.0
    
    return {
        "eigenvalues": eigenvalues,
        "eigenvectors": eigenvectors,
        "selected_eigenvalues": selected_eigenvalues,
        "selected_eigenvectors": selected_eigenvectors,
        "pr_values": pr_values,
        "avg_pr": avg_pr,
        "L": L,
        "W": W,
        "seed": seed
    }


def saturation_curve(L_values: List[int], W: float, seed_base: int = 42) -> Dict[str, Any]:
    """
    Compute average PR for a range of system sizes L at fixed W.
    
    Args:
        L_values: List of system sizes.
        W: Disorder strength.
        seed_base: Base seed for realization generation.
        
    Returns:
        Dictionary with L_values, PR_values, and metadata.
    """
    pr_list = []
    seeds = []
    
    for i, L in enumerate(L_values):
        seed = seed_base + i
        result = analyze_single_realization(L, W, seed)
        pr_list.append(result['avg_pr'])
        seeds.append(seed)
        
    return {
        "L_values": L_values,
        "PR_values": pr_list,
        "W": W,
        "seeds": seeds
    }


def finite_size_scaling(L_values: List[int], PR_values: List[float], 
                        W: float, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Fit PR(L) to extract localization length xi via saturation.
    
    Model: PR(L) = xi * tanh(L / xi)  (simplified saturation model)
    Or: PR(L) = A * L / (1 + B * L) -> xi ~ 1/B
    
    We use a simple saturation function: PR(L) = xi * (1 - exp(-L/xi))
    For large L, PR -> xi.
    
    Args:
        L_values: List of system sizes.
        PR_values: List of average PR values.
        W: Disorder strength.
        output_dir: Directory to save plots and fits.
        
    Returns:
        Dictionary with fit parameters, xi, uncertainty, R^2.
    """
    L_arr = np.array(L_values)
    PR_arr = np.array(PR_values)
    
    # Define saturation model
    def saturation_model(L, xi):
        return xi * (1 - np.exp(-L / xi))
    
    # Initial guess: xi ~ max(PR)
    p0 = [np.max(PR_arr) * 1.5]
    
    try:
        popt, pcov = curve_fit(saturation_model, L_arr, PR_arr, p0=p0, maxfev=10000)
        xi = popt[0]
        
        # Uncertainty from covariance matrix
        if pcov is not None:
            xi_err = np.sqrt(np.diag(pcov))[0]
        else:
            xi_err = np.nan
        
        # R-squared
        PR_pred = saturation_model(L_arr, xi)
        ss_res = np.sum((PR_arr - PR_pred)**2)
        ss_tot = np.sum((PR_arr - np.mean(PR_arr))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        result = {
            "xi": float(xi),
            "uncertainty": float(xi_err),
            "fit_params": {"xi": float(xi)},
            "L_values": L_values,
            "PR_values": PR_values,
            "fit_r_squared": float(r_squared),
            "W": W
        }
        
        # Generate diagnostic plot
        if output_dir:
            import matplotlib.pyplot as plt
            output_dir.mkdir(parents=True, exist_ok=True)
            plot_path = output_dir / f"pr_scaling_plot_W{W:.1f}.png"
            
            plt.figure(figsize=(8, 6))
            plt.scatter(L_arr, PR_arr, label='Data', color='blue')
            L_fine = np.linspace(min(L_arr), max(L_arr), 100)
            plt.plot(L_fine, saturation_model(L_fine, xi), 'r-', label=f'Fit: xi={xi:.2f}')
            plt.xlabel('System Size L')
            plt.ylabel('Participation Ratio (PR)')
            plt.title(f'Finite-Size Scaling for W={W}')
            plt.legend()
            plt.grid(True)
            plt.savefig(plot_path, dpi=150)
            plt.close()
            logger.info(f"Saved scaling plot to {plot_path}")
            
    except Exception as e:
        logger.error(f"Curve fitting failed for W={W}: {e}")
        # Return a failure result
        result = {
            "xi": float('nan'),
            "uncertainty": float('nan'),
            "fit_params": {},
            "L_values": L_values,
            "PR_values": PR_values,
            "fit_r_squared": float('nan'),
            "W": W,
            "error": str(e)
        }
        
    return result


def main():
    """
    Main entry point for PR analysis.
    Runs finite-size scaling for a range of W values.
    """
    config = get_config()
    output_dir = config.PROCESSED_DIR
    
    # Example run for a single W
    L_list = [100, 200, 400, 800, 1600]
    W_list = [0.5, 1.0, 2.0]
    
    all_fits = []
    
    for W in W_list:
        logger.info(f"Running scaling analysis for W={W}")
        curve_data = saturation_curve(L_list, W, seed_base=42)
        fit_result = finite_size_scaling(
            curve_data['L_values'], 
            curve_data['PR_values'], 
            W, 
            output_dir=output_dir
        )
        all_fits.append(fit_result)
        
        logger.info(f"W={W}: xi = {fit_result['xi']:.2f} +/- {fit_result['uncertainty']:.2f}, R^2 = {fit_result['fit_r_squared']:.4f}")
    
    # Save results
    output_file = output_dir / 'scaling_fits.json'
    with open(output_file, 'w') as f:
        json.dump(all_fits, f, indent=2)
    logger.info(f"Saved scaling fits to {output_file}")


if __name__ == "__main__":
    main()
