"""
Participation Ratio analysis for 1D disordered systems.
Computes localization lengths via finite-size scaling of PR saturation.
"""
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from scipy import linalg
from scipy import sparse
from scipy.sparse.linalg import eigsh, ArpackNoConvergence
from scipy.optimize import curve_fit
import json
import os
from pathlib import Path
import logging

from code.config import get_config
from code.logger import get_logger
from code.generate_hamiltonian import generate_hamiltonian

logger = logging.getLogger(__name__)

def compute_participation_ratio(eigenvectors: np.ndarray, 
                               eigenvalues: np.ndarray,
                               energy_window: float = 0.1) -> Dict[str, Any]:
    """
    Compute Participation Ratio for eigenstates within a given energy window.
    
    PR = (Σ|ψᵢ|²)² / Σ|ψᵢ|⁴
    
    Args:
        eigenvectors: Matrix of eigenvectors (columns).
        eigenvalues: Array of eigenvalues.
        energy_window: Energy range around E=0 to consider (default: 0.1).
        
    Returns:
        Dictionary with PR values and metadata.
    """
    # Filter eigenstates within energy window
    mask = np.abs(eigenvalues) < energy_window
    filtered_eigenvectors = eigenvectors[:, mask]
    filtered_eigenvalues = eigenvalues[mask]
    
    if len(filtered_eigenvalues) == 0:
        return {
            "pr_values": [],
            "eigenvalues": [],
            "n_states": 0
        }
    
    # Compute PR for each eigenstate
    pr_values = []
    for i in range(filtered_eigenvectors.shape[1]):
        psi = filtered_eigenvectors[:, i]
        psi_sq = np.abs(psi) ** 2
        pr = (np.sum(psi_sq) ** 2) / np.sum(psi_sq ** 2)
        pr_values.append(pr)
    
    return {
        "pr_values": np.array(pr_values),
        "eigenvalues": filtered_eigenvalues,
        "n_states": len(filtered_eigenvalues)
    }

def analyze_single_realization(L: int, W: float, seed: int, 
                              realization_index: int,
                              energy_window: float = 0.1) -> Dict[str, Any]:
    """
    Analyze a single disorder realization.
    
    Args:
        L: System size.
        W: Disorder strength.
        seed: Random seed.
        realization_index: Index of this realization.
        energy_window: Energy range around E=0.
        
    Returns:
        Dictionary with PR results and metadata.
    """
    config = get_config()
    logger_instance = get_logger()
    
    # Generate Hamiltonian
    H, eigvals, eigvecs, residual, converged = generate_hamiltonian(L, W, seed)
    
    # Log residual and convergence
    logger_instance.log_residual(
        norm=float(residual),
        flag=bool(converged),
        task="eigh",
        L=L,
        W=W,
        realization_index=realization_index
    )
    
    # Compute PR
    pr_result = compute_participation_ratio(eigvecs, eigvals, energy_window)
    
    return {
        "L": L,
        "W": W,
        "seed": seed,
        "realization_index": realization_index,
        "pr_values": pr_result["pr_values"].tolist(),
        "eigenvalues": pr_result["eigenvalues"].tolist(),
        "n_states": pr_result["n_states"],
        "residual_norm": float(residual),
        "converged": bool(converged)
    }

def saturation_curve(L_values: List[int], W: float, seeds: List[int],
                    energy_window: float = 0.1) -> Dict[str, Any]:
    """
    Compute PR saturation curve across system sizes for a given disorder strength.
    
    Args:
        L_values: List of system sizes.
        W: Disorder strength.
        seeds: List of seeds for each L.
        energy_window: Energy range around E=0.
        
    Returns:
        Dictionary with PR vs L data.
    """
    results = []
    
    for i, (L, seed) in enumerate(zip(L_values, seeds)):
        result = analyze_single_realization(L, W, seed, i, energy_window)
        # Use mean PR for the energy window
        mean_pr = np.mean(result["pr_values"]) if len(result["pr_values"]) > 0 else 0.0
        results.append({
            "L": L,
            "mean_pr": mean_pr,
            "std_pr": float(np.std(result["pr_values"])) if len(result["pr_values"]) > 1 else 0.0,
            "n_states": result["n_states"]
        })
    
    return {
        "W": W,
        "L_values": L_values,
        "results": results
    }

