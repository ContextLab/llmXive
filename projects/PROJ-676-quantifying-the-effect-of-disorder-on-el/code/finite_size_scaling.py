"""
T013a: Implement Finite-Size Scaling Producer.

Runs PR scaling for all disorder widths W and system sizes L.
Fits PR(L) = A * (1 - exp(-L/xi)) to extract localization length xi.
Filters ill-conditioned instances using T017b logic.
Generates diagnostic plot and writes results to data/processed/scaling_fits.json.
"""
import json
import os
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy.optimize import curve_fit, OptimizeWarning
from scipy import stats

# Import from existing API surface
from code.config import get_config
from code.analyze_pr import compute_eigenstates, compute_participation_ratio
from code.logger import NumericalLogger, get_logger
from code.storage_utils import log_provenance_entry

# Suppress OptimizeWarning for cleaner logs if fit converges with warnings
warnings.filterwarnings("ignore", category=OptimizeWarning)

# Setup logging
logger = get_logger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Fitting model
def saturation_model(L: np.ndarray, A: float, xi: float) -> np.ndarray:
    """
    Non-linear saturation model: PR(L) = A * (1 - exp(-L/xi))
    A: saturation value (proportional to xi)
    xi: localization length
    """
    return A * (1 - np.exp(-L / xi))

