"""Generate a Markdown report from correlation analysis results.

This script is invoked by the project's quickstart run‑book:

    python code/viz/generate_report.py --input <csv> --output <md>

It reads a CSV file containing correlation results (as produced by the
analysis pipeline) and writes a self‑contained Markdown report summarising
the findings.  The implementation is deliberately lightweight and relies
only on the standard library and ``pandas`` (which is already a declared
dependency of the project).

The core public API consists of two callables:

* ``generate_report(results: dict) -> str``
  Takes a dictionary representation of the analysis results and returns a
  Markdown string.

* ``main()`` – the CLI entry point used by the run‑book.

The script raises clear errors when required inputs are missing or malformed,
ensuring that failures are loud and informative rather than silently producing
fabricated output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _load_csv(csv_path: Path) -> pd.DataFrame:
    """Load the correlation results CSV.

    Parameters
    ----------
    csv_path: Path
        Path to the CSV file produced by ``code/analysis/correlations.py``.
        The file must contain at least the columns ``metric_name``,
        ``r``, ``p``, ``q`` and ``significant`` (the latter should be a
        boolean or a value that can be interpreted as such).

    Returns
    -------
    pd.DataFrame
        The parsed data frame.

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist.
    ValueError
        If required columns are missing.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Correlation results CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required = {"metric_name", "r", "p", "q", "significant"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV file {csv_path} is missing required columns: {', '.join(missing)}"
        )
    return df


def _summarise_results(df: pd.DataFrame) -> Dict[str, Any]:
    """Create a dictionary summarising the key findings.

    The summary includes:

    * total number of tested metrics
    * number and proportion of significant results (q < 0.05)
    * a list of significant metrics with their effect sizes.

    Returns
    -------
    dict
        Keys ``total``, ``significant_count``, ``significant_pct`` and
        ``significant_metrics`` (a list of dicts with ``metric_name``,
        ``r`` and ``q``).
    """
    total = len(df)
    # Treat any truthy value in the ``significant`` column as significant.
    sig_mask = df["significant"].astype(bool)
    significant_count = int(sig_mask.sum())
    significant_pct = (
        significant_count / total * 100 if total > 0 else 0.0
    )

    significant_metrics = (
        df.loc[sig_mask, ["metric_name", "r", "q"]]
        .rename(columns={"q": "q_value"})
        .to_dict(orient="records")
    )

    return {
        "total": total,
        "significant_count": significant_count,
        "significant_pct": round(significant_pct, 2),
        "significant_metrics": significant_metrics,
    }


def _format_table(df: pd.DataFrame) -> str:
    """Render the full results table as a Markdown table."""
    # Use the original column order for readability.
    header = " | ".join(df.columns)
    separator = " | ".join(["---"] * len(df.columns))
    rows = "\n".join(
        " | ".join(map(str, row)) for row in df.itertuples(index=False, name=None)
    )
    return f"{header}\n{separator}\n{rows}"


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def generate_report(results: Dict[str, Any]) -> str:
    """Return a Markdown string representing the analysis report.

    Parameters
    ----------
    results: dict
        A dictionary with at least the keys produced by
        ``_summarise_results`` and ``_format_table``.  Expected keys:

        * ``summary`` – dict returned by ``_summarise_results``.
        * ``table_md`` – a Markdown‑formatted table string.

    Returns
    -------
    str
        The complete Markdown document.
    """
    summary = results.get("summary", {})
    table_md = results.get("table_md", "")

    title = "# Correlation Analysis Report\n"
    intro = (
        "This report summarises the association between brain network metrics "
        "and the behavioural covariates of interest.\n"
    )

    # Basic summary paragraph
    summary_paragraph = (
        f"- **Total metrics tested:** {summary.get('total', 'N/A')}\n"
        f"- **Significant after FDR correction (q < 0.05):** "
        f"{summary.get('significant_count', 'N/A')} "
        f"({summary.get('significant_pct', 'N/A')}%)\n"
    )

    # Detailed list of significant metrics (if any)
    sig_metrics = summary.get("significant_metrics", [])
    if sig_metrics:
        sig_section = "\n## Significant Metrics\n\n"
        for metric in sig_metrics:
            sig_section += (
                f"* **{metric.get('metric_name', 'N/A')}** – "
                f"r = {metric.get('r', 'N/A'):.3f}, "
                f"q = {metric.get('q_value', 'N/A'):.3f}\n"
            )
    else:
        sig_section = "\n*No metrics survived FDR correction.*\n"

    # Assemble the final document
    markdown = (
        f"{title}\n"
        f"{intro}\n"
        f"{summary_paragraph}\n"
        f"{sig_section}\n"
        f"---\n"
        f"## Full Results Table\n\n"
        f"{table_md}\n"
    )
    return markdown


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments for the script."""
    parser = argparse.ArgumentParser(
        description="Generate a Markdown report from correlation results."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to the CSV file containing correlation results.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Path where the generated Markdown report will be written.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    """Run the report generation pipeline."""
    args = parse_args(argv)

    # Load and validate the CSV
    df = _load_csv(args.input)

    # Build the data structures expected by ``generate_report``
    summary = _summarise_results(df)
    table_md = _format_table(df)

    report_md = generate_report(
        {
            "summary": summary,
            "table_md": table_md,
        }
    )

    # Ensure the parent directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write the Markdown file
    args.output.write_text(report_md, encoding="utf-8")
    print(f"Report written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()