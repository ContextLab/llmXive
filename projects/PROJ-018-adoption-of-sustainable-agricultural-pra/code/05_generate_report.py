"""
Report Generation Module for PROJ-018

Generates a comprehensive PDF report containing:
- Descriptive statistics
- Regression table
- VIF diagnostics
- ROC plot
- Mediation results
- Sensitivity analysis
- Validity metrics
"""
from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests

# Report generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Local imports (matching API surface)
from config import get_config
from logging_config import log_operation, get_logger

logger = get_logger("report_generation")

# --------------------------------------------------------------------------
# Data Loading Helpers
# --------------------------------------------------------------------------

def load_cleaned_data(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Load cleaned data from the processed directory."""
    path = Path(config["paths"]["processed_data"]) / "cleaned_data.csv"
    if not path.exists():
        logger.log("error", f"Cleaned data not found at {path}")
        return None
    return pd.read_csv(path)

def load_engineered_data(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Load engineered data from the processed directory."""
    path = Path(config["paths"]["processed_data"]) / "engineered_data.csv"
    if not path.exists():
        logger.log("error", f"Engineered data not found at {path}")
        return None
    return pd.read_csv(path)

def load_model_results(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load model results from the results directory."""
    path = Path(config["paths"]["results"]) / "model_results.yaml"
    if not path.exists():
        logger.log("error", f"Model results not found at {path}")
        return None
    import yaml
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_validity_metrics(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load validity metrics from the results directory."""
    path = Path(config["paths"]["results"]) / "validity_metrics.yaml"
    if not path.exists():
        logger.log("error", f"Validity metrics not found at {path}")
        return None
    import yaml
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_modeling_log(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load the modeling log."""
    path = Path(config["paths"]["logs"]) / "modeling_log.yaml"
    if not path.exists():
        logger.log("error", f"Modeling log not found at {path}")
        return None
    import yaml
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# --------------------------------------------------------------------------
# Report Content Generators
# --------------------------------------------------------------------------

def generate_report_header(styles: Dict[str, Any]) -> List[Any]:
    """Generate the report header."""
    story = styles['Normal']
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=story,
        fontSize=24,
        textColor='#003366',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=story,
        fontSize=14,
        textColor='#666666',
        spaceAfter=20,
        alignment=TA_CENTER
    )

    elements = []
    elements.append(Paragraph("Adoption of Sustainable Agricultural Practices", title_style))
    elements.append(Paragraph("Analysis of Community Engagement in Low-Income Areas", subtitle_style))
    elements.append(Spacer(1, 20))
    return elements

def generate_descriptive_stats(df: pd.DataFrame, styles: Dict[str, Any]) -> List[Any]:
    """Generate descriptive statistics section."""
    elements = []
    story = styles['Normal']

    elements.append(Paragraph("1. Descriptive Statistics", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if df is None:
        elements.append(Paragraph("No data available for descriptive statistics.", story))
        return elements

    # Basic stats
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    desc_table_data = [["Variable", "Mean", "Std Dev", "Min", "Max"]]

    for col in numeric_cols:
        if col in ['adoption_binary']:
            continue  # Skip binary for mean description
        row = [
            col,
            f"{df[col].mean():.2f}",
            f"{df[col].std():.2f}",
            f"{df[col].min():.2f}",
            f"{df[col].max():.2f}"
        ]
        desc_table_data.append(row)

    table = Table(desc_table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#eeeeee'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('GRID', (0, 0), (-1, -1), 1, '#dddddd'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    return elements

def generate_regression_table(results: Dict[str, Any], styles: Dict[str, Any]) -> List[Any]:
    """Generate regression results table."""
    elements = []
    story = styles['Normal']

    elements.append(Paragraph("2. Logistic Regression Results", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if not results or 'regression' not in results:
        elements.append(Paragraph("No regression results available.", story))
        return elements

    reg_data = results['regression']
    coef_data = reg_data.get('coefficients', [])

    if not coef_data:
        elements.append(Paragraph("No coefficients found.", story))
        return elements

    table_data = [["Variable", "Coefficient", "Std Error", "Z-Value", "P-Value", "Sig"]]
    for row in coef_data:
        var_name = row.get('variable', 'Unknown')
        coef = row.get('coef', 0)
        std_err = row.get('std_err', 0)
        z_val = row.get('z', 0)
        p_val = row.get('pvalue', 1)
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""

        table_data.append([
            str(var_name),
            f"{coef:.4f}",
            f"{std_err:.4f}",
            f"{z_val:.4f}",
            f"{p_val:.4f}",
            sig
        ])

    table = Table(table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#eeeeee'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, '#dddddd'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("* p<0.05, ** p<0.01, *** p<0.001", story))
    elements.append(Spacer(1, 20))
    return elements

def generate_vif_section(results: Dict[str, Any], styles: Dict[str, Any]) -> List[Any]:
    """Generate VIF diagnostics section."""
    elements = []
    story = styles['Normal']

    elements.append(Paragraph("3. Multicollinearity Diagnostics (VIF)", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if not results or 'vif' not in results:
        elements.append(Paragraph("VIF diagnostics not available.", story))
        return elements

    vif_data = results['vif']
    table_data = [["Variable", "VIF", "Status"]]
    for row in vif_data:
        var_name = row.get('variable', 'Unknown')
        vif_val = row.get('vif', 0)
        status = "OK" if vif_val < 5 else "WARNING" if vif_val < 10 else "CRITICAL"
        table_data.append([str(var_name), f"{vif_val:.2f}", status])

    table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#eeeeee'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, '#dddddd'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    return elements

def generate_roc_section(results: Dict[str, Any], config: Dict[str, Any], styles: Dict[str, Any]) -> List[Any]:
    """Generate ROC curve section with embedded image."""
    elements = []
    story = styles['Normal']
    results_dir = Path(config["paths"]["results"])

    elements.append(Paragraph("4. Model Performance (ROC Curve)", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if not results or 'roc' not in results:
        elements.append(Paragraph("ROC metrics not available.", story))
        return elements

    auc_val = results['roc'].get('auc', 0)
    elements.append(Paragraph(f"AUC: {auc_val:.4f}", story))
    elements.append(Spacer(1, 10))

    # Check if ROC plot exists
    roc_path = results_dir / "roc_curve.png"
    if roc_path.exists():
        try:
            elements.append(ReportLabImage(str(roc_path), width=4*inch, height=3*inch))
        except Exception as e:
            elements.append(Paragraph(f"Could not load ROC image: {e}", story))
    else:
        elements.append(Paragraph("ROC curve image not found.", story))

    elements.append(Spacer(1, 20))
    return elements

def generate_mediation_section(results: Dict[str, Any], styles: Dict[str, Any]) -> List[Any]:
    """Generate mediation analysis section."""
    elements = []
    story = styles['Normal']

    elements.append(Paragraph("5. Mediation Analysis", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if not results or 'mediation' not in results:
        elements.append(Paragraph("Mediation analysis not available.", story))
        return elements

    med_data = results['mediation']
    elements.append(Paragraph("Indirect Effects (Bootstrap 1000 resamples):", story))
    elements.append(Spacer(1, 5))

    table_data = [["Path", "Effect", "SE", "95% CI Lower", "95% CI Upper"]]
    if 'indirect_effects' in med_data:
        for eff in med_data['indirect_effects']:
            table_data.append([
                eff.get('path', 'N/A'),
                f"{eff.get('effect', 0):.4f}",
                f"{eff.get('se', 0):.4f}",
                f"{eff.get('ci_lower', 0):.4f}",
                f"{eff.get('ci_upper', 0):.4f}"
            ])

    if len(table_data) > 1:
        table = Table(table_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#eeeeee'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, '#dddddd'),
        ]))
        elements.append(table)

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Note: Mediation analysis is exploratory.", story))
    elements.append(Spacer(1, 20))
    return elements

def generate_sensitivity_section(results: Dict[str, Any], styles: Dict[str, Any]) -> List[Any]:
    """Generate sensitivity analysis section (E-values)."""
    elements = []
    story = styles['Normal']

    elements.append(Paragraph("6. Sensitivity Analysis", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if not results or 'sensitivity' not in results:
        elements.append(Paragraph("Sensitivity analysis not available.", story))
        return elements

    sens_data = results['sensitivity']

    elements.append(Paragraph("E-Values:", story))
    if 'evalues' in sens_data:
        for ev in sens_data['evalues']:
            elements.append(Paragraph(
                f"- {ev.get('variable', 'Unknown')}: E-value = {ev.get('evalue', 0):.2f} "
                f"(95% CI: {ev.get('ci_lower', 0):.2f} - {ev.get('ci_upper', 0):.2f})",
                story
            ))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Rosenbaum Bounds (Gamma sensitivity):", story))
    if 'rosenbaum' in sens_data:
        for rb in sens_data['rosenbaum']:
            elements.append(Paragraph(
                f"- Gamma = {rb.get('gamma', 0):.1f}: Significant = {rb.get('significant', False)}",
                story
            ))

    elements.append(Spacer(1, 20))
    return elements

def generate_validity_section(validity_metrics: Dict[str, Any], styles: Dict[str, Any]) -> List[Any]:
    """Generate validity metrics section."""
    elements = []
    story = styles['Normal']

    elements.append(Paragraph("7. Reliability and Validity Metrics", styles['Heading2']))
    elements.append(Spacer(1, 12))

    if not validity_metrics:
        elements.append(Paragraph("Validity metrics not available.", story))
        return elements

    # Cronbach's Alpha
    if 'cronbach_alpha' in validity_metrics:
        alpha_val = validity_metrics['cronbach_alpha']
        elements.append(Paragraph(f"Cronbach's Alpha: {alpha_val:.3f}", story))
        if alpha_val >= 0.7:
            elements.append(Paragraph("Interpretation: Acceptable internal consistency.", story))
        else:
            elements.append(Paragraph("Interpretation: Low internal consistency.", story))

    elements.append(Spacer(1, 10))

    # EFA
    if 'efa' in validity_metrics:
        elements.append(Paragraph("Exploratory Factor Analysis (Varimax Rotation):", story))
        if 'factors' in validity_metrics['efa']:
            for i, factor in enumerate(validity_metrics['efa']['factors']):
                elements.append(Paragraph(f"Factor {i+1} (Eigenvalue: {factor.get('eigenvalue', 0):.2f}):", story))
                for var, loading in factor.get('loadings', {}).items():
                    elements.append(Paragraph(f"  - {var}: {loading:.3f}", story))

    elements.append(Spacer(1, 20))
    return elements

# --------------------------------------------------------------------------
# Main Report Generation
# --------------------------------------------------------------------------

def plot_roc_curve(results: Dict[str, Any], output_path: Path) -> bool:
    """Plot and save ROC curve to disk."""
    if not results or 'roc' not in results:
        return False

    fpr = results['roc'].get('fpr', [])
    tpr = results['roc'].get('tpr', [])
    auc_val = results['roc'].get('auc', 0)

    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc_val:.2f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return True

def generate_pdf_report(config: Dict[str, Any]) -> bool:
    """Generate the full PDF report."""
    logger.log("report_generation_start", {"status": "starting"})

    # Load data
    cleaned_df = load_cleaned_data(config)
    engineered_df = load_engineered_data(config)
    model_results = load_model_results(config)
    validity_metrics = load_validity_metrics(config)
    modeling_log = load_modeling_log(config)

    # Prepare styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Heading2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#003366',
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    ))

    # Build elements
    elements = []
    elements.extend(generate_report_header(styles))
    elements.extend(generate_descriptive_stats(cleaned_df, styles))
    elements.extend(generate_regression_table(model_results, styles))
    elements.extend(generate_vif_section(model_results, styles))
    elements.extend(generate_roc_section(model_results, config, styles))
    elements.extend(generate_mediation_section(model_results, styles))
    elements.extend(generate_sensitivity_section(model_results, styles))
    elements.extend(generate_validity_section(validity_metrics, styles))

    # Finalize
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles['Normal']
    ))

    # Write PDF
    output_path = Path(config["paths"]["results"]) / "final_report.pdf"
    try:
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        doc.build(elements)
        logger.log("report_generation_complete", {"output_file": str(output_path)})
        return True
    except Exception as e:
        logger.log("report_generation_failed", {"error": str(e)})
        return False

@log_operation("generate_report_main")
def main():
    """Main entry point for report generation."""
    config = get_config()
    success = generate_pdf_report(config)
    if success:
        print("Report generated successfully.")
    else:
        print("Report generation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()