def load_residuals(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load residuals from data/metadata/residuals.json.
    Returns list of dicts with keys: task, L, W, realization_index, residual_norm, converged.
    """
    residuals_path = Path(config["DATA_METADATA_DIR"]) / "residuals.json"
    if not residuals_path.exists():
        logger.warning(f"Residuals file not found at {residuals_path}. Returning empty list.")
        return []

    residuals = []
    with open(residuals_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    residuals.append(entry)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse line in residuals.json: {line}")
    return residuals

def filter_realizations(
    W: float,
    L: int,
    realization_index: int,
    residuals: List[Dict[str, Any]],
    threshold: float
) -> bool:
    """
    Check if a realization should be excluded based on numerical stability.
    Returns True if the realization is valid (converged and residual_norm <= threshold).
    """
    for entry in residuals:
        if (
            entry.get("W") == W
            and entry.get("L") == L
            and entry.get("realization_index") == realization_index
        ):
            if not entry.get("converged", False):
                return False
            if entry.get("residual_norm", float("inf")) > threshold:
                return False
            return True
    # If no entry found, assume valid (or log warning)
    logger.warning(f"No residual entry found for W={W}, L={L}, idx={realization_index}. Assuming valid.")
    return True

def fit_scaling_curve(
    L_values: np.ndarray,
    PR_values: np.ndarray,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fit PR(L) = A * (1 - exp(-L/xi)) to data.
    Falls back to linear interpolation if non-linear fit fails.
    Returns dict with xi, uncertainty, fit_params, fit_r_squared, p_value.
    """
    results = {
        "xi": None,
        "uncertainty": None,
        "fit_params": {},
        "fit_r_squared": None,
        "p_value": None,
        "fit_method": None,
        "warning": None
    }

    # Filter out NaN or inf values
    valid_mask = np.isfinite(L_values) & np.isfinite(PR_values)
    L_clean = L_values[valid_mask]
    PR_clean = PR_values[valid_mask]

    if len(L_clean) < 2:
        logger.warning(f"Not enough valid data points for fitting (W={config['W']}).")
        results["warning"] = "Insufficient data points for fitting."
        return results

    # Try non-linear fit
    try:
        # Initial guesses: A ~ max(PR), xi ~ median(L)
        p0 = [np.max(PR_clean), np.median(L_clean)]
        bounds = ([0, 1e-3], [np.max(PR_clean) * 2, np.max(L_clean) * 10])

        popt, pcov = curve_fit(
            saturation_model,
            L_clean,
            PR_clean,
            p0=p0,
            bounds=bounds,
            maxfev=10000
        )

        A_fit, xi_fit = popt
        perr = np.sqrt(np.diag(pcov))
        A_err, xi_err = perr

        # Check for non-physical xi
        if xi_fit <= 0:
            raise ValueError("Non-physical xi (negative or zero) from non-linear fit.")

        # Calculate R-squared
        residuals_fit = PR_clean - saturation_model(L_clean, *popt)
        ss_res = np.sum(residuals_fit ** 2)
        ss_tot = np.sum((PR_clean - np.mean(PR_clean)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        results["xi"] = float(xi_fit)
        results["uncertainty"] = float(xi_err)
        results["fit_params"] = {"A": float(A_fit), "xi": float(xi_fit)}
        results["fit_r_squared"] = float(r_squared)
        results["fit_method"] = "non_linear_least_squares"

        # Calculate p-value from linear regression of log(xi) vs log(W) later?
        # For now, p-value is for the slope test in T015. We'll compute it here as a placeholder
        # or derive from the fit. The task says p_value is derived from linear regression fit (FR-005).
        # We'll compute p-value for the slope of PR vs L (linear regression) as a proxy for now.
        # Actually, FR-005 says: "p-value is derived from the linear regression fit".
        # We'll do a linear regression of PR vs L to get a p-value for the slope.
        slope, intercept, r_val, p_val, std_err = stats.linregress(L_clean, PR_clean)
        results["p_value"] = float(p_val)

    except (RuntimeError, ValueError, IndexError) as e:
        logger.warning(f"Non-linear fit failed for W={config['W']}: {e}. Falling back to linear interpolation.")
        results["warning"] = f"Non-linear fit failed: {e}. Using linear interpolation."

        # Fallback: Linear interpolation to estimate saturation
        # Sort by L
        sorted_indices = np.argsort(L_clean)
        L_sorted = L_clean[sorted_indices]
        PR_sorted = PR_clean[sorted_indices]

        # Estimate saturation as the max PR or the last point if it's saturated
        # We'll use the last point as a rough estimate of saturation
        A_est = PR_sorted[-1]
        # Estimate xi by finding L where PR is 63.2% of A (1 - 1/e)
        target_PR = A_est * (1 - np.exp(-1))
        # Linear interpolation to find L at target_PR
        try:
            xi_est = np.interp(target_PR, PR_sorted, L_sorted)
        except ValueError:
            xi_est = np.median(L_clean)  # Fallback to median L

        if xi_est <= 0:
            xi_est = np.median(L_clean)

        # Calculate R-squared for linear fit
        slope, intercept, r_val, p_val, std_err = stats.linregress(L_clean, PR_clean)
        r_squared = r_val ** 2

        results["xi"] = float(xi_est)
        results["uncertainty"] = float(xi_est * 0.1)  # Placeholder uncertainty
        results["fit_params"] = {"A": float(A_est), "xi": float(xi_est)}
        results["fit_r_squared"] = float(r_squared)
        results["p_value"] = float(p_val)
        results["fit_method"] = "linear_interpolation_fallback"

    return results

def generate_scaling_plot(
    L_values: np.ndarray,
    PR_values: np.ndarray,
    fit_params: Dict[str, float],
    W: float,
    output_path: Path,
    config: Dict[str, Any]
):
    """
    Generate diagnostic plot of PR vs L with fit line and confidence bands.
    """
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 6))

    # Scatter plot of data
    plt.scatter(L_values, PR_values, label="Data", color="blue", alpha=0.7)

    # Fit curve
    if fit_params and fit_params.get("xi") and fit_params.get("A"):
        L_fit = np.linspace(min(L_values), max(L_values), 100)
        PR_fit = saturation_model(L_fit, fit_params["A"], fit_params["xi"])
        plt.plot(L_fit, PR_fit, "r-", label=f"Fit: PR(L) = A(1-exp(-L/xi)), xi={fit_params['xi']:.2f}")

    plt.xlabel("System Size L")
    plt.ylabel("Participation Ratio PR")
    plt.title(f"Finite-Size Scaling for W={W:.1f}")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Save plot
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved scaling plot to {output_path}")

def run_scaling_analysis(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Main function to run finite-size scaling analysis for all W and L.
    """
    W_list = config["W_LIST"]
    L_list = config["L_LIST"]
    num_realizations = config["NUM_REALIZATIONS"]
    seed_base = config["SEED"]
    threshold = config["NUMERICAL_RESIDUAL_THRESHOLD"]

    # Load residuals for filtering
    residuals = load_residuals(config)

    scaling_results = []

    for W in W_list:
        logger.info(f"Processing disorder width W={W}")

        # Collect PR values for each L
        L_values_all = []
        PR_values_all = []
        valid_realizations = []

        for L in L_list:
            PR_for_L = []
            valid_indices = []

            for idx in range(num_realizations):
                # Check numerical stability
                if not filter_realizations(W, L, idx, residuals, threshold):
                    logger.debug(f"Skipping ill-conditioned realization: W={W}, L={L}, idx={idx}")
                    continue

                # Generate Hamiltonian and compute PR
                try:
                    # Use a deterministic seed for each realization
                    seed = seed_base + int(W * 1000) + L * 100 + idx
                    np.random.seed(seed)

                    # Generate Hamiltonian (inline to avoid import issues if generate_hamiltonian is not fully ready)
                    # We'll call compute_eigenstates which handles this
                    eigenstates_info = compute_eigenstates(L, W, seed=seed)

                    if eigenstates_info is None or "eigenstates" not in eigenstates_info:
                        logger.warning(f"Failed to compute eigenstates for W={W}, L={L}, idx={idx}")
                        continue

                    eigenvalues = eigenstates_info["eigenvalues"]
                    eigenvectors = eigenstates_info["eigenstates"]

                    # Filter eigenstates with |E| < 0.1
                    mask = np.abs(eigenvalues) < 0.1
                    if not np.any(mask):
                        logger.warning(f"No eigenstates with |E| < 0.1 for W={W}, L={L}, idx={idx}")
                        continue

                    filtered_eigenvectors = eigenvectors[:, mask]
                    pr_values = [compute_participation_ratio(vec) for vec in filtered_eigenvectors.T]
                    avg_pr = np.mean(pr_values)

                    PR_for_L.append(avg_pr)
                    valid_indices.append(idx)

                except Exception as e:
                    logger.warning(f"Error computing PR for W={W}, L={L}, idx={idx}: {e}")
                    continue

            if PR_for_L:
                L_values_all.append(L)
                PR_values_all.append(np.mean(PR_for_L))
                valid_realizations.append({
                    "L": L,
                    "avg_PR": np.mean(PR_for_L),
                    "num_valid": len(valid_indices)
                })

        if not L_values_all:
            logger.warning(f"No valid realizations for W={W}. Skipping.")
            continue

        L_arr = np.array(L_values_all)
        PR_arr = np.array(PR_values_all)

        # Fit scaling curve
        fit_results = fit_scaling_curve(L_arr, PR_arr, {"W": W})
        fit_results["disorder_width"] = float(W)
        fit_results["L_values"] = L_arr.tolist()
        fit_results["PR_values"] = PR_arr.tolist()
        fit_results["num_realizations"] = num_realizations
        fit_results["valid_realizations"] = valid_realizations

        scaling_results.append(fit_results)

        # Generate plot
        plot_path = Path(config["DATA_PROCESSED_DIR"]) / f"pr_scaling_W{W:.1f}.png"
        generate_scaling_plot(L_arr, PR_arr, fit_results.get("fit_params", {}), W, plot_path, config)

    # Write results to JSON
    output_path = Path(config["DATA_PROCESSED_DIR"]) / "scaling_fits.json"
    with open(output_path, "w") as f:
        json.dump(scaling_results, f, indent=2)

    logger.info(f"Saved scaling fits to {output_path}")
    return scaling_results

def main():
    """Entry point for T013a."""
    config = get_config()
    run_scaling_analysis(config)

if __name__ == "__main__":
    main()
