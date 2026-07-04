"""
Generate comprehensive PDF report for the sustainable agriculture adoption study.

This script produces a PDF report containing:
- Descriptive statistics
- Regression table with coefficients and p-values
- VIF diagnostics
- ROC curve plot
- Mediation analysis results
- Sensitivity analysis (E-values and Rosenbaum bounds)
- Validity metrics (Cronbach's alpha, factor loadings)
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for PDF generation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Import from sibling modules
from config import get_config, get_data_path
from logging_config import get_logger

# Setup logging
logger = get_logger(__name__)

def load_cleaned_data() -> pd.DataFrame:
    """Load cleaned data from the processed data directory."""
    config = get_config()
    data_path = get_data_path()
    cleaned_file = data_path / 'processed' / 'cleaned_data.csv'
    
    if not cleaned_file.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_file}")
    
    logger.info(f"Loading cleaned data from {cleaned_file}")
    return pd.read_csv(cleaned_file)

def load_engineered_data() -> pd.DataFrame:
    """Load engineered data from the processed data directory."""
    config = get_config()
    data_path = get_data_path()
    engineered_file = data_path / 'processed' / 'engineered_data.csv'
    
    if not engineered_file.exists():
        raise FileNotFoundError(f"Engineered data file not found: {engineered_file}")
    
    logger.info(f"Loading engineered data from {engineered_file}")
    return pd.read_csv(engineered_file)

def load_model_results() -> Dict[str, Any]:
    """Load model analysis results from the results directory."""
    config = get_config()
    data_path = get_data_path()
    results_file = data_path.parent / 'results' / 'model_results.yaml'
    
    if not results_file.exists():
        # Try alternative location
        results_file = data_path / 'model_results.yaml'
    
    if not results_file.exists():
        raise FileNotFoundError(f"Model results file not found: {results_file}")
    
    logger.info(f"Loading model results from {results_file}")
    with open(results_file, 'r') as f:
        return yaml.safe_load(f)

def load_validity_metrics() -> Dict[str, Any]:
    """Load validity metrics from the results directory."""
    config = get_config()
    data_path = get_data_path()
    validity_file = data_path.parent / 'results' / 'validity_metrics.yaml'
    
    if not validity_file.exists():
        # Try alternative location
        validity_file = data_path / 'validity_metrics.yaml'
    
    if not validity_file.exists():
        raise FileNotFoundError(f"Validity metrics file not found: {validity_file}")
    
    logger.info(f"Loading validity metrics from {validity_file}")
    with open(validity_file, 'r') as f:
        return yaml.safe_load(f)

def load_modeling_log() -> Dict[str, Any]:
    """Load the modeling log."""
    config = get_config()
    data_path = get_data_path()
    log_file = data_path.parent / 'modeling_log.yaml'
    
    if not log_file.exists():
        raise FileNotFoundError(f"Modeling log file not found: {log_file}")
    
    with open(log_file, 'r') as f:
        return yaml.safe_load(f)

def generate_descriptive_stats(df: pd.DataFrame) -> str:
    """Generate descriptive statistics section."""
    lines = []
    lines.append("## Descriptive Statistics")
    lines.append("")
    
    # Numerical variables
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        lines.append("### Numerical Variables")
        lines.append("")
        stats = df[num_cols].describe()
        lines.append(stats.to_string())
        lines.append("")
    
    # Categorical variables
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        lines.append("### Categorical Variables")
        lines.append("")
        for col in cat_cols[:5]:  # Limit to first 5 categorical columns
            lines.append(f"**{col}**:")
            value_counts = df[col].value_counts()
            lines.append(value_counts.to_string())
            lines.append("")
    
    return "\n".join(lines)

def generate_regression_table(results: Dict[str, Any]) -> str:
    """Generate regression table section."""
    lines = []
    lines.append("## Logistic Regression Results")
    lines.append("")
    lines.append("### Model Summary")
    lines.append("")
    
    if 'model_summary' in results:
        summary = results['model_summary']
        for key, value in summary.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")
    
    lines.append("### Coefficients")
    lines.append("")
    
    if 'coefficients' in results:
        coef_df = pd.DataFrame(results['coefficients'])
        # Ensure all necessary columns exist
        required_cols = ['variable', 'coef', 'std_err', 'z', 'P>|z|', '[95.0% Conf. Interval]']
        for col in required_cols:
            if col not in coef_df.columns:
                coef_df[col] = 'N/A'
        
        # Format the table
        lines.append("| Variable | Coef | Std Err | z | P>|z| | 95% CI |")
        lines.append("|----------|------|---------|---|-------|--------|")
        
        for _, row in coef_df.iterrows():
            coef = row['coef'] if pd.notna(row['coef']) else 'N/A'
            std_err = row['std_err'] if pd.notna(row['std_err']) else 'N/A'
            z_val = row['z'] if pd.notna(row['z']) else 'N/A'
            p_val = row['P>|z|'] if pd.notna(row['P>|z|']) else 'N/A'
            ci = row['[95.0% Conf. Interval]'] if pd.notna(row['[95.0% Conf. Interval]']) else 'N/A'
            
            lines.append(f"| {row['variable']} | {coef:.4f} | {std_err:.4f} | {z_val:.4f} | {p_val:.4f} | {ci} |")
        lines.append("")
    
    if 'fdr_results' in results:
        lines.append("### FDR-Corrected P-values")
        lines.append("")
        fdr_df = pd.DataFrame(results['fdr_results'])
        lines.append("| Variable | Original P-value | FDR-Adjusted P-value | Significant (q ≤ 0.10) |")
        lines.append("|----------|------------------|----------------------|------------------------|")
        
        for _, row in fdr_df.iterrows():
            sig = "Yes" if row.get('significant', False) else "No"
            lines.append(f"| {row['variable']} | {row['original_p']:.4f} | {row['adjusted_p']:.4f} | {sig} |")
        lines.append("")
    
    return "\n".join(lines)

def generate_vif_section(results: Dict[str, Any]) -> str:
    """Generate VIF diagnostics section."""
    lines = []
    lines.append("## VIF Diagnostics")
    lines.append("")
    
    if 'vif_results' in results:
        vif_df = pd.DataFrame(results['vif_results'])
        lines.append("| Variable | VIF | Flag |")
        lines.append("|----------|-----|------|")
        
        for _, row in vif_df.iterrows():
            vif_val = row['vif'] if pd.notna(row['vif']) else 'N/A'
            flag = "⚠️ Collinearity" if row.get('flag', False) else "✓ OK"
            lines.append(f"| {row['variable']} | {vif_val:.2f} | {flag} |")
        lines.append("")
        
        # Summary
        max_vif = vif_df['vif'].max() if 'vif' in vif_df.columns else 0
        lines.append(f"**Maximum VIF**: {max_vif:.2f}")
        lines.append("")
        if max_vif >= 5:
            lines.append("⚠️ **Warning**: Some predictors have VIF ≥ 5, indicating potential multicollinearity.")
        else:
            lines.append("✓ No significant multicollinearity detected (all VIF < 5).")
        lines.append("")
    
    return "\n".join(lines)

def generate_roc_section(results: Dict[str, Any], output_dir: Path) -> str:
    """Generate ROC curve section and save plot."""
    lines = []
    lines.append("## ROC Curve Analysis")
    lines.append("")
    
    if 'roc_metrics' in results:
        roc = results['roc_metrics']
        lines.append(f"- **AUC**: {roc.get('auc', 'N/A'):.4f}" if isinstance(roc.get('auc'), (int, float)) else f"- **AUC**: {roc.get('auc', 'N/A')}")
        lines.append(f"- **Accuracy**: {roc.get('accuracy', 'N/A'):.4f}" if isinstance(roc.get('accuracy'), (int, float)) else f"- **Accuracy**: {roc.get('accuracy', 'N/A')}")
        lines.append(f"- **Sensitivity**: {roc.get('sensitivity', 'N/A'):.4f}" if isinstance(roc.get('sensitivity'), (int, float)) else f"- **Sensitivity**: {roc.get('sensitivity', 'N/A')}")
        lines.append(f"- **Specificity**: {roc.get('specificity', 'N/A'):.4f}" if isinstance(roc.get('specificity'), (int, float)) else f"- **Specificity**: {roc.get('specificity', 'N/A')}")
        lines.append("")
    
    # Create ROC plot
    if 'roc_data' in results and results['roc_data']:
        roc_data = results['roc_data']
        fpr = roc_data.get('fpr', [])
        tpr = roc_data.get('tpr', [])
        
        if fpr and tpr:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(fpr, tpr, label=f'ROC Curve (AUC = {results.get("roc_metrics", {}).get("auc", 0):.2f})', color='blue', linewidth=2)
            ax.plot([0, 1], [0, 1], 'k--', label='Random Chance', linewidth=1)
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            ax.set_title('Receiver Operating Characteristic (ROC) Curve')
            ax.legend(loc='lower right')
            ax.grid(True, alpha=0.3)
            
            # Save plot
            plot_path = output_dir / 'roc_curve.png'
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            lines.append(f"**Figure 1**: ROC Curve (saved to {plot_path.name})")
            lines.append("")
    
    return "\n".join(lines)

def generate_mediation_section(results: Dict[str, Any]) -> str:
    """Generate mediation analysis section."""
    lines = []
    lines.append("## Mediation Analysis")
    lines.append("")
    lines.append("*Note: Results are exploratory as per study design.*")
    lines.append("")
    
    if 'mediation_results' in results:
        med = results['mediation_results']
        
        lines.append("### Baron & Kenny Approach")
        lines.append("")
        lines.append(f"- **Total Effect (c)**: {med.get('total_effect', 'N/A'):.4f}" if isinstance(med.get('total_effect'), (int, float)) else f"- **Total Effect (c)**: {med.get('total_effect', 'N/A')}")
        lines.append(f"- **Direct Effect (c')**: {med.get('direct_effect', 'N/A'):.4f}" if isinstance(med.get('direct_effect'), (int, float)) else f"- **Direct Effect (c')**: {med.get('direct_effect', 'N/A')}")
        lines.append(f"- **Indirect Effect (ab)**: {med.get('indirect_effect', 'N/A'):.4f}" if isinstance(med.get('indirect_effect'), (int, float)) else f"- **Indirect Effect (ab)**: {med.get('indirect_effect', 'N/A')}")
        
        if 'bootstrap_ci' in med:
            ci = med['bootstrap_ci']
            lines.append(f"- **95% Bootstrap CI for Indirect Effect**: [{ci.get('lower', 'N/A'):.4f}, {ci.get('upper', 'N/A'):.4f}]" if all(isinstance(ci.get(k), (int, float)) for k in ['lower', 'upper']) else f"- **95% Bootstrap CI for Indirect Effect**: [{ci.get('lower', 'N/A')}, {ci.get('upper', 'N/A')}]")
        lines.append("")
    
    return "\n".join(lines)

def generate_sensitivity_section(results: Dict[str, Any], log: Dict[str, Any]) -> str:
    """Generate sensitivity analysis section."""
    lines = []
    lines.append("## Sensitivity Analysis")
    lines.append("")
    
    # E-values
    if 'sensitivity_analysis' in results:
        sens = results['sensitivity_analysis']
        
        lines.append("### E-values")
        lines.append("")
        if 'evalues' in sens:
            ev = sens['evalues']
            lines.append(f"- **E-value for point estimate**: {ev.get('point_estimate', 'N/A'):.4f}" if isinstance(ev.get('point_estimate'), (int, float)) else f"- **E-value for point estimate**: {ev.get('point_estimate', 'N/A')}")
            lines.append(f"- **E-value for CI limit**: {ev.get('ci_limit', 'N/A'):.4f}" if isinstance(ev.get('ci_limit'), (int, float)) else f"- **E-value for CI limit**: {ev.get('ci_limit', 'N/A')}")
        lines.append("")
        
        lines.append("### Rosenbaum Bounds")
        lines.append("")
        if 'rosenbaum_bounds' in sens:
            rb = sens['rosenbaum_bounds']
            lines.append("Gamma values tested and corresponding bounds:")
            lines.append("")
            lines.append("| Gamma | Significance |")
            lines.append("|-------|--------------|")
            for gamma, sig in rb.items():
                lines.append(f"| {gamma} | {'Significant' if sig else 'Not Significant'} |")
        lines.append("")
    
    return "\n".join(lines)

def generate_validity_section(validity_metrics: Dict[str, Any]) -> str:
    """Generate validity metrics section."""
    lines = []
    lines.append("## Validity Metrics")
    lines.append("")
    
    # Cronbach's Alpha
    lines.append("### Reliability (Cronbach's Alpha)")
    lines.append("")
    if 'cronbach_alpha' in validity_metrics:
        alpha = validity_metrics['cronbach_alpha']
        lines.append(f"- **Cronbach's α**: {alpha:.4f}" if isinstance(alpha, (int, float)) else f"- **Cronbach's α**: {alpha}")
        lines.append("")
        if isinstance(alpha, (int, float)):
            if alpha >= 0.9:
                lines.append("✓ Excellent internal consistency")
            elif alpha >= 0.8:
                lines.append("✓ Good internal consistency")
            elif alpha >= 0.7:
                lines.append("✓ Acceptable internal consistency")
            elif alpha >= 0.6:
                lines.append("⚠️ Marginal internal consistency")
            else:
                lines.append("⚠️ Poor internal consistency")
        lines.append("")
    
    # Factor Analysis
    lines.append("### Exploratory Factor Analysis (EFA)")
    lines.append("")
    if 'efa_results' in validity_metrics:
        efa = validity_metrics['efa_results']
        lines.append(f"- **Extraction Method**: {efa.get('extraction_method', 'N/A')}")
        lines.append(f"- **Rotation Method**: {efa.get('rotation_method', 'N/A')}")
        lines.append(f"- **Factors Retained (Kaiser's rule)**: {efa.get('factors_retained', 'N/A')}")
        lines.append("")
        
        if 'factor_loadings' in efa:
            lines.append("**Factor Loadings:**")
            lines.append("")
            loadings = efa['factor_loadings']
            if isinstance(loadings, list):
                for loading in loadings:
                    var = loading.get('variable', 'N/A')
                    factor = loading.get('factor', 'N/A')
                    value = loading.get('loading', 'N/A')
                    lines.append(f"- {var} on Factor {factor}: {value:.4f}" if isinstance(value, (int, float)) else f"- {var} on Factor {factor}: {value}")
            lines.append("")
    
    # Convergent Validity
    if 'convergent_validity' in validity_metrics:
        conv = validity_metrics['convergent_validity']
        lines.append("### Convergent Validity")
        lines.append("")
        lines.append(f"- **Status**: {conv.get('status', 'N/A')}")
        lines.append("")
        if 'correlations' in conv:
            lines.append("**Correlations with related constructs:**")
            lines.append("")
            for construct, corr in conv['correlations'].items():
                lines.append(f"- {construct}: {corr:.4f}" if isinstance(corr, (int, float)) else f"- {construct}: {corr}")
            lines.append("")
    
    return "\n".join(lines)

def generate_report_header() -> str:
    """Generate report header with metadata."""
    lines = []
    lines.append("# Sustainable Agricultural Practices Adoption Study")
    lines.append("")
    lines.append(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)

def generate_pdf_report():
    """Main function to generate the PDF report."""
    try:
        config = get_config()
        data_path = get_data_path()
        results_dir = data_path.parent / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = results_dir / 'study_report.pdf'
        logger.info(f"Generating PDF report: {report_path}")
        
        # Load all required data
        logger.info("Loading data...")
        cleaned_data = load_cleaned_data()
        engineered_data = load_engineered_data()
        model_results = load_model_results()
        validity_metrics = load_validity_metrics()
        modeling_log = load_modeling_log()
        
        # Generate report content
        report_content = []
        report_content.append(generate_report_header())
        report_content.append(generate_descriptive_stats(cleaned_data))
        report_content.append(generate_regression_table(model_results))
        report_content.append(generate_vif_section(model_results))
        report_content.append(generate_roc_section(model_results, results_dir))
        report_content.append(generate_mediation_section(model_results))
        report_content.append(generate_sensitivity_section(model_results, modeling_log))
        report_content.append(generate_validity_section(validity_metrics))
        
        # Create PDF
        with PdfPages(report_path) as pdf:
            # Create a figure for the report
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis('off')
            
            # Add content to the page
            text = "\n".join(report_content)
            # Split text into lines for better formatting
            lines = text.split('\n')
            
            y = 0.95
            line_height = 0.04
            page_height = 0.95
            
            current_page = 1
            current_lines = []
            current_y = y
            
            for line in lines:
                # Check if we need a new page
                if current_y - line_height < 0.05:
                    # Save current page
                    text_obj = ax.text(0.05, current_y, '\n'.join(current_lines), 
                                     fontsize=8, va='top', family='monospace',
                                     transform=ax.transAxes, wrap=True)
                    pdf.savefig(fig)
                    plt.close(fig)
                    
                    # Start new page
                    fig, ax = plt.subplots(figsize=(8.5, 11))
                    ax.axis('off')
                    current_page += 1
                    current_y = y
                    current_lines = [line]
                else:
                    current_lines.append(line)
                    current_y -= line_height
            
            # Save last page
            if current_lines:
                text_obj = ax.text(0.05, current_y, '\n'.join(current_lines), 
                                 fontsize=8, va='top', family='monospace',
                                 transform=ax.transAxes, wrap=True)
                pdf.savefig(fig)
                plt.close(fig)
        
        logger.info(f"PDF report successfully generated: {report_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
        raise

def main():
    """Entry point for the report generation script."""
    logger.info("Starting report generation...")
    generate_pdf_report()
    logger.info("Report generation completed.")

if __name__ == "__main__":
    main()
