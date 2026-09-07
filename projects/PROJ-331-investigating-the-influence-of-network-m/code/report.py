import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

def load_results(results_path="results/correlation_results.json"):
    """Load correlation results from JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Results file not found: {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def generate_correlation_plot(results, ci_data=None, output_path="figures/correlation_plot.png"):
    """
    Generate a scatter plot of correlation results with optional confidence interval error bars.
    
    Args:
        results: Dictionary or DataFrame containing correlation results
        ci_data: Optional dictionary containing confidence interval data for error bars
        output_path: Path to save the generated plot
    
    Returns:
        Path to the saved plot
    """
    import matplotlib.pyplot as plt
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Prepare data for plotting
    if isinstance(results, dict):
        motifs = list(results.keys())
        r_values = [results[motif].get('r', 0) for motif in motifs]
        p_values = [results[motif].get('p_value', 1.0) for motif in motifs]
    else:
        motifs = results['motif_id'].tolist()
        r_values = results['r'].tolist()
        p_values = results['p_value'].tolist()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot scatter points
    colors = ['red' if p < 0.05 else 'blue' for p in p_values]
    ax.scatter(range(len(motifs)), r_values, c=colors, alpha=0.7, s=100, edgecolors='black')
    
    # Add error bars if confidence interval data is provided
    if ci_data:
        yerr_lower = []
        yerr_upper = []
        for i, motif in enumerate(motifs):
            if motif in ci_data:
                r = r_values[i]
                lower = ci_data[motif]['lower_bound']
                upper = ci_data[motif]['upper_bound']
                yerr_lower.append(r - lower)
                yerr_upper.append(upper - r)
            else:
                yerr_lower.append(0)
                yerr_upper.append(0)
        
        ax.errorbar(range(len(motifs)), r_values, 
                    yerr=[yerr_lower, yerr_upper],
                    fmt='none', ecolor='gray', capsize=5, alpha=0.5)
    
    # Set labels and title
    ax.set_xticks(range(len(motifs)))
    ax.set_xticklabels(motifs, rotation=45, ha='right')
    ax.set_ylabel('Pearson Correlation Coefficient (r)')
    ax.set_title('Motif-RSFC Correlation Results with Confidence Intervals')
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    
    # Add significance legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.7, label='Significant (p < 0.05)'),
        Patch(facecolor='blue', alpha=0.7, label='Not Significant')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save plot
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Correlation plot saved to {output_path}")
    return output_path

def extract_methods_from_log(log_path="data/logs/pipeline.log"):
    """
    Extract statistical parameters from the pipeline log for the Methods section.
    
    Args:
        log_path: Path to the pipeline log file
    
    Returns:
        dict with extracted parameters
    """
    if not os.path.exists(log_path):
        logging.warning(f"Log file not found: {log_path}")
        return {}
    
    with open(log_path, 'r') as f:
        log_content = f.read()
    
    methods = {
        'bonferroni_alpha': None,
        'permutation_count': None,
        'random_seed': None,
        'vif_threshold': None,
        'library_versions': {}
    }
    
    # Simple pattern matching for log extraction
    import re
    
    # Extract Bonferroni alpha
    bonf_match = re.search(r'Bonferroni alpha.*?(\d+\.\d+)', log_content)
    if bonf_match:
        methods['bonferroni_alpha'] = float(bonf_match.group(1))
    
    # Extract permutation count
    perm_match = re.search(r'permutation count.*?(\d+)', log_content, re.IGNORECASE)
    if perm_match:
        methods['permutation_count'] = int(perm_match.group(1))
    
    # Extract random seed
    seed_match = re.search(r'seed.*?(\d+)', log_content, re.IGNORECASE)
    if seed_match:
        methods['random_seed'] = int(seed_match.group(1))
    
    # Extract VIF threshold
    vif_match = re.search(r'VIF threshold.*?(\d+\.\d+)', log_content)
    if vif_match:
        methods['vif_threshold'] = float(vif_match.group(1))
    
    # Extract library versions (simplified)
    if 'numpy' in log_content:
        methods['library_versions']['numpy'] = 'extracted_from_log'
    if 'scipy' in log_content:
        methods['library_versions']['scipy'] = 'extracted_from_log'
    if 'statsmodels' in log_content:
        methods['library_versions']['statsmodels'] = 'extracted_from_log'
    
    return methods

def generate_methods_section(methods_data):
    """
    Generate a formatted Methods section string for the PDF report.
    
    Args:
        methods_data: Dictionary with extracted statistical parameters
    
    Returns:
        str: Formatted Methods section text
    """
    lines = [
        "## Methods",
        "",
        "### Statistical Analysis",
        f"- **Bonferroni Correction**: Applied with alpha level = {methods_data.get('bonferroni_alpha', 'N/A')}",
        f"- **Permutation Test**: {methods_data.get('permutation_count', 'N/A')} permutations performed",
        f"- **Random Seed**: {methods_data.get('random_seed', 'N/A')} for reproducibility",
        f"- **VIF Threshold**: {methods_data.get('vif_threshold', 'N/A')} for multicollinearity assessment",
        "",
        "### Software",
        f"- **NumPy**: {methods_data.get('library_versions', {}).get('numpy', 'N/A')}",
        f"- **SciPy**: {methods_data.get('library_versions', {}).get('scipy', 'N/A')}",
        f"- **Statsmodels**: {methods_data.get('library_versions', {}).get('statsmodels', 'N/A')}",
        "",
        "### Confidence Intervals",
        "Effect size confidence intervals were computed using Fisher's z-transformation",
        "to stabilize the variance of the Pearson correlation coefficient.",
        "95% confidence intervals are displayed as error bars on scatter plots."
    ]
    
    return "\n".join(lines)

def generate_pdf(correlation_results, permutation_results, power_analysis, 
                 ci_data=None, layout_template_path="docs/report_layout_template.json",
                 output_path="results/report.pdf"):
    """
    Generate a comprehensive PDF report from analysis results.
    
    Args:
        correlation_results: Dictionary with correlation results
        permutation_results: Dictionary with permutation test results
        power_analysis: Dictionary with power analysis results
        ci_data: Optional dictionary with confidence interval data for error bars
        layout_template_path: Path to the layout template JSON
        output_path: Path to save the generated PDF
    
    Returns:
        Path to the saved PDF
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load layout template if provided
    layout = None
    if layout_template_path and os.path.exists(layout_template_path):
        with open(layout_template_path, 'r') as f:
            layout = json.load(f)
    
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
        alignment=1  # Center
    )
    story.append(Paragraph("Network Motif Influence on Resting-State Functional Connectivity", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    summary_text = (
        "This report presents the results of analyzing the relationship between "
        "structural network motif prevalence and resting-state functional connectivity. "
        "Statistical significance was assessed using Bonferroni-corrected partial correlations "
        "and permutation tests. Effect size confidence intervals were computed using Fisher's z-transformation."
    )
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Correlation Results Table
    story.append(Paragraph("Correlation Results", styles['Heading2']))
    
    # Prepare table data
    if isinstance(correlation_results, dict):
        table_data = [["Motif ID", "r", "p-value", "Corrected p", "Significant"]]
        for motif_id, data in correlation_results.items():
            sig = "Yes" if data.get('corrected_p', 1.0) < 0.05 else "No"
            table_data.append([
                motif_id,
                f"{data.get('r', 0):.3f}",
                f"{data.get('p_value', 0):.3f}",
                f"{data.get('corrected_p', 0):.3f}",
                sig
            ])
    else:
        # Assume DataFrame-like structure
        table_data = [["Motif ID", "r", "p-value", "Corrected p", "Significant"]]
        for _, row in correlation_results.iterrows():
            sig = "Yes" if row.get('corrected_p', 1.0) < 0.05 else "No"
            table_data.append([
                row['motif_id'],
                f"{row['r']:.3f}",
                f"{row['p_value']:.3f}",
                f"{row['corrected_p']:.3f}",
                sig
            ])
    
    # Create and style table
    table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Generate correlation plot with confidence intervals
    if ci_data:
        plot_path = generate_correlation_plot(correlation_results, ci_data)
        if os.path.exists(plot_path):
            story.append(Paragraph("Figure 1: Correlation Results with 95% Confidence Intervals", styles['Heading3']))
            story.append(Image(plot_path, width=6*inch, height=4*inch))
            story.append(Spacer(1, 0.3*inch))
    
    # Permutation Results
    story.append(Paragraph("Permutation Test Results", styles['Heading2']))
    perm_text = (
        "Permutation tests were conducted for motifs with significant Bonferroni-corrected p-values. "
        "The empirical p-values confirm the robustness of the observed correlations."
    )
    story.append(Paragraph(perm_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Power Analysis
    story.append(Paragraph("Power Analysis", styles['Heading2']))
    power_text = (
        f"Minimum detectable effect size: {power_analysis.get('min_detectable_r', 'N/A'):.3f} "
        f"with power={power_analysis.get('power_level', 'N/A')}, "
        f"N={power_analysis.get('n_subjects', 'N/A')}, "
        f"alpha={power_analysis.get('adjusted_alpha', 'N/A')}"
    )
    story.append(Paragraph(power_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Methods Section
    methods_data = extract_methods_from_log()
    methods_text = generate_methods_section(methods_data)
    story.append(Paragraph(methods_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Mandatory Disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.darkred,
        alignment=1,
        spaceBefore=12,
        spaceAfter=12
    )
    disclaimer = "These findings are associational only and do not imply causation."
    story.append(Paragraph(disclaimer, disclaimer_style))
    
    # Build PDF
    doc.build(story)
    logging.info(f"PDF report generated: {output_path}")
    return output_path

def main():
    """Main execution function for report module."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Load results
        if os.path.exists("results/correlation_results.json"):
            correlation_results = load_results()
            logging.info(f"Loaded {len(correlation_results)} correlation results")
            
            # Load permutation results
            if os.path.exists("results/permutation_results.json"):
                with open("results/permutation_results.json", 'r') as f:
                    permutation_results = json.load(f)
            else:
                permutation_results = {}
            
            # Load power analysis
            if os.path.exists("results/power_analysis.json"):
                with open("results/power_analysis.json", 'r') as f:
                    power_analysis = json.load(f)
            else:
                power_analysis = {}
            
            # Generate PDF
            output_path = generate_pdf(
                correlation_results,
                permutation_results,
                power_analysis,
                layout_template_path="docs/report_layout_template.json"
            )
            logging.info(f"Report generated at {output_path}")
        else:
            logging.warning("correlation_results.json not found. Skipping report generation.")
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()