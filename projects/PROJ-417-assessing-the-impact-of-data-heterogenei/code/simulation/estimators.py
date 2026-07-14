"""
Estimators for meta-analysis: Fixed-Effects, DerSimonian-Laird (DL), REML.
"""

import math
from typing import List, Tuple, Optional
import numpy as np
from scipy import optimize

from utils.logging import get_logger

logger = get_logger(__name__)


class EstimationResult:
    """Container for estimation results."""
    def __init__(
        self,
        pooled_estimate: float,
        ci_lower: float,
        ci_upper: float,
        tau_squared: float,
        i_squared: float,
        converged: bool,
        method: str
    ):
        self.pooled_estimate = pooled_estimate
        self.ci_lower = ci_lower
        self.ci_upper = ci_upper
        self.tau_squared = tau_squared
        self.i_squared = i_squared
        self.converged = converged
        self.method = method

    def to_dict(self):
        return {
            "pooled_estimate": self.pooled_estimate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "tau_squared": self.tau_squared,
            "i_squared": self.i_squared,
            "converged": self.converged,
            "method": self.method
        }


def estimate_fixed_effects(
    effects: List[float],
    ses: List[float]
) -> EstimationResult:
    """
    Estimates pooled effect using Fixed-Effects model (Inverse Variance).
    Assumes tau^2 = 0.
    """
    if len(effects) == 0:
        return EstimationResult(0, 0, 0, 0, 0, False, "FixedEffects")

    weights = [1.0 / (se**2) for se in ses]
    w_sum = sum(weights)
    pooled = sum(w * e for w, e in zip(weights, effects)) / w_sum

    se_pooled = math.sqrt(1.0 / w_sum)
    ci_lower = pooled - 1.96 * se_pooled
    ci_upper = pooled + 1.96 * se_pooled

    # Calculate I^2 for reporting (using pooled as estimate)
    # Q statistic
    q = sum(w * (e - pooled)**2 for w, e in zip(weights, effects))
    k = len(effects)
    df = k - 1
    i_sq = 0.0
    if q > df and q > 0:
        i_sq = (q - df) / q * 100.0

    return EstimationResult(
        pooled_estimate=pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau_squared=0.0,
        i_squared=i_sq,
        converged=True,
        method="FixedEffects"
    )


def estimate_dersimonian_laird(
    effects: List[float],
    ses: List[float]
) -> EstimationResult:
    """
    Estimates pooled effect using DerSimonian-Laird random effects model.
    """
    if len(effects) == 0:
        return EstimationResult(0, 0, 0, 0, 0, False, "DL")

    weights = [1.0 / (se**2) for se in ses]
    w_sum = sum(weights)
    pooled_fe = sum(w * e for w, e in zip(weights, effects)) / w_sum

    # Q statistic
    q = sum(w * (e - pooled_fe)**2 for w, e in zip(weights, effects))
    k = len(effects)
    df = k - 1

    if df <= 0:
        return EstimationResult(pooled_fe, pooled_fe-1, pooled_fe+1, 0, 0, True, "DL")

    c = w_sum - (sum(w**2) / w_sum)
    tau_sq = (q - df) / c if c > 0 else 0.0
    tau_sq = max(0.0, tau_sq) # DL can be negative, truncate to 0

    # Recalculate weights with tau^2
    weights_re = [1.0 / (se**2 + tau_sq) for se in ses]
    w_re_sum = sum(weights_re)
    pooled_re = sum(w * e for w, e in zip(weights_re, effects)) / w_re_sum

    se_pooled = math.sqrt(1.0 / w_re_sum)
    ci_lower = pooled_re - 1.96 * se_pooled
    ci_upper = pooled_re + 1.96 * se_pooled

    # I^2
    i_sq = 0.0
    if q > df and q > 0:
        i_sq = (q - df) / q * 100.0

    return EstimationResult(
        pooled_estimate=pooled_re,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau_squared=tau_sq,
        i_squared=i_sq,
        converged=True,
        method="DL"
    )


def estimate_reml(
    effects: List[float],
    ses: List[float]
) -> EstimationResult:
    """
    Estimates pooled effect using REML (Restricted Maximum Likelihood).
    Uses optimization to find tau^2.
    """
    if len(effects) == 0:
        return EstimationResult(0, 0, 0, 0, 0, False, "REML")

    k = len(effects)
    if k < 2:
        return EstimationResult(effects[0], effects[0]-1, effects[0]+1, 0, 0, True, "REML")

    ses_arr = np.array(ses)
    effects_arr = np.array(effects)

    def reml_log_likelihood(tau_sq):
        if tau_sq <= 0:
            tau_sq = 1e-6
        w = 1.0 / (ses_arr**2 + tau_sq)
        w_sum = np.sum(w)
        mu = np.sum(w * effects_arr) / w_sum

        # Log likelihood components
        # -0.5 * sum(log(2*pi) + log(v_i) + (y_i - mu)^2 / v_i)
        # v_i = se_i^2 + tau^2
        v = ses_arr**2 + tau_sq
        ll = -0.5 * (np.sum(np.log(2 * np.pi * v)) + np.sum((effects_arr - mu)**2 / v))

        # REML correction: subtract 0.5 * log(det(X' V^-1 X))
        # Here X is a column of 1s, so X' V^-1 X = sum(1/v_i) = w_sum
        ll -= 0.5 * np.log(w_sum)

        return -ll # Minimize negative log likelihood

    try:
        # Optimize tau^2
        res = optimize.minimize_scalar(
            reml_log_likelihood,
            bounds=(1e-6, 10.0),
            method='bounded'
        )

        if not res.success:
            logger.warning("REML optimization failed. Falling back to DL.")
            return estimate_dersimonian_laird(effects, ses)

        tau_sq = res.x
        if tau_sq < 0:
            tau_sq = 0.0

        # Calculate pooled estimate with final tau^2
        w = 1.0 / (ses_arr**2 + tau_sq)
        w_sum = np.sum(w)
        pooled = np.sum(w * effects_arr) / w_sum
        se_pooled = math.sqrt(1.0 / w_sum)

        ci_lower = pooled - 1.96 * se_pooled
        ci_upper = pooled + 1.96 * se_pooled

        # I^2 (approximate using Q from DL for consistency or recalculate)
        # Recalculating Q with REML weights for I^2
        mu_fe = np.sum((1.0/ses_arr**2) * effects_arr) / np.sum(1.0/ses_arr**2)
        q = np.sum((1.0/ses_arr**2) * (effects_arr - mu_fe)**2)
        df = k - 1
        i_sq = 0.0
        if q > df and q > 0:
            i_sq = (q - df) / q * 100.0

        return EstimationResult(
            pooled_estimate=pooled,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            tau_squared=float(tau_sq),
            i_squared=float(i_sq),
            converged=True,
            method="REML"
        )

    except Exception as e:
        logger.error(f"REML estimation error: {e}")
        # Fallback to DL on failure
        return estimate_dersimonian_laird(effects, ses)


def apply_estimator(
    method: str,
    effects: List[float],
    ses: List[float]
) -> EstimationResult:
    """Factory function to apply the specified estimator."""
    if method == "FixedEffects":
        return estimate_fixed_effects(effects, ses)
    elif method == "DL":
        return estimate_dersimonian_laird(effects, ses)
    elif method == "REML":
        return estimate_reml(effects, ses)
    else:
        raise ValueError(f"Unknown estimator method: {method}")
