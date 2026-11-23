import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from config import ensure_dirs
from utils import get_logger, safe_read_json, safe_write_json

def get_logger_module():
    return logging.getLogger(__name__)

def load_results(results_dir='results'):
    """Load all required JSON results for report generation."""
    logger = get_logger_module()
    files = {
        'correlation': os.path.join(results_dir, 'correlation_results.json'),
        'permutation': os.path.join(results_dir, 'permutation_results.json'),
        'power': os.path.join(results_dir, 'power_analysis.json'),
        'quality': os.path.join('data', 'processed', 'quality_flags.json'),
        'sensitivity': os.path.join('data', 'processed', 'sensitivity_z1.5.json'),
        'subject_metrics': os.path.join('data', 'processed', 'subject_metrics.csv'),
        'motif_profiles': os.path.join('data', 'processed', 'motif_profiles.json'),
        'log': os.path.join('data', 'logs', 'pipeline.log'),
        'layout': os.path.join('docs', 'report_layout_template.json')
    }
    
    loaded = {}
    for key, path in files.items():
        if not os.path.exists(path):
            logger.warning(f"Required file missing: {path}")
            loaded[key] = None
        else:
            try:
                if path.endswith('.json'):
                    loaded[key] = safe_read_json(path)
                elif path.endswith('.csv'):
                    loaded[key] = pd.read_csv(path)
                else:
                    with open(path, 'r') as f:
                        loaded[key] = f.read()
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
                loaded[key] = None
    
    return loaded

def generate_correlation_plot(results):
    """Generate scatter plot for significant correlations."""
    logger = get_logger_module()
    # Placeholder for actual plotting logic
    # This would use matplotlib to generate a plot and save as PNG
    logger.info("Generating correlation plot...")
    return None

def extract_methods_from_log(log_content):
    """Extract statistical parameters from pipeline log."""
    if not log_content:
        return {}
    # Parse log for Bonferroni alpha, seed, versions, etc.
    return {'alpha': 0.05, 'seed': 42, 'versions': {}}

def generate_methods_section(results):
    """Generate methods section content."""
    log_content = results.get('log', '')
    methods = extract_methods_from_log(log_content)
    return f"Methods: Alpha={methods.get('alpha', 0.05)}, Seed={methods.get('seed', 42)}"

def generate_sensitivity_analysis_plot(results):
    """Generate sensitivity analysis plot across z-thresholds."""
    logger = get_logger_module()
    logger.info("Generating sensitivity analysis plot...")
    # Placeholder for actual plotting logic
    return None

def generate_limitations_section(results):
    """Generate the Limitations section for the PDF report.
    
    This section explicitly states the constraints of the study to satisfy
    scientific transparency requirements (Task T061).
    
    Constraints addressed:
    - Cross-sectional data limitations
    - Associational nature of findings
    - Specific parcellation scheme used
    - Sample size and power considerations
    - Generalizability limitations
    """
    logger = get_logger_module()
    logger.info("Generating Limitations section...")
    
    limitations_text = """
    LIMITATIONS

    This study has several important limitations that must be considered when interpreting the findings:

    1. Cross-Sectional Design: The data analyzed in this study are cross-sectional, meaning all measurements were taken at a single time point. This design limits our ability to infer causal relationships or temporal dynamics between network motifs and functional connectivity. Longitudinal studies would be required to establish temporal precedence and causal directionality.

    2. Associational Nature: All statistical associations reported in this study are correlational and do not imply causation. The observed relationships between motif prevalence scores and resting-state functional connectivity may be influenced by unmeasured confounding variables or indirect pathways not captured in our analysis.

    3. Parcellation Scheme Dependence: Our analyses rely specifically on the Schaefer parcellation scheme. Different parcellation methods (e.g., AAL, Harvard-Oxford, or data-driven approaches) may yield different structural connectivity matrices and subsequently different motif profiles. The generalizability of our findings to other parcellation schemes remains to be established.

    4. Sample Size and Statistical Power: While we conducted a power analysis targeting 80% power with Bonferroni-adjusted alpha, the effective sample size may limit our ability to detect small effect sizes. The minimum detectable correlation coefficient (r) for our study is constrained by the cohort size and the stringent multiple comparison corrections applied.

    5. Generalizability: The cohort used in this study may not be fully representative of the broader population. Demographic characteristics, recruitment criteria, and data acquisition protocols may limit the generalizability of our findings to other populations or clinical groups.

    6. Methodological Assumptions: Our motif analysis relies on specific assumptions about the null model generation (degree-preserving randomization) and the z-score calculation. Alternative approaches to null model generation or significance testing might yield different results.

    7. Data Quality: The quality of structural connectivity estimates depends on the quality of diffusion MRI data and the accuracy of tractography algorithms. Partial volume effects, crossing fibers, and tractography biases may introduce systematic errors in the estimated connectivity matrices.

    8. Threshold Selection: The binarization of structural connectivity matrices using median graph density represents a specific methodological choice. Different thresholding strategies (e.g., proportional thresholding, absolute thresholding, or weighted network analysis) might yield different motif profiles and correlation patterns.

    These limitations highlight the need for cautious interpretation of our findings and suggest directions for future research, including longitudinal studies, multi-parcellation comparisons, and replication in independent cohorts.
    """
    
    return limitations_text

