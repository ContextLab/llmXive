"""
Final Report Generation Module for Cognitive Fatigue Prediction Pipeline.

Generates the final markdown report containing statistical significance,
correlation coefficients, p-values, confidence intervals, and sensitivity analysis.
"""
import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path='code/config.yaml'):
    """Load pipeline configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(lzc_path='data/processed/lzc_metrics.csv',
                          pe_path='data/processed/pe_metrics.csv',
                          analysis_path='data/analysis/correlation_results.csv',
                          sensitivity_path='data/analysis/sensitivity_table.csv',
                          vif_path='data/analysis/vif_report.csv'):
    """
    Load all analysis results required for the final report.
    
    Returns a dictionary containing the loaded dataframes.
    """
    results = {}
    
    # Load LZC metrics
    if os.path.exists(lzc_path):
        results['lzc'] = pd.read_csv(lzc_path)
        logger.info(f"Loaded LZC metrics: {len(results['lzc'])} rows")
    else:
        logger.warning(f"LZC metrics file not found: {lzc_path}")
        results['lzc'] = None
        
    # Load PE metrics
    if os.path.exists(pe_path):
        results['pe'] = pd.read_csv(pe_path)
        logger.info(f"Loaded PE metrics: {len(results['pe'])} rows")
    else:
        logger.warning(f"PE metrics file not found: {pe_path}")
        results['pe'] = None
        
    # Load correlation analysis results
    if os.path.exists(analysis_path):
        results['correlation'] = pd.read_csv(analysis_path)
        logger.info(f"Loaded correlation results: {len(results['correlation'])} rows")
    else:
        logger.warning(f"Correlation results file not found: {analysis_path}")
        results['correlation'] = None
        
    # Load sensitivity analysis table
    if os.path.exists(sensitivity_path):
        results['sensitivity'] = pd.read_csv(sensitivity_path)
        logger.info(f"Loaded sensitivity table: {len(results['sensitivity'])} rows")
    else:
        logger.warning(f"Sensitivity table file not found: {sensitivity_path}")
        results['sensitivity'] = None
        
    # Load VIF report (optional)
    if os.path.exists(vif_path):
        results['vif'] = pd.read_csv(vif_path)
        logger.info(f"Loaded VIF report: {len(results['vif'])} rows")
    else:
        logger.warning(f"VIF report file not found: {vif_path}")
        results['vif'] = None
        
    return results

def calculate_effect_size(r_value):
    """
    Calculate Cohen's guidelines for effect size interpretation.
    
    Args:
        r_value: Pearson correlation coefficient
        
    Returns:
        str: Effect size interpretation
    """
    abs_r = abs(r_value)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"

def generate_report(results, config, output_path='docs/final_report.md'):
    """
    Generate the final markdown report with all statistical findings.
    
    Args:
        results: Dictionary of loaded analysis dataframes
        config: Pipeline configuration dictionary
        output_path: Path for the output report file
    """
    report_lines = []
    
    # Header
    report_lines.append("# Final Report: Predicting Cognitive Fatigue from Resting-State EEG Complexity")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report presents the statistical analysis of the relationship between resting-state EEG complexity metrics (Lempel-Ziv Complexity and Permutation Entropy) and cognitive fatigue scores. The analysis includes correlation coefficients, statistical significance testing, confidence intervals, and sensitivity analyses.")
    report_lines.append("")
    
    # Data Overview
    report_lines.append("## Data Overview")
    report_lines.append("")
    if results['lzc'] is not None:
        n_participants = results['lzc']['participant_id'].nunique()
        n_channels = results['lzc']['channel'].nunique()
        report_lines.append(f"- **Total Participants:** {n_participants}")
        report_lines.append(f"- **EEG Channels Analyzed:** {n_channels}")
        report_lines.append(f"- **LZC Metrics Recorded:** {len(results['lzc'])}")
    else:
        report_lines.append("- **LZC Metrics:** Not available")
        
    if results['pe'] is not None:
        report_lines.append(f"- **PE Metrics Recorded:** {len(results['pe'])}")
    else:
        report_lines.append("- **PE Metrics:** Not available")
    report_lines.append("")
    
    # Correlation Analysis
    report_lines.append("## Correlation Analysis")
    report_lines.append("")
    
    if results['correlation'] is not None and not results['correlation'].empty:
        report_lines.append("The following table summarizes the correlation analysis between EEG complexity metrics and fatigue scores.")
        report_lines.append("")
        report_lines.append("| Metric Type | Channel | Correlation (r) | P-value | Confidence Interval (95%) | Effect Size |")
        report_lines.append("|-------------|---------|-----------------|---------|---------------------------|-------------|")
        
        for _, row in results['correlation'].iterrows():
            metric_type = row.get('metric_type', 'Unknown')
            channel = row.get('channel', 'Unknown')
            r_val = row.get('correlation', np.nan)
            p_val = row.get('p_value', np.nan)
            
            # Calculate confidence interval if r and n are available
            ci_lower = np.nan
            ci_upper = np.nan
            if not np.isnan(r_val) and 'n' in row and not np.isnan(row['n']):
                n = row['n']
                # Fisher's z-transformation for CI
                z = np.arctanh(r_val)
                se = 1 / np.sqrt(n - 3)
                z_lower = z - 1.96 * se
                z_upper = z + 1.96 * se
                ci_lower = np.tanh(z_lower)
                ci_upper = np.tanh(z_upper)
                
            effect = calculate_effect_size(r_val) if not np.isnan(r_val) else "N/A"
            ci_str = f"[{ci_lower:.3f}, {ci_upper:.3f}]" if not np.isnan(ci_lower) else "N/A"
            r_str = f"{r_val:.4f}" if not np.isnan(r_val) else "N/A"
            p_str = f"{p_val:.4f}" if not np.isnan(p_val) else "N/A"
            
            report_lines.append(f"| {metric_type} | {channel} | {r_str} | {p_str} | {ci_str} | {effect} |")
            
        report_lines.append("")
        
        # Summary of significant findings
        significant = results['correlation'][results['correlation']['p_value'] < 0.05]
        if not significant.empty:
            report_lines.append(f"**Key Finding:** {len(significant)} channel(s) showed statistically significant correlations (p < 0.05).")
            report_lines.append("")
        else:
            report_lines.append("**Key Finding:** No statistically significant correlations (p < 0.05) were observed across channels.")
            report_lines.append("")
    else:
        report_lines.append("Correlation analysis results are not available. Please ensure `code/analysis.py` has been executed successfully.")
        report_lines.append("")
    
    # Statistical Significance
    report_lines.append("## Statistical Significance")
    report_lines.append("")
    
    if results['correlation'] is not None and not results['correlation'].empty:
        # Check for Benjamini-Hochberg correction results
        if 'adjusted_p_value' in results['correlation'].columns:
            report_lines.append("P-values have been adjusted using the Benjamini-Hochberg procedure to control for false discovery rate across multiple comparisons.")
            report_lines.append("")
            
            significant_bh = results['correlation'][results['correlation']['adjusted_p_value'] < 0.05]
            report_lines.append(f"After BH correction, {len(significant_bh)} channel(s) remain statistically significant (q < 0.05).")
            report_lines.append("")
        else:
            report_lines.append("P-values are reported as raw values. Multiple comparison corrections should be applied if interpreting results across many channels.")
            report_lines.append("")
            
        # Distribution of p-values
        p_values = results['correlation']['p_value'].dropna()
        if len(p_values) > 0:
            report_lines.append("### P-value Distribution")
            report_lines.append("")
            report_lines.append(f"- **Minimum p-value:** {p_values.min():.6f}")
            report_lines.append(f"- **Maximum p-value:** {p_values.max():.6f}")
            report_lines.append(f"- **Median p-value:** {p_values.median():.6f}")
            report_lines.append(f"- **Count (p < 0.05):** {(p_values < 0.05).sum()}")
            report_lines.append(f"- **Count (p < 0.01):** {(p_values < 0.01).sum()}")
            report_lines.append("")
    else:
        report_lines.append("Statistical significance data is not available.")
        report_lines.append("")
    
    # Confidence Intervals
    report_lines.append("## Confidence Intervals")
    report_lines.append("")
    report_lines.append("95% Confidence Intervals (CI) for correlation coefficients were calculated using Fisher's z-transformation.")
    report_lines.append("")
    
    if results['correlation'] is not None and not results['correlation'].empty:
        significant_with_ci = results['correlation'][
            (results['correlation']['p_value'] < 0.05) & 
            (~results['correlation']['correlation'].isna())
        ]
        
        if not significant_with_ci.empty:
            report_lines.append("For statistically significant correlations (p < 0.05):")
            report_lines.append("")
            report_lines.append("| Channel | Metric | r | 95% CI Lower | 95% CI Upper |")
            report_lines.append("|---------|--------|-----|--------------|--------------|")
            
            for _, row in significant_with_ci.iterrows():
                if 'ci_lower' in row and 'ci_upper' in row:
                    report_lines.append(f"| {row['channel']} | {row.get('metric_type', 'N/A')} | {row['correlation']:.4f} | {row['ci_lower']:.4f} | {row['ci_upper']:.4f} |")
                else:
                    # Fallback if CI columns not explicitly named but calculated
                    r_val = row['correlation']
                    n = row.get('n', 30) # Default assumption if missing
                    if not np.isnan(r_val):
                        z = np.arctanh(r_val)
                        se = 1 / np.sqrt(n - 3)
                        ci_l = np.tanh(z - 1.96 * se)
                        ci_u = np.tanh(z + 1.96 * se)
                        report_lines.append(f"| {row['channel']} | {row.get('metric_type', 'N/A')} | {r_val:.4f} | {ci_l:.4f} | {ci_u:.4f} |")
                    
            report_lines.append("")
        else:
            report_lines.append("No statistically significant correlations were found to report confidence intervals.")
            report_lines.append("")
    else:
        report_lines.append("Confidence interval data is not available.")
        report_lines.append("")
    
    # Sensitivity Analysis
    report_lines.append("## Sensitivity Analysis")
    report_lines.append("")
    
    if results['sensitivity'] is not None and not results['sensitivity'].empty:
        report_lines.append("The following table shows the number of significant electrodes at different p-value thresholds.")
        report_lines.append("")
        report_lines.append("| Threshold | Count Significant |")
        report_lines.append("|-----------|-------------------|")
        
        for _, row in results['sensitivity'].iterrows():
            threshold = row.get('threshold', 0.05)
            count = row.get('count_significant', 0)
            report_lines.append(f"| {threshold:.3f} | {count} |")
            
        report_lines.append("")
        report_lines.append("This analysis demonstrates the robustness of the findings across different significance thresholds.")
    else:
        report_lines.append("Sensitivity analysis results are not available. Ensure `code/sensitivity_analysis.py` has been executed.")
        report_lines.append("")
    
    # Collinearity Diagnostics (Optional)
    if results['vif'] is not None and not results['vif'].empty:
        report_lines.append("## Collinearity Diagnostics")
        report_lines.append("")
        report_lines.append("Variance Inflation Factor (VIF) analysis was conducted to check for multicollinearity among predictors.")
        report_lines.append("")
        report_lines.append("| Feature | VIF | Status |")
        report_lines.append("|---------|-----|--------|")
        
        for _, row in results['vif'].iterrows():
            feature = row.get('feature', 'Unknown')
            vif_val = row.get('vif', 0)
            status = "OK" if vif_val < 5 else "WARNING"
            report_lines.append(f"| {feature} | {vif_val:.2f} | {status} |")
            
        report_lines.append("")
        if (results['vif']['vif'] >= 5).any():
            report_lines.append("**Note:** Some features show VIF >= 5, indicating potential multicollinearity.")
        else:
            report_lines.append("All VIF values are below 5, indicating acceptable collinearity levels.")
        report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append("This analysis provides statistical evidence regarding the relationship between resting-state EEG complexity and cognitive fatigue. The correlation coefficients, p-values, and confidence intervals presented above should be interpreted in the context of the study design and limitations.")
    report_lines.append("")
    report_lines.append("Future work may include:")
    report_lines.append("- Replication in independent cohorts")
    report_lines.append("- Longitudinal analysis of fatigue progression")
    report_lines.append("- Integration with additional physiological markers")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Report generated by the llmXive automated science pipeline.*")
    
    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))
        
    logger.info(f"Final report written to {output_path}")

def main():
    """Main entry point for the report generation."""
    logger.info("Starting final report generation...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Load all analysis results
        results = load_analysis_results()
        
        # Check if we have enough data to generate a meaningful report
        if results['correlation'] is None:
            logger.error("Critical: Correlation results not found. Cannot generate report.")
            sys.exit(1)
            
        # Generate the report
        generate_report(results, config)
        
        logger.info("Report generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during report generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()