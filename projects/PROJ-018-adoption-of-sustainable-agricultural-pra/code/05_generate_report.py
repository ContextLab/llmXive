"""Generate a PDF research report for the sustainable‑agriculture project.

The script pulls together:
* Descriptive statistics from the cleaned survey data.
* The regression summary (logistic model) produced by ``04_model_analysis.py``.
* VIF diagnostics.
* ROC curve image and AUC value.
* Mediation analysis results.
* Sensitivity analysis (E‑values, Rosenbaum bounds).
* Validity metrics (Cronbach’s α, factor loadings, convergent‑validity).

All artefacts are written to the ``results/`` directory; the PDF is saved as
``results/report.pdf``.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from logging_config import log_operation, update_log_section

# ``reportlab`` is a pure‑Python PDF generator; it is listed in
# ``code/requirements.txt`` by this task.
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

# ----------------------------------------------------------------------
# Helper loading functions – each raises a clear error if the expected
# file is missing, allowing the caller (or CI) to see the exact problem.
# ----------------------------------------------------------------------
@log_operation("load_cleaned_data")
def load_cleaned_data() -> Path:
    """Return the path to the cleaned survey data CSV."""
    path = Path("data/processed/cleaned_data.csv")
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned data not found at {path}")
    return path


@log_operation("load_engineered_data")
def load_engineered_data() -> Path:
    """Return the path to the engineered dataset CSV."""
    path = Path("data/processed/engineered_data.csv")
    if not path.is_file():
        raise FileNotFoundError(f"Engineered data not found at {path}")
    return path


@log_operation("load_model_results")
def load_model_results() -> Dict[str, Any]:
    """Load the regression summary JSON produced by the modelling step."""
    path = Path("results/regression_summary.json")
    if not path.is_file():
        raise FileNotFoundError(f"Regression summary not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@log_operation("load_vif")
def load_vif() -> Dict[str, Any]:
    """Load VIF diagnostics (saved as JSON)."""
    path = Path("results/vif.json")
    if not path.is_file():
        raise FileNotFoundError(f"VIF results not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@log_operation("load_roc")
def load_roc() -> Dict[str, Any]:
    """Load ROC metrics and return the path to the ROC plot image."""
    metrics_path = Path("results/roc_metrics.json")
    image_path = Path("figures/roc_curve.png")
    if not metrics_path.is_file() or not image_path.is_file():
        raise FileNotFoundError("ROC metrics or plot image missing.")
    with metrics_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)
    metrics["image_path"] = str(image_path)
    return metrics


@log_operation("load_mediation_results")
def load_mediation_results() -> Dict[str, Any]:
    """Load mediation analysis outcomes."""
    path = Path("results/mediation_results.json")
    if not path.is_file():
        raise FileNotFoundError(f"Mediation results not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@log_operation("load_validity_metrics")
def load_validity_metrics() -> Dict[str, Any]:
    """Load the validity metrics YAML produced by the feature‑engineering step."""
    path = Path("results/validity_metrics.yaml")
    if not path.is_file():
        raise FileNotFoundError(f"Validity metrics not found at {path}")
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise ImportError("PyYAML is required to read validity metrics.") from e
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@log_operation("generate_report_header")
def generate_report_header() -> List[Paragraph]:
    """Create a title page for the PDF."""
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Adoption of Sustainable Agricultural Practices</b>", styles["Title"])
    subtitle = Paragraph(
        "Community‑Engagement Impact Study – Final Report", styles["Heading2"]
    )
    authors = Paragraph(
        "Research Team – Project 018", styles["Normal"]
    )
    return [title, Spacer(1, 12), subtitle, Spacer(1, 24), authors, Spacer(1, 48)]


# ----------------------------------------------------------------------
# Section generators – each returns a list of Flowable objects that can be
# appended to the report document.
# ----------------------------------------------------------------------
@log_operation("generate_descriptive_stats")
def generate_descriptive_stats(cleaned_path: Path) -> List[Any]:
    """Compute and format simple descriptive statistics."""
    import pandas as pd

    df = pd.read_csv(cleaned_path)
    desc = df.describe(include="all").reset_index()

    data = [desc.columns.tolist()] + desc.values.tolist()
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    styles = getSampleStyleSheet()
    header = Paragraph("<b>Descriptive Statistics</b>", styles["Heading2"])
    return [header, Spacer(1, 12), table, Spacer(1, 24)]


@log_operation("generate_regression_table")
def generate_regression_table(model_summary: Dict[str, Any]) -> List[Any]:
    """Render the logistic regression summary as a table."""
    styles = getSampleStyleSheet()
    header = Paragraph("<b>Logistic Regression Results</b>", styles["Heading2"])

    # Expected structure: {'params': [{...}, ...]}
    params = model_summary.get("params", [])
    if not params:
        raise ValueError("Regression summary missing 'params' key.")

    # Table header
    table_data = [["Variable", "Coef.", "Std.Err.", "z", "P>|z|", "[0.025", "0.975]"]]
    for p in params:
        row = [
            p.get("name", ""),
            f"{p.get('coef', ''):.4f}",
            f"{p.get('std_err', ''):.4f}",
            f"{p.get('z', ''):.3f}",
            f"{p.get('p_value', ''):.3f}",
            f"{p.get('conf_low', ''):.3f}",
            f"{p.get('conf_high', ''):.3f}",
        ]
        table_data.append(row)

    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    return [header, Spacer(1, 12), table, Spacer(1, 24)]


@log_operation("generate_vif_section")
def generate_vif_section(vif_data: Dict[str, Any]) -> List[Any]:
    """Present VIF diagnostics."""
    styles = getSampleStyleSheet()
    header = Paragraph("<b>Variance Inflation Factor (VIF) Diagnostics</b>", styles["Heading2"])

    table_data = [["Predictor", "VIF"]]
    for var, vif in vif_data.items():
        table_data.append([var, f"{vif:.2f}"])

    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    return [header, Spacer(1, 12), table, Spacer(1, 24)]


@log_operation("generate_roc_section")
def generate_roc_section(roc_info: Dict[str, Any]) -> List[Any]:
    """Insert ROC curve image and report AUC."""
    styles = getSampleStyleSheet()
    header = Paragraph("<b>Receiver Operating Characteristic (ROC) Curve</b>", styles["Heading2"])
    auc = roc_info.get("auc")
    auc_par = Paragraph(f"AUC = <b>{auc:.3f}</b>", styles["Normal"])
    img_path = Path(roc_info["image_path"])
    if not img_path.is_file():
        raise FileNotFoundError(f"ROC image not found at {img_path}")
    img = Image(str(img_path), width=400, height=300)
    return [header, Spacer(1, 12), auc_par, Spacer(1, 12), img, Spacer(1, 24)]


@log_operation("generate_mediation_section")
def generate_mediation_section(mediation: Dict[str, Any]) -> List[Any]:
    """Summarise mediation analysis results."""
    styles = getSampleStyleSheet()
    header = Paragraph("<b>Mediation Analysis (Baron & Kenny)</b>", styles["Heading2"])

    # Expected keys: indirect_effect, ci_lower, ci_upper, p_value, e_value, rosenbaum_gamma
    rows = [
        ["Indirect Effect", f"{mediation.get('indirect_effect', 'NA'):.4f}"],
        ["95% CI Lower", f"{mediation.get('ci_lower', 'NA'):.4f}"],
        ["95% CI Upper", f"{mediation.get('ci_upper', 'NA'):.4f}"],
        ["p‑value", f"{mediation.get('p_value', 'NA'):.4f}"],
        ["E‑value", f"{mediation.get('e_value', 'NA'):.4f}"],
        ["Rosenbaum γ (sensitivity)", f"{mediation.get('rosenbaum_gamma', 'NA')}"],
    ]

    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ]
        )
    )
    return [header, Spacer(1, 12), table, Spacer(1, 24)]


@log_operation("generate_validity_section")
def generate_validity_section(validity: Dict[str, Any]) -> List[Any]:
    """Render Cronbach’s α, factor loadings and convergent‑validity correlations."""
    styles = getSampleStyleSheet()
    header = Paragraph("<b>Construct Validity Metrics</b>", styles["Heading2"])

    parts: List[Any] = [header, Spacer(1, 12)]

    # Cronbach's α
    alpha = validity.get("cronbach_alpha")
    if alpha is not None:
        parts.append(Paragraph(f"Cronbach’s α = <b>{alpha:.3f}</b>", styles["Normal"]))
        parts.append(Spacer(1, 12))

    # Factor loadings – expected as a dict of {factor: {item: loading}}
    loadings = validity.get("factor_loadings")
    if isinstance(loadings, dict):
        for factor, items in loadings.items():
            parts.append(Paragraph(f"<b>Factor: {factor}</b>", styles["Heading3"]))
            table_data = [["Item", "Loading"]]
            for item, val in items.items():
                table_data.append([item, f"{val:.3f}"])
            tbl = Table(table_data, hAlign="LEFT")
            tbl.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ]
                )
            )
            parts.extend([tbl, Spacer(1, 12)])

    # Convergent validity correlations
    conv = validity.get("convergent_validity")
    if isinstance(conv, dict):
        parts.append(Paragraph("<b>Convergent Validity Correlations</b>", styles["Heading3"]))
        table_data = [["Construct", "Correlation"]]
        for name, corr in conv.items():
            table_data.append([name, f"{corr:.3f}"])
        tbl = Table(table_data, hAlign="LEFT")
        tbl.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ]
            )
        )
        parts.extend([tbl, Spacer(1, 12)])

    return parts


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
@log_operation("generate_report")
def generate_report() -> Path:
    """Assemble all sections and write the final PDF."""
    # Resolve all required inputs – any missing file aborts early.
    cleaned_path = load_cleaned_data()
    engineered_path = load_engineered_data()
    model_summary = load_model_results()
    vif_data = load_vif()
    roc_info = load_roc()
    mediation = load_mediation_results()
    validity = load_validity_metrics()

    # Build the document.
    doc_path = Path("results/report.pdf")
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(doc_path), pagesize=A4, rightMargin=30,
                            leftMargin=30, topMargin=30, bottomMargin=30)

    flowables: List[Any] = []
    flowables.extend(generate_report_header())
    flowables.append(Spacer(1, 24))

    flowables.extend(generate_descriptive_stats(cleaned_path))
    flowables.extend(generate_regression_table(model_summary))
    flowables.extend(generate_vif_section(vif_data))
    flowables.extend(generate_roc_section(roc_info))
    flowables.extend(generate_mediation_section(mediation))
    flowables.extend(generate_validity_section(validity))

    doc.build(flowables)

    # Log the location of the generated report.
    update_log_section("report_generation", log_operation("report_written", path=str(doc_path)))
    return doc_path


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for ``python -m code/05_generate_report.py``."""
    try:
        report_path = generate_report()
        print(f"Report successfully created at: {report_path}")
    except Exception as exc:
        # Log the failure – the logger will swallow the error but we also
        # print it for immediate visibility.
        log_operation("report_generation_failed", error=str(exc))
        print(f"Failed to generate report: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
