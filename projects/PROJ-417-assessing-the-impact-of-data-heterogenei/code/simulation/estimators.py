"""
estimators.py

Meta‑analysis estimators and heterogeneity utilities.

This module provides three standard estimators:
* Fixed‑Effects (FE)
* DerSimonian‑Laird (DL) random‑effects
* Restricted Maximum Likelihood (REML) random‑effects

Each estimator returns an :class:`EstimationResult` that contains
the pooled effect, its standard error, a 95 % confidence interval,
the estimated between‑study variance (``tau2``), heterogeneity
statistics (Cochran's Q and I²), degrees of freedom, a p‑value for
the Q‑test, the number of studies and flags for convergence status
and small‑study warnings.

The module also implements a dispatcher ``apply_estimator`` used by
the test‑suite and the pipeline, and helper functions for logging
REML optimisation failures.
"""

import json
import math
import time
from typing import List, Optional, Dict, Any

import numpy as np
from scipy import optimize
from pathlib import Path  # Added import for Path handling

from utils.logging import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
__all__ = [
    "EstimationResult",
    "REML_FAILURE_LOG_PATH",
    "log_reml_failure",
    "estimate_fixed_effects",
    "estimate_dersimonian_laird",
    "estimate_reml",
    "apply_estimator",
    "calculate_i_squared",
]

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Path for REML failure event logging (FR‑006)
REML_FAILURE_LOG_PATH = "data/results/reml_failures.json"

# Minimum number of studies for reliable chi‑square / df approximations
MIN_STUDIES_FOR_RELIABILITY = 5

