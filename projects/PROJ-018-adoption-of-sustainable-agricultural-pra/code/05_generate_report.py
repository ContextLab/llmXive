"""Generate a PDF report for the Sustainable Agricultural Practices study.

This script reads the processed data and analysis results produced by earlier
pipeline steps and assembles a concise PDF report containing:

* Header & project metadata
* Descriptive statistics of the engineered dataset
* Regression summary table
* VIF diagnostics
* ROC curve and AUC
* Mediation analysis results
* Sensitivity analysis (E‑values)
* Validity metrics (Cronbach's α, factor loadings, convergent validity)

The script is deliberately defensive: if any expected file is missing or
malformed, the corresponding section is omitted rather than causing the
whole script to fail. All outputs are written under the ``results/`` folder,
which is created automatically if it does not exist.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, Image)

# --------------------------------------------------------------------------- #
# Helper functions to load various artefacts
# --------------------------------------------------------------------------- #

def _safe_read_csv(path: Path) -> Optional[pd.DataFrame]:
    """Read a CSV file safely; return ``None`` if the file does not exist."""
    if not path.is_file():
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:  # pragma: no cover
        print(f"Failed to read CSV {path}: {exc}", file=sys.stderr)
        return None

def _safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    """Read a JSON file safely; return ``None`` on failure."""
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # pragma: no cover
        print(f"Failed to read JSON {path}: {exc}", file=sys.stderr)
        return None

def _safe_read_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Read a YAML file safely; return ``None`` on failure."""
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:  # pragma: no cover
        print(f"Failed to read YAML {path}: {exc}", file=sys.stderr)
        return None

# --------------------------------------------------------------------------- #
# Public loading functions used by the report generation pipeline
# --------------------------------------------------------------------------- #

def load_cleaned_data() -> Optional[pd.DataFrame]:
    """Load ``data/processed/cleaned_data.csv``."""
    return _safe_read_csv(Path("data/processed/cleaned_data.csv"))

def load_engineered_data() -> Optional[pd.DataFrame]:
    """Load ``data/processed/engineered_data.csv``."""
    return _safe_read_csv(Path("data/processed/engineered_data.csv"))

def load_model_results() -> Optional[Dict[str, Any]]:
    """Load model results stored as JSON (e.g. ``results/model_results.json``)."""
    return _safe_read_json(Path("results/model_results.json"))

def load_mediation_results() -> Optional[Dict[str, Any]]:
    """Load mediation analysis output (``results/mediation_results.json``)."""
    return _safe_read_json(Path("results/mediation_results.json"))

def load_validity_metrics() -> Optional[Dict[str, Any]]:
    """Load validity metrics written by the feature‑engineering step."""
    return _safe_read_yaml(Path("results/validity_metrics.yaml"))

# --------------------------------------------------------------------------- #
# Report section generators
# --------------------------------------------------------------------------- #

def generate_report_header() -> Paragraph:
    """Create a simple header paragraph."""
    styles = getSampleStyleSheet()
    title = "Sustainable Agricultural Practices – Study Report"
    subtitle = "Community Engagement & Adoption Analysis"
    header = f"<para align='center'><b>{title}</b><br/>{subtitle}</para>"
    return Paragraph(header, styles["Title"])

def generate_descriptive_stats(df: pd.DataFrame) -> List[Paragraph]:
    """Generate a list of Paragraph objects with basic descriptive statistics."""
    styles = getSampleStyleSheet()
    paragraphs: List[Paragraph] = [Paragraph("<b>Descriptive Statistics</b>", styles["Heading2"])]
    if df is None or df.empty:
        paragraphs.append(Paragraph("No cleaned data available.", styles["Normal"]))
        return paragraphs

    # Compute a few useful aggregates
    desc = df.describe(include="all").round(2).reset_index()
    # Convert the DataFrame to a list of lists for a Table
    table_data = [desc.columns.tolist()] + desc.values.tolist()
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    paragraphs.extend([Spacer(1, 12), table])
    return paragraphs

