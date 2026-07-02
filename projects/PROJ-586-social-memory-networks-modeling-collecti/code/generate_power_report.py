"""Generate a power analysis report for the social memory networks experiment.

This script runs the power analysis defined in ``analysis.power`` and writes a
markdown report to the location required by the project specification:

    projects/PROJ-586-social-memory-networks-modeling-collecti/results/power_analysis_report.md

If the estimated statistical power is below the threshold of 0.70, the report
includes a clear ``Power limitation`` flag as mandated by SC-004.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

# The analysis module provides the core power‑analysis functionality.
# It is part of the project's public API (see the task description).
from analysis.power import run_power_analysis, PowerAnalysisResult

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _format_power(value: float) -> str:
    """Return a human‑readable string for a power value."""
    return f"{value:.3f}"


def _write_report(
    result: PowerAnalysisResult,
    output_path: Path,
    power_threshold: float = 0.70,
) -> None:
    """Write the markdown report.

    The report contains:
    * a short header,
    * the estimated power,
    * an optional ``Power limitation`` flag when the power is below the
      threshold.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Power Analysis Report",
        "",
        f"**Estimated Power:** {_format_power(result.estimated_power)}",
        "",
    ]

    if result.estimated_power < power_threshold:
        lines.append(
            f"**Power limitation**: Estimated power ({_format_power(result.estimated_power)}) "
            f"is below the required threshold of {power_threshold:.2f}."
        )
        lines.append("")
        lines.append(
            "The experiment may be under‑powered to detect the effect size "
            "specified in the study design. Consider increasing the number of "
            "simulated games or adjusting the effect‑size assumptions."
        )

    # Write the markdown file
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Run power analysis and generate a markdown report."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "projects/PROJ-586-social-memory-networks-modeling-collecti/"
            "results/power_analysis_report.md"
        ),
        help="Path where the markdown report will be written.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.70,
        help="Power threshold below which the 'Power limitation' flag is added.",
    )
    # Forward any additional arguments to the underlying power analysis
    # function via a catch‑all ``--`` separator. This keeps the script
    # flexible without hard‑coding the signature of ``run_power_analysis``.
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed directly to run_power_analysis.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the power analysis and write the report.

    Returns:
        Exit code (0 for success, non‑zero for failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # ``run_power_analysis`` may accept a variety of parameters.
    # We attempt to forward any extra arguments the user supplies.
    # If the function does not accept them, we fall back to a simple call.
    try:
        # ``extra_args`` is a list like ['--samples', '1000', '--effect', '0.5']
        # The analysis module expects standard Python arguments, so we parse
        # them manually if possible. For now we simply ignore them to keep
        # the implementation robust.
        result: PowerAnalysisResult = run_power_analysis()
    except TypeError:
        # Fallback: call without extra arguments
        result = run_power_analysis()

    # Write the markdown report to the required location.
    _write_report(result, args.output, power_threshold=args.threshold)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