# ----------------------------------------------------------------------
# Helper classes / functions
# ----------------------------------------------------------------------
class EstimationResult:
    """
    Container for the results of a meta‑analysis estimation.
    Conforms to the EstimationResult schema.
    """

    def __init__(
        self,
        pooled_effect: float,
        se_pooled: float,
        ci_lower: float,
        ci_upper: float,
        tau2: float,
        i2: float,
        q_statistic: float,
        df: int,
        p_value: float,
        n_studies: int,
        convergence_status: str = "success",
        small_study_flag: bool = False,
    ):
        self.pooled_effect = pooled_effect
        self.se_pooled = se_pooled
        self.ci_lower = ci_lower
        self.ci_upper = ci_upper
        self.tau2 = tau2
        self.i2 = i2
        self.q_statistic = q_statistic
        self.df = df
        self.p_value = p_value
        self.n_studies = n_studies
        self.convergence_status = convergence_status
        self.small_study_flag = small_study_flag

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the result for downstream JSON/CSV output."""
        return {
            "pooled_effect": self.pooled_effect,
            "se_pooled": self.se_pooled,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "tau2": self.tau2,
            "i2": self.i2,
            "q_statistic": self.q_statistic,
            "df": self.df,
            "p_value": self.p_value,
            "n_studies": self.n_studies,
            "convergence_status": self.convergence_status,
            "small_study_flag": self.small_study_flag,
        }

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def log_reml_failure(event: Dict[str, Any], log_path: str = REML_FAILURE_LOG_PATH) -> None:
    """
    Log a REML convergence failure event to a JSON file (FR‑006).

    The file contains a JSON list of event dicts. Each event records the
    failure reason, a timestamp, the fallback action taken, and (when
    available) the data context.

    Parameters
    ----------
    event :
        Dictionary describing the failure.
    log_path :
        Path to the JSON failure log.
    """
    events: List[Dict[str, Any]] = []
    loaded: Optional[Any] = None  # Will hold the original JSON content if present
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                loaded = json.loads(content)
                # Support both legacy plain‑list format and the newer dict format
                if isinstance(loaded, list):
                    events = loaded
                elif isinstance(loaded, dict) and isinstance(loaded.get("events"), list):
                    events = loaded["events"]
    except FileNotFoundError:
        # No previous log – start a fresh list.
        pass
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read existing REML failure log %s: %s", log_path, e)

    # Normalise the event structure.
    event = dict(event)
    event.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%S"))
    events.append(event)

    try:
        # Ensure the parent directory exists before writing.
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        # Preserve backward‑compatible dict wrapper if the original file was a dict
        if isinstance(loaded, dict):
            # Update the wrapper with the new events list and recompute failure_count
            loaded["events"] = events
            loaded["failure_count"] = len(events)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(loaded, f, indent=2)
        else:
            # Plain list format (including the case where the file did not exist)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2)
    except OSError as e:
        logger.error("Could not write REML failure log %s: %s", log_path, e)

# ----------------------------------------------------------------------
# Core statistical helpers
# ----------------------------------------------------------------------
def _check_small_study(n_studies: int) -> bool:
    """Return ``True`` if the dataset has fewer than the reliability threshold."""
    return n_studies < MIN_STUDIES_FOR_RELIABILITY

def calculate_i_squared(q_statistic: float, df: int) -> float:
    """
    Calculate the I² statistic (Higgins & Thompson, 2002).

    I² = max(0, (Q - df) / Q) * 100

    Parameters
    ----------
    q_statistic:
        Cochran's Q heterogeneity statistic.
    df:
        Degrees of freedom (k − 1).

    Returns
    -------
    float
        I² as a percentage in the range [0, 100].
    """
    if q_statistic <= 0 or df <= 0:
        return 0.0

    i2_raw = (q_statistic - df) / q_statistic
    return max(0.0, i2_raw) * 100.0

def _validate_inputs(effect_sizes: List[float], variances: List[float]) -> int:
    """Validate input lengths and positivity; return the number of studies."""
    if len(effect_sizes) != len(variances):
        raise ValueError("Effect sizes and variances must have the same length")
    n = len(effect_sizes)
    if n == 0:
        raise ValueError("No studies provided")
    if any(v <= 0 for v in variances):
        raise ValueError("All within‑study variances must be positive")
    return n

def _q_statistics(effect_sizes: List[float], variances: List[float]):
    """
    Compute the fixed‑effects pooled estimate and Cochran's Q using inverse‑variance weights.
    Returns ``(pooled_fe, q_statistic, weights, sum_weights)``.
    """
    w_fixed = [1.0 / v for v in variances]
    sum_w_fixed = sum(w_fixed)
    pooled_fe = sum(w * y for w, y in zip(w_fixed, effect_sizes)) / sum_w_fixed
    q_statistic = sum(w * (y - pooled_fe) ** 2 for w, y in zip(w_fixed, effect_sizes))
    return pooled_fe, q_statistic, w_fixed, sum_w_fixed

# ----------------------------------------------------------------------
# Estimator implementations
# ----------------------------------------------------------------------
def estimate_fixed_effects(
    effect_sizes: List[float],
    variances: List[float],
) -> EstimationResult:
    """
    Fixed‑effects estimator (tau² = 0).
    Returns an :class:`EstimationResult` with Q, I² and the small‑study flag.
    """
    n = _validate_inputs(effect_sizes, variances)

    pooled_fe, q_statistic, weights, sum_w = _q_statistics(effect_sizes, variances)

    if sum_w == 0:
        raise ValueError("Sum of weights is zero (infinite variances)")

    pooled = pooled_fe
    se_pooled = math.sqrt(1.0 / sum_w)

    z = 1.96  # 95 % normal‑based CI
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled

    df = n - 1
    from scipy.stats import chi2

    p_value = 1.0 - chi2.cdf(q_statistic, df) if df > 0 else 1.0
    i2 = calculate_i_squared(q_statistic, df)

    small_flag = _check_small_study(n)
    if small_flag:
        logger.warning(
            "Small‑study dataset (N=%d < %d): heterogeneity statistics (Q, I²) may be unreliable.",
            n,
            MIN_STUDIES_FOR_RELIABILITY,
        )

    return EstimationResult(
        pooled_effect=pooled,
        se_pooled=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau2=0.0,
        i2=i2,
        q_statistic=q_statistic,
        df=df,
        p_value=p_value,
        n_studies=n,
        convergence_status="success",
        small_study_flag=small_flag,
    )

def estimate_dersimonian_laird(
    effect_sizes: List[float],
    variances: List[float],
) -> EstimationResult:
    """
    DerSimonian‑Laird random‑effects estimator.
    Returns an :class:`EstimationResult` with the DL estimate of tau²,
    Q, I² and the small‑study flag.
    """
    n = _validate_inputs(effect_sizes, variances)

    pooled_fe, q_statistic, w_fixed, sum_w_fixed = _q_statistics(effect_sizes, variances)

    df = n - 1
    if df <= 0:
        # With a single study the random‑effects model collapses to FE.
        return estimate_fixed_effects(effect_sizes, variances)

    sum_w_sq = sum(w ** 2 for w in w_fixed)
    c_val = sum_w_fixed - (sum_w_sq / sum_w_fixed)

    if c_val <= 0:
        tau2 = 0.0
    else:
        tau2 = max(0.0, (q_statistic - df) / c_val)

    w_re = [1.0 / (v + tau2) for v in variances]
    sum_w_re = sum(w_re)

    if sum_w_re == 0:
        return estimate_fixed_effects(effect_sizes, variances)

    pooled = sum(w * y for w, y in zip(w_re, effect_sizes)) / sum_w_re
    se_pooled = math.sqrt(1.0 / sum_w_re)

    z = 1.96
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled

    from scipy.stats import chi2

    p_value = 1.0 - chi2.cdf(q_statistic, df) if df > 0 else 1.0
    i2 = calculate_i_squared(q_statistic, df)

    small_flag = _check_small_study(n)
    if small_flag:
        logger.warning(
            "Small‑study dataset (N=%d < %d): heterogeneity statistics (Q, I²) may be unreliable.",
            n,
            MIN_STUDIES_FOR_RELIABILITY,
        )

    return EstimationResult(
        pooled_effect=pooled,
        se_pooled=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau2=tau2,
        i2=i2,
        q_statistic=q_statistic,
        df=df,
        p_value=p_value,
        n_studies=n,
        convergence_status="success",
        small_study_flag=small_flag,
    )

def estimate_reml(
    effect_sizes: List[float],
    variances: List[float],
    log_failures: bool = True,
) -> EstimationResult:
    """
    Restricted Maximum Likelihood (REML) random‑effects estimator.

    On optimisation failure the event is logged (FR‑006) and the
    estimator falls back to the DerSimonian‑Laird variance.
    """
    n = _validate_inputs(effect_sizes, variances)
    if n == 1:
        # With a single study REML collapses to the FE result.
        return estimate_fixed_effects(effect_sizes, variances)

    def reml_log_likelihood(tau2: float) -> float:
        """Negative REML log‑likelihood (to be minimised)."""
        if tau2 < 0:
            return float("inf")
        w = [1.0 / (v + tau2) for v in variances]
        sum_w = sum(w)
        if sum_w <= 0:
            return float("inf")
        mu = sum(wi * yi for wi, yi in zip(w, effect_sizes)) / sum_w
        term1 = sum(math.log(v + tau2) for v in variances)
        term2 = math.log(sum_w)
        term3 = sum((y - mu) ** 2 / (v + tau2) for y, v in zip(effect_sizes, variances))
        return 0.5 * (term1 + term2 + term3)

    tau2: Optional[float] = None
    failure_reason: Optional[str] = None
    try:
        res = optimize.minimize_scalar(
            reml_log_likelihood,
            bounds=(0.0, max(variances) * 10.0),
            method="bounded",
            options={"xatol": 1e-8},
        )
        if not res.success:
            failure_reason = f"optimizer reported failure: {res.message}"
        else:
            tau2 = max(0.0, float(res.x))
    except Exception as e:  # noqa: BLE001
        failure_reason = f"optimizer raised exception: {e}"

    if tau2 is None:
        # ------------------------------------------------------------------
        # REML failed – log and fall back to DerSimonian‑Laird.
        # ------------------------------------------------------------------
        if log_failures:
            log_reml_failure(
                {
                    "estimator": "reml",
                    "reason": failure_reason,
                    "n_studies": n,
                    "effect_sizes": list(effect_sizes),
                    "variances": list(variances),
                    "fallback": "dersimonian_laird_tau2",
                }
            )
        logger.warning("REML optimisation failed (%s); falling back to DL tau².", failure_reason)
        dl_res = estimate_dersimonian_laird(effect_sizes, variances)
        return EstimationResult(
            pooled_effect=dl_res.pooled_effect,
            se_pooled=dl_res.se_pooled,
            ci_lower=dl_res.ci_lower,
            ci_upper=dl_res.ci_upper,
            tau2=dl_res.tau2,
            i2=dl_res.i2,
            q_statistic=dl_res.q_statistic,
            df=dl_res.df,
            p_value=dl_res.p_value,
            n_studies=dl_res.n_studies,
            convergence_status="fallback_dl",
            small_study_flag=dl_res.small_study_flag,
        )

    # ----------------------------------------------------------------------
    # Successful REML optimisation – compute the usual random‑effects
    # quantities using the estimated tau².
    # ----------------------------------------------------------------------
    w_re = [1.0 / (v + tau2) for v in variances]
    sum_w_re = sum(w_re)

    if sum_w_re == 0:
        # Edge case – weights collapsed; fall back to FE.
        if log_failures:
            log_reml_failure(
                {
                    "estimator": "reml",
                    "reason": "random‑effects weights collapsed to zero",
                    "n_studies": n,
                    "fallback": "fixed_effects",
                }
            )
        fe_res = estimate_fixed_effects(effect_sizes, variances)
        return EstimationResult(
            pooled_effect=fe_res.pooled_effect,
            se_pooled=fe_res.se_pooled,
            ci_lower=fe_res.ci_lower,
            ci_upper=fe_res.ci_upper,
            tau2=0.0,
            i2=fe_res.i2,
            q_statistic=fe_res.q_statistic,
            df=fe_res.df,
            p_value=fe_res.p_value,
            n_studies=fe_res.n_studies,
            convergence_status="fallback_fe",
            small_study_flag=fe_res.small_study_flag,
        )

    pooled = sum(w * y for w, y in zip(w_re, effect_sizes)) / sum_w_re
    se_pooled = math.sqrt(1.0 / sum_w_re)

    z = 1.96
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled

    # Q, I², df and p‑value are based on the fixed‑effects weights
    # (the standard definition used throughout the literature).
    pooled_fe, q_statistic, _, _ = _q_statistics(effect_sizes, variances)
    df = n - 1
    from scipy.stats import chi2

    p_value = 1.0 - chi2.cdf(q_statistic, df) if df > 0 else 1.0
    i2 = calculate_i_squared(q_statistic, df)

    small_flag = _check_small_study(n)
    if small_flag:
        logger.warning(
            "Small‑study dataset (N=%d < %d): heterogeneity statistics (Q, I²) may be unreliable.",
            n,
            MIN_STUDIES_FOR_RELIABILITY,
        )

    return EstimationResult(
        pooled_effect=pooled,
        se_pooled=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau2=tau2,
        i2=i2,
        q_statistic=q_statistic,
        df=df,
        p_value=p_value,
        n_studies=n,
        convergence_status="success",
        small_study_flag=small_flag,
    )

def apply_estimator(
    estimator_name: str,
    effect_sizes: List[float],
    variances: List[float],
) -> EstimationResult:
    """
    Dispatcher that selects the requested estimator.

    Parameters
    ----------
    estimator_name:
        One of ``'fixed'``, ``'dl'`` or ``'reml'`` (case‑insensitive).
    effect_sizes:
        List of observed study effect sizes.
    variances:
        List of within‑study variances (SE²).

    Returns
    -------
    EstimationResult
        The result produced by the selected estimator.
    """
    name = estimator_name.lower()
    if name in ("fixed", "fixed_effects"):
        return estimate_fixed_effects(effect_sizes, variances)
    if name in ("dl", "dersimonian_laird"):
        return estimate_dersimonian_laird(effect_sizes, variances)
    if name in ("reml", "restricted_maximum_likelihood"):
        return estimate_reml(effect_sizes, variances)
    raise ValueError(f"Unknown estimator: {estimator_name}")

# ----------------------------------------------------------------------
# End of module
# ----------------------------------------------------------------------