def generate_regression_table(model_res: Dict[str, Any]) -> List[Paragraph]:
    """Render the regression summary stored in ``model_res``."""
    styles = getSampleStyleSheet()
    paragraphs: List[Paragraph] = [Paragraph("<b>Logistic Regression Summary</b>", styles["Heading2"])]
    if not model_res or "params" not in model_res:
        paragraphs.append(Paragraph("Regression results not available.", styles["Normal"]))
        return paragraphs

    params = model_res["params"]
    rows = [["Variable", "Coef.", "Std.Err.", "z", "P>|z|", "95% CI"]]
    for var, stats in params.items():
        row = [
            var,
            f"{stats.get('coef', ''):.3f}",
            f"{stats.get('std_err', ''):.3f}",
            f"{stats.get('z', ''):.2f}",
            f"{stats.get('p', ''):.3f}",
            f"{stats.get('ci_lower', ''):.3f} – {stats.get('ci_upper', ''):.3f}",
        ]
        rows.append(row)

    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    paragraphs.extend([Spacer(1, 12), table])
    return paragraphs

def generate_vif_section(vif_dict: Dict[str, float]) -> List[Paragraph]:
    """Create a VIF diagnostics section."""
    styles = getSampleStyleSheet()
    paragraphs: List[Paragraph] = [Paragraph("<b>VIF Diagnostics</b>", styles["Heading2"])]
    if not vif_dict:
        paragraphs.append(Paragraph("VIF information not available.", styles["Normal"]))
        return paragraphs

    rows = [["Predictor", "VIF"]]
    for predictor, vif in vif_dict.items():
        rows.append([predictor, f"{vif:.2f}"])
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    paragraphs.extend([Spacer(1, 12), table])
    return paragraphs

def generate_roc_section(roc_info: Dict[str, Any]) -> List[Paragraph]:
    """Add ROC curve image (if present) and AUC value."""
    styles = getSampleStyleSheet()
    paragraphs: List[Paragraph] = [Paragraph("<b>ROC Curve & AUC</b>", styles["Heading2"])]
    if not roc_info:
        paragraphs.append(Paragraph("ROC information not available.", styles["Normal"]))
        return paragraphs

    auc = roc_info.get("auc")
    paragraphs.append(Paragraph(f"AUC: {auc:.3f}" if auc is not None else "AUC not reported.", styles["Normal"]))

    # Expect a PNG plot at ``results/roc_curve.png`` – include if it exists
    roc_path = Path("results/roc_curve.png")
    if roc_path.is_file():
        img = Image(str(roc_path), width=400, height=300)
        paragraphs.append(Spacer(1, 12))
        paragraphs.append(img)
    else:
        paragraphs.append(Paragraph("ROC plot image not found.", styles["Normal"]))
    return paragraphs

def generate_mediation_section(med_res: Dict[str, Any]) -> List[Paragraph]:
    """Render mediation analysis results."""
    styles = getSampleStyleSheet()
    paragraphs: List[Paragraph] = [Paragraph("<b>Mediation Analysis</b>", styles["Heading2"])]
    if not med_res:
        paragraphs.append(Paragraph("Mediation results not available.", styles["Normal"]))
        return paragraphs

    rows = [["Path", "Estimate", "95% CI", "p-value", "Significant?"]]
    for path, details in med_res.items():
        est = details.get("estimate")
        ci_low = details.get("ci_lower")
        ci_up = details.get("ci_upper")
        p = details.get("p")
        sig = "Yes" if p is not None and p < 0.05 else "No"
        rows.append(
            [
                path,
                f"{est:.3f}" if est is not None else "",
                f"{ci_low:.3f} – {ci_up:.3f}" if ci_low is not None else "",
                f"{p:.3f}" if p is not None else "",
                sig,
            ]
        )
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    paragraphs.extend([Spacer(1, 12), table])
    return paragraphs

