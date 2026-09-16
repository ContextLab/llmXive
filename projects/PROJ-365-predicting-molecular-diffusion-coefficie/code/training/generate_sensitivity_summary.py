"""
generate_sensitivity_summary.py
--------------------------------
This module reads the results of the hyper‑parameter sensitivity sweep
(``artifacts/reports/sensitivity_report.json``) and the ablation study
(``artifacts/reports/ablation_report.json``) and produces a concise
Markdown summary at ``artifacts/reports/sensitivity_summary.md``.

The summary contains:
* a table of all Pearson‑r values that were recorded,
* a **stability** field that is ``stable`` when **every** r value is
  greater than the 0.7 threshold required by the specification,
  otherwise ``unstable``.

The script is deliberately lightweight – it only depends on the standard
library and the project's ``utils.config`` helper for locating the project
root.

It can be executed directly:

    $ python code/training/generate_sensitivity_summary.py

or imported and used programmatically via ``generate_summary()``.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from utils.config import get_project_root


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content.

    Parameters
    ----------
    path: Path
        Path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON content.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Required report not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_r_values_from_sensitivity(report: Dict[str, Any]) -> List[float]:
    """
    The sensitivity report is expected to be a list of dictionaries,
    each representing a hyper‑parameter configuration.  The exact schema
    is not hard‑coded; we simply look for a numeric ``r`` key.

    Parameters
    ----------
    report: dict
        The loaded JSON content (list or dict with ``results`` key).

    Returns
    -------
    List[float]
        All Pearson‑r values found.
    """
    r_values: List[float] = []

    # The report may be a list directly or wrapped in a dict.
    if isinstance(report, list):
        entries = report
    elif isinstance(report, dict) and "results" in report:
        entries = report["results"]
    else:
        entries = []

    for entry in entries:
        if isinstance(entry, dict):
            r = entry.get("r")
            if isinstance(r, (int, float)):
                r_values.append(float(r))
    return r_values


def _extract_r_values_from_ablation(report: Dict[str, Any]) -> List[float]:
    """
    The ablation report contains explicit fields for the GNN and the
    baseline Pearson‑r values (named ``gnn_r`` and ``baseline_r`` in the
    implementation of T025b).  We extract both if present.

    Parameters
    ----------
    report: dict
        Loaded JSON content.

    Returns
    -------
    List[float]
        List containing the two r values (may be empty if keys are missing).
    """
    r_values: List[float] = []
    for key in ("gnn_r", "baseline_r"):
        r = report.get(key)
        if isinstance(r, (int, float)):
            r_values.append(float(r))
    return r_values


# ----------------------------------------------------------------------
# Core functionality
# ----------------------------------------------------------------------
def generate_summary() -> str:
    """
    Generate the Markdown summary for the sensitivity analysis.

    Returns
    -------
    str
        Markdown text that will be written to ``sensitivity_summary.md``.
    """
    project_root = get_project_root()

    # Expected locations of the prerequisite reports
    sensitivity_path = project_root / "artifacts" / "reports" / "sensitivity_report.json"
    ablation_path = project_root / "artifacts" / "reports" / "ablation_report.json"

    # Load the JSON files (will raise FileNotFoundError if missing)
    sensitivity_json = _load_json(sensitivity_path)
    ablation_json = _load_json(ablation_path)

    # Pull out all Pearson‑r values
    r_values: List[float] = []
    r_values.extend(_extract_r_values_from_sensitivity(sensitivity_json))
    r_values.extend(_extract_r_values_from_ablation(ablation_json))

    # Determine stability
    THRESHOLD = 0.7
    stability = "stable" if all(r > THRESHOLD for r in r_values) else "unstable"

    # Build a simple Markdown table
    table_lines = ["| Source | Pearson r |", "|--------|-----------|"]
    # Sensitivity entries – we label them by index
    for idx, r in enumerate(_extract_r_values_from_sensitivity(sensitivity_json), start=1):
        table_lines.append(f"| Sensitivity #{idx} | {r:.4f} |")
    # Ablation entries – explicit naming
    for key, r in zip(("GNN (ablation)", "Baseline (ablation)"),
                      _extract_r_values_from_ablation(ablation_json)):
        table_lines.append(f"| {key} | {r:.4f} |")

    markdown = (
        "# Sensitivity Summary\\n\\n"
        f"**Stability:** `{stability}`\\n\\n"
        "## Pearson‑r values across all variations\\n\\n"
        + "\n".join(table_lines)
        + "\\n"
    )

    return markdown


def main() -> None:
    """
    Entry‑point used by the CI / pipeline.  It writes the markdown file to
    ``artifacts/reports/sensitivity_summary.md``.
    """
    summary_md = generate_summary()

    output_path = get_project_root() / "artifacts" / "reports" / "sensitivity_summary.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"Sensitivity summary written to {output_path}")


if __name__ == "__main__":
    main()