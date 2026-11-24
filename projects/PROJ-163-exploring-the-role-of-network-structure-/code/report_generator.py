"""
Thin wrapper around the existing ``generate_report`` module that writes the
final markdown report to the location required by task T008
(``data/results/report.md``).

The heavy‑lifting logic lives in ``code.generate_report``; this file only
forwards the call with the correct output path and provides a simple CLI.
"""

import logging
from pathlib import Path

# Import the full report generation function from the existing module.
from code.generate_report import generate_report

logger = logging.getLogger(__name__)

def main() -> None:
    """
    Generate the research report at ``data/results/report.md``.
    """
    logging.basicConfig(level=logging.INFO)
    output_path = Path("data/results/report.md")
    logger.info(f"Generating report at {output_path}")
    generate_report(output_path=str(output_path))

if __name__ == "__main__":
    main()