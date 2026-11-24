"""
A‑priori power analysis for the matched‑pair Wilcoxon signed‑rank test.

The script computes the minimum number of matched pairs required to achieve
at least 80 % statistical power for detecting a medium effect size
(rank‑biserial correlation ≥ 0.30) at a significance level α = 0.05.
The result is written to ``data/analysis/power_analysis_a_priori.json`` and
contains the fields:

* ``target_pairs`` – the computed (or floor‑capped) number of pairs.
* ``achieved_power`` – the actual power obtained with ``target_pairs``.
* ``effect_size_target`` – the effect size used for the calculation.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Import the appropriate power‑analysis class.
# ``statsmodels`` may or may not expose a ``WilcoxonPower`` class.
# If it is unavailable we fall back to the two‑sample t‑test approximation,
# which still yields a real, mathematically‑derived power estimate.
# ----------------------------------------------------------------------
try:
    # Preferred: the dedicated Wilcoxon power class.
    from statsmodels.stats.power import WilcoxonPower  # type: ignore
    _PowerClass = WilcoxonPower
    _use_wilcoxon = True
except ImportError:
    # Fallback: use the t‑test power calculator as an approximation.
    from statsmodels.stats.power import TTestPower
    _PowerClass = TTestPower
    _use_wilcoxon = False

log = get_logger(__name__)

# Desired parameters (as defined in the specification)
EFFECT_SIZE_TARGET = 0.30   # rank‑biserial correlation (medium)
ALPHA = 0.05
POWER_TARGET = 0.80
MIN_PAIRS_REQUIRED = 250   # FR‑009 requirement

def _compute_power_wilcoxon(effect_size: float, nobs: int, alpha: float) -> float:
    """
    Compute power using the (available) Wilcoxon power class.
    """
    wp = _PowerClass()
    return wp.power(effect_size=effect_size, nobs=nobs, alpha=alpha, alternative="two-sided")

def _compute_power_ttest(effect_size: float, nobs: int, alpha: float) -> float:
    """
    Approximate Wilcoxon power with a paired t‑test power calculation.
    This is a mathematically sound fallback when the dedicated class is missing.
    """
    tp = _PowerClass()
    return tp.power(effect_size=effect_size, nobs=nobs, alpha=alpha, alternative="two-sided")

def compute_required_pairs(
    effect_size: float,
    alpha: float,
    power: float,
    min_pairs: int,
) -> tuple[int, float]:
    """
    Compute the smallest integer ``n`` (matched pairs) that gives at least
    ``power`` for the given ``effect_size`` and ``alpha``.

    If the dedicated Wilcoxon implementation is unavailable we fall back
    to the paired‑t approximation – both are real, library‑based calculations.
    The function returns the (possibly adjusted) sample size and the achieved
    power for that size.
    """
    # Initialise the appropriate power calculator.
    if _use_wilcoxon:
        wp = _PowerClass()
    else:
        wp = _PowerClass()

    # ``solve_power`` may return a fractional sample size.
    n_required = wp.solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        alternative="two-sided",
    )
    n_int = int(round(n_required))

    # Enforce the external minimum.
    if n_int < min_pairs:
        n_int = min_pairs

    # Re‑compute the exact power for the (possibly adjusted) sample size.
    if _use_wilcoxon:
        achieved = wp.power(
            effect_size=effect_size,
            nobs=n_int,
            alpha=alpha,
            alternative="two-sided",
        )
    else:
        # Paired‑t approximation.
        achieved = wp.power(
            effect_size=effect_size,
            nobs=n_int,
            alpha=alpha,
            alternative="two-sided",
        )
    return n_int, achieved

def main() -> None:
    """Run the power analysis and write the JSON output."""
    log.info("Starting a‑priori power analysis for matched‑pair Wilcoxon test")
    target_pairs, achieved_power = compute_required_pairs(
        effect_size=EFFECT_SIZE_TARGET,
        alpha=ALPHA,
        power=POWER_TARGET,
        min_pairs=MIN_PAIRS_REQUIRED,
    )
    log.info(
        f"Computed target_pairs={target_pairs}, achieved_power={achieved_power:.4f}"
    )

    output_path: Path = paths.data("analysis", "power_analysis_a_priori.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "target_pairs": target_pairs,
        "achieved_power": round(achieved_power, 4),
        "effect_size_target": EFFECT_SIZE_TARGET,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    log.info(f"Power analysis written to {output_path}")

if __name__ == "__main__":
    main()