def generate_sensitivity_section(sens_res: Dict[str, Any]) -> List[Paragraph]:
    """Render sensitivity analysis (E‑values)."""
    styles = getSampleStyleSheet()
    paragraphs: List[Paragraph] = [Paragraph("<b>Sensitivity Analysis (E‑values)</b>", styles["Heading2"])]
    if not sens_res:
        paragraphs.append(Paragraph("Sensitivity analysis not available.", styles["Normal"]))
        return paragraphs

    rows = [["Effect", "E‑value"]]
    for effect, ev in sens_res.items():
        rows.append([effect, f"{ev:.3f}" if isinstance(ev, (int, float)) else str(ev)])
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    paragraphs.extend([Spacer(1, 12), table])
    return paragraphs

def generate_validity_section(validity: Dict[str, Any]) -> List[Paragraph]:
    """Create a section summarising reliability and factor analysis."""
    styles = getSampleStyleSheet()
    paragraphs: List[Paragraph] = [Paragraph("<b>Validity Metrics</b>", styles["Heading2"])]
    if not validity:
        paragraphs.append(Paragraph("Validity metrics not available.", styles["Normal"]))
        return paragraphs

    # Cronbach's alpha
    alpha = validity.get("cronbach_alpha")
    if alpha is not None:
        paragraphs.append(Paragraph(f"Cronbach's α: {alpha:.3f}", styles["Normal"]))

    # Factor loadings – defensive handling of missing/empty structures
    loadings = validity.get("factor_loadings", {})
    if isinstance(loadings, dict) and loadings:
        # Determine number of factors from first entry
        first_key = next(iter(loadings))
        num_factors = len(loadings[first_key]) if isinstance(loadings[first_key], (list, tuple)) else 1
        header = ["Variable"] + [f"Factor {i+1}" for i in range(num_factors)]
        rows = [header]
        for var, vals in loadings.items():
            if isinstance(vals, (list, tuple)):
                rows.append([var] + [f"{v:.3f}" for v in vals])
            else:
                rows.append([var, f"{vals:.3f}"])
        table = Table(rows, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )
        paragraphs.extend([Spacer(1, 12), table])
    else:
        paragraphs.append(Paragraph("Factor loadings not available.", styles["Normal"]))

    # Convergent validity correlations (if present)
    conv = validity.get("convergent_validity", {})
    if conv:
        rows = [["Construct", "Correlation"]]
        for name, corr in conv.items():
            rows.append([name, f"{corr:.3f}" if isinstance(corr, (int, float)) else str(corr)])
        table = Table(rows, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )
        paragraphs.extend([Spacer(1, 12), Paragraph("Convergent Validity", styles["Heading3"]), table])
    return paragraphs

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #

def main() -> None:
    """Assemble the PDF report."""
    # Ensure the results directory exists
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    doc_path = results_dir / "report.pdf"
    doc = SimpleDocTemplate(str(doc_path), pagesize=LETTER)
    story: List[Any] = []

    # Header
    story.append(generate_report_header())
    story.append(Spacer(1, 24))

    # Load data artefacts (each step is optional)
    cleaned = load_cleaned_data()
    engineered = load_engineered_data()
    model_res = load_model_results()
    mediation_res = load_mediation_results()
    validity = load_validity_metrics()

    # Descriptive stats
    story.extend(generate_descriptive_stats(engineered or cleaned))

    # Regression table
    story.extend(generate_regression_table(model_res))

    # VIF diagnostics (expect a dict under ``model_res["vif"]``)
    vif_info = model_res.get("vif") if isinstance(model_res, dict) else None
    story.extend(generate_vif_section(vif_info))

    # ROC / AUC
    roc_info = model_res.get("roc") if isinstance(model_res, dict) else None
    story.extend(generate_roc_section(roc_info))

    # Mediation analysis
    story.extend(generate_mediation_section(mediation_res))

    # Sensitivity analysis (E‑values)
    sens_info = model_res.get("evalues") if isinstance(model_res, dict) else None
    story.extend(generate_sensitivity_section(sens_info))

    # Validity metrics
    story.extend(generate_validity_section(validity))

    # Build PDF
    doc.build(story)
    print(f"Report generated at: {doc_path}")

if __name__ == "__main__":
    main()
