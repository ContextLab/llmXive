"""
src/analysis/power_analysis.py
--------------------------------
Statistical Power Analysis utility for the llmXive follow‑up project.

This module provides a simple command‑line interface that estimates the
minimum number of simulation runs (i.e., distinct noise seeds) required
to detect a specified effect size with a desired statistical power.
The calculation uses a two‑sample t‑test power analysis, which is
appropriate for the planned comparisons between the neural baseline and
deterministic CA variants.

The script writes its result to a JSON file under the project's
``data/processed`` directory (created automatically via the llmxive_toolkit
``paths`` helper).  The output schema is::

    {
        "effect_size": <float>,
        "power": <float>,
        "alpha": <float>,
        "required_runs": <int>
    }

The default parameters correspond to a *medium* effect size (Cohen's d =
0.5), a conventional power of 0.8, and a significance level of 0.05.
"""

import argparse
import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from statsmodels.stats.power import TTestIndPower

log = get_logger(__name__)

def compute_minimum_runs(
    effect_size: float = 0.5,
    power: float = 0.8,
    alpha: float = 0.05,
    ratio: float = 1.0,
) -> int:
    """
    Compute the required sample size per group for a two‑sample t‑test.

    Parameters
    ----------
    effect_size : float
        Cohen's d (difference between group means divided by pooled std).
    power : float
        Desired statistical power (1 - β). Typical values are 0.8 or 0.9.
    alpha : float
        Type‑I error rate (significance level). Default 0.05.
    ratio : float
        Ratio of sample size in group 2 to group 1 (default 1.0 for equal
        sized groups).

    Returns
    -------
    int
        Minimum integer number of runs **per group** required to achieve
        the specified power.  The total number of simulation runs is twice
        this value (one set for the baseline, one for the CA variant).
    """
    power_analyzer = TTestIndPower()
    # ``solve_power`` returns the sample size for *one* group.
    n_per_group = power_analyzer.solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        ratio=ratio,
        alternative="two-sided",
    )
    # Round up to the next whole number.
    return int(round(n_per_group + 0.5))

def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate the minimum number of simulation runs (noise seeds) "
            "required to detect a given effect size with a desired power."
        )
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        default=0.5,
        help="Cohen's d effect size (default: 0.5 for a medium effect).",
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.8,
        help="Desired statistical power (default: 0.8).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05).",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=1.0,
        help=(
            "Sample size ratio of group2 / group1 (default: 1.0 for equal "
            "group sizes)."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.results("power_analysis.json")),
        help="Path to JSON file where the result will be written.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_cli_args()
    log.info(
        "Running power analysis with effect_size=%.3f, power=%.3f, alpha=%.3f, ratio=%.3f",
        args.effect_size,
        args.power,
        args.alpha,
        args.ratio,
    )

    required_per_group = compute_minimum_runs(
        effect_size=args.effect_size,
        power=args.power,
        alpha=args.alpha,
        ratio=args.ratio,
    )
    total_required = required_per_group * 2  # baseline + CA variant

    result = {
        "effect_size": args.effect_size,
        "power": args.power,
        "alpha": args.alpha,
        "ratio": args.ratio,
        "required_runs_per_group": required_per_group,
        "total_required_runs": total_required,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2)

    log.info("Power analysis result written to %s", output_path)
    log.info("Required runs per group: %d (total %d)", required_per_group, total_required)

if __name__ == "__main__":
    main()