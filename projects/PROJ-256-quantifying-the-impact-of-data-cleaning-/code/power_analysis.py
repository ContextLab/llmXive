"""
Power analysis script for the project.

Computes the a‑priori power for:
1. A two‑sample t‑test detecting Cohen's d = 0.5.
2. A paired Wilcoxon signed‑rank test detecting a medium effect
   (approximated with a paired t‑test, effect size d = 0.5).

The results are written to ``power_analysis.txt`` in the project root.
The file contains the required sample sizes and the achieved power
(both ≥ 0.8), followed by a short justification (< 150 words).
"""

import math
import json
from pathlib import Path

from statsmodels.stats.power import TTestIndPower, TTestPower
from llmxive_toolkit import paths

def _two_sample_t_test():
    """Compute required per‑group size and achieved power for a two‑sample t‑test."""
    power_analysis = TTestIndPower()
    # Solve for the number of observations per group that gives 0.8 power.
    n_per_group = power_analysis.solve_power(
        effect_size=0.5, alpha=0.05, power=0.8, alternative="two-sided"
    )
    # Round up to the next whole observation.
    n_per_group = math.ceil(n_per_group)

    # Verify the achieved power with the rounded sample size.
    achieved_power = power_analysis.power(
        effect_size=0.5,
        nobs1=n_per_group,
        alpha=0.05,
        ratio=1.0,
        alternative="two-sided",
    )
    return n_per_group, achieved_power

def _paired_wilcoxon_approx():
    """
    Approximate the paired Wilcoxon signed‑rank test power using a paired
    t‑test (the two have very similar power for medium effects).
    """
    power_analysis = TTestPower()
    n_obs = power_analysis.solve_power(
        effect_size=0.5, alpha=0.05, power=0.8, alternative="two-sided"
    )
    n_obs = math.ceil(n_obs)

    achieved_power = power_analysis.power(
        effect_size=0.5, nobs=n_obs, alpha=0.05, alternative="two-sided"
    )
    return n_obs, achieved_power

def main():
    # Compute the two analyses.
    n_two, power_two = _two_sample_t_test()
    n_paired, power_paired = _paired_wilcoxon_approx()

    # Build the human‑readable report (<150 words).
    report_lines = [
        "Power analysis:",
        "",
        f"1. Two‑sample t‑test (Cohen's d = 0.5):",
        f"   Required sample size per group = {n_two}",
        f"   Achieved power = {power_two:.3f}",
        "",
        f"2. Paired Wilcoxon signed‑rank test (medium effect, approximated by a paired t‑test):",
        f"   Required total sample size = {n_paired}",
        f"   Achieved power = {power_paired:.3f}",
        "",
        "Both designs exceed the target power of 0.80, justifying the chosen"
        " dataset collection size for the study.",
    ]
    report_text = "\n".join(report_lines)

    # Write the report to the project root.
    out_path = paths.root / "power_analysis.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_text, encoding="utf-8")

if __name__ == "__main__":
    main()
