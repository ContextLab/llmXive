"""
Report Generation Module for Sustainable Agriculture Adoption Study.

Produces a comprehensive PDF report containing:
- Descriptive statistics
- Regression table with coefficients and significance
- VIF diagnostics
- ROC curve and AUC metrics
- Mediation analysis results
- Sensitivity analysis (E-values, Rosenbaum bounds)
- Validity metrics (Cronbach's alpha, EFA results)
"""
from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import yaml
import pandas as pd
import numpy as np

# Import from sibling modules per API surface
from logging_config import log_operation, update_log_section
from config import load_config

# Try to import matplotlib for ROC plot
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for PDF generation
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logging.warning("matplotlib not available; ROC plot will be skipped")

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logging.error("reportlab not installed; PDF generation will fail")

@log_operation("load_cleaned_data")
def load_cleaned_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the cleaned dataset from disk."""
    path = config.get("processed_data_path", "data/processed/cleaned_data.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned data file not found at {path}")
    return pd.read_csv(path)

@log_operation("load_engineered_data")
def load_engineered_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the engineered dataset from disk."""
    path = config.get("processed_data_path", "data/processed/engineered_data.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Engineered data file not found at {path}")
    return pd.read_csv(path)

@log_operation("load_model_results")
def load_model_results(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load model analysis results from YAML."""
    path = config.get("results_path", "results/model_results.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model results file not found at {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

@log_operation("load_validity_metrics")
def load_validity_metrics(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load validity metrics from YAML."""
    path = config.get("validity_metrics_path", "results/validity_metrics.yaml")
    if not os.path.exists(path):
        logging.warning(f"Validity metrics file not found at {path}; section will be skipped")
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f)

