"""Generate the final PDF report for the sustainable agriculture study.

This script aggregates results from previous stages (descriptives, regression,
VIF, ROC, mediation, sensitivity, validity) and produces a comprehensive PDF report.

It consumes:
- data/processed/cleaned_data.csv
- data/processed/engineered_data.csv
- results/model_results.yaml
- results/validity_metrics.yaml
- modeling_log.yaml
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Try to import matplotlib and reportlab
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("WARNING: matplotlib not installed. ROC plot will be skipped.")

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    )
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("WARNING: reportlab not installed. PDF generation will fail.")

# Import configuration
from config import get_config

# Paths
PROJECT_ROOT = Path(get_config("project_root", "."))
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELING_LOG_PATH = PROJECT_ROOT / "modeling_log.yaml"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_cleaned_data() -> pd.DataFrame:
    """Load cleaned data."""
    path = PROCESSED_DIR / "cleaned_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {path}")
    return pd.read_csv(path)

def load_engineered_data() -> pd.DataFrame:
    """Load engineered data."""
    path = PROCESSED_DIR / "engineered_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"Engineered data not found at {path}")
    return pd.read_csv(path)

def load_model_results() -> Dict[str, Any]:
    """Load model results from YAML."""
    path = RESULTS_DIR / "model_results.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Model results not found at {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_validity_metrics() -> Dict[str, Any]:
    """Load validity metrics from YAML."""
    path = RESULTS_DIR / "validity_metrics.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Validity metrics not found at {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_modeling_log() -> Dict[str, Any]:
    """Load modeling log."""
    if not MODELING_LOG_PATH.exists():
        return {}
    with open(MODELING_LOG_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def generate_report_header() -> List[Paragraph]:
    """Generate the report header."""
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = styles['Normal']

    title = Paragraph("Adoption of Sustainable Agricultural Practices in Low‑Income Areas", title_style)
    subtitle = Paragraph(
        "Impact of Community Engagement: A Statistical Analysis",
        styles['Heading2']
    )
    date = Paragraph(
        f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        subtitle_style
    )

    return [title, Spacer(0, 0.2*inch), subtitle, Spacer(0, 0.2*inch), date]

def generate_descriptive_stats(df: pd.DataFrame) -> List[Any]:
    """Generate descriptive statistics section."""
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Descriptive Statistics", styles['Heading2']))
    content.append(Spacer(0, 0.2*inch))

    # Basic stats
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) > 0:
        stats = df[numeric_cols].describe()
        # Convert to list of lists for Table
        data = [["Variable", "Mean", "Std", "Min", "Max"]]
        for col in numeric_cols:
            row = [
                col,
                f"{stats.loc['mean', col]:.2f}",
                f"{stats.loc['std', col]:.2f}",
                f"{stats.loc['min', col]:.2f}",
                f"{stats.loc['max', col]:.2f}"
            ]
            data.append(row)

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(table)

    # Categorical counts
    content.append(Spacer(0, 0.3*inch))
    content.append(Paragraph("Categorical Variables", styles['Heading3']))
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in cat_cols:
        content.append(Paragraph(f"<b>{col}</b>", styles['Normal']))
        counts = df[col].value_counts()
        data = [["Category", "Count", "Percent"]]
        for val, count in counts.items():
            pct = (count / len(df)) * 100
            data.append([str(val), str(count), f"{pct:.1f}%"])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(table)
        content.append(Spacer(0, 0.2*inch))

    return content

def generate_regression_table(results: Dict[str, Any]) -> List[Any]:
    """Generate regression results table."""
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Logistic Regression Results", styles['Heading2']))
    content.append(Spacer(0, 0.2*inch))

    reg_data = results.get("regression", {})
    coeffs = reg_data.get("coefficients", [])

    if not coeffs:
        content.append(Paragraph("No regression results available.", styles['Normal']))
        return content

    data = [["Variable", "Coefficient", "Std Err", "z-value", "P>|z|", "Adj P (FDR)"]]
    for row in coeffs:
        var_name = row.get('variable', 'Unknown')
        coef = row.get('coef', 0)
        std_err = row.get('std_err', 0)
        z_val = row.get('z', 0)
        p_val = row.get('pval', 0)
        adj_p = row.get('adj_pval', p_val)

        # Significance stars
        stars = ""
        if adj_p < 0.001:
            stars = "***"
        elif adj_p < 0.01:
            stars = "**"
        elif adj_p < 0.05:
            stars = "*"

        data.append([
            var_name,
            f"{coef:.3f}{stars}",
            f"{std_err:.3f}",
            f"{z_val:.3f}",
            f"{p_val:.4f}",
            f"{adj_p:.4f}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)

    # Model fit stats
    content.append(Spacer(0, 0.3*inch))
    content.append(Paragraph("Model Fit Statistics", styles['Heading3']))
    fit_stats = reg_data.get("fit_statistics", {})
    data = [["Statistic", "Value"]]
    for key, val in fit_stats.items():
        data.append([key, str(val)])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)

    return content

def generate_vif_section(results: Dict[str, Any]) -> List[Any]:
    """Generate VIF diagnostics section."""
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Variance Inflation Factor (VIF) Diagnostics", styles['Heading2']))
    content.append(Spacer(0, 0.2*inch))

    vif_data = results.get("vif", [])
    if not vif_data:
        content.append(Paragraph("No VIF data available.", styles['Normal']))
        return content

    data = [["Variable", "VIF", "Status"]]
    for row in vif_data:
        var = row.get('variable', 'Unknown')
        vif_val = row.get('vif', 0)
        status = "OK" if vif_val < 5 else "WARNING (≥5)"
        data.append([var, f"{vif_val:.2f}", status])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)
    return content

def generate_roc_section(results: Dict[str, Any]) -> List[Any]:
    """Generate ROC curve section."""
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Model Performance (ROC Curve)", styles['Heading2']))
    content.append(Spacer(0, 0.2*inch))

    # ROC metrics
    roc_data = results.get("roc", {})
    auc = roc_data.get("auc", 0)
    content.append(Paragraph(f"Area Under Curve (AUC): {auc:.3f}", styles['Normal']))
    content.append(Spacer(0, 0.2*inch))

    # Plot ROC if possible
    if HAS_MATPLOTLIB and roc_data.get("fpr") and roc_data.get("tpr"):
        fpr = roc_data["fpr"]
        tpr = roc_data["tpr"]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(fpr, tpr, label=f'ROC curve (AUC = {auc:.3f})', color='darkorange')
        ax.plot([0, 1], [0, 1], 'k--', label='Random')
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('Receiver Operating Characteristic')
        ax.legend(loc="lower right")
        ax.grid(True)

        # Save to temp file
        temp_path = RESULTS_DIR / "roc_curve.png"
        fig.savefig(temp_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        content.append(Image(str(temp_path), width=5*inch, height=3.5*inch))
    else:
        content.append(Paragraph("ROC plot could not be generated (matplotlib or data missing).", styles['Normal']))

    return content

def generate_mediation_section(results: Dict[str, Any]) -> List[Any]:
    """Generate mediation analysis section."""
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Mediation Analysis", styles['Heading2']))
    content.append(Spacer(0, 0.2*inch))

    mediation = results.get("mediation", {})
    if not mediation:
        content.append(Paragraph("No mediation analysis results available.", styles['Normal']))
        return content

    # Direct effect
    direct = mediation.get("direct_effect", {})
    content.append(Paragraph("<b>Direct Effect (Engagement -> Adoption)</b>", styles['Normal']))
    data = [["Estimate", "SE", "95% CI Lower", "95% CI Upper"]]
    data.append([
        f"{direct.get('estimate', 0):.3f}",
        f"{direct.get('se', 0):.3f}",
        f"{direct.get('ci_lower', 0):.3f}",
        f"{direct.get('ci_upper', 0):.3f}"
    ])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)
    content.append(Spacer(0, 0.2*inch))

    # Indirect effect
    indirect = mediation.get("indirect_effect", {})
    content.append(Paragraph("<b>Indirect Effect (via mediator)</b>", styles['Normal']))
    data = [["Estimate", "SE", "95% CI Lower", "95% CI Upper"]]
    data.append([
        f"{indirect.get('estimate', 0):.3f}",
        f"{indirect.get('se', 0):.3f}",
        f"{indirect.get('ci_lower', 0):.3f}",
        f"{indirect.get('ci_upper', 0):.3f}"
    ])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)

    content.append(Spacer(0, 0.3*inch))
    content.append(Paragraph(
        "<i>Note: Mediation analysis is exploratory. Interpret with caution.</i>",
        styles['Italic']
    ))

    return content

def generate_sensitivity_section(results: Dict[str, Any]) -> List[Any]:
    """Generate sensitivity analysis section."""
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Sensitivity Analysis", styles['Heading2']))
    content.append(Spacer(0, 0.2*inch))

    sensitivity = results.get("sensitivity", {})
    if not sensitivity:
        content.append(Paragraph("No sensitivity analysis results available.", styles['Normal']))
        return content

    # E-value
    e_val = sensitivity.get("e_value", {})
    content.append(Paragraph("<b>E-value for Unmeasured Confounding</b>", styles['Normal']))
    data = [["Metric", "Value"]]
    data.append(["E-value", f"{e_val.get('e_value', 0):.3f}"])
    data.append(["Lower Bound 95% CI", f"{e_val.get('lower_ci', 0):.3f}"])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)
    content.append(Spacer(0, 0.2*inch))

    # Rosenbaum bounds
    rosenbaum = sensitivity.get("rosenbaum_bounds", {})
    content.append(Paragraph("<b>Rosenbaum Bounds (Gamma Sensitivity)</b>", styles['Normal']))
    data = [["Gamma", "p-value"]]
    for row in rosenbaum.get("bounds", []):
        data.append([f"{row.get('gamma', 0):.1f}", f"{row.get('p_val', 0):.4f}"])

    if data:
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(table)

    return content

def generate_validity_section(validity: Dict[str, Any]) -> List[Any]:
    """Generate validity metrics section."""
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph("Validity and Reliability Metrics", styles['Heading2']))
    content.append(Spacer(0, 0.2*inch))

    # Cronbach's Alpha
    alpha = validity.get("cronbach_alpha", 0)
    content.append(Paragraph(f"<b>Cronbach's Alpha:</b> {alpha:.3f}", styles['Normal']))
    content.append(Spacer(0, 0.1*inch))

    # EFA results
    efa = validity.get("efa", {})
    if efa:
        content.append(Paragraph("<b>Exploratory Factor Analysis (EFA)</b>", styles['Heading3']))
        content.append(Paragraph(f"Extraction Method: {efa.get('extraction', 'N/A')}", styles['Normal']))
        content.append(Paragraph(f"Rotation Method: {efa.get('rotation', 'N/A')}", styles['Normal']))
        content.append(Paragraph(f"Factors Retained: {efa.get('factors_retained', 0)}", styles['Normal']))
        content.append(Spacer(0, 0.2*inch))

        # Loadings table
        loadings = efa.get("loadings", [])
        if loadings:
            # Group by variable
            var_loadings = {}
            for row in loadings:
                var = row.get('variable', 'Unknown')
                factor = row.get('factor', 'Unknown')
                loading = row.get('loading', 0)
                if var not in var_loadings:
                    var_loadings[var] = {}
                var_loadings[var][factor] = loading

            data = [["Variable"] + [f"Factor {i+1}" for i in range(efa.get('factors_retained', 0))]]
            for var, factors in var_loadings.items():
                row = [var]
                for i in range(efa.get('factors_retained', 0)):
                    f_key = str(i+1)
                    val = factors.get(f_key, 0)
                    row.append(f"{val:.3f}")
                data.append(row)

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            content.append(table)

    # Convergent validity
    conv = validity.get("convergent_validity", {})
    if conv:
        content.append(Spacer(0, 0.3*inch))
        content.append(Paragraph("<b>Convergent Validity</b>", styles['Heading3']))
        content.append(Paragraph(f"Status: {conv.get('status', 'N/A')}", styles['Normal']))
        content.append(Paragraph(f"Correlation: {conv.get('correlation', 0):.3f}", styles['Normal']))

    return content

def generate_pdf_report(doc: SimpleDocTemplate, story: List[Any]) -> str:
    """Build and save the PDF report."""
    doc.build(story)
    return str(doc.filename)

def main():
    """Main entry point for report generation."""
    print("Starting report generation...")

    if not HAS_REPORTLAB:
        print("ERROR: reportlab is required for PDF generation.")
        sys.exit(1)

    # Load all data
    try:
        cleaned_df = load_cleaned_data()
        engineered_df = load_engineered_data()
        model_results = load_model_results()
        validity_metrics = load_validity_metrics()
        modeling_log = load_modeling_log()
    except FileNotFoundError as e:
        print(f"ERROR: Missing required data file: {e}")
        sys.exit(1)

    # Build report story
    story = []

    # Header
    story.extend(generate_report_header())
    story.append(PageBreak())

    # Descriptives
    story.extend(generate_descriptive_stats(cleaned_df))
    story.append(PageBreak())

    # Regression
    story.extend(generate_regression_table(model_results))
    story.append(PageBreak())

    # VIF
    story.extend(generate_vif_section(model_results))
    story.append(PageBreak())

    # ROC
    story.extend(generate_roc_section(model_results))
    story.append(PageBreak())

    # Mediation
    story.extend(generate_mediation_section(model_results))
    story.append(PageBreak())

    # Sensitivity
    story.extend(generate_sensitivity_section(model_results))
    story.append(PageBreak())

    # Validity
    story.extend(generate_validity_section(validity_metrics))

    # Save PDF
    output_path = RESULTS_DIR / "final_report.pdf"
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    generate_pdf_report(doc, story)

    print(f"Report successfully generated: {output_path}")
    return output_path

if __name__ == "__main__":
    main()