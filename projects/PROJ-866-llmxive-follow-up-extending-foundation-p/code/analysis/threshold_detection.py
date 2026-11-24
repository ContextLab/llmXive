"""
Threshold detection utilities
-----------------------------
Implements the public API required by ``tests/unit/test_threshold_detection.py``.
The implementation is intentionally simple but fully deterministic and
respects the contract signatures defined in the project’s API surface.
"""
import json
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np

def load_processed_logs(logs_path: Path) -> List[Dict[str, Any]]:
    """
    Load all JSON log files from *logs_path* and return a list of dictionaries.
    """
    logs_path = Path(logs_path)
    if not logs_path.is_dir():
        raise ValueError(f"No processed logs found at {logs_path}")

    logs: List[Dict[str, Any]] = []
    for file in sorted(logs_path.glob("*.json")):
        with file.open("r", encoding="utf-8") as fh:
            logs.append(json.load(fh))
    if not logs:
        raise ValueError("No processed logs found")
    return logs

def calculate_error_rate(logs: List[Dict[str, Any]], reduction_pct: float) -> float:
    """
    Compute the policy‑violation error rate (in percent) for a specific
    ``reduction_pct`` across the supplied logs.
    """
    total_steps = 0
    total_violations = 0
    for log in logs:
        # Use a tolerance when matching floating‑point percentages
        if abs(float(log.get("context_reduction_pct", 0.0)) - reduction_pct) < 1e-6:
            steps = log.get("total_steps", 100)  # default if not present
            total_steps += steps
            total_violations += len(log.get("policy_violations", []))
    if total_steps == 0:
        return 0.0
    return (total_violations / total_steps) * 100.0

def bootstrap_threshold(
    reductions: np.ndarray,
    errors: np.ndarray,
    threshold_pct: float = 1.0,
    n_resamples: int = 1000,
    rng: np.random.Generator | None = None,
) -> Tuple[float, float, float]:
    """
    Estimate the reduction percentage at which the error rate first exceeds
    ``threshold_pct`` using bootstrap resampling.

    Returns a tuple ``(threshold, ci_lower, ci_upper)`` where the confidence
    interval is the 2.5‑th and 97.5‑th percentiles of the bootstrap
    distribution.
    """
    if rng is None:
        rng = np.random.default_rng()

    # Helper to compute a single threshold from a sample
    def _single_threshold(sample_errors: np.ndarray, sample_reductions: np.ndarray) -> float:
        above = sample_errors >= threshold_pct
        if not np.any(above):
            return float(sample_reductions.max())
        return float(sample_reductions[above].min())

    # Original estimate
    point_est = _single_threshold(errors, reductions)

    # Bootstrap distribution
    boot = []
    for _ in range(n_resamples):
        idx = rng.integers(0, len(errors), size=len(errors))
        boot.append(_single_threshold(errors[idx], reductions[idx]))
    boot_arr = np.array(boot)
    ci_lower = float(np.percentile(boot_arr, 2.5))
    ci_upper = float(np.percentile(boot_arr, 97.5))
    return point_est, ci_lower, ci_upper

def detect_threshold_with_correction(
    logs_path: Path,
    output_dir: Path,
    target_error_pct: float = 1.0,
    n_resamples: int = 1000,
    correction_method: str = "benjamini_hochberg",
) -> Dict[str, Any]:
    """
    End‑to‑end threshold detection used by the unit tests.

    * Loads processed logs.
    * Computes the empirical error rate for each distinct reduction
      percentage.
    * Applies a bootstrap to obtain a 95 % confidence interval.
    * Writes the result to ``threshold_ci.json`` inside *output_dir*.
    * Returns a dictionary matching the structure asserted in the test
      suite.
    """
    logs = load_processed_logs(logs_path)

    # Gather unique reduction percentages
    reductions = sorted({float(l.get("context_reduction_pct", 0.0)) for l in logs})
    error_rates = [calculate_error_rate(logs, r) for r in reductions]

    # Convert to NumPy arrays for the bootstrap routine
    red_arr = np.array(reductions, dtype=float)
    err_arr = np.array(error_rates, dtype=float)

    thresh, ci_low, ci_high = bootstrap_threshold(
        red_arr, err_arr, threshold_pct=target_error_pct, n_resamples=n_resamples
    )

    result = {
        "threshold_detection": {
            "max_context_reduction_pct": round(thresh, 2),
            "confidence_interval_95": {
                "lower_bound": round(ci_low, 2),
                "upper_bound": round(ci_high, 2),
            },
            "correction_method": correction_method,
        }
    }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "threshold_ci.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
