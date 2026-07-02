"""Generate a Power Analysis Report with a limitation flag.

This script runs the existing power analysis implementation (provided in
``code/analysis/power.py``) and writes a markdown report to the required
location:

    projects/PROJ-586-social-memory-networks-modeling-collecti/results/power_analysis_report.md

If the estimated statistical power is below the threshold of 0.70, a
**Power limitation** warning is included in the report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the public API from the existing power analysis module.
# The module is expected to expose a ``run_power_analysis`` function that
# returns a ``PowerAnalysisResult`` data class with a ``power`` attribute.
from analysis.power import run_power_analysis, PowerAnalysisResult  # type: ignore

# Threshold for acceptable power (as specified in the task description).
POWER_THRESHOLD = 0.70

def _format_power(value: float) -> str:
    """Return a nicely formatted power value."""
    return f"{value:.3f}"

def _write_report(result: PowerAnalysisResult, output_path: Path) -> None:
    """Write the markdown report, inserting a limitation flag when needed."""
    power_value = getattr(result, "power", None)
    if power_value is None:
        # ``run_power_analysis`` may return a dict‑like object; fall back to attribute access.
        power_value = result.get("power") if isinstance(result, dict) else None

    if power_value is None:
        raise ValueError("Power analysis result does not contain a 'power' field.")

    flag_needed = power_value < POWER_THRESHOLD

    report_lines = [
        "# Power Analysis Report",
        "",
        f"Estimated Power: {_format_power(power_value)}",
        "",
    ]

    if flag_needed:
        report_lines.append("**Power limitation**: Estimated power is below the acceptable threshold of 0.70.")
    else:
        report_lines.append("Power is adequate (≥ 0.70).")

    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

def main(argv: list[str] | None = None) -> int:
    """Entry point for the script.

    The function returns an exit code compatible with typical CLI conventions.
    """
    if argv is None:
        argv = sys.argv[1:]

    # The script does not accept any command‑line arguments; they are ignored
    # but parsing them allows future extensibility without breaking the interface.
    _ = argv  # placeholder for potential future flags

    try:
        # Run the existing power analysis routine.
        result = run_power_analysis()
    except Exception as exc:
        sys.stderr.write(f"Error running power analysis: {exc}\\n")
        return 1

    # Define the required output location.
    output_md = Path(
        "projects/PROJ-586-social-memory-networks-modeling-collecti/results/power_analysis_report.md"
    )

    try:
        _write_report(result, output_md)
    except Exception as exc:
        sys.stderr.write(f"Failed to write power analysis report: {exc}\\n")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
