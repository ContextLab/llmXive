"""
add_auc_summary.py

This script appends a summary section to the project's final report
(``docs/report.md``) with the average AUC and its 95 % confidence interval
obtained from the cross‑validation results produced by the modeling
pipeline, together with a baseline random‑classifier reference (AUC = 0.5).

The script is intended to be executed after the main report has been
generated (e.g. after ``python code/generate_report.py``).  It reads the
JSON file ``data/processed/cv_metrics.json`` which must contain the
keys ``average_auc``, ``ci_lower`` and ``ci_upper``.  If the required file
or keys are missing, the script raises an informative exception so that
the failure is loud and visible.
"""

import json
from pathlib import Path
import sys

def load_cv_metrics(metrics_path: Path) -> dict:
    """Load cross‑validation metrics from a JSON file.

    The JSON must contain:
        - ``average_auc``: float
        - ``ci_lower``: float (lower bound of 95 % CI)
        - ``ci_upper``: float (upper bound of 95 % CI)

    Parameters
    ----------
    metrics_path: Path
        Path to the ``cv_metrics.json`` file.

    Returns
    -------
    dict
        Dictionary with the three required keys.

    Raises
    ------
    FileNotFoundError
        If ``metrics_path`` does not exist.
    KeyError
        If any of the required keys are missing.
    ValueError
        If the values cannot be converted to ``float``.
    """
    if not metrics_path.is_file():
        raise FileNotFoundError(f"Cross‑validation metrics file not found: {metrics_path}")

    with metrics_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    required_keys = {"average_auc", "ci_lower", "ci_upper"}
    missing = required_keys - data.keys()
    if missing:
        raise KeyError(f"Missing required keys {missing} in {metrics_path}")

    # Ensure values are floats
    try:
        data["average_auc"] = float(data["average_auc"])
        data["ci_lower"] = float(data["ci_lower"])
        data["ci_upper"] = float(data["ci_upper"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Metric values must be numeric: {exc}") from exc

    return data

def append_summary_to_report(report_path: Path, metrics: dict) -> None:
    """Append the AUC summary section to the markdown report.

    The function creates the section if it does not already exist;
    otherwise it replaces the existing section to keep the report
    idempotent.

    Parameters
    ----------
    report_path: Path
        Path to ``docs/report.md``.
    metrics: dict
        Dictionary containing ``average_auc``, ``ci_lower`` and ``ci_upper``.
    """
    if not report_path.is_file():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    # Build the markdown block
    summary_md = (
        "\n## Model Performance Summary\n\n"
        f"- **Average AUC (cross‑validation)**: {metrics['average_auc']:.3f} "
        f"(95 % CI: {metrics['ci_lower']:.3f} – {metrics['ci_upper']:.3f})\n"
        "- **Baseline random‑classifier AUC**: 0.5\n"
    )

    # Read existing content
    with report_path.open("r", encoding="utf-8") as f:
        content = f.read()

    # If the section already exists, replace it; otherwise append.
    marker = "## Model Performance Summary"
    if marker in content:
        # Split at the marker and keep everything before it
        pre, _ = content.split(marker, 1)
        new_content = pre + summary_md
    else:
        new_content = content.rstrip() + summary_md

    # Write back
    with report_path.open("w", encoding="utf-8") as f:
        f.write(new_content)

def main() -> None:
    """Entry point for the script."""
    project_root = Path(__file__).resolve().parents[1]  # assumes this file is in ``code/``
    metrics_path = project_root / "data" / "processed" / "cv_metrics.json"
    report_path = project_root / "docs" / "report.md"

    try:
        metrics = load_cv_metrics(metrics_path)
        append_summary_to_report(report_path, metrics)
        print(f"✅ AUC summary appended to {report_path}")
    except Exception as exc:
        print(f"❌ Failed to add AUC summary: {exc}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
