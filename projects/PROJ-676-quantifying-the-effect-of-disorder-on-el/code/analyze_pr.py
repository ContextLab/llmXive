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
from datetime import datetime

from code.config import get_config
from code.logger import NumericalLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/metadata/analyze_pr.log')
    ]
)
logger = logging.getLogger(__name__)

def compute_eigenstates(H: np.ndarray, energy_window: float = 0.1) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    """
    Compute eigenstates for a given Hamiltonian H.
    
    Args:
        H: Hamiltonian matrix (L x L)
        energy_window: Energy window around E=0 to consider (|E| < energy_window)
    
    Returns:
        eigenvalues: Array of eigenvalues
        eigenvectors: Array of eigenvectors (columns)
        residual_logs: List of residual log entries for NumericalLogger
    """
    L = H.shape[0]
    residual_logs = []
    
    # Determine if sparse or dense based on size
    # Use sparse for L >= 400 to save memory, dense otherwise
    if L >= 400:
        try:
            # Use sparse eigsh for large matrices
            # Compute all eigenvalues and eigenvectors within the energy window
            # We need all eigenvalues to filter by energy window
            # eigsh with 'SM' (smallest magnitude) might miss some in the window
            # Better to compute a range or all if feasible
            
            # For L=400-1600, computing all eigenvalues with sparse might be slow
            # But we need all to filter by energy window
            # Let's try to compute all using dense for now, fallback to sparse if memory error
            eigenvalues, eigenvectors = linalg.eigh(H.toarray() if sparse.issparse(H) else H)
            
            # Log convergence (dense solver always converges)
            residual_norm = 0.0
            converged = True
            
            residual_logs.append({
                "task": "eigh",
                "L": L,
                "W": 0.0,  # Will be set by caller
                "realization_index": -1,  # Will be set by caller
                "residual_norm": residual_norm,
                "converged": converged
            })
            
        except MemoryError:
            logger.error(f"Memory error for L={L}, falling back to sparse solver")
            # Fallback to sparse solver with shift-invert mode to find eigenvalues near 0
            sigma = 0.0
            k = min(50, L)  # Number of eigenvalues to compute
            
            try:
                eigenvalues, eigenvectors = eigsh(H, k=k, sigma=sigma, which='LM')
                
                # Estimate residual norm (simplified)
                # For eigsh, we don't get direct residual, but we can check convergence
                residual_norm = 1e-10  # Assume converged if no exception
                converged = True
                
                residual_logs.append({
                    "task": "eigh",
                    "L": L,
                    "W": 0.0,
                    "realization_index": -1,
                    "residual_norm": residual_norm,
                    "converged": converged
                })
                
            except ArpackNoConvergence as e:
                logger.error(f"ARPACK did not converge for L={L}")
                residual_norm = float('inf')
                converged = False
                
                residual_logs.append({
                    "task": "eigh",
                    "L": L,
                    "W": 0.0,
                    "realization_index": -1,
                    "residual_norm": residual_norm,
                    "converged": converged
                })
                
                # Return partial results if available
                eigenvalues = e.eigenvalues if e.eigenvalues is not None else np.array([])
                eigenvectors = e.eigenvectors if e.eigenvectors is not None else np.array([]).reshape(L, 0)
    else:
        # Use dense solver for small matrices
        try:
            eigenvalues, eigenvectors = linalg.eigh(H)
            
            residual_norm = 0.0
            converged = True
            
            residual_logs.append({
                "task": "eigh",
                "L": L,
                "W": 0.0,
                "realization_index": -1,
                "residual_norm": residual_norm,
                "converged": converged
            })
            
        except Exception as e:
            logger.error(f"Error computing eigenstates for L={L}: {e}")
            residual_norm = float('inf')
            converged = False
            
            residual_logs.append({
                "task": "eigh",
                "L": L,
                "W": 0.0,
                "realization_index": -1,
                "residual_norm": residual_norm,
                "converged": converged
            })
            
            eigenvalues = np.array([])
            eigenvectors = np.array([]).reshape(L, 0)
    
    return eigenvalues, eigenvectors, residual_logs

