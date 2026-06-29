"""Generate a concise research report for the statistical analysis project.

This script creates an HTML report that includes:
  * Summary tables (e.g., thresholds, corrected p‑values) if the corresponding CSV files exist.
  * All PNG figures found under the project ``figures/`` directory.
  * A minimal introduction and title.

The report is written to ``data/report/report.html`` relative to the project root.
The script can be executed directly or imported and called from other code.

The implementation deliberately uses only standard‑library modules and the
project's existing dependencies (pandas, pathlib, etc.) to avoid adding new
requirements.
"""

from __future__ import annotations

import pathlib
import sys
from pathlib import Path

import pandas as pd

__all__ = ["generate_report"]


def _project_root() -> Path:
    """Return the absolute path to the repository root.

    The file lives in ``code/report/generate_report.py``; the repository root
    is therefore two parents up.
    """
    return Path(__file__).resolve().parents[2]


def _load_csv_as_html(csv_path: Path) -> str:
    """Load a CSV file with pandas and return an HTML table string.

    If the file cannot be read, an empty string is returned.
    """
    try:
        df = pd.read_csv(csv_path)
        # pandas' ``to_html`` already produces a full table; we suppress the index.
        return df.to_html(index=False, border=0, classes="dataframe")
    except Exception as exc:  # pragma: no cover – defensive programming
        print(f"Warning: could not load CSV {csv_path}: {exc}", file=sys.stderr)
        return ""


def _collect_figures_html(figures_dir: Path) -> str:
    """Collect all PNG files under *figures_dir* and return HTML fragments.

    Each figure is displayed with its filename as a heading and the image
    embedded using a relative path (relative to the generated HTML file).
    """
    html_parts = []
    for img_path in sorted(figures_dir.rglob("*.png")):
        # Compute the path that the HTML file will use to locate the image.
        # The HTML file lives in ``data/report/``; we need a relative path from there.
        rel_path = Path("..") / img_path.relative_to(_project_root())
        html_parts.append(
            f"<h3>{img_path.name}</h3>\n"
            f'<img src="{rel_path.as_posix()}" '
            f'style="max-width:800px; height:auto;" alt="{img_path.name}"/>'
        )
    return "\n".join(html_parts)


def generate_report() -> pathlib.Path:
    """Generate the HTML report and return the path to the written file."""
    root = _project_root()
    report_dir = root / "data" / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    out_path = report_dir / "report.html"

    # ------------------------------------------------------------------
    # 1. Assemble tables
    # ------------------------------------------------------------------
    tables_html = ""

    thresholds_csv = root / "data" / "thresholds.csv"
    if thresholds_csv.is_file():
        tables_html += "<h2>Thresholds</h2>\n"
        tables_html += _load_csv_as_html(thresholds_csv) + "\n"

    corrected_pvalues_csv = root / "data" / "model" / "corrected_pvalues.csv"
    if corrected_pvalues_csv.is_file():
        tables_html += "<h2>Corrected p‑values</h2>\n"
        tables_html += _load_csv_as_html(corrected_pvalues_csv) + "\n"

    # ------------------------------------------------------------------
    # 2. Assemble figures
    # ------------------------------------------------------------------
    figures_dir = root / "figures"
    figures_html = ""
    if figures_dir.is_dir():
        figures_html = _collect_figures_html(figures_dir)

    # ------------------------------------------------------------------
    # 3. Compose final HTML
    # ------------------------------------------------------------------
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>Statistical Analysis of Code Complexity – Research Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2rem; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 1.5rem; }}
        h3 {{ margin-top: 1rem; }}
        table.dataframe {{ border-collapse: collapse; width: 100%; }}
        table.dataframe th, table.dataframe td {{ border: 1px solid #ddd; padding: 8px; }}
        table.dataframe th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Statistical Analysis of Code Complexity – Research Report</h1>
    <p>
        This report summarises the results of the statistical modelling pipeline
        for predicting bug‑prone code units. It includes key tables and the
        visualisations generated during the analysis.
    </p>
    {tables_html}
    <h2>Figures</h2>
    {figures_html if figures_html else "<p>No figures were found.</p>"}
</body>
</html>
"""

    out_path.write_text(html_content, encoding="utf-8")
    print(f"Report generated at: {out_path}", file=sys.stderr)
    return out_path


if __name__ == "__main__":
    # Running the module directly will generate the report.
    generate_report()