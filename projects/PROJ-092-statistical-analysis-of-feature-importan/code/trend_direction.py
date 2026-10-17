"""Trend direction logic for the Mann-Kendall trend test (T022, FR-005).

Maps a Kendall's Tau statistic to a human-readable trend direction:
  - Tau < 0  -> "monotonic decrease"
  - Tau > 0  -> "monotonic increase"
  - Tau == 0 -> "no trend"

This module is designed to be composed with
``significance_test.mann_kendall_test``, which returns
``(tau, trend_direction, p_value)``: the direction string produced
here follows exactly the contract expected by that API and by
``generate_final_report.aggregate_global_stats`` (key
``trend_direction``).
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

MONOTONIC_DECREASE = "monotonic decrease"
MONOTONIC_INCREASE = "monotonic increase"
NO_TREND = "no trend"


def determine_trend_direction(tau: float) -> str:
    """Return the trend direction string for a Kendall's Tau value.

    Implements FR-005: report "monotonic decrease" if Tau < 0.

    Args:
        tau: Kendall's Tau statistic, expected in [-1, 1].

    Returns:
        One of "monotonic decrease", "monotonic increase", "no trend".

    Raises:
        TypeError: if tau is not a real number.
        ValueError: if tau is outside [-1, 1] or is NaN.
    """
    if isinstance(tau, bool) or not isinstance(tau, (int, float)):
        raise TypeError(f"tau must be a real number, got {type(tau).__name__}")
    tau_f = float(tau)
    if tau_f != tau_f:  # NaN check
        raise ValueError("tau must not be NaN")
    if tau_f < -1.0 or tau_f > 1.0:
        raise ValueError(f"tau must be within [-1, 1], got {tau_f}")

    if tau_f < 0:
        direction = MONOTONIC_DECREASE
    elif tau_f > 0:
        direction = MONOTONIC_INCREASE
    else:
        direction = NO_TREND
    logger.info("Kendall's Tau=%.4f -> trend direction: %s", tau_f, direction)
    return direction


def trend_direction_from_metrics(drift_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Derive the trend direction from a list of drift metric rows.

    Each row is expected to carry a ``rho`` (or ``tau``) numeric field;
    rows without a usable numeric value are skipped. The mean of the
    sequence is used as the trend statistic when no per-row tau is
    available, mirroring the block-permutation test's statistic.

    Returns:
        Dict with keys ``trend_direction``, ``tau`` (the statistic used),
        and ``n_points`` (number of usable points).
    """
    values: List[float] = []
    for row in drift_metrics or []:
        for key in ("tau", "rho", "spearman_rho"):
            raw = row.get(key) if isinstance(row, dict) else None
            if raw is None:
                continue
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            if val == val:  # skip NaN
                values.append(val)
                break

    if not values:
        logger.warning("No usable rho/tau values found; defaulting to 'no trend'.")
        return {"trend_direction": NO_TREND, "tau": 0.0, "n_points": 0}

    statistic = sum(values) / len(values)
    # Clamp to [-1, 1] since a mean of rho values is a valid correlation-like statistic.
    statistic = max(-1.0, min(1.0, statistic))
    return {
        "trend_direction": determine_trend_direction(statistic),
        "tau": statistic,
        "n_points": len(values),
    }


def load_drift_metrics(csv_path: str) -> List[Dict[str, Any]]:
    """Load drift metric rows from ``outputs/drift_metrics.csv``.

    Fails loudly if the file does not exist (never fabricates data).
    """
    import csv

    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(
          f"Drift metrics file not found: {path}. Run the drift analysis "
          "step (code/drift_analysis.py) first."
      )
    with open(path, "r", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def main() -> None:
    """CLI: read drift_metrics.csv, write trend direction to outputs/trend_direction.json.

    Usage:
        python code/trend_direction.py [drift_metrics_csv] [output_json]
    """
    args = sys.argv[1:]
    metrics_path = args[0] if len(args) > 0 else "outputs/drift_metrics.csv"
    output_path = args[1] if len(args) > 1 else "outputs/trend_direction.json"

    metrics = load_drift_metrics(metrics_path)
    result = trend_direction_from_metrics(metrics)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    logger.info("Trend direction report saved to %s", out)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