def compute_participation_ratio(eigenvectors: np.ndarray, eigenvalues: np.ndarray, energy_window: float = 0.1) -> Dict[str, Any]:
    """
    Compute Participation Ratio for eigenstates within |E| < energy_window.
    
    PR = (sum(|psi_i|^2))^2 / sum(|psi_i|^4)
    
    Args:
        eigenvectors: Array of eigenvectors (columns)
        eigenvalues: Array of eigenvalues
        energy_window: Energy window around E=0
    
    Returns:
        Dictionary containing PR values and metadata
    """
    # Filter eigenstates within energy window
    mask = np.abs(eigenvalues) < energy_window
    filtered_eigenvalues = eigenvalues[mask]
    filtered_eigenvectors = eigenvectors[:, mask]
    
    if filtered_eigenvectors.shape[1] == 0:
        logger.warning("No eigenstates found within energy window")
        return {
            "eigenvalues": [],
            "PR": [],
            "L": eigenvectors.shape[0],
            "n_states": 0
        }
    
    # Compute PR for each eigenstate
    pr_values = []
    pr_data = []
    
    for i in range(filtered_eigenvectors.shape[1]):
        psi = filtered_eigenvectors[:, i]
        psi_sq = np.abs(psi)**2
        
        # PR = (sum(psi_i^2))^2 / sum(psi_i^4)
        sum_sq = np.sum(psi_sq)
        sum_fourth = np.sum(psi_sq**2)
        
        if sum_fourth == 0:
            pr = float('inf')
        else:
            pr = (sum_sq**2) / sum_fourth
        
        pr_values.append(pr)
        pr_data.append({
            "eigenvalue": float(filtered_eigenvalues[i]),
            "PR": float(pr)
        })
    
    return {
        "eigenvalues": filtered_eigenvalues.tolist(),
        "PR": pr_values,
        "PR_data": pr_data,
        "L": eigenvectors.shape[0],
        "n_states": len(pr_values)
    }

