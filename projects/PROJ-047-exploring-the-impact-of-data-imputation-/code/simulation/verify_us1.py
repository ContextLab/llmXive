"""
Verification logic for User Story 1 (T014).
Calculates Spearman correlation between the missingness mask M and the
*complete* outcome Y for each simulation run, stores the result in a JSON
file, and flags runs that do not meet the specification.
"""
import json
import hashlib
import os
from typing import List, Dict, Any, Tuple

import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

# Default output location – can be overridden by callers
DEFAULT_OUTPUT_PATH = "data/results/us1_verification.json"


def compute_run_id(seed: int, beta: float) -> str:
    """
    Compute a deterministic SHA‑256 hash for a run based on its seed and
    MNAR parameter beta.

    Parameters
    ----------
    seed : int
        Random seed used for the simulation run.
    beta : float
        MNAR intensity parameter for the run.

    Returns
    -------
    str
        Hex‑encoded SHA‑256 hash of the string ``f"{seed}_{beta}"``.
    """
    return hashlib.sha256(f"{seed}_{beta}".encode()).hexdigest()


def verify_mnar_correlation(mask: np.ndarray, y_complete: np.ndarray) -> Tuple[float, float]:
    """
    Compute the Spearman rank correlation between the missingness mask and the
    complete outcome vector.

    Parameters
    ----------
    mask : np.ndarray
        1‑D array (or flattenable) indicating missingness (1 = missing, 0 = observed).
    y_complete : np.ndarray
        1‑D array (or flattenable) of the *complete* outcome values before masking.

    Returns
    -------
    Tuple[float, float]
        (rho, p_value) – Spearman correlation coefficient and two‑tailed p‑value.
    """
    # Ensure 1‑D vectors
    mask_flat = np.asarray(mask).ravel()
    y_flat = np.asarray(y_complete).ravel()

    # Guard against degenerate inputs
    if mask_flat.size < 2 or y_flat.size < 2:
        logger.warning("Not enough data points for Spearman correlation.")
        return 0.0, 1.0

    # Remove any NaNs (should not be present, but be safe)
    valid = ~np.isnan(mask_flat) & ~np.isnan(y_flat)
    if np.sum(valid) < 2:
        logger.warning("All data points contain NaNs after filtering.")
        return 0.0, 1.0

    rho, p_value = stats.spearmanr(mask_flat[valid], y_flat[valid])
    # scipy can return nan if constant; handle gracefully
    if np.isnan(rho) or np.isnan(p_value):
        logger.warning("Spearman calculation returned NaN.")
        return 0.0, 1.0

    return float(rho), float(p_value)


def _load_existing_results(output_path: str) -> List[Dict[str, Any]]:
    """
    Helper to load previously saved verification results, if any.
    """
    if os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    logger.warning(
                        f"Unexpected JSON structure in {output_path}; resetting file."
                    )
        except Exception as e:
            logger.error(f"Failed to read existing verification file: {e}")
    return []


def _save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the list of verification dictionaries to ``output_path``.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)


def run_verification_and_save(
    seed: int,
    beta: float,
    mask_data: np.ndarray,
    complete_y: np.ndarray,
    output_path: str = DEFAULT_OUTPUT_PATH,
) -> Dict[str, Any]:
    """
    Perform verification for a single run and append the result to the
    JSON file at ``output_path``.

    Parameters
    ----------
    seed : int
        Random seed for the simulation run.
    beta : float
        MNAR intensity parameter.
    mask_data : np.ndarray
        Missingness indicator array (same length as ``complete_y``).
    complete_y : np.ndarray
        Complete outcome values before missingness injection.
    output_path : str, optional
        Destination JSON file. Defaults to ``data/results/us1_verification.json``.

    Returns
    -------
    Dict[str, Any]
        The verification record that was written.
    """
    run_id = compute_run_id(seed, beta)
    rho, p_value = verify_mnar_correlation(mask_data, complete_y)

    status = "passed" if (rho > 0.5 and p_value < 0.01) else "failed"
    if status == "failed":
        logger.warning(
            f"Run {run_id}: MNAR verification failed (rho={rho:.4f}, p={p_value:.4f})"
        )

    record = {
        "run_id": run_id,
        "correlation": rho,
        "p_value": p_value,
        "status": status,
    }

    # Load existing results, append, and write back
    results = _load_existing_results(output_path)
    # Ensure we don't duplicate entries for the same run_id
    results = [r for r in results if r.get("run_id") != run_id]
    results.append(record)
    _save_results(results, output_path)

    return record


def main() -> None:
    """
    CLI entry point – useful for ad‑hoc verification outside the main
    simulation loop. Accepts file paths for mask and complete Y so the
    script can be invoked independently.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify MNAR correlation for a single simulation run"
    )
    parser.add_argument("--seed", type=int, required=True, help="Run seed")
    parser.add_argument("--beta", type=float, required=True, help="MNAR beta")
    parser.add_argument(
        "--mask-file",
        type=str,
        required=True,
        help="Path to a NumPy ``.npy`` file containing the mask array",
    )
    parser.add_argument(
        "--y-file",
        type=str,
        required=True,
        help="Path to a NumPy ``.npy`` file containing the complete Y array",
    )
    parser.add_argument(
        "--output",
      type=str,
        default=DEFAULT_OUTPUT_PATH,
        help="Destination JSON file for verification results",
    )

    args = parser.parse_args()

    # Load arrays from the provided .npy files
    mask_array = np.load(args.mask_file)
    y_array = np.load(args.y_file)

    run_verification_and_save(
        seed=args.seed,
        beta=args.beta,
        mask_data=mask_array,
        complete_y=y_array,
        output_path=args.output,
    )
    print(f"Verification result written to {args.output}")


if __name__ == "__main__":
    main()