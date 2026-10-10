"""
Metrics calculation module for meta-analysis estimation results.

Calculates bias, coverage, and I^2 statistics (FR-003).

The true effect used for bias and coverage is read STRICTLY from the
``injected_true_effect`` column of the simulation output; no other
source of the ground truth is accepted.
"""

import math
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

from utils.logging import get_logger

logger = get_logger(__name__)

# Column name that is the single source of truth for the ground truth
# effect size injected during simulation.
TRUE_EFFECT_COLUMN = "injected_true_effect"


class MetricsResult:
    """Container for calculated metrics."""
    def __init__(
        self,
        replicate_id: int,
        true_effect: float,
        pooled_estimate: float,
        ci_lower: float,
        ci_upper: float,
        tau_squared_estimate: float,
        i_squared: float,
        bias: float,
        coverage_flag: bool
    ):
        self.replicate_id = replicate_id
        self.true_effect = true_effect
        self.pooled_estimate = pooled_estimate
        self.ci_lower = ci_lower
        self.ci_upper = ci_upper
        self.tau_squared_estimate = tau_squared_estimate
        self.i_squared = i_squared
        self.bias = bias
        self.coverage_flag = coverage_flag

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replicate_id": self.replicate_id,
            "true_effect": self.true_effect,
            "pooled_estimate": self.pooled_estimate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "tau_squared_estimate": self.tau_squared_estimate,
            "i_squared": self.i_squared,
            "bias": self.bias,
            "coverage_flag": self.coverage_flag
        }


def calculate_bias(pooled_estimate: float, true_effect: float) -> float:
    """Calculates the bias of the pooled estimate."""
    return pooled_estimate - true_effect


def calculate_coverage(
    ci_lower: float,
    ci_upper: float,
    true_effect: float
) -> bool:
    """Checks if the true effect is within the confidence interval."""
    return ci_lower <= true_effect <= ci_upper


def calculate_i_squared(
    effect_sizes: List[float],
    standard_errors: List[float],
    pooled_estimate: float
) -> float:
    """
    Calculates the I^2 statistic.
    I^2 = max(0, (Q - df) / Q) * 100
    where Q = sum(w_i * (y_i - pooled)^2) and df = k - 1
    """
    k = len(effect_sizes)
    if k < 2:
        return 0.0

    # Weights (inverse variance)
    weights = [1.0 / (se**2) for se in standard_errors]

    # Q statistic
    q = sum(w * (y - pooled_estimate)**2 for w, y in zip(weights, effect_sizes))
    df = k - 1

    if q <= df:
        return 0.0

    i_squared = (q - df) / q
    return i_squared * 100.0


def _extract_true_effect(record: Dict[str, Any]) -> float:
    """
    Extract the true effect STRICTLY from the ``injected_true_effect``
    column of a simulation-output record.

    Raises:
        KeyError: If the ``injected_true_effect`` column is absent.
            No fallback column is ever consulted.
        ValueError: If the value is not a finite number.
    """
    if TRUE_EFFECT_COLUMN not in record:
        raise KeyError(
            f"Simulation output record is missing the required column "
            f"'{TRUE_EFFECT_COLUMN}'; the true effect must be read "
            f"strictly from that column (FR-003)."
        )
    value = record[TRUE_EFFECT_COLUMN]
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Column '{TRUE_EFFECT_COLUMN}' contains a non-numeric "
            f"value: {record[TRUE_EFFECT_COLUMN]!r}"
        )
    if not math.isfinite(value):
        raise ValueError(
            f"Column '{TRUE_EFFECT_COLUMN}' contains a non-finite "
            f"value: {value!r}"
        )
    return value


def compute_metrics_from_simulation(
    simulation_records: List[Dict[str, Any]]
) -> List[MetricsResult]:
    """
    Compute per-replicate metrics (bias, 95% CI coverage) from the
    simulation output, reading the true effect strictly from the
    ``injected_true_effect`` column of each record (FR-003).

    Each record is expected to contain:
      - injected_true_effect: the ground-truth effect size
      - pooled_effect: the estimated pooled effect
      - ci_lower / ci_upper: confidence interval bounds
      - replicate_id (optional): replicate identifier
      - tau_squared_estimate (optional): estimated tau^2
      - i_squared (optional): I^2 statistic; if absent it is computed
        from effect_sizes / standard_errors when those are present,
        otherwise defaults to 0.0

    Returns:
        List of MetricsResult, one per record.

    Raises:
        KeyError: If any required column is missing.
        ValueError: If any required value is non-numeric/non-finite.
    """
    if not simulation_records:
        return []

    results: List[MetricsResult] = []
    for idx, record in enumerate(simulation_records):
        true_effect = _extract_true_effect(record)

        for key in ("pooled_effect", "ci_lower", "ci_upper"):
            if key not in record:
                raise KeyError(
                    f"Simulation output record {idx} is missing the "
                    f"required column '{key}'."
                )

        pooled = float(record["pooled_effect"])
        ci_lower = float(record["ci_lower"])
        ci_upper = float(record["ci_upper"])
        for name, value in (
            ("pooled_effect", pooled),
            ("ci_lower", ci_lower),
            ("ci_upper", ci_upper),
        ):
            if not math.isfinite(value):
                raise ValueError(
                    f"Record {idx}: '{name}' is non-finite ({value!r})."
                )

        replicate_id = int(record.get("replicate_id", idx))
        tau2 = float(record.get("tau_squared_estimate", 0.0) or 0.0)

        if "i_squared" in record and record["i_squared"] is not None:
            i_squared = float(record["i_squared"])
        elif "effect_sizes" in record and "standard_errors" in record:
            i_squared = calculate_i_squared(
                list(record["effect_sizes"]),
                list(record["standard_errors"]),
                pooled,
            )
        else:
            i_squared = 0.0

        bias = calculate_bias(pooled, true_effect)
        coverage_flag = calculate_coverage(ci_lower, ci_upper, true_effect)

        results.append(
            MetricsResult(
                replicate_id=replicate_id,
                true_effect=true_effect,
                pooled_estimate=pooled,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                tau_squared_estimate=tau2,
                i_squared=i_squared,
                bias=bias,
                coverage_flag=coverage_flag,
            )
        )
        logger.debug(
            "Replicate %s: bias=%.6f coverage=%s",
            replicate_id, bias, coverage_flag,
        )

    logger.info(
        "Computed metrics for %d simulation records "
        "(true effect from '%s').",
        len(results), TRUE_EFFECT_COLUMN,
    )
    return results


def aggregate_metrics(
    results: List[MetricsResult],
    true_effect: Optional[float] = None
) -> Dict[str, Any]:
    """
    Aggregates metrics across all replicates.
    Calculates mean bias, coverage rate, and mean I^2.

    The optional ``true_effect`` argument is retained for backward
    compatibility but is NOT used as a source of the ground truth;
    each MetricsResult already carries the true effect read from the
    ``injected_true_effect`` column.
    """
    if not results:
        return {
            "mean_bias": 0.0,
            "coverage_rate": 0.0,
            "mean_i_squared": 0.0,
            "total_replicates": 0
        }

    biases = [r.bias for r in results]
    coverage_flags = [1.0 if r.coverage_flag else 0.0 for r in results]
    i_squares = [r.i_squared for r in results]

    return {
        "mean_bias": float(np.mean(biases)),
        "mean_absolute_bias": float(np.mean(np.abs(biases))),
        "coverage_rate": float(np.mean(coverage_flags)),
        "mean_i_squared": float(np.mean(i_squares)),
        "total_replicates": len(results)
    }