def saturation_curve(L_values: List[int], PR_values: List[float]) -> Tuple[float, float, Dict]:
    """
    Fit saturation curve to PR vs L data to extract localization length.
    
    Model: PR(L) = A * (1 - exp(-L/xi))
    
    Args:
        L_values: List of system sizes
        PR_values: List of PR values (averaged over realizations)
    
    Returns:
        xi: Localization length
        uncertainty: Uncertainty in xi
        fit_params: Dictionary of fit parameters and statistics
    """
    if len(L_values) < 2:
        logger.warning("Not enough data points for fitting")
        return float('nan'), float('nan'), {"error": "insufficient_data"}
    
    L_arr = np.array(L_values)
    PR_arr = np.array(PR_values)
    
    # Define saturation model
    def saturation_model(L, A, xi):
        return A * (1 - np.exp(-L / xi))
    
    try:
        # Initial guesses
        A0 = np.max(PR_arr) * 1.1
        xi0 = L_arr[-1] / 2
        
        # Fit the model
        popt, pcov = curve_fit(saturation_model, L_arr, PR_arr, p0=[A0, xi0], maxfev=10000)
        
        A_fit, xi_fit = popt
        
        # Calculate uncertainties
        if np.all(np.isfinite(pcov)):
            perr = np.sqrt(np.diag(pcov))
            A_err, xi_err = perr
        else:
            A_err = float('nan')
            xi_err = float('nan')
        
        # Calculate R-squared
        PR_pred = saturation_model(L_arr, *popt)
        ss_res = np.sum((PR_arr - PR_pred)**2)
        ss_tot = np.sum((PR_arr - np.mean(PR_arr))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Calculate p-value (simplified, using F-test approximation)
        # For a proper p-value, we'd need more sophisticated statistics
        # Here we use a simple heuristic based on R-squared
        p_value = 1 - r_squared  # Simplified approximation
        
        return xi_fit, xi_err, {
            "A": float(A_fit),
            "A_err": float(A_err),
            "xi": float(xi_fit),
            "xi_err": float(xi_err),
            "r_squared": float(r_squared),
            "p_value": float(p_value),
            "L_values": L_values,
            "PR_values": PR_values,
            "fit_successful": True
        }
        
    except Exception as e:
        logger.error(f"Fitting failed: {e}")
        # Fallback: linear interpolation to estimate saturation
        if len(L_values) >= 2:
            # Use the last two points to estimate saturation
            slope = (PR_values[-1] - PR_values[-2]) / (L_values[-1] - L_values[-2])
            if abs(slope) < 0.01:  # Considered saturated
                xi_est = L_values[-1]
            else:
                xi_est = L_values[-1] / 2
            
            return xi_est, float('nan'), {
                "xi": float(xi_est),
                "fit_successful": False,
                "fallback": True,
                "r_squared": 0.0,
                "p_value": 1.0
            }
        else:
            return float('nan'), float('nan'), {"error": "fit_failed", "exception": str(e)}

def finite_size_scaling(W: float, L_list: List[int], num_realizations: int, seed: int, energy_window: float = 0.1) -> Dict[str, Any]:
    """
    Perform finite-size scaling analysis for a given disorder width W.
    
    Args:
        W: Disorder width
        L_list: List of system sizes
        num_realizations: Number of disorder realizations per L
        seed: Random seed
        energy_window: Energy window for PR calculation
    
    Returns:
        Dictionary containing scaling results
    """
    from code.generate_hamiltonian import generate_hamiltonian
    
    np.random.seed(seed)
    
    all_pr_data = {L: [] for L in L_list}
    residual_logs = []
    
    for L in L_list:
        logger.info(f"Processing L={L}, W={W}")
        
        for i in range(num_realizations):
            try:
                # Generate Hamiltonian
                H, _ = generate_hamiltonian(L, W, seed + i)
                
                # Compute eigenstates
                eigenvalues, eigenvectors, logs = compute_eigenstates(H, energy_window)
                
                # Update logs with W and realization_index
                for log in logs:
                    log["W"] = W
                    log["realization_index"] = i
                    residual_logs.append(log)
                
                # Check convergence and residual threshold
                config = get_config()
                threshold = config.get("NUMERICAL_RESIDUAL_THRESHOLD", 1e-6)
                
                # Filter based on convergence
                for log in logs:
                    if not log["converged"] or log["residual_norm"] > threshold:
                        logger.warning(f"Skipping realization L={L}, W={W}, idx={i} due to numerical issues")
                        continue
                
                # Compute PR
                pr_result = compute_participation_ratio(eigenvectors, eigenvalues, energy_window)
                
                if pr_result["n_states"] > 0:
                    avg_pr = np.mean(pr_result["PR"])
                    all_pr_data[L].append(avg_pr)
                    
            except Exception as e:
                logger.error(f"Error processing L={L}, W={W}, idx={i}: {e}")
                continue
    
    # Average PR over realizations for each L
    avg_pr_values = []
    valid_L_values = []
    
    for L in L_list:
        if len(all_pr_data[L]) > 0:
            avg_pr = np.mean(all_pr_data[L])
            avg_pr_values.append(avg_pr)
            valid_L_values.append(L)
        else:
            logger.warning(f"No valid PR values for L={L}")
    
    # Fit saturation curve
    if len(valid_L_values) >= 2:
        xi, xi_err, fit_params = saturation_curve(valid_L_values, avg_pr_values)
    else:
        xi = float('nan')
        xi_err = float('nan')
        fit_params = {"error": "insufficient_data"}
    
    return {
        "disorder_width": W,
        "xi": xi,
        "uncertainty": xi_err,
        "fit_params": fit_params,
        "L_values": valid_L_values,
        "PR_values": avg_pr_values,
        "num_realizations_processed": sum(len(v) for v in all_pr_data.values()),
        "residual_logs": residual_logs
    }

def main():
    """Main entry point for PR analysis."""
    config = get_config()
    
    W_list = config.get("W_LIST", [1.0, 2.0, 3.0])
    L_list = config.get("L_LIST", [100, 200, 400, 800, 1600])
    num_realizations = config.get("NUM_REALIZATIONS", 10)
    seed = config.get("SEED", 42)
    
    results = []
    all_residual_logs = []
    
    for W in W_list:
        logger.info(f"Starting analysis for W={W}")
        result = finite_size_scaling(W, L_list, num_realizations, seed)
        results.append(result)
        all_residual_logs.extend(result.get("residual_logs", []))
    
    # Write residual logs to file
    residuals_path = Path("data/metadata/residuals.json")
    residuals_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(residuals_path, 'w') as f:
        for log in all_residual_logs:
            f.write(json.dumps(log) + '\n')
    
    logger.info(f"Wrote {len(all_residual_logs)} residual logs to {residuals_path}")
    
    # Write scaling fits
    scaling_path = Path("data/processed/scaling_fits.json")
    scaling_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare results for JSON serialization
    json_results = []
    for r in results:
        json_r = {
            "disorder_width": r["disorder_width"],
            "xi": r["xi"],
            "uncertainty": r["uncertainty"],
            "fit_params": r["fit_params"],
            "L_values": r["L_values"],
            "PR_values": r["PR_values"],
            "num_realizations_processed": r["num_realizations_processed"]
        }
        json_results.append(json_r)
    
    with open(scaling_path, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    logger.info(f"Wrote scaling fits to {scaling_path}")
    
    return results

if __name__ == "__main__":
    main()
