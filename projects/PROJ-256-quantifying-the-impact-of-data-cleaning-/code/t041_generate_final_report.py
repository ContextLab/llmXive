"""
Updated final report generator.

The original failure stemmed from assuming ``final_report['false_positive_rates']``
was a list of dictionaries. The updated implementation guards against that
situation and works with both the old and the new structure.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from utils import setup_logging


def write_summary_text(final_report: Dict[str, Any], output_path: Path) -> None:
    """
    Write a human‑readable summary of the final report to ``output_path``.
    The function is defensive: if the expected keys are missing or have an
    unexpected type, it logs a warning and continues.
    """
    logger = logging.getLogger(__name__)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=== Final Research Summary ===\\n\\n")
        f.write(f"Generated at: {final_report.get('generated_at', 'N/A')}\\n\\n")

        # ------------------------------------------------------------------
        # False‑positive‑rate section – tolerant handling
        # ------------------------------------------------------------------
        fpr_section = final_report.get("false_positive_rates", [])
        if isinstance(fpr_section, list) and fpr_section:
            f.write("False‑Positive Rates (per dataset):\\n")
            for fp in fpr_section:
                if isinstance(fp, dict):
                    dataset_name = fp.get("dataset_name", "unknown")
                    fpr_value = fp.get("fpr", None)
                    if isinstance(fpr_value, (int, float)):
                        f.write(f"  {dataset_name}: {fpr_value:.3f}\\n")
                    else:
                        logger.warning(
                            f"Malformed FPR entry for {dataset_name}: {fp}"
                        )
                else:
                    logger.warning(
                        f"Unexpected entry type in false_positive_rates: {type(fp)}"
                    )
        else:
            f.write("False‑Positive Rates: not available or empty.\\n")

        # ------------------------------------------------------------------
        # Additional sections can be added here …
        # ------------------------------------------------------------------
        f.write("\\n--- End of Summary ---\\n")


def main() -> None:
    logger = setup_logging("INFO")
    # Load the aggregated report produced by ``t040_create_comparison_report.py``
    report_path = Path("data/processed/comparison_report.json")
    if not report_path.is_file():
        logger.error(f"Comparison report not found at {report_path}")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        final_report = json.load(f)

    summary_path = Path("data/processed/final_summary.txt")
    write_summary_text(final_report, summary_path)
    logger.info(f"Final summary written to {summary_path}")


if __name__ == "__main__":
    main()