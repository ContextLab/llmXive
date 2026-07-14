"""
Report Generation Module for Sustainable Agriculture Adoption Study.

Produces a comprehensive PDF report containing:
- Descriptive statistics
- Regression table with coefficients and p-values
- VIF diagnostics
- ROC curve plot
- Mediation analysis results
- Sensitivity analysis (E-values, Rosenbaum bounds)
- Validity metrics (Cronbach's alpha, EFA results)

Consumes artifacts from previous pipeline stages:
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

import numpy as np
import pandas as pd
import yaml

# Try to import reportlab, provide clear error if missing
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        PageBreak,
        Preformatted,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("WARNING: reportlab not installed. PDF generation will fail.")
    print("Install with: pip install reportlab")

from config import get_config


def load_cleaned_data() -> pd.DataFrame:
    """Load cleaned data from the processed directory."""
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    processed_path = base_dir / config.get("processed_data_path", "data/processed")
    file_path = processed_path / "cleaned_data.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {file_path}")

    return pd.read_csv(file_path)


def load_engineered_data() -> pd.DataFrame:
    """Load engineered data with engagement scores and adoption binary."""
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    processed_path = base_dir / config.get("processed_data_path", "data/processed")
    file_path = processed_path / "engineered_data.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"Engineered data not found at {file_path}")

    return pd.read_csv(file_path)


def load_model_results() -> Dict[str, Any]:
    """Load model results from YAML file."""
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    results_path = base_dir / config.get("results_path", "results")
    file_path = results_path / "model_results.yaml"

    if not file_path.exists():
        raise FileNotFoundError(f"Model results not found at {file_path}")

    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def load_validity_metrics() -> Dict[str, Any]:
    """Load validity metrics from YAML file."""
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    results_path = base_dir / config.get("results_path", "results")
    file_path = results_path / "validity_metrics.yaml"

    if not file_path.exists():
        raise FileNotFoundError(f"Validity metrics not found at {file_path}")

    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def load_modeling_log() -> Dict[str, Any]:
    """Load the modeling log."""
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    file_path = base_dir / "modeling_log.yaml"

    if not file_path.exists():
        raise FileNotFoundError(f"Modeling log not found at {file_path}")

    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def generate_report_header() -> List[Paragraph]:
    """Generate the report header with title and metadata."""
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    elements = []

    title = Paragraph(
        "Adoption of Sustainable Agricultural Practices in Low-Income Areas<br/>"
        "Through Community Engagement: Analysis Report",
        title_style
    )
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    subtitle = Paragraph(
        "A Statistical Analysis of Survey Data",
        subtitle_style
    )
    elements.append(subtitle)
    elements.append(Spacer(1, 0.2 * inch))

    # Metadata
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_text = f"Report Generated: {timestamp}<br/>"
    meta_text += f"Project: PROJ-018<br/>"
    meta_text += f"Methodology: Logistic Regression with Mediation Analysis"

    meta = Paragraph(meta_text, normal_style)
    elements.append(meta)
    elements.append(Spacer(1, 0.5 * inch))

    return elements


def generate_descriptive_stats(cleaned_data: pd.DataFrame, engineered_data: pd.DataFrame) -> List[Any]:
    """Generate descriptive statistics section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph("1. Descriptive Statistics", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Basic counts
    n_total = len(cleaned_data)
    n_adopters = engineered_data['adoption_binary'].sum() if 'adoption_binary' in engineered_data.columns else 0
    adoption_rate = (n_adopters / n_total * 100) if n_total > 0 else 0

    desc_text = (
        f"Total Sample Size: {n_total} respondents<br/>"
        f"Sustainable Practice Adopters: {n_adopters} ({adoption_rate:.1f}%)<br/>"
        f"Non-Adopters: {n_total - n_adopters} ({100 - adoption_rate:.1f}%)"
    )
    elements.append(Paragraph(desc_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Continuous variables summary
    elements.append(Paragraph("Continuous Variables Summary", styles['Heading3']))
    elements.append(Spacer(1, 0.1 * inch))

    num_vars = ['age', 'education', 'farm_size', 'engagement_score']
    available_vars = [v for v in num_vars if v in engineered_data.columns]

    if available_vars:
        stats_data = []
        headers = ["Variable", "Mean", "Std Dev", "Min", "Max", "N"]
        stats_data.append(headers)

        for var in available_vars:
            col = engineered_data[var]
            stats_data.append([
                var.replace('_', ' ').title(),
                f"{col.mean():.2f}",
                f"{col.std():.2f}",
                f"{col.min():.2f}",
                f"{col.max():.2f}",
                str(col.count())
            ])

        t = Table(stats_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.3 * inch))

    # Categorical variables
    elements.append(Paragraph("Categorical Variables Summary", styles['Heading3']))
    elements.append(Spacer(1, 0.1 * inch))

    cat_vars = ['credit_access', 'region']
    for var in cat_vars:
        if var in engineered_data.columns:
            counts = engineered_data[var].value_counts()
            var_text = f"<b>{var.replace('_', ' ').title()}:</b><br/>"
            for idx, count in counts.items():
                pct = (count / n_total * 100)
                var_text += f"&nbsp;&nbsp;- {idx}: {count} ({pct:.1f}%)<br/>"
            elements.append(Paragraph(var_text, normal_style))

    elements.append(Spacer(1, 0.5 * inch))
    return elements


def generate_regression_table(results: Dict[str, Any]) -> List[Any]:
    """Generate the regression results table."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph("2. Logistic Regression Results", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(
        "Association between community engagement intensity and sustainable practice adoption.",
        normal_style
    ))
    elements.append(Spacer(1, 0.2 * inch))

    reg_data = results.get("regression", {})
    coefficients = reg_data.get("coefficients", [])

    if coefficients:
        table_data = [
            ["Variable", "Coefficient", "Std Error", "Z-value", "P-value", "Adj. P-value", "OR (95% CI)"]
        ]

        for coef in coefficients:
            var_name = coef.get("variable", "")
            coef_val = coef.get("coef", 0)
            std_err = coef.get("std_err", 0)
            z_val = coef.get("z", 0)
            p_val = coef.get("pvalue", 1)
            adj_p = coef.get("adj_pvalue", p_val)
            odds_ratio = np.exp(coef_val)
            ci_lower = np.exp(coef_val - 1.96 * std_err)
            ci_upper = np.exp(coef_val + 1.96 * std_err)

            # Highlight significant results
            sig_marker = "*" if adj_p < 0.05 else ""

            table_data.append([
                var_name,
                f"{coef_val:.3f}{sig_marker}",
                f"{std_err:.3f}",
                f"{z_val:.3f}",
                f"{p_val:.4f}",
                f"{adj_p:.4f}",
                f"{odds_ratio:.2f} ({ci_lower:.2f}-{ci_upper:.2f})"
            ])

        t = Table(table_data, colWidths=[1.8*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.1*inch, 1.8*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "* indicates p < 0.05 after Benjamini-Hochberg FDR correction.",
            normal_style
        ))
    else:
        elements.append(Paragraph("No regression coefficients available.", normal_style))

    elements.append(Spacer(1, 0.5 * inch))
    return elements


def generate_vif_section(results: Dict[str, Any]) -> List[Any]:
    """Generate VIF diagnostics section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph("3. Multicollinearity Diagnostics (VIF)", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    vif_data = results.get("vif", [])

    if vif_data:
        table_data = [["Variable", "VIF", "Status"]]
        for vif_item in vif_data:
            var_name = vif_item.get("variable", "")
            vif_val = vif_item.get("vif", 0)
            status = "OK" if vif_val < 5 else "WARNING (VIF ≥ 5)"

            table_data.append([var_name, f"{vif_val:.2f}", status])

        t = Table(table_data, colWidths=[2*inch, 1*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2 * inch))

        max_vif = max([v.get("vif", 0) for v in vif_data])
        if max_vif >= 5:
            elements.append(Paragraph(
                "<b>Warning:</b> Some predictors exhibit high multicollinearity (VIF ≥ 5). "
                "Results should be interpreted with caution.",
                normal_style
            ))
        else:
            elements.append(Paragraph(
                "No significant multicollinearity detected (all VIF < 5).",
                normal_style
            ))
    else:
        elements.append(Paragraph("VIF diagnostics not available.", normal_style))

    elements.append(Spacer(1, 0.5 * inch))
    return elements


def generate_roc_section(results: Dict[str, Any]) -> List[Any]:
    """Generate ROC curve and AUC section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph("4. Model Performance (ROC Analysis)", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    auc = results.get("auc", 0)
    roc_path = results.get("roc_plot_path", "")

    # AUC Interpretation
    elements.append(Paragraph(f"Area Under the Curve (AUC): {auc:.3f}", styles['Heading3']))
    elements.append(Spacer(1, 0.1 * inch))

    auc_interpretation = interpret_auc(auc)
    elements.append(Paragraph(auc_interpretation, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # ROC Plot
    if roc_path and os.path.exists(roc_path):
        elements.append(Paragraph("ROC Curve:", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))

        try:
            img = Image(roc_path, width=5*inch, height=4*inch)
            elements.append(img)
        except Exception as e:
            elements.append(Paragraph(f"Could not load ROC plot: {str(e)}", normal_style))
    else:
        elements.append(Paragraph("ROC plot not available.", normal_style))

    elements.append(Spacer(1, 0.5 * inch))
    return elements


def interpret_auc(auc: float) -> str:
    """Interpret AUC value."""
    if auc < 0.5:
        return "Poor discrimination (worse than random)"
    elif auc < 0.6:
        return "Fail"
    elif auc < 0.7:
        return "Acceptable"
    elif auc < 0.8:
        return "Excellent"
    elif auc < 0.9:
        return "Outstanding"
    else:
        return "Near Perfect"


def generate_mediation_section(results: Dict[str, Any]) -> List[Any]:
    """Generate mediation analysis section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph("5. Mediation Analysis", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(
        "Analysis of indirect effects and potential mediators in the relationship between "
        "community engagement and adoption behavior.",
        normal_style
    ))
    elements.append(Spacer(1, 0.2 * inch))

    mediation = results.get("mediation", {})
    if mediation:
        direct_effect = mediation.get("direct_effect", {})
        indirect_effect = mediation.get("indirect_effect", {})

        elements.append(Paragraph("Direct Effect:", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        if direct_effect:
            coef = direct_effect.get("coef", 0)
            pval = direct_effect.get("pvalue", 1)
            ci = direct_effect.get("ci", [0, 0])
            elements.append(Paragraph(
                f"Coefficient: {coef:.3f}, p-value: {pval:.4f}, 95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]",
                normal_style
            ))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph("Indirect Effect (Mediated):", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))
        if indirect_effect:
            coef = indirect_effect.get("coef", 0)
            pval = indirect_effect.get("pvalue", 1)
            ci = indirect_effect.get("ci", [0, 0])
            elements.append(Paragraph(
                f"Coefficient: {coef:.3f}, p-value: {pval:.4f}, 95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]",
                normal_style
            ))
            if pval < 0.05:
                elements.append(Paragraph(
                    "The indirect effect is statistically significant, suggesting mediation.",
                    styles['Normal']
                ))
            else:
                elements.append(Paragraph(
                    "The indirect effect is not statistically significant.",
                    styles['Normal']
                ))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph(
            "<b>Note:</b> This analysis is exploratory. Causal inference requires stronger "
            "research designs and assumptions.",
            normal_style
        ))
    else:
        elements.append(Paragraph("Mediation analysis results not available.", normal_style))

    elements.append(Spacer(1, 0.5 * inch))
    return elements


def generate_sensitivity_section(results: Dict[str, Any]) -> List[Any]:
    """Generate sensitivity analysis section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph("6. Sensitivity Analysis", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(
        "Assessment of how robust the findings are to potential unobserved confounding.",
        normal_style
    ))
    elements.append(Spacer(1, 0.2 * inch))

    sensitivity = results.get("sensitivity", {})

    # E-values
    elements.append(Paragraph("E-value Analysis:", styles['Heading3']))
    elements.append(Spacer(1, 0.1 * inch))
    if sensitivity.get("evalues"):
        eval_data = sensitivity["evalues"]
        for item in eval_data:
            var = item.get("variable", "")
            eval = item.get("evalue", 0)
            ci = item.get("ci_lower", 0)
            elements.append(Paragraph(
                f"Variable '{var}': E-value = {eval:.3f} (95% CI lower bound: {ci:.3f})",
                normal_style
            ))
            elements.append(Paragraph(
                f"  Interpretation: An unobserved confounder would need to be associated "
                f"with both the exposure and outcome by an odds ratio of {eval:.3f} or greater "
                f"to fully explain away the observed effect.",
                normal_style
            ))
    else:
        elements.append(Paragraph("E-values not computed.", normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Rosenbaum bounds
    elements.append(Paragraph("Rosenbaum Sensitivity Bounds:", styles['Heading3']))
    elements.append(Spacer(1, 0.1 * inch))
    if sensitivity.get("rosenbaum"):
        rb_data = sensitivity["rosenbaum"]
        elements.append(Paragraph(
            f"Gamma (Γ) values tested: {rb_data.get('gamma_range', [])}",
            normal_style
        ))
        elements.append(Paragraph(
            f"Significance threshold: {rb_data.get('p_threshold', 0.05)}",
            normal_style
        ))
        if rb_data.get("robustness"):
            elements.append(Paragraph(
                f"Results remain significant up to Γ = {rb_data.get('max_robust_gamma', 0):.2f}",
                styles['Normal']
            ))
    else:
        elements.append(Paragraph("Rosenbaum bounds not computed.", normal_style))

    elements.append(Spacer(1, 0.5 * inch))
    return elements


def generate_validity_section(validity_metrics: Dict[str, Any]) -> List[Any]:
    """Generate validity metrics section."""
    elements = []
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    elements.append(Paragraph("7. Measurement Validity & Reliability", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Cronbach's Alpha
    elements.append(Paragraph("Reliability (Cronbach's Alpha):", styles['Heading3']))
    elements.append(Spacer(1, 0.1 * inch))
    alpha = validity_metrics.get("cronbach_alpha", {})
    if alpha:
        alpha_val = alpha.get("alpha", 0)
        items = alpha.get("n_items", 0)
        elements.append(Paragraph(
            f"Cronbach's α = {alpha_val:.3f} (n = {items} items)",
            normal_style
        ))
        if alpha_val >= 0.7:
            elements.append(Paragraph(
                "Interpretation: Acceptable internal consistency.",
                normal_style
            ))
        elif alpha_val >= 0.6:
            elements.append(Paragraph(
                "Interpretation: Marginal internal consistency.",
                normal_style
            ))
        else:
            elements.append(Paragraph(
                "Interpretation: Low internal consistency. Consider revising items.",
                normal_style
            ))
    else:
        elements.append(Paragraph("Cronbach's alpha not computed.", normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # EFA Results
    elements.append(Paragraph("Exploratory Factor Analysis (EFA):", styles['Heading3']))
    elements.append(Spacer(1, 0.1 * inch))
    efa = validity_metrics.get("efa", {})
    if efa:
        factors = efa.get("factors_retained", 0)
        method = efa.get("extraction_method", "Principal Axis Factoring")
        rotation = efa.get("rotation_method", "Varimax")
        elements.append(Paragraph(
            f"Factors retained: {factors} (Kaiser's rule, eigenvalues > 1)",
            normal_style
        ))
        elements.append(Paragraph(
            f"Extraction: {method}, Rotation: {rotation}",
            normal_style
        ))

        # Factor loadings table if available
        loadings = efa.get("factor_loadings", [])
        if loadings and len(loadings) > 0:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Factor Loadings:", styles['Heading4']))

            # Build table for top loadings
            table_data = [["Item", "Factor 1", "Factor 2", "Factor 3"]]
            # Limit to first 10 items for brevity
            for i, item in enumerate(loadings[:10]):
                row = [item.get("item", "")]
                for f in range(1, 4):
                    val = item.get(f"factor_{f}", "")
                    row.append(f"{val:.2f}" if isinstance(val, float) else str(val))
                table_data.append(row)

            t = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(t)
    else:
        elements.append(Paragraph("EFA results not available.", normal_style))

    elements.append(Spacer(1, 0.5 * inch))
    return elements


def generate_pdf_report(
    cleaned_data: pd.DataFrame,
    engineered_data: pd.DataFrame,
    model_results: Dict[str, Any],
    validity_metrics: Dict[str, Any],
    modeling_log: Dict[str, Any],
    output_path: str
) -> str:
    """Assemble all sections into a PDF report."""
    if not REPORTLAB_AVAILABLE:
        raise ImportError(
            "reportlab is required for PDF generation. "
            "Install it with: pip install reportlab"
        )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    story = []

    # Header
    story.extend(generate_report_header())

    # Descriptive Statistics
    story.extend(generate_descriptive_stats(cleaned_data, engineered_data))

    # Regression Results
    story.extend(generate_regression_table(model_results))

    # VIF Diagnostics
    story.extend(generate_vif_section(model_results))

    # ROC Analysis
    story.extend(generate_roc_section(model_results))

    # Mediation Analysis
    story.extend(generate_mediation_section(model_results))

    # Sensitivity Analysis
    story.extend(generate_sensitivity_section(model_results))

    # Validity Metrics
    story.extend(generate_validity_section(validity_metrics))

    # Build PDF
    doc.build(story)
    return output_path


def main():
    """Main entry point for report generation."""
    print("Starting report generation...")

    try:
        # Load all required data
        cleaned_data = load_cleaned_data()
        engineered_data = load_engineered_data()
        model_results = load_model_results()
        validity_metrics = load_validity_metrics()
        modeling_log = load_modeling_log()

        # Configure output path
        config = get_config()
        base_dir = Path(config.get("project_root", "."))
        results_path = base_dir / config.get("results_path", "results")
        output_file = results_path / "final_report.pdf"

        # Generate the report
        print(f"Generating PDF report at: {output_file}")
        generate_pdf_report(
            cleaned_data,
            engineered_data,
            model_results,
            validity_metrics,
            modeling_log,
            str(output_file)
        )

        print(f"Report successfully generated: {output_file}")

    except FileNotFoundError as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
    except ImportError as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during report generation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()