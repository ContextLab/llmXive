"""
Power analysis utilities for the Parasocial Relationships project.

This module provides functions to compute the smallest detectable
Cohen's d (effect size) for a given sample size (N) at a target
statistical power (default 0.80) and significance level (default
α = 0.05).  The results are written to a YAML report that can be
consumed by downstream validation steps.
"""

from pathlib import Path
import yaml
import logging

from statsmodels.stats.power import TTestIndPower

# Obtain a logger that follows the project's logging conventions.
from src.utils.logging import get_logger

log = get_logger(__name__)

def compute_detectable_d(
    nobs: int,
    power: float = 0.80,
    alpha: float = 0.05,
    ratio: float = 1.0,
    alternative: str = "two-sided",
) -> float:
    """
    Compute the minimum detectable Cohen's d for a two‑sample t‑test.

    Parameters
    ----------
    nobs : int
        Number of observations in the first sample (the matched
        user count).  The second sample is assumed to have the same
        size unless ``ratio`` is changed.
    power : float, optional
        Desired statistical power (default 0.80).
    alpha : float, optional
        Significance level (default 0.05).
    ratio : float, optional
        Ratio of sample sizes (n2 / n1).  The default assumes equal
        groups.
    alternative : str, optional
        Direction of the test – ``"two-sided"``, ``"larger"``, or
        ``"smaller"``.  The default matches the typical two‑tailed
        hypothesis.

    Returns
    -------
    float
        The smallest Cohen's d that can be detected with the
        specified power and α.
    """
    analysis = TTestIndPower()
    d = analysis.solve_power(
        effect_size=None,
        nobs1=nobs,
        alpha=alpha,
        power=power,
        ratio=ratio,
        alternative=alternative,
    )
    log.debug(
        f"Computed detectable d = {d:.4f} for nobs={nobs}, power={power}, alpha={alpha}"
    )
    return d

def write_power_report(
    nobs: int,
    output_path: Path,
    power: float = 0.80,
    alpha: float = 0.05,
    ratio: float = 1.0,
) -> dict:
    """
    Generate a YAML power‑analysis report.

    The report contains the detectable effect size and a warning
    flag if the effect size exceeds the threshold of 0.8 (i.e.
    the study would be under‑powered for medium‑to‑large effects).

    Parameters
    ----------
    nobs : int
        Matched user count (sample size).
    output_path : Path
        Destination path for ``power_analysis_report.yaml``.
    power, alpha, ratio : float
        Parameters passed to :func:`compute_detectable_d`.

    Returns
    -------
    dict
        The report dictionary that was written to disk.
    """
    detectable_d = compute_detectable_d(
        nobs=nobs, power=power, alpha=alpha, ratio=ratio
    )

    report = {
        "detectable_d": round(detectable_d, 4),
        "power_target": power,
        "alpha": alpha,
    }

    if detectable_d > 0.8:
        report["warning"] = "Detectable effect size exceeds 0.8"

    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)

    log.info(f"Power analysis report written to {output_path}")
    return report
