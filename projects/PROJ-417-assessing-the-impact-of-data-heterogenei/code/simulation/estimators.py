import json
import math
import time
from typing import List, Optional, Dict, Any
import numpy as np
from scipy import optimize
from utils.logging import get_logger

logger = get_logger(__name__)

# Path for REML failure event logging (FR-006)
REML_FAILURE_LOG_PATH = "data/results/reml_failures.json"

# Minimum number of studies for reliable chi-square / df approximations
MIN_STUDIES_FOR_RELIABILITY = 5


def log_reml_failure(event: Dict[str, Any], log_path: str = REML_FAILURE_LOG_PATH) -> None:
    """
    Log a REML convergence failure event to a JSON file (FR-006).

    The file contains a JSON list of event dicts. Each event records the
    failure reason, a timestamp, the fallback action taken, and (when
    available) the data context.

    Parameters:
        event: Dictionary describing the failure.
        log_path: Path to the JSON failure log.
    """
    events: List[Dict[str, Any]] = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                loaded = json.loads(content)
                if isinstance(loaded, list):
                    events = loaded
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read existing REML failure log %s: %s", log_path, e)

    event = dict(event)
    event.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%S"))
    events.append(event)

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
    except OSError as e:
        logger.error("Could not write REML failure log %s: %s", log_path, e)


class EstimationResult:
    """
    Container for the results of a meta-analysis estimation.
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
        small_study_flag: bool = False
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
        # Spec Edge Case: datasets with N < 5 studies must be explicitly
        # flagged because chi-square / df approximations are unreliable.
        self.small_study_flag = small_study_flag

    def to_dict(self) -> Dict[str, Any]:
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
            "small_study_flag": self.small_study_flag
        }


def _check_small_study(n_studies: int) -> bool:
    """Return True if the dataset has fewer than MIN_STUDIES_FOR_RELIABILITY studies."""
    return n_studies < MIN_STUDIES_FOR_RELIABILITY


def calculate_i_squared(q_statistic: float, df: int) -> float:
    """
    Calculates the I^2 statistic (Higgins & Thompson, 2002).

    I^2 = max(0, (Q - df) / Q) * 100

    Parameters:
        q_statistic: The Cochran's Q heterogeneity statistic.
        df: Degrees of freedom (k - 1).

    Returns:
        I^2 value as a percentage (0.0 to 100.0).
    """
    if q_statistic <= 0 or df <= 0:
        return 0.0

    i2_raw = (q_statistic - df) / q_statistic
    i2 = max(0.0, i2_raw) * 100.0
    return i2


def _validate_inputs(effect_sizes: List[float], variances: List[float]) -> int:
    if len(effect_sizes) != len(variances):
        raise ValueError("Effect sizes and variances must have the same length")
    n = len(effect_sizes)
    if n == 0:
        raise ValueError("No studies provided")
    if any(v <= 0 for v in variances):
        raise ValueError("All within-study variances must be positive")
    return n


def _q_statistics(effect_sizes: List[float], variances: List[float]):
    """Compute FE pooled estimate and Cochran's Q with FE weights."""
    w_fixed = [1.0 / v for v in variances]
    sum_w_fixed = sum(w_fixed)
    pooled_fe = sum(w * y for w, y in zip(w_fixed, effect_sizes)) / sum_w_fixed
    q_statistic = sum(w * (y - pooled_fe) ** 2 for w, y in zip(w_fixed, effect_sizes))
    return pooled_fe, q_statistic, w_fixed, sum_w_fixed


def estimate_fixed_effects(
    effect_sizes: List[float],
    variances: List[float]
) -> EstimationResult:
    """
    Calculates the Fixed-Effects meta-analysis estimate.
    Assumes tau^2 = 0.
    """
    n = _validate_inputs(effect_sizes, variances)

    pooled_fe, q_statistic, weights, sum_w = _q_statistics(effect_sizes, variances)

    if sum_w == 0:
        raise ValueError("Sum of weights is zero (infinite variances)")

    pooled = pooled_fe
    se_pooled = math.sqrt(1.0 / sum_w)

    z = 1.96
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled

    df = n - 1
    from scipy.stats import chi2
    p_value = 1.0 - chi2.cdf(q_statistic, df) if df > 0 else 1.0
    i2 = calculate_i_squared(q_statistic, df)

    small_flag = _check_small_study(n)
    if small_flag:
        logger.warning(
            "Small-study dataset (N=%d < %d): heterogeneity statistics "
            "(Q, I^2) may be unreliable due to insufficient degrees of freedom.",
            n, MIN_STUDIES_FOR_RELIABILITY
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
        small_study_flag=small_flag
    )


