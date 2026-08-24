"""Report generation with dynamic sample size reporting.

This module extends the existing report generation logic (Task T033) by
inserting the actual number of subjects processed and the number of
subjects excluded, as required by Task T074.

It reads ``validation_status.json`` and ``qc_summary.csv`` from the
``data/analysis`` directory, computes the sample statistics, and injects
them into the report template (``templates/report_template.md``).  The
final Markdown report is written to ``reports/summary.md``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# ----------------------------------------------------------------------
# Helper functions – loading data
# ----------------------------------------------------------------------
def load_template(template_path: Path) -> str:
    """Load the Markdown template used for the final report.

    Parameters
    ----------
    template_path: Path
        Path to the Markdown template file.

    Returns
    -------
    str
        The raw template text.
    """
    if not template_path.is_file():
        raise FileNotFoundError(f"Report template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def load_validation_status(status_path: Path) -> Dict[str, Any]:
    """Load ``validation_status.json`` produced by the QC pipeline.

    Parameters
    ----------
    status_path: Path
        Path to the JSON status file.

    Returns
    -------
    dict
        Parsed JSON content.
    """
    if not status_path.is_file():
        raise FileNotFoundError(f"validation_status.json not found at {status_path}")
    with status_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_qc_summary(qc_path: Path) -> pd.DataFrame:
    """Load ``qc_summary.csv`` containing per‑subject QC metrics.

    The CSV is expected to have at least a column named ``included`` that
    indicates whether the subject passed QC (True/False or 1/0).

    Parameters
    ----------
    qc_path: Path
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
        DataFrame with the QC summary.
    """
    if not qc_path.is_file():
        raise FileNotFoundError(f"qc_summary.csv not found at {qc_path}")
    df = pd.read_csv(qc_path)
    if "included" not in df.columns:
        # Fall back to a boolean interpretation: any non‑null row is included.
        df["included"] = True
    return df


# ----------------------------------------------------------------------
# Core logic – compute sample statistics
# ----------------------------------------------------------------------
def format_sample_info(
    validation_path: Path,
    qc_summary_path: Path,
) -> str:
    """Create a human‑readable block with sample size information.

    The function follows the specification of Task T074:
    * read ``validation_status.json`` and ``qc_summary.csv``
    * determine the number of subjects that were processed (i.e. passed
      QC) and the number that were excluded
    * return a formatted string suitable for insertion into the Markdown
      report.

    Parameters
    ----------
    validation_path: Path
        Path to ``validation_status.json``.
    qc_summary_path: Path
        Path to ``qc_summary.csv``.

    Returns
    -------
    str
        Formatted Markdown snippet.
    """
    # Load files
    validation = load_validation_status(validation_path)
    qc_df = load_qc_summary(qc_summary_path)

    # Primary source for counts is the QC summary.  The JSON may contain
    # explicit counts, but we treat the CSV as authoritative.
    processed = int(qc_df["included"].astype(bool).sum())
    total = len(qc_df)
    excluded = total - processed

    # If the JSON supplies explicit numbers, verify consistency.
    json_processed = validation.get("subjects_processed")
    json_excluded = validation.get("subjects_excluded")
    if json_processed is not None and json_processed != processed:
        # Log a warning via the tolerant logger (if available)
        try:
            from code.logging_config import get_logger

            logger = get_logger(__name__)
            logger.warning(
                "Mismatch between QC CSV and validation_status.json: "
                f"processed {json_processed} (JSON) vs {processed} (CSV). "
                "Using CSV values."
            )
        except Exception:
            pass  # logger optional – continue with CSV values

    # Build the Markdown snippet
    sample_info = (
        f"**Number of subjects processed:** {processed}\\n"
        f"**Number of subjects excluded:** {excluded}\\n"
    )
    return sample_info


# ----------------------------------------------------------------------
# Report assembly
# ----------------------------------------------------------------------
def generate_report(
    template_path: Path,
    output_path: Path,
    validation_path: Path,
    qc_summary_path: Path,
) -> None:
    """Generate the final Markdown report with dynamic sample size info.

    Parameters
    ----------
    template_path: Path
        Path to the report template (Markdown with a ``{{SAMPLE_INFO}}``
        placeholder).
    output_path: Path
        Destination path for the rendered report.
    validation_path: Path
        Path to ``validation_status.json``.
    qc_summary_path: Path
        Path to ``qc_summary.csv``.
    """
    # Load the base template
    template = load_template(template_path)

    # Compute the sample‑size block
    sample_info = format_sample_info(validation_path, qc_summary_path)

    # Insert the sample information.  The placeholder ``{{SAMPLE_INFO}}`` is
    # defined in the template; if it is missing we append the block at the
    # end of the document.
    placeholder = "{{SAMPLE_INFO}}"
    if placeholder in template:
        report_content = template.replace(placeholder, sample_info)
    else:
        report_content = f"{template}\n\n{sample_info}"

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the final report
    output_path.write_text(report_content, encoding="utf-8")

    # Inform the (tolerant) logger that the report was produced
    try:
        from code.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info(f"Report written to {output_path}")
    except Exception:
        pass  # logger optional


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """Command‑line interface for the report generator.

    Expected arguments (mirroring the original quick‑start script):
    1. ``--template`` path to the Markdown template.
    2. ``--output``   path where the report should be written.
    3. ``--validation`` path to ``validation_status.json``.
    4. ``--qc-summary`` path to ``qc_summary.csv``.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate the final analysis report with dynamic sample‑size statistics."
    )
    parser.add_argument(
        "--template",
        type=Path,
        required=True,
        help="Path to the Markdown report template.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path where the rendered Markdown report will be saved.",
    )
    parser.add_argument(
        "--validation",
        type=Path,
        required=True,
        help="Path to validation_status.json produced by the QC pipeline.",
    )
    parser.add_argument(
        "--qc-summary",
        type=Path,
        required=True,
        help="Path to qc_summary.csv produced by the QC pipeline.",
    )

    args = parser.parse_args(argv)

    try:
        generate_report(
            template_path=args.template,
            output_path=args.output,
            validation_path=args.validation,
            qc_summary_path=args.qc_summary,
        )
    except Exception as exc:
        # Use the tolerant logger if possible; otherwise print to stderr.
        try:
            from code.logging_config import get_logger

            logger = get_logger(__name__)
            logger.error(f"Report generation failed: {exc}")
        except Exception:
            print(f"Report generation failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
