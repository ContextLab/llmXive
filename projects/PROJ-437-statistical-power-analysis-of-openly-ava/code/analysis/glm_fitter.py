"""
GLM Fitter module for estimating effect sizes and p-values.

This version implements the full reusable ``fit_glm`` function required by
task T016 and ensures that convergence information is logged to
``data/aggregated/convergence_log.json`` in the schema expected by the
convergence monitor.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

from utils.seed_manager import set_global_seed, get_seed

logger = logging.getLogger(__name__)


class GLMFitError(Exception):
    """Raised when GLM fitting fails."""


class ConvergenceLogger:
    """Handles logging of GLM convergence status."""

    def __init__(self, log_path: Union[str, Path] = "data/aggregated/convergence_log.json"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[Dict[str, Any]] = self._load_existing()

    def _load_existing(self) -> List[Dict[str, Any]]:
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Support both legacy and new formats
                    if isinstance(data, dict) and "convergence_records" in data:
                        return data["convergence_records"]
                    if isinstance(data, list):
                        return data
            except (json.JSONDecodeError, IOError):
                logger.warning("Failed to read existing convergence log; starting fresh.")
        return []

    def log(
        self,
        iteration_id: int,
        sample_size: int,
        kernel: str,
        converged: bool,
        max_iterations: int,
        tolerance: float,
        error_message: Union[str, None] = None,
    ) -> None:
        """
        Record a single GLM fit entry.

        The schema matches the one required by the convergence monitor:
        {
            "iteration_id": int,
            "sample_size": int,
            "kernel": str,
            "converged": bool,
            "max_iterations": int,
            "tolerance": float,
            "error_message": str | null
        }
        """
        entry = {
            "iteration_id": iteration_id,
            "sample_size": sample_size,
            "kernel": kernel,
            "converged": converged,
            "max_iterations": max_iterations,
            "tolerance": tolerance,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._entries.append(entry)

    def save(self) -> None:
        """Write the accumulated entries to disk."""
        payload = {"metadata": {"generated_at": datetime.utcnow().isoformat()}, "convergence_records": self._entries}
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Saved {len(self._entries)} convergence entries to {self.log_path}")


def load_and_subsample_data(data_path: Union[str, Path], sample_size: int, seed: Union[int, None] = None) -> pd.DataFrame:
    """
    Load data from CSV or NumPy file and randomly subsample ``sample_size`` rows.
    """
    if seed is None:
        seed = get_seed()
    set_global_seed(seed)

    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    if data_path.suffix == ".csv":
        df = pd.read_csv(data_path)
    elif data_path.suffix == ".npy":
        arr = np.load(data_path)
        df = pd.DataFrame(arr)
    else:
        raise ValueError(f"Unsupported data format: {data_path.suffix}")

    actual_n = min(sample_size, len(df))
    if actual_n < sample_size:
        logger.warning(f"Requested {sample_size} subjects but only {len(df)} available; using {actual_n}.")
    return df.sample(n=actual_n, random_state=seed).reset_index(drop=True)


def fit_glm(y: np.ndarray, X: np.ndarray, max_iter: int = 100, tol: float = 1e-4) -> Tuple[bool, Dict[str, float]]:
    """
    Fit a linear regression model using OLS.

    Returns a tuple ``(converged, result_dict)`` where ``result_dict`` contains
    ``rsquared``, ``rsquared_adj``, ``f_pvalue`` and the coefficient list.
    """
    try:
        X_const = add_constant(X)
        model = OLS(y, X_const)
        results = model.fit(maxiter=max_iter, tol=tol)
        converged = results.rank == X_const.shape[1]
        return converged, {
            "rsquared": float(results.rsquared),
            "rsquared_adj": float(results.rsquared_adj),
            "f_pvalue": float(results.f_pvalue),
            "coefs": results.params.tolist(),
        }
    except Exception as exc:
        logger.error(f"GLM fitting error: {exc}")
        return False, {"error": str(exc)}


def estimate_effect_size(control: np.ndarray, treatment: np.ndarray) -> float:
    """
    Compute Cohen's d between two groups.
    """
    mean_c = np.mean(control)
    mean_t = np.mean(treatment)
    pooled_std = np.sqrt((np.var(control) + np.var(treatment)) / 2)
    if pooled_std == 0:
        return 0.0
    return (mean_t - mean_c) / pooled_std


def fit_glm_batch(
    data: pd.DataFrame,
    design_matrix: np.ndarray,
    sample_size: int,
    seed: Union[int, None] = None,
    iteration_id: int = 0,
    paradigm: str = "unknown",
    kernel: str = "default",
) -> Dict[str, Any]:
    """
    Perform a full GLM fitting pipeline on a subsampled dataset.

    The function:

    1. Subsamples ``sample_size`` rows.
    2. Fits a GLM.
    3. Estimates Cohen's d between the first and second half of the outcome.
    4. Logs convergence information.

    Returns a dictionary with ``effect_size``, ``p_value``, ``converged`` and
    ``sample_size_used``.
    """
    if seed is None:
        seed = get_seed()
    set_global_seed(seed)

    # Subsample
    if len(data) > sample_size:
        df = data.sample(n=sample_size, random_state=seed).reset_index(drop=True)
    else:
        df = data.copy()

    # Prepare y and X
    y = df.iloc[:, 0].to_numpy()
    X = design_matrix[: len(df)]
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    # Fit GLM
    converged, fit_res = fit_glm(y, X)

    # Effect size (compare first vs second half)
    half = len(y) // 2
    if half > 1:
        control = y[:half]
        treatment = y[half : half * 2]
        effect_size = estimate_effect_size(control, treatment)
        t_stat, p_value = stats.ttest_ind(control, treatment)
    else:
        effect_size = 0.0
        p_value = 1.0

    # Log convergence
    logger_entry = ConvergenceLogger()
    logger_entry.log(
        iteration_id=iteration_id,
        sample_size=len(df),
        kernel=kernel,
        converged=converged,
        max_iterations=100,
        tolerance=1e-4,
        error_message=None if converged else "GLM did not converge",
    )
    logger_entry.save()

    return {
        "effect_size": float(effect_size),
        "p_value": float(p_value),
        "converged": converged,
        "sample_size_used": len(df),
        "rsquared": float(fit_res.get("rsquared", 0.0)),
    }


def main() -> int:
    """CLI entry point for quick manual testing."""
    parser = argparse.ArgumentParser(description="Fit GLM on a dataset")
    parser.add_argument("--data", type=str, required=True, help="Path to CSV or NPY data file")
    parser.add_argument("--sample-size", type=int, default=20, help="Number of subjects to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/aggregated/glm_results.json")
    args = parser.parse_args()

    df = load_and_subsample_data(args.data, args.sample_size, args.seed)
    design = np.ones((len(df), 1))  # intercept only
    result = fit_glm_batch(df, design, args.sample_size, seed=args.seed, iteration_id=0, paradigm="cli")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"GLM fitting complete – results written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())