def estimate_dersimonian_laird(
    effect_sizes: List[float],
    variances: List[float]
) -> EstimationResult:
    """
    Calculates the DerSimonian-Laird random-effects estimate.
    """
    n = _validate_inputs(effect_sizes, variances)

    pooled_fe, q_statistic, w_fixed, sum_w_fixed = _q_statistics(effect_sizes, variances)

    df = n - 1
    if df <= 0:
        # If only 1 study, tau2 is undefined/zero
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
            "Small-study dataset (N=%d < %d): heterogeneity statistics "
            "(Q, I^2) may be unreliable due to insufficient degrees of freedom.",
            n, MIN_STUDIES_FOR_RELIABILITY
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
        small_study_flag=small_flag
    )


def estimate_reml(
    effect_sizes: List[float],
    variances: List[float],
    log_failures: bool = True
) -> EstimationResult:
    """
    Calculates the Restricted Maximum Likelihood (REML) estimate.

    On convergence failure the event is logged to
    data/results/reml_failures.json (FR-006) and estimation proceeds
    with a fallback variance (the DerSimonian-Laird tau^2).
    """
    n = _validate_inputs(effect_sizes, variances)
    if n == 1:
        return estimate_fixed_effects(effect_sizes, variances)

    def reml_log_likelihood(tau2: float) -> float:
        """Negative REML log-likelihood to minimize."""
        if tau2 < 0:
            return float('inf')
        w = [1.0 / (v + tau2) for v in variances]
        sum_w = sum(w)
        if sum_w <= 0:
            return float('inf')
        mu = sum(wi * yi for wi, yi in zip(w, effect_sizes)) / sum_w
        term1 = sum(math.log(v + tau2) for v in variances)
        term2 = math.log(sum_w)
        term3 = sum((y - mu) ** 2 / (v + tau2) for y, v in zip(effect_sizes, variances))
        return 0.5 * (term1 + term2 + term3)

    tau2 = None
    failure_reason = None
    try:
        res = optimize.minimize_scalar(
            reml_log_likelihood,
            bounds=(0.0, max(variances) * 10.0),
            method='bounded',
            options={'xatol': 1e-8}
        )
        if not res.success:
            failure_reason = f"optimizer reported failure: {res.message}"
        else:
            tau2 = max(0.0, float(res.x))
    except Exception as e:  # noqa: BLE001
        failure_reason = f"optimizer raised exception: {e}"

    if tau2 is None:
        # FR-006: log the failure event and proceed with a fallback
        # variance (DL tau^2) rather than crashing the simulation.
        if log_failures:
            log_reml_failure({
                "estimator": "reml",
                "reason": failure_reason,
                "n_studies": n,
                "effect_sizes": list(effect_sizes),
                "variances": list(variances),
                "fallback": "dersimonian_laird_tau2"
            })
        logger.warning("REML optimization failed (%s); falling back to DL tau^2.", failure_reason)
        dl_res = estimate_dersimonian_laird(effect_sizes, variances)
        # Rebuild the result with the fallback tau2 but mark convergence status.
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
            small_study_flag=dl_res.small_study_flag
        )

    w_re = [1.0 / (v + tau2) for v in variances]
    sum_w_re = sum(w_re)
    if sum_w_re == 0:
        if log_failures:
            log_reml_failure({
                "estimator": "reml",
                "reason": "random-effects weights collapsed to zero",
                "n_studies": n,
                "fallback": "fixed_effects"
            })
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
            small_study_flag=fe_res.small_study_flag
        )

    pooled = sum(w * y for w, y in zip(w_re, effect_sizes)) / sum_w_re
    se_pooled = math.sqrt(1.0 / sum_w_re)

    z = 1.96
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled

    pooled_fe, q_statistic, _, _ = _q_statistics(effect_sizes, variances)
    df = n - 1
    from scipy.stats import chi2
    p_value = 1.0 - chi2.cdf(q_statistic, df) if df > 0 else 1.0
    i2 = calculate_i_squared(q_statistic, df)

    small_flag = _check_small_study(n)
    if small_flag:
        logger.warning(
            "Small-study dataset (N=%d < %d): heterogeneity statistics "
            "(Q, I^2) may be unreliable due to insufficient degrees of freedom.",
            n, MIN_STUDIES_FOR_RELIABILITY
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
        small_study_flag=small_flag
    )


def apply_estimator(
    estimator_name: str,
    effect_sizes: List[float],
    variances: List[float]
) -> EstimationResult:
    """
    Dispatches to the appropriate estimator function.

    Parameters:
        estimator_name: One of 'fixed', 'dl', 'reml'.
        effect_sizes: List of observed effect sizes.
        variances: List of within-study variances.

    Returns:
        EstimationResult object.
    """
    name = estimator_name.lower()
    if name in ['fixed', 'fixed_effects']:
        return estimate_fixed_effects(effect_sizes, variances)
    elif name in ['dl', 'dersimonian_laird']:
        return estimate_dersimonian_laird(effect_sizes, variances)
    elif name in ['reml', 'restricted_max_likelihood']:
        return estimate_reml(effect_sizes, variances)
    else:
        raise ValueError(f"Unknown estimator: {estimator_name}")