def finite_size_scaling(L_values: List[int], W: float, seeds: List[int],
                       energy_window: float = 0.1) -> Dict[str, Any]:
    """
    Perform finite-size scaling to extract localization length ξ.
    
    Fits PR(L) saturation curve to extract ξ.
    
    Args:
        L_values: List of system sizes.
        W: Disorder strength.
        seeds: List of seeds for each L.
        energy_window: Energy range around E=0.
        
    Returns:
        Dictionary with fit results and localization length.
    """
    config = get_config()
    
    # Get saturation curve data
    curve_data = saturation_curve(L_values, W, seeds, energy_window)
    
    L_vals = np.array([d["L"] for d in curve_data["results"]])
    pr_vals = np.array([d["mean_pr"] for d in curve_data["results"]])
    
    # Filter out zero PR values
    valid_mask = pr_vals > 0
    L_valid = L_vals[valid_mask]
    pr_valid = pr_vals[valid_mask]
    
    if len(L_valid) < 3:
        logger.warning(f"Not enough valid data points for W={W}")
        return {
            "W": W,
            "xi": None,
            "uncertainty": None,
            "fit_params": None,
            "L_values": L_vals.tolist(),
            "PR_values": pr_vals.tolist(),
            "fit_r_squared": None,
            "is_delocalized": False
        }
    
    # Fit saturation curve: PR(L) = ξ * tanh(L/ξ)
    def saturation_model(L, xi):
        return xi * np.tanh(L / xi)
    
    try:
        # Initial guess: ξ ≈ PR at largest L
        initial_guess = [pr_valid[-1]]
        
        popt, pcov = curve_fit(
            saturation_model, 
            L_valid, 
            pr_valid, 
            p0=initial_guess,
            bounds=(0, np.inf)
        )
        
        xi = popt[0]
        xi_error = np.sqrt(np.diag(pcov))[0]
        
        # Calculate R²
        pr_pred = saturation_model(L_valid, xi)
        ss_res = np.sum((pr_valid - pr_pred) ** 2)
        ss_tot = np.sum((pr_valid - np.mean(pr_valid)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Check for delocalized case (W=0)
        is_delocalized = (W == 0.0)
        if is_delocalized:
            # For W=0, PR should scale linearly with L
            # Verify by checking if PR/L is approximately constant
            pr_per_L = pr_valid / L_valid
            if np.std(pr_per_L) / np.mean(pr_per_L) < 0.1:
                is_delocalized = True
            else:
                is_delocalized = False
        
        return {
            "W": W,
            "xi": float(xi),
            "uncertainty": float(xi_error),
            "fit_params": {"xi": float(xi)},
            "L_values": L_valid.tolist(),
            "PR_values": pr_valid.tolist(),
            "fit_r_squared": float(r_squared),
            "is_delocalized": is_delocalized
        }
        
    except Exception as e:
        logger.error(f"Fit failed for W={W}: {e}")
        return {
            "W": W,
            "xi": None,
            "uncertainty": None,
            "fit_params": None,
            "L_values": L_vals.tolist(),
            "PR_values": pr_vals.tolist(),
            "fit_r_squared": None,
            "is_delocalized": False,
            "error": str(e)
        }

def main():
    """
    Main entry point for PR analysis.
    """
    config = get_config()
    
    # Example: Run finite-size scaling for a single W
    L_list = config.L_LIST
    W_list = config.W_LIST
    
    for W in W_list:
        seeds = [config.SEED + i for i in range(len(L_list))]
        result = finite_size_scaling(L_list, W, seeds)
        
        # Save results
        output_path = config.SCALING_FITS_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing results or create new
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                all_results = json.load(f)
        else:
            all_results = []
        
        all_results.append(result)
        
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"Saved scaling fit for W={W}: ξ={result.get('xi', 'N/A')}")

if __name__ == "__main__":
    main()
