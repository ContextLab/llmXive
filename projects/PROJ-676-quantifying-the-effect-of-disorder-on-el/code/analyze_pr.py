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
from code.logger import NumericalLogger, get_logger, log_residual_decorator, inject_log_residual
from code.storage_utils import log_provenance_entry
from code.generate_hamiltonian import generate_hamiltonian

logger = logging.getLogger(__name__)

def compute_eigenstates(hamiltonian: np.ndarray, energy_window: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """Compute eigenstates within a specific energy window."""
    L = hamiltonian.shape[0]
    try:
        if L > 1000:
            eigenvalues, eigenvectors = eigsh(hamiltonian, k=L-1, which='SM', tol=1e-8)
        else:
            eigenvalues, eigenvectors = linalg.eigh(hamiltonian)
        
        mask = np.abs(eigenvalues) < energy_window
        selected_eigenvalues = eigenvalues[mask]
        selected_eigenvectors = eigenvectors[:, mask]
        
        return selected_eigenvalues, selected_eigenvectors
    except ArpackNoConvergence as e:
        logger.warning(f"ARPACK did not converge. Falling back to dense. {e}")
        eigenvalues, eigenvectors = linalg.eigh(hamiltonian)
        mask = np.abs(eigenvalues) < energy_window
        return eigenvalues[mask], eigenvectors[:, mask]

def compute_participation_ratio(eigenvectors: np.ndarray) -> np.ndarray:
    """Compute Participation Ratio for a set of eigenvectors."""
    if eigenvectors.ndim == 1:
        eigenvectors = eigenvectors.reshape(-1, 1)
    
    pr_values = []
    for i in range(eigenvectors.shape[1]):
        psi = eigenvectors[:, i]
        prob_density = np.abs(psi) ** 2
        pr = (np.sum(prob_density) ** 2) / np.sum(prob_density ** 2)
        pr_values.append(pr)
    
    return np.array(pr_values)

def saturation_model(L, PR_inf, xi):
    """Saturation model for finite-size scaling."""
    return PR_inf * (1 - np.exp(-L / xi))

def finite_size_scaling(L_values: List[int], pr_values: List[float]) -> Optional[Dict[str, float]]:
    """Perform finite-size scaling fit to extract localization length."""
    if len(L_values) < 3:
        logger.warning("Insufficient data points for scaling fit.")
        return None
    
    try:
        popt, pcov = curve_fit(saturation_model, L_values, pr_values, p0=[max(pr_values), 100], maxfev=5000)
        PR_inf, xi = popt
        
        if xi <= 0 or PR_inf <= 0:
            logger.warning(f"Non-physical fit result: xi={xi}, PR_inf={PR_inf}")
            return None
        
        # Calculate R-squared
        pr_pred = saturation_model(np.array(L_values), *popt)
        ss_res = np.sum((np.array(pr_values) - pr_pred) ** 2)
        ss_tot = np.sum((np.array(pr_values) - np.mean(pr_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        if r_squared < 0.95:
            logger.warning(f"Fit R-squared too low: {r_squared}")
            return None
        
        # Estimate uncertainty
        perr = np.sqrt(np.diag(pcov))
        uncertainty = perr[1]
        
        return {
            "xi": float(xi),
            "uncertainty": float(uncertainty),
            "r_squared": float(r_squared)
        }
    except Exception as e:
        logger.warning(f"Scaling fit failed: {e}")
        return None

def analyze_single_realization(W: float, L: int, realization_index: int, seed: int, energy_window: float = 0.1) -> Dict[str, Any]:
    """Analyze a single disorder realization."""
    config = get_config()
    logger_instance = get_logger()
    
    # Generate Hamiltonian
    hamiltonian = generate_hamiltonian(L, W, seed + realization_index)
    
    # Compute eigenstates
    eigenvalues, eigenvectors = compute_eigenstates(hamiltonian, energy_window)
    
    if len(eigenvalues) == 0:
        logger.warning(f"No eigenstates found within energy window for W={W}, L={L}")
        return None
    
    # Compute PR
    pr_values = compute_participation_ratio(eigenvectors)
    
    results = []
    for i, (ev, pr) in enumerate(zip(eigenvalues, pr_values)):
        results.append({
            "W": W,
            "L": L,
            "realization_index": realization_index,
            "energy": float(ev),
            "pr": float(pr)
        })
        
        # Log residual
        logger_instance.log_residual(pr, True)
    
    return results

def run_scaling_analysis(W: float, L_list: List[int], num_realizations: int, seed: int) -> List[Dict[str, Any]]:
    """Run scaling analysis for a specific disorder width across multiple system sizes."""
    all_results = []
    
    for L in L_list:
        for r_idx in range(num_realizations):
            res = analyze_single_realization(W, L, r_idx, seed)
            if res:
                all_results.extend(res)
    
    return all_results

def analyze_w0_delocalization(L_list: List[int], num_realizations: int, seed: int) -> Dict[str, Any]:
    """Analyze the W=0 (clean) limit to verify delocalization."""
    results = []
    pr_values_by_L = {}
    
    for L in L_list:
        pr_vals = []
        for r_idx in range(num_realizations):
            # For W=0, generate clean Hamiltonian
            hamiltonian = np.zeros((L, L))
            for i in range(L - 1):
                hamiltonian[i, i+1] = 1.0
                hamiltonian[i+1, i] = 1.0
            
            eigenvalues, eigenvectors = linalg.eigh(hamiltonian)
            # Select states near E=0
            mask = np.abs(eigenvalues) < 0.1
            selected_vecs = eigenvectors[:, mask]
            
            if selected_vecs.shape[1] > 0:
                pr = compute_participation_ratio(selected_vecs)[0]
                pr_vals.append(pr)
                results.append({
                    "W": 0.0,
                    "L": L,
                    "realization_index": r_idx,
                    "energy": float(eigenvalues[mask][0]),
                    "pr": float(pr)
                })
        
        if pr_vals:
            avg_pr = np.mean(pr_vals)
            pr_values_by_L[L] = avg_pr
            logger.info(f"W=0, L={L}, Avg PR={avg_pr:.2f} (Expected ~L/3)")
    
    # Check extensive scaling: PR should scale linearly with L
    is_delocalized = False
    if len(pr_values_by_L) >= 2:
        sorted_L = sorted(pr_values_by_L.keys())
        # Check if PR/L is roughly constant
        ratios = [pr_values_by_L[L] / L for L in sorted_L]
        if np.std(ratios) / np.mean(ratios) < 0.2: # 20% variance threshold
            is_delocalized = True
    
    return {
        "is_delocalized": is_delocalized,
        "PR_values": pr_values_by_L,
        "raw_results": results
    }

def main():
    """Main entry point for PR analysis."""
    config = get_config()
    W_list = config.get("W_LIST", [1.0])
    L_list = config.get("L_LIST", [100, 200, 400])
    num_realizations = config.get("NUM_REALIZATIONS", 10)
    seed = config.get("SEED", 42)
    output_path = Path("data/processed/pr_raw.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_data = []
    
    # Handle W=0 separately if present
    if 0.0 in W_list:
        logger.info("Processing W=0 (clean limit)...")
        w0_data = analyze_w0_delocalization(L_list, num_realizations, seed)
        # Save W=0 specific results
        w0_output = Path("data/processed/w0_results.json")
        with open(w0_output, 'w') as f:
            json.dump({
                "is_delocalized": w0_data["is_delocalized"],
                "PR_values": w0_data["PR_values"]
            }, f, indent=2)
        all_data.extend(w0_data["raw_results"])
        W_list = [w for w in W_list if w != 0.0] # Remove 0.0 from main loop
    
    for W in W_list:
        logger.info(f"Processing W={W}")
        results = run_scaling_analysis(W, L_list, num_realizations, seed)
        all_data.extend(results)
    
    # Write raw PR data
    with open(output_path, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    logger.info(f"Raw PR data written to {output_path}")

if __name__ == "__main__":
    main()
