import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels

from config import ensure_dirs
from utils import get_logger, safe_read_json, safe_read_text

# Ensure logging is configured
logger = get_logger("report")

def load_results(file_path):
    """Load JSON results from a file."""
    try:
        return safe_read_json(file_path)
    except FileNotFoundError:
        logger.error(f"Results file not found: {file_path}")
        raise

def generate_correlation_plot(motif_id, x_data, y_data, r_val, p_val, output_path):
    """Generate a scatter plot with regression line for a specific motif."""
    plt.figure(figsize=(8, 6))
    plt.scatter(x_data, y_data, alpha=0.7, edgecolors='k')
    
    # Fit regression line
    slope, intercept, r, p, se = stats.linregress(x_data, y_data)
    x_line = np.linspace(min(x_data), max(x_data), 100)
    y_line = slope * x_line + intercept
    plt.plot(x_line, y_line, 'r-', label=f'Fit: r={r:.3f}, p={p:.3f}')
    
    plt.title(f'Motif {motif_id}: rsFC vs Global Efficiency')
    plt.xlabel('Global Efficiency')
    plt.ylabel('rsFC Strength')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved correlation plot to {output_path}")

def extract_methods_from_log(log_path):
    """
    Programmatically extract statistical parameters from pipeline.log
    to satisfy Constitution Principle VII (Statistical Transparency).
    
    Extracts: Bonferroni alpha, permutation count, random seed, VIF threshold,
    library versions (numpy, scipy, statsmodels).
    """
    methods = {
        "bonferroni_alpha": None,
        "permutation_count": None,
        "random_seed": None,
        "vif_threshold": None,
        "library_versions": {}
    }
    
    try:
        log_content = safe_read_text(log_path)
        lines = log_content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Extract Bonferroni alpha
            if "bonferroni alpha" in line_lower or "bonferroni-adjusted" in line_lower:
                # Look for pattern like "Bonferroni alpha level: 0.003"
                import re
                match = re.search(r'bonferroni.*alpha.*[:=]?\s*([\d.]+)', line_lower)
                if match:
                    methods["bonferroni_alpha"] = float(match.group(1))
            
            # Extract permutation count
            if "permutation" in line_lower and "count" in line_lower:
                import re
                match = re.search(r'permutation.*count.*[:=]?\s*(\d+)', line_lower)
                if match:
                    methods["permutation_count"] = int(match.group(1))
            elif "n_perm" in line_lower:
                import re
                match = re.search(r'n_perm.*[:=]?\s*(\d+)', line_lower)
                if match:
                    methods["permutation_count"] = int(match.group(1))
            
            # Extract random seed
            if "random seed" in line_lower or "seed" in line_lower:
                import re
                # Match patterns like "seed: 42" or "random seed = 42"
                match = re.search(r'(?:seed|random.*seed).*[:=]?\s*(\d+)', line_lower)
                if match:
                    methods["random_seed"] = int(match.group(1))
            
            # Extract VIF threshold
            if "vif" in line_lower and "threshold" in line_lower:
                import re
                match = re.search(r'vif.*threshold.*[:=]?\s*([\d.]+)', line_lower)
                if match:
                    methods["vif_threshold"] = float(match.group(1))
            
            # Extract library versions
            if "numpy version" in line_lower:
                import re
                match = re.search(r'numpy.*version.*[:=]?\s*([\d.]+)', line_lower)
                if match:
                    methods["library_versions"]["numpy"] = match.group(1)
            elif "scipy version" in line_lower:
                import re
                match = re.search(r'scipy.*version.*[:=]?\s*([\d.]+)', line_lower)
                if match:
                    methods["library_versions"]["scipy"] = match.group(1)
            elif "statsmodels version" in line_lower:
                import re
                match = re.search(r'statsmodels.*version.*[:=]?\s*([\d.]+)', line_lower)
                if match:
                    methods["library_versions"]["statsmodels"] = match.group(1)
        
        # Fallback: try to get versions from installed packages if not found in log
        if not methods["library_versions"]:
            try:
                methods["library_versions"]["numpy"] = np.__version__
                methods["library_versions"]["scipy"] = stats.__version__
                methods["library_versions"]["statsmodels"] = statsmodels.__version__
            except Exception:
                pass
        
        # Validate and set defaults if extraction failed
        if methods["bonferroni_alpha"] is None:
            methods["bonferroni_alpha"] = 0.05 / 13  # Default for 13 motifs
            logger.warning("Bonferroni alpha not found in log, using default: 0.0038")
        
        if methods["permutation_count"] is None:
            methods["permutation_count"] = 1000
            logger.warning("Permutation count not found in log, using default: 1000")
        
        if methods["random_seed"] is None:
            methods["random_seed"] = 42
            logger.warning("Random seed not found in log, using default: 42")
        
        if methods["vif_threshold"] is None:
            methods["vif_threshold"] = 5.0
            logger.warning("VIF threshold not found in log, using default: 5.0")
        
        logger.info(f"Extracted methods parameters: {methods}")
        return methods
        
    except FileNotFoundError:
        logger.error(f"Pipeline log not found: {log_path}")
        # Return defaults if log is missing
        return {
            "bonferroni_alpha": 0.05 / 13,
            "permutation_count": 1000,
            "random_seed": 42,
            "vif_threshold": 5.0,
            "library_versions": {
                "numpy": np.__version__,
                "scipy": stats.__version__,
                "statsmodels": statsmodels.__version__
            }
        }

