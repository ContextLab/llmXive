"""
Power analysis utility for the project.

This module provides functions to perform an a priori power analysis for a
two‑sample t‑test using the specified effect size (Cohen's d), significance
level (α), desired power, and allocation ratio. The result is written to a
plain‑text file ``power_analysis.txt`` at the repository root.

The implementation relies on ``statsmodels.stats.power.TTestIndPower``,
which implements the standard non‑central t‑distribution based calculations.
"""

import sys
from pathlib import Path
from typing import Tuple

from statsmodels.stats.power import TTestIndPower


def perform_power_analysis(
    effect_size: float = 0.5,
    alpha: float = 0.05,
    power_target: float = 0.8,
    allocation_ratio: float = 1.0,
) -> Tuple[int, float]:
    """
    Compute the required sample size per group (rounded up to the nearest
    integer) for a two‑sample t‑test given the desired parameters.

    Parameters
    ----------
    effect_size : float
        Cohen's d (standardised mean difference) to detect.
    alpha : float
        Type‑I error rate (significance level).
    power_target : float
        Desired statistical power (1 - β).
    allocation_ratio : float
        Ratio of sample size in group 2 to group 1 (n2 / n1). 1.0 means equal
        allocation.

    Returns
    -------
    n_per_group : int
        Required sample size for the smaller group (group 1).  The larger
        group size is ``ceil(n_per_group * allocation_ratio)``.
    achieved_power : float
        The power achieved with the computed sample size (should be very
        close to ``power_target``).
    """
    # TTestIndPower expects the allocation ratio as n2 / n1
    analysis = TTestIndPower()
    # solve for total sample size per group to achieve the target power
    n_per_group = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power_target,
        ratio=allocation_ratio,
        alternative="two-sided",
    )
    # ``solve_power`` returns a float; we need an integer number of subjects
    n_per_group_int = int(round(n_per_group))
    # Re‑calculate the achieved power with the integer sample size
    achieved_power = analysis.power(
        effect_size=effect_size,
        nobs1=n_per_group_int,
        alpha=alpha,
        ratio=allocation_ratio,
        alternative="two-sided",
    )
    return n_per_group_int, achieved_power


def write_power_analysis_report(
    output_path: Path,
    effect_size: float = 0.5,
    alpha: float = 0.05,
    power_target: float = 0.8,
    allocation_ratio: float = 1.0,
) -> None:
    """
    Write a human‑readable report of the a priori power analysis to
    ``output_path``.  The report contains the input parameters, the computed
    required sample size per group, the corresponding size of the second
    group (based on the allocation ratio), and the achieved power.

    The function raises ``ValueError`` if the achieved power is below the
    target, ensuring the verification step (T1235‑V) can rely on the file
    contents.
    """
    n_per_group, achieved_power = perform_power_analysis(
        effect_size=effect_size,
        alpha=alpha,
        power_target=power_target,
        allocation_ratio=allocation_ratio,
    )
    if achieved_power < power_target - 1e-6:
        raise ValueError(
            f"Achieved power {achieved_power:.4f} is below the target {power_target:.4f}"
        )

    n_group2 = int(round(n_per_group * allocation_ratio))

    report_lines = [
        "A priori power analysis for a two‑sample t‑test",
        "------------------------------------------------",
        f"Effect size (Cohen's d)      : {effect_size}",
        f"Significance level (α)       : {alpha}",
        f"Desired power (1‑β)          : {power_target}",
        f"Allocation ratio (n2 / n1)   : {allocation_ratio}",
        "",
        "Computed sample sizes:",
        f"  Group 1 (smaller)          : {n_per_group}",
        f"  Group 2 (larger)           : {n_group2}",
        "",
        f"Achieved power with integer sample sizes: {achieved_power:.4f}",
    ]

    output_path.write_text("\\n".join(report_lines))
    # Also log to stdout for visibility when the module is run directly
    print("\\n".join(report_lines))


def main(argv: list | None = None) -> int:
    """
    Command‑line entry point.

    The script accepts optional arguments to override the default parameters.
    It writes ``power_analysis.txt`` to the repository root.

    Returns
    -------
    int
        Exit status (0 for success, non‑zero for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Perform a priori power analysis for a two‑sample t‑test."
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        default=0.5,
        help="Cohen's d (default: 0.5)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)",
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.8,
        help="Desired power (default: 0.8)",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=1.0,
        help="Allocation ratio n2/n1 (default: 1.0 for equal groups)",
    )
    args = parser.parse_args(argv)

    try:
        report_path = Path("power_analysis.txt")
        write_power_analysis_report(
            output_path=report_path,
            effect_size=args.effect_size,
            alpha=args.alpha,
            power_target=args.power,
            allocation_ratio=args.ratio,
        )
    except Exception as exc:
        print(f"Error during power analysis: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())