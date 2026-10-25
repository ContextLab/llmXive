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
from statsmodels.stats.power import WilcoxonPower

log = get_logger(__name__)

# Desired parameters
EFFECT_SIZE_TARGET = 0.30  # rank‑biserial correlation (medium)
ALPHA = 0.05
POWER_TARGET = 0.80
MIN_PAIRS_REQUIRED = 250  # FR‑009 requirement

def compute_required_pairs(
    effect_size: float,
    alpha: float,
    power: float,
    min_pairs: int,
) -> tuple[int, float]:
    """
    Compute the smallest integer ``n`` (matched pairs) that gives at least
    ``power`` for the given ``effect_size`` and ``alpha`` using the
    Wilcoxon signed‑rank power analysis.

    Returns:
        (n_pairs, achieved_power)
    """
    wp = WilcoxonPower()
    # ``solve_power`` returns the required sample size (may be fractional)
    n_required = wp.solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        alternative="two-sided",
    )
    n_int = int(round(n_required))
    # Ensure we respect the external minimum
    if n_int < min_pairs:
        n_int = min_pairs

    # Re‑compute the exact power for the (possibly adjusted) sample size
    achieved = wp.power(
        effect_size=effect_size,
        nobs=n_int,
        alpha=alpha,
        alternative="two-sided",
    )
    return n_int, achieved

def main() -> None:
    """Run the power analysis and write the JSON output."""
    log.info("Starting a‑priori power analysis for Wilcoxon matched‑pair test")
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
