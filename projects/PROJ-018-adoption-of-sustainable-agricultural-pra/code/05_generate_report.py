"""Generate a comprehensive PDF report for the sustainable‑agriculture study.

The script pulls together:
* Descriptive statistics of the cleaned survey data.
* The logistic‑regression summary.
* VIF diagnostics.
* ROC curve (with AUC).
* Mediation analysis results.
* Sensitivity analysis (E‑values, Rosenbaum bounds).
* Validity metrics (Cronbach’s α, factor loadings, convergent validity).

The resulting PDF is written to ``results/report.pdf``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Helper functions – each loads a specific artefact.
# ---------------------------------------------------------------------------
def _load_cleaned_data() -> pd.DataFrame:
    from config import get_processed_data_path

    path = get_processed_data_path() / "cleaned_data.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned data not found at {path}")
    return pd.read_csv(path)

def _load_engineered_data() -> pd.DataFrame:
    from config import get_processed_data_path

    path = get_processed_data_path() / "engineered_data.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Engineered data not found at {path}")
    return pd.read_csv(path)

def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"YAML file not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

# ---------------------------------------------------------------------------
# Section generators – each returns a list of Flowable objects.
# ---------------------------------------------------------------------------
def generate_report_header() -> list:
    """Title page."""
    styles = getSampleStyleSheet()
    title = Paragraph(
        "<font size=24><b>Sustainable Agricultural Practices Adoption Report</b></font>",
        styles["Title"],
    )
    subtitle = Paragraph(
        f"<font size=12>{datetime.now().strftime('%B %d, %Y')}</font>",
        styles["Normal"],
    )
    return [title, Spacer(1, 12), subtitle, Spacer(1, 24)]

def generate_descriptive_stats(df: pd.DataFrame) -> list:
    """Create a table with basic descriptive statistics."""
    numeric = df.select_dtypes(include="number")
    descr = numeric.describe().round(2)
    data = [["Metric"] + list(descr.columns)]
    for idx in descr.index:
        data.append([str(idx)] + [f"{v:.2f}" for v in descr.loc[idx]])
    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>1. Descriptive Statistics</b>", styles["Heading2"])
    return [heading, Spacer(1, 12), table, Spacer(1, 24)]

def generate_regression_table(regression: dict) -> list:
    """Render the regression summary as a table."""
    rows = regression.get("coefficients", [])
    data = [
        ["Variable", "Coef.", "Std.Err.", "z", "P>|z|"],
    ]
    for row in rows:
        data.append(
            [
                row.get("var", ""),
                f"{row.get('coef', 0):.4f}",
                f"{row.get('std_err', 0):.4f}",
                f"{row.get('z', 0):.2f}",
                f"{row.get('p', 0):.4f}",
            ]
        )
    # Add model‑level statistics
    footer = [
        ["Observations", regression.get("n", "NA")],
        ["AIC", regression.get("aic", "NA")],
        ["BIC", regression.get("bic", "NA")],
    ]
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>2. Logistic Regression Summary</b>", styles["Heading2"])
    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    footer_table = Table(footer, hAlign="LEFT")
    footer_table.setStyle(
        TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)])
    )
    return [
        heading,
        Spacer(1, 12),
        table,
        Spacer(1, 12),
        footer_table,
        Spacer(1, 24),
    ]

def generate_vif_section(vif: dict) -> list:
    """Render VIF diagnostics."""
    data = [["Predictor", "VIF"]]
    for var, val in vif.items():
        data.append([var, f"{val:.2f}"])
    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>3. Variance Inflation Factors (VIF)</b>", styles["Heading2"])
    return [heading, Spacer(1, 12), table, Spacer(1, 24)]

def generate_roc_section(roc: dict) -> list:
    """Create ROC plot image and embed it."""
    fpr = roc.get("fpr")
    tpr = roc.get("tpr")
    auc = roc.get("auc")
    if fpr is None or tpr is None:
        raise ValueError("ROC data must contain 'fpr' and 'tpr' lists.")

    # Plot ROC curve
    plt.figure(figsize=(4, 4))
    plt.plot(fpr, tpr, label=f"AUC = {auc:.3f}", color="navy")
    plt.plot([0, 1], [0, 1], linestyle="--", color="grey")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    img_path = Path("results/roc_curve.png")
    img_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(img_path, format="png")
    plt.close()

    styles = getSampleStyleSheet()
    heading = Paragraph("<b>4. ROC Curve & AUC</b>", styles["Heading2"])
    img = Image(str(img_path), width=400, height=400)
    caption = Paragraph(f"AUC = {auc:.3f}", styles["Normal"])
    return [heading, Spacer(1, 12), img, Spacer(1, 6), caption, Spacer(1, 24)]

def generate_mediation_section(mediation: dict) -> list:
    """Present mediation analysis results."""
    rows = [
        ["Effect", "Estimate"],
        ["Indirect Effect", f"{mediation.get('indirect_effect', 'NA'):.4f}"],
        ["Direct Effect", f"{mediation.get('direct_effect', 'NA'):.4f}"],
        ["Total Effect", f"{mediation.get('total_effect', 'NA'):.4f}"],
    ]
    ci = mediation.get("indirect_ci", ["NA", "NA"])
    rows.append(
        [
            "95% CI (Indirect)",
            f"{ci[0]:.4f} – {ci[1]:.4f}" if isinstance(ci[0], (int, float)) else "NA",
        ]
    )
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>5. Mediation Analysis (Baron & Kenny)</b>", styles["Heading2"])
    return [heading, Spacer(1, 12), table, Spacer(1, 24)]

def generate_sensitivity_section(sensitivity: dict) -> list:
    """Show E‑value and Rosenbaum‑bound sensitivity analysis."""
    evalue = sensitivity.get("e_value", "NA")
    rosenbaum = sensitivity.get("rosenbaum_bounds", {})
    rows = [["Metric", "Value"]]
    rows.append(["E‑value", f"{evalue:.3f}" if isinstance(evalue, (int, float)) else "NA"])
    for gamma, bound in rosenbaum.items():
        rows.append([f"Rosenbaum γ={gamma}", f"{bound:.3f}" if isinstance(bound, (int, float)) else "NA"])
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>6. Sensitivity Analysis</b>", styles["Heading2"])
    return [heading, Spacer(1, 12), table, Spacer(1, 24)]

def generate_validity_section(validity: dict) -> list:
    """Report reliability and factor‑analysis metrics."""
    alpha = validity.get("cronbach_alpha", "NA")
    loadings = validity.get("factor_loadings", {})
    rows = [["Metric", "Value"]]
    rows.append(["Cronbach's α", f"{alpha:.3f}" if isinstance(alpha, (int, float)) else "NA"])
    # Flatten factor loadings for display
    for factor, items in loadings.items():
        for var, loading in items.items():
            rows.append([f"Loading: {var} on {factor}", f"{loading:.3f}"])
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>7. Validity & Reliability Metrics</b>", styles["Heading2"])
    return [heading, Spacer(1, 12), table, Spacer(1, 24)]

# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------
def generate_pdf_report() -> None:
    """Assemble all sections and write the final PDF."""
    from config import get_results_path

    # Load all artefacts – each helper raises a clear error if the file is missing.
    cleaned_df = _load_cleaned_data()
    engineered_df = _load_engineered_data()
    regression = _load_json(get_results_path() / "regression_summary.json")
    vif = _load_json(get_results_path() / "vif.json")
    roc = _load_json(get_results_path() / "roc.json")
    mediation = _load_json(get_results_path() / "mediation.json")
    sensitivity = _load_json(get_results_path() / "sensitivity.json")
    validity = _load_yaml(get_results_path() / "validity_metrics.yaml")

    # Build the document flow.
    flowables: list = []
    flowables.extend(generate_report_header())
    flowables.extend(generate_descriptive_stats(cleaned_df))
    flowables.extend(generate_regression_table(regression))
    flowables.extend(generate_vif_section(vif))
    flowables.extend(generate_roc_section(roc))
    flowables.extend(generate_mediation_section(mediation))
    flowables.extend(generate_sensitivity_section(sensitivity))
    flowables.extend(generate_validity_section(validity))

    # Output PDF
    output_path = get_results_path() / "report.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    doc.build(flowables)

    print(f"PDF report generated at: {output_path}")

# ---------------------------------------------------------------------------
# Command‑line entry point
# ---------------------------------------------------------------------------
def main() -> None:  # pragma: no cover
    """Run the report generation when the module is executed as a script."""
    try:
        generate_pdf_report()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"Error generating report: {exc}\\n")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
