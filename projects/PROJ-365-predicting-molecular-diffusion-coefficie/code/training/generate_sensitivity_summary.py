"""
generate_sensitivity_summary.py

This module generates the final sensitivity summary report
``artifacts/reports/sensitivity_summary.md``.  It reads the two JSON
artifacts produced by the sensitivity sweep (``sensitivity_report.json``)
and the ablation study (``ablation_report.json``), extracts all Pearson
correlation coefficients, determines whether every coefficient meets the
stability threshold (r ≥ 0.7), and writes a human‑readable Markdown file
containing:

* A table of the sensitivity sweep results (hyper‑parameter settings and
  the corresponding Pearson r).
* A short section summarising the ablation study results.
* A ``stability`` field indicating ``stable`` if *all* Pearson r values
  (both sweep and ablation) are ≥ 0.7, otherwise ``unstable``.

The script is deliberately minimal and has no side‑effects other than
writing the Markdown file.  It is intended to be executed directly, e.g.:

    python code/training/generate_sensitivity_summary.py

The implementation relies only on the public API defined in the project
(``utils.config`` for locating the repository root).
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from utils.config import get_project_root


def _load_json(path: Path) -> Any:
    """Load a JSON file and return the parsed object."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_pearson_values_from_sensitivity(
    sweep_data: List[Dict[str, Any]]
) -> List[float]:
    """
    Extract Pearson r values from the sensitivity sweep JSON.

    The expected format of each entry in ``sweep_data`` is a mapping that
    contains a ``pearson_r`` key (float).  If the key is missing we ignore
    the entry – this makes the function tolerant to future schema changes.
    """
    r_vals: List[float] = []
    for entry in sweep_data:
        r = entry.get("pearson_r")
        if isinstance(r, (int, float)):
            r_vals.append(float(r))
    return r_vals


def _extract_pearson_values_from_ablation(ablation_data: Dict[str, Any]) -> List[float]:
    """
    Extract Pearson r values from the ablation report.

    The ablation JSON is expected to contain at least the following keys:
    ``gnn_pearson_r`` and ``baseline_pearson_r``.  Any additional Pearson
    values are also collected if they follow the ``*_pearson_r`` naming
    convention.
    """
    r_vals: List[float] = []
    for key, value in ablation_data.items():
        if key.endswith("_pearson_r") and isinstance(value, (int, float)):
            r_vals.append(float(value))
    return r_vals


def _determine_stability(all_r: List[float], threshold: float = 0.7) -> str:
    """
    Return ``stable`` if *all* Pearson r values are greater than or equal to
    ``threshold``, otherwise ``unstable``.
    """
    if not all_r:
        # No data – treat as unstable to avoid false positives.
        return "unstable"
    return "stable" if all(r >= threshold for r in all_r) else "unstable"


def generate_summary() -> Path:
    """
    Generate ``sensitivity_summary.md`` and return its path.

    The function performs the following steps:

    1. Load ``artifacts/reports/sensitivity_report.json``.
    2. Load ``artifacts/reports/ablation_report.json``.
    3. Collect all Pearson r values from both artifacts.
    4. Determine the stability flag.
    5. Write a Markdown file containing:
       * A table of the sweep results.
       * A brief description of the ablation results.
       * The ``stability`` field.
    """
    project_root = get_project_root()
    reports_dir = project_root / "artifacts" / "reports"

    # 1. Load the sensitivity sweep report.
    sweep_path = reports_dir / "sensitivity_report.json"
    sweep_data = _load_json(sweep_path)  # Expected to be a list of dicts

    # 2. Load the ablation report.
    ablation_path = reports_dir / "ablation_report.json"
    ablation_data = _load_json(ablation_path)  # Expected to be a dict

    # 3. Extract Pearson r values.
    sweep_r = _extract_pearson_values_from_sensitivity(sweep_data)
    ablation_r = _extract_pearson_values_from_ablation(ablation_data)
    all_r = sweep_r + ablation_r

    # 4. Determine stability.
    stability = _determine_stability(all_r, threshold=0.7)

    # 5. Build Markdown content.
    md_lines: List[str] = [
        "# Sensitivity Summary",
        "",
        "This report aggregates the results of the hyper‑parameter sensitivity sweep"
        " and the solvent‑removal ablation study.  The goal is to assess whether the"
        " model’s Pearson correlation coefficient remains robust (r ≥ 0.7) across"
        " all examined variations.",
        "",
        "## Sensitivity Sweep Results",
        "",
        "| # | Hyper‑parameters | Pearson r |",
        "|---|------------------|-----------|",
    ]

    # Populate the table rows.
    for idx, entry in enumerate(sweep_data, start=1):
        # Build a human‑readable representation of the hyper‑parameters.
        # We join key‑value pairs excluding the Pearson r itself.
        hyper_params = ", ".join(
            f"{k}={v}"
            for k, v in entry.items()
            if k != "pearson_r"
        )
        r_val = entry.get("pearson_r", "N/A")
        md_lines.append(f"| {idx} | {hyper_params} | {r_val} |")

    md_lines.extend(
        [
            "",
            "## Ablation Study Results",
            "",
            f"* GNN Pearson r: {ablation_data.get('gnn_pearson_r', 'N/A')}",
            f"* Baseline Pearson r: {ablation_data.get('baseline_pearson_r', 'N/A')}",
            f"* GNN variation delta: {ablation_data.get('gnn_variation_delta', 'N/A')}",
            f"* Baseline variation delta: {ablation_data.get('baseline_variation_delta', 'N/A')}",
            "",
            "## Stability Assessment",
            "",
            f"**stability:** `{stability}`",
            "",
            "_All Pearson r values observed in the sensitivity sweep and the"
            " ablation study were examined against the 0.7 threshold._",
        ]
    )

    summary_path = reports_dir / "sensitivity_summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(md_lines), encoding="utf-8")

    return summary_path


def main() -> None:
    """
    Entry‑point for the script.  It simply calls :func:`generate_summary`
    and prints the location of the generated file.
    """
    summary_path = generate_summary()
    print(f"Sensitivity summary written to: {summary_path}")


if __name__ == "__main__":
    main()