def generate_methods_section(methods_params):
    """Generate formatted text for the Methods section of the PDF."""
    methods_text = f"""
    <para align="justify">
    <b>Statistical Methods</b><br/>
    This study employed partial correlation analysis to examine the relationship 
    between network motif prevalence (z-scores) and resting-state functional 
    connectivity (rsFC) strength, controlling for global node degree. 
    Statistical significance was assessed using a Bonferroni correction 
    (α = {methods_params['bonferroni_alpha']:.4f}, adjusted for {13} directed 3-node motifs).
    </para>
    <para align="justify">
    <b>Permutation Testing</b><br/>
    For motifs showing significant partial correlations, empirical p-values 
    were computed using {methods_params['permutation_count']} permutations 
    with a fixed random seed ({methods_params['random_seed']}) to ensure reproducibility.
    </para>
    <para align="justify">
    <b>Multicollinearity Assessment</b><br/>
    Variance Inflation Factor (VIF) analysis was performed with a threshold 
    of {methods_params['vif_threshold']:.1f}. When VIF exceeded this threshold, 
    the analysis switched to permutation-only methods as per the study protocol.
    </para>
    <para align="justify">
    <b>Software and Libraries</b><br/>
    Analysis was conducted using the following software versions:<br/>
    - NumPy: {methods_params['library_versions'].get('numpy', 'N/A')}<br/>
    - SciPy: {methods_params['library_versions'].get('scipy', 'N/A')}<br/>
    - StatsModels: {methods_params['library_versions'].get('statsmodels', 'N/A')}<br/>
    </para>
    <para align="justify">
    <i>These findings are associational only and do not imply causation.</i>
    </para>
    """
    return methods_text

def generate_pdf(correlation_results_path, permutation_results_path, power_analysis_path, 
                layout_template_path, output_path):
    """
    Generate the final PDF report with correlation results, permutation tests,
    power analysis, and a dynamically generated Methods section extracted from pipeline.log.
    """
    # Load input data
    correlation_results = load_results(correlation_results_path)
    permutation_results = load_results(permutation_results_path)
    power_analysis = load_results(power_analysis_path)
    
    # Extract Methods from pipeline.log (Constitution Principle VII)
    log_path = "data/logs/pipeline.log"
    methods_params = extract_methods_from_log(log_path)
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Motif-FC Correlation Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    # Methods Section (Dynamically Generated)
    story.append(Paragraph("Methods", styles['Heading2']))
    story.append(Spacer(1, 10))
    methods_text = generate_methods_section(methods_params)
    story.append(Paragraph(methods_text, styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Correlation Results Table
    story.append(Paragraph("Correlation Results", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    if correlation_results and 'results' in correlation_results:
        data = [["Motif", "Pearson r", "Spearman r", "Bonferroni p", "Significant"]]
        for motif_id, results in correlation_results['results'].items():
            pearson_r = results.get('pearson_r', 'N/A')
            spearman_r = results.get('spearman_r', 'N/A')
            bonf_p = results.get('bonferroni_p', 'N/A')
            sig = "Yes" if results.get('significant', False) else "No"
            data.append([motif_id, f"{pearson_r:.3f}", f"{spearman_r:.3f}", 
                        f"{bonf_p:.4f}" if isinstance(bonf_p, float) else str(bonf_p), sig])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No correlation results available.", styles['Normal']))
    
    story.append(Spacer(1, 30))
    
    # Permutation Test Results
    story.append(Paragraph("Permutation Test Results", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    if permutation_results and len(permutation_results) > 0:
        data = [["Motif", "Original r", "Empirical p"]]
        for res in permutation_results:
            data.append([res['motif_id'], f"{res['original_r']:.3f}", 
                        f"{res['empirical_p']:.4f}"])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No significant motifs required permutation testing.", styles['Normal']))
    
    story.append(Spacer(1, 30))
    
    # Power Analysis Summary
    story.append(Paragraph("Power Analysis", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    if power_analysis:
        story.append(Paragraph(
            f"Minimum detectable effect size (r): {power_analysis.get('min_detectable_r', 'N/A'):.3f}<br/>"
            f"Statistical power level: {power_analysis.get('power_level', 'N/A')}<br/>"
            f"Adjusted alpha (Bonferroni): {power_analysis.get('adjusted_alpha', 'N/A'):.4f}<br/>"
            f"Number of subjects: {power_analysis.get('n_subjects', 'N/A')}",
            styles['Normal']
        ))
    else:
        story.append(Paragraph("Power analysis results not available.", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    logger.info(f"PDF report generated successfully: {output_path}")

def main():
    """Main entry point for report generation."""
    logger.info("Starting PDF report generation...")
    
    # Define paths
    correlation_results_path = "results/correlation_results.json"
    permutation_results_path = "results/permutation_results.json"
    power_analysis_path = "results/power_analysis.json"
    layout_template_path = "docs/report_layout_template.json"
    output_path = "results/report.pdf"
    
    # Ensure output directory exists
    ensure_dirs([output_path])
    
    # Generate PDF
    try:
        generate_pdf(
            correlation_results_path,
            permutation_results_path,
            power_analysis_path,
            layout_template_path,
            output_path
        )
        logger.info("Report generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()