@log_operation("load_modeling_log")
def load_modeling_log(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load the modeling log."""
    path = config.get("modeling_log_path", "modeling_log.yaml")
    if not os.path.exists(path):
        logging.warning(f"Modeling log not found at {path}; using empty log")
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f)

@log_operation("generate_report_header")
def generate_report_header(title: str, subtitle: str) -> List:
    """Generate the report header elements."""
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = styles['Heading2']
    
    elements = [
        Paragraph(title, title_style),
        Spacer(0, 0.2*inch),
        Paragraph(subtitle, subtitle_style),
        Spacer(0, 0.5*inch)
    ]
    return elements

@log_operation("generate_descriptive_stats")
def generate_descriptive_stats(df: pd.DataFrame, config: Dict[str, Any]) -> List:
    """Generate descriptive statistics section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    
    elements.append(Paragraph("1. Descriptive Statistics", heading_style))
    elements.append(Spacer(0, 0.1*inch))
    
    # Select key columns for summary
    key_cols = ['age', 'education', 'farm_size', 'adoption_binary']
    available_cols = [c for c in key_cols if c in df.columns]
    
    if available_cols:
        summary = df[available_cols].describe()
        # Convert to table format
        table_data = [['Variable', 'Mean', 'Std', 'Min', 'Max']]
        for idx in summary.index:
            row = [idx] + [f"{summary.loc[idx, col]:.2f}" for col in summary.columns]
            table_data.append(row)
        
        table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No descriptive statistics available.", styles['Normal']))
    
    elements.append(Spacer(0, 0.5*inch))
    return elements

@log_operation("generate_regression_table")
def generate_regression_table(reg_data: Dict[str, Any]) -> List:
    """Generate the regression results table."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    
    elements.append(Paragraph("2. Logistic Regression Results", heading_style))
    elements.append(Spacer(0, 0.1*inch))
    
    coef_data = reg_data.get('coefficients', [])
    if not coef_data:
        elements.append(Paragraph("No regression coefficients available.", styles['Normal']))
    else:
        table_data = [['Variable', 'Coef', 'Std Err', 'Z', 'P>|z|', 'Significant']]
        for row in coef_data:
            var_name = row.get('variable', 'Unknown')
            coef = row.get('coef', 0)
            std_err = row.get('std_err', 0)
            z_val = row.get('z', 0)
            p_val = row.get('pvalue', 1)
            sig = "Yes" if p_val < 0.05 else "No"
            table_data.append([
                var_name,
                f"{coef:.3f}",
                f"{std_err:.3f}",
                f"{z_val:.3f}",
                f"{p_val:.4f}",
                sig
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
    
    elements.append(Spacer(0, 0.5*inch))
    return elements

@log_operation("generate_vif_section")
def generate_vif_section(vif_data: List[Dict[str, Any]]) -> List:
    """Generate VIF diagnostics section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    
    elements.append(Paragraph("3. Multicollinearity Diagnostics (VIF)", heading_style))
    elements.append(Spacer(0, 0.1*inch))
    
    if not vif_data:
        elements.append(Paragraph("No VIF data available.", styles['Normal']))
    else:
        table_data = [['Variable', 'VIF', 'Warning']]
        for row in vif_data:
            var = row.get('variable', 'Unknown')
            vif = row.get('vif', 0)
            warning = "Yes (VIF >= 5)" if vif >= 5 else "No"
            table_data.append([var, f"{vif:.2f}", warning])
        
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
    
    elements.append(Spacer(0, 0.5*inch))
    return elements

@log_operation("generate_roc_section")
def generate_roc_section(roc_data: Dict[str, Any], output_path: Path) -> List:
    """Generate ROC curve section and save plot."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    
    elements.append(Paragraph("4. Model Performance (ROC Curve)", heading_style))
    elements.append(Spacer(0, 0.1*inch))
    
    auc = roc_data.get('auc', 0)
    elements.append(Paragraph(f"Area Under Curve (AUC): {auc:.4f}", styles['Normal']))
    elements.append(Spacer(0, 0.1*inch))
    
    # Generate ROC plot if matplotlib is available
    if HAS_MATPLOTLIB and roc_data.get('fpr') is not None and roc_data.get('tpr') is not None:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(roc_data['fpr'], roc_data['tpr'], label=f'ROC curve (AUC = {auc:.2f})')
        ax.plot([0, 1], [0, 1], 'k--', label='Random')
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC Curve for Adoption Prediction')
        ax.legend(loc='lower right')
        ax.grid(True)
        
        plot_path = output_path / "roc_curve.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        # Add image to report (ReportLab can handle PNG)
        from reportlab.platypus import Image
        elements.append(Image(str(plot_path), width=4*inch, height=3*inch))
    else:
        elements.append(Paragraph("ROC plot could not be generated (matplotlib unavailable or data missing).", styles['Normal']))
    
    elements.append(Spacer(0, 0.5*inch))
    return elements

@log_operation("generate_mediation_section")
def generate_mediation_section(mediation_data: Dict[str, Any]) -> List:
    """Generate mediation analysis results section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    
    elements.append(Paragraph("5. Mediation Analysis", heading_style))
    elements.append(Spacer(0, 0.1*inch))
    
    if not mediation_data:
        elements.append(Paragraph("No mediation analysis results available.", styles['Normal']))
    else:
        direct_effect = mediation_data.get('direct_effect', {})
        indirect_effect = mediation_data.get('indirect_effect', {})
        
        elements.append(Paragraph("Direct Effect:", styles['Heading4']))
        if direct_effect:
            coef = direct_effect.get('coef', 0)
            pval = direct_effect.get('pvalue', 0)
            ci_low = direct_effect.get('ci_low', 0)
            ci_high = direct_effect.get('ci_high', 0)
            elements.append(Paragraph(
                f"Coefficient: {coef:.3f}, p-value: {pval:.4f}, 95% CI: [{ci_low:.3f}, {ci_high:.3f}]",
                styles['Normal']
            ))
        
        elements.append(Spacer(0, 0.1*inch))
        elements.append(Paragraph("Indirect Effect (Mediation):", styles['Heading4']))
        if indirect_effect:
            coef = indirect_effect.get('coef', 0)
            ci_low = indirect_effect.get('ci_low', 0)
            ci_high = indirect_effect.get('ci_high', 0)
            elements.append(Paragraph(
                f"Coefficient: {coef:.3f}, 95% CI: [{ci_low:.3f}, {ci_high:.3f}]",
                styles['Normal']
            ))
            if ci_low > 0 or ci_high < 0:
                elements.append(Paragraph("Interpretation: Significant mediation effect detected.", styles['Normal']))
            else:
                elements.append(Paragraph("Interpretation: Mediation effect not statistically significant.", styles['Normal']))
        
        elements.append(Spacer(0, 0.1*inch))
        elements.append(Paragraph("Note: These results are exploratory and should be interpreted with caution.", styles['Italic']))
    
    elements.append(Spacer(0, 0.5*inch))
    return elements

@log_operation("generate_sensitivity_section")
def generate_sensitivity_section(sensitivity_data: Dict[str, Any]) -> List:
    """Generate sensitivity analysis section (E-values, Rosenbaum bounds)."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    
    elements.append(Paragraph("6. Sensitivity Analysis", heading_style))
    elements.append(Spacer(0, 0.1*inch))
    
    # E-values
    evalue_data = sensitivity_data.get('evalues', {})
    if evalue_data:
        elements.append(Paragraph("E-values:", styles['Heading4']))
        evalue = evalue_data.get('evalue', 0)
        ci_low = evalue_data.get('ci_low', 0)
        ci_high = evalue_data.get('ci_high', 0)
        elements.append(Paragraph(
            f"E-value: {evalue:.2f} [95% CI: {ci_low:.2f} - {ci_high:.2f}]",
            styles['Normal']
        ))
        elements.append(Paragraph(
            "Interpretation: An unmeasured confounder would need to increase the odds of both exposure and outcome by at least this factor to fully explain away the observed effect.",
            styles['Normal']
        ))
        elements.append(Spacer(0, 0.2*inch))
    
    # Rosenbaum bounds
    rosenbaum_data = sensitivity_data.get('rosenbaum_bounds', [])
    if rosenbaum_data:
        elements.append(Paragraph("Rosenbaum Bounds:", styles['Heading4']))
        table_data = [['Gamma', 'Significant at alpha=0.05?']]
        for row in rosenbaum_data:
            gamma = row.get('gamma', 0)
            significant = "Yes" if row.get('significant', False) else "No"
            table_data.append([f"{gamma:.1f}", significant])
        
        table = Table(table_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
    
    elements.append(Spacer(0, 0.5*inch))
    return elements

@log_operation("generate_validity_section")
def generate_validity_section(validity_metrics: Dict[str, Any]) -> List:
    """Generate validity metrics section (Cronbach's alpha, EFA)."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading3']
    
    elements.append(Paragraph("7. Reliability and Validity Metrics", heading_style))
    elements.append(Spacer(0, 0.1*inch))
    
    if not validity_metrics:
        elements.append(Paragraph("No validity metrics available.", styles['Normal']))
    else:
        # Cronbach's Alpha
        alpha = validity_metrics.get('cronbach_alpha')
        if alpha is not None:
            elements.append(Paragraph("Cronbach's Alpha:", styles['Heading4']))
            elements.append(Paragraph(
                f"Reliability coefficient: {alpha:.3f}",
                styles['Normal']
            ))
            if alpha >= 0.7:
                elements.append(Paragraph("Interpretation: Good internal consistency.", styles['Normal']))
            elif alpha >= 0.6:
                elements.append(Paragraph("Interpretation: Acceptable internal consistency.", styles['Normal']))
            else:
                elements.append(Paragraph("Interpretation: Questionable internal consistency.", styles['Normal']))
            elements.append(Spacer(0, 0.2*inch))
        
        # EFA Results
        efa = validity_metrics.get('efa', {})
        if efa:
            elements.append(Paragraph("Exploratory Factor Analysis (EFA):", styles['Heading4']))
            factors_retained = efa.get('factors_retained', 0)
            extraction = efa.get('extraction', 'Unknown')
            rotation = efa.get('rotation', 'Unknown')
            elements.append(Paragraph(
                f"Factors retained (Kaiser's rule): {factors_retained}",
                styles['Normal']
            ))
            elements.append(Paragraph(
                f"Extraction method: {extraction}",
                styles['Normal']
            ))
            elements.append(Paragraph(
                f"Rotation method: {rotation}",
                styles['Normal']
            ))
            
            # Factor loadings table if available
            loadings = efa.get('loadings', [])
            if loadings:
                elements.append(Spacer(0, 0.1*inch))
                elements.append(Paragraph("Key Factor Loadings:", styles['Heading5']))
                table_data = [['Variable', 'Factor 1', 'Factor 2']]
                for row in loadings[:5]:  # Show top 5
                    var = row.get('variable', 'Unknown')
                    f1 = row.get('factor1', 0)
                    f2 = row.get('factor2', 0)
                    table_data.append([var, f"{f1:.2f}", f"{f2:.2f}"])
                
                table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
    
    elements.append(Spacer(0, 0.5*inch))
    return elements

@log_operation("plot_roc_curve")
def plot_roc_curve(y_true: np.ndarray, y_prob: np.ndarray, output_path: Path) -> Dict[str, Any]:
    """Plot ROC curve and return metrics."""
    if not HAS_MATPLOTLIB:
        return {}
    
    from sklearn.metrics import roc_curve, auc
    
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('Receiver Operating Characteristic')
    ax.legend(loc="lower right")
    ax.grid(True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return {
        'auc': roc_auc,
        'fpr': fpr.tolist(),
        'tpr': tpr.tolist(),
        'thresholds': thresholds.tolist()
    }

@log_operation("generate_pdf_report")
def generate_pdf_report(elements: List, output_path: Path, title: str) -> None:
    """Generate the final PDF report."""
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is required to generate PDF reports")
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    doc.build(elements)

@log_operation("generate_report_main")
def main():
    """Main entry point for report generation."""
    # Load configuration
    config = load_config()
    
    # Ensure output directory exists
    output_dir = Path(config.get("results_path", "results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all required data
    try:
        cleaned_data = load_cleaned_data(config)
        engineered_data = load_engineered_data(config)
        model_results = load_model_results(config)
        validity_metrics = load_validity_metrics(config)
        modeling_log = load_modeling_log(config)
    except FileNotFoundError as e:
        update_log_section("report_generation", {"status": "failed", "error": str(e)})
        raise
    
    # Initialize report elements
    elements = []
    
    # 1. Header
    title = "Adoption of Sustainable Agricultural Practices"
    subtitle = "Analysis Report: Community Engagement and Low-Income Areas"
    elements.extend(generate_report_header(title, subtitle))
    
    # 2. Descriptive Statistics
    elements.extend(generate_descriptive_stats(cleaned_data, config))
    
    # 3. Regression Results
    reg_data = model_results.get('regression', {})
    elements.extend(generate_regression_table(reg_data))
    
    # 4. VIF Diagnostics
    vif_data = model_results.get('vif', [])
    elements.extend(generate_vif_section(vif_data))
    
    # 5. ROC Curve
    roc_data = model_results.get('roc', {})
    plot_path = output_dir / "roc_curve.png"
    elements.extend(generate_roc_section(roc_data, plot_path))
    
    # 6. Mediation Analysis
    mediation_data = model_results.get('mediation', {})
    elements.extend(generate_mediation_section(mediation_data))
    
    # 7. Sensitivity Analysis
    sensitivity_data = model_results.get('sensitivity', {})
    elements.extend(generate_sensitivity_section(sensitivity_data))
    
    # 8. Validity Metrics
    elements.extend(generate_validity_section(validity_metrics))
    
    # 9. Limitations from modeling log
    elements.append(Spacer(0, 0.5*inch))
    elements.append(Paragraph("8. Study Limitations", getSampleStyleSheet()['Heading3']))
    elements.append(Spacer(0, 0.1*inch))
    
    limitations = modeling_log.get('limitations', [])
    if limitations:
        for lim in limitations:
            elements.append(Paragraph(f"- {lim}", getSampleStyleSheet()['Normal']))
    else:
        elements.append(Paragraph("No specific limitations recorded.", getSampleStyleSheet()['Normal']))
    
    # Generate PDF
    pdf_path = output_dir / "final_report.pdf"
    try:
        generate_pdf_report(elements, pdf_path, title)
        logging.info(f"Report successfully generated at {pdf_path}")
        update_log_section("report_generation", {"status": "completed", "output": str(pdf_path)})
    except Exception as e:
        update_log_section("report_generation", {"status": "failed", "error": str(e)})
        raise

if __name__ == "__main__":
    main()