"""
Report utility functions for appending mandatory disclaimers to generated reports.

This module provides functionality to inject the required associational analysis
disclaimer into markdown report text, ensuring compliance with scientific
communication standards.
"""

import os
import sys
from typing import Optional

from .logging import get_logger

# The mandatory disclaimer text required for all reports
MANDATORY_DISCLAIMER = (
    "DISCLAIMER: This report presents an associational analysis only. "
    "No causal inference can be drawn from the observed correlations. "
    "Predictive performance does not imply mechanistic understanding."
)


def inject_disclaimer(report_text: str, position: str = "append") -> str:
    """
    Inject the mandatory disclaimer into the provided report text.

    Args:
        report_text: The original markdown report content.
        position: Where to place the disclaimer. Options:
            - "append": Add at the end of the document (default).
            - "prepend": Add at the beginning of the document.
            - "footer": Add as a distinct footer section.

    Returns:
        The report text with the mandatory disclaimer injected.
    """
    if not report_text:
        return MANDATORY_DISCLAIMER

    position = position.lower()

    if position == "prepend":
        return f"{MANDATORY_DISCLAIMER}\n\n{report_text}"

    elif position == "footer":
        return f"{report_text}\n\n---\n\n{MANDATORY_DISCLAIMER}"

    else:  # Default: append
        return f"{report_text}\n\n{MANDATORY_DISCLAIMER}"


def finalize_report_markdown(
    report_content: str,
    output_path: Optional[str] = None
) -> str:
    """
    Finalize a report by appending the mandatory disclaimer and optionally saving.

    This function ensures that every generated report includes the required
    disclaimer about associational analysis. It can also write the finalized
    report to a file if a path is provided.

    Args:
        report_content: The raw markdown content of the report.
        output_path: Optional file path to save the finalized report.

    Returns:
        The finalized report content with the disclaimer included.
    """
    logger = get_logger(__name__)
    finalized_content = inject_disclaimer(report_content, position="append")

    if output_path:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(finalized_content)
            logger.info(f"Report with disclaimer saved to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save report to {output_path}: {e}")
            raise

    return finalized_content