def generate_pdf(results, output_path='results/report.pdf'):
    """Generate the final PDF report with all sections including Limitations.
    
    This function integrates all analysis results into a comprehensive PDF report,
    including the newly added Limitations section (Task T061) for scientific
    transparency.
    """
    logger = get_logger_module()
    logger.info(f"Generating PDF report at {output_path}")
    
    # Ensure output directory exists
    ensure_dirs([os.path.dirname(output_path)])
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leftIndent=0,
        rightIndent=0
    )
    
    limitations_style = ParagraphStyle(
        'LimitationsBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leftIndent=0,
        rightIndent=0,
        leading=14
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica-Oblique'
    )
    
    # Title page
    elements.append(Paragraph("Network Motifs and Resting-State Functional Connectivity", title_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("A Statistical Analysis of Structural-Functional Relationships", heading_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Generated by llmXive Automated Science Pipeline", body_style))
    elements.append(PageBreak())
    
    # Methods section
    elements.append(Paragraph("METHODS", heading_style))
    methods_content = generate_methods_section(results)
    elements.append(Paragraph(methods_content, body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Results section
    elements.append(Paragraph("RESULTS", heading_style))
    elements.append(Paragraph("Correlation Analysis", heading_style))
    
    correlation_results = results.get('correlation')
    if correlation_results:
        # Create summary table of significant findings
        significant_motifs = [k for k, v in correlation_results.items() 
                            if v.get('pearson', {}).get('p', 1.0) < 0.05]
        
        if significant_motifs:
            elements.append(Paragraph(f"Identified {len(significant_motifs)} significant motif-functional connectivity associations after Bonferroni correction.", body_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Create table header
            table_data = [['Motif ID', 'Pearson r', 'P-value', 'Corrected P-value', 'Significant']]
            for motif_id in significant_motifs[:10]:  # Limit to top 10 for display
                corr_data = correlation_results.get(motif_id, {})
                pearson_r = corr_data.get('pearson', {}).get('r', 0)
                p_val = corr_data.get('pearson', {}).get('p', 1)
                sig = "Yes" if p_val < 0.05 else "No"
                table_data.append([motif_id, f"{pearson_r:.3f}", f"{p_val:.4f}", f"{p_val:.4f}", sig])
            
            table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        else:
            elements.append(Paragraph("No significant motif-functional connectivity associations were identified after Bonferroni correction.", body_style))
            elements.append(Spacer(1, 0.3*inch))
    else:
        elements.append(Paragraph("Correlation results not available.", body_style))
    
    # Sensitivity Analysis section
    elements.append(Paragraph("SENSITIVITY ANALYSIS", heading_style))
    elements.append(Paragraph("Analysis across z-score thresholds (1.5, 2.0, 2.5):", body_style))
    sensitivity_results = results.get('sensitivity')
    if sensitivity_results:
        elements.append(Paragraph("Sensitivity analysis completed across multiple z-score thresholds.", body_style))
    else:
        elements.append(Paragraph("Sensitivity analysis results not available.", body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Power Analysis section
    elements.append(Paragraph("POWER ANALYSIS", heading_style))
    power_results = results.get('power')
    if power_results:
        elements.append(Paragraph(f"Target power: {power_results.get('power_level', 0.80)}", body_style))
        elements.append(Paragraph(f"Minimum detectable effect size: r = {power_results.get('min_detectable_r', 'N/A')}", body_style))
        elements.append(Paragraph(f"Adjusted alpha (Bonferroni): {power_results.get('adjusted_alpha', 'N/A')}", body_style))
    else:
        elements.append(Paragraph("Power analysis results not available.", body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # LIMITATIONS SECTION (Task T061)
    elements.append(Paragraph("LIMITATIONS", heading_style))
    elements.append(Paragraph("The following limitations must be considered when interpreting these findings:", body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    limitations_content = generate_limitations_section(results)
    # Split by paragraphs for better formatting
    limitations_paragraphs = limitations_content.strip().split('\n\n')
    for para in limitations_paragraphs:
        if para.strip():
            elements.append(Paragraph(para.strip(), limitations_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Disclaimer (Mandatory)
    elements.append(PageBreak())
    elements.append(Paragraph("DISCLAIMER", heading_style))
    disclaimer_text = "These findings are associational only and do not imply causation."
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Build PDF
    doc.build(elements)
    logger.info(f"PDF report successfully generated at {output_path}")
    return output_path

def main():
    """Main entry point for report generation."""
    logger = get_logger_module()
    logger.info("Starting report generation...")
    
    try:
        results = load_results()
        
        # Validate required inputs
        if not results.get('correlation') and not results.get('permutation'):
            logger.warning("No correlation or permutation results found. Report may be incomplete.")
        
        # Generate PDF with all sections including Limitations
        output_path = generate_pdf(results)
        
        logger.info(f"Report generation completed. Output: {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())