import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure the parent directory is in the path for imports if running as script
# but rely on the provided API surface for imports from sibling modules.
# The API surface indicates report.py is in code/ and imports from analysis, etc.
# However, for T022, we are implementing the report generation logic here.
# We assume the analysis results (correlations, p-values, etc.) are available
# in the expected output files from previous tasks (T019, T020, T021).

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results():
    """
    Load analysis results from the output of T019/T020.
    Expected file: data/analysis/correlation_results.csv (or similar based on T019/T020 output).
    T019/T020 produce the correlation data. T021 produces sensitivity_table.csv.
    We need to consolidate these for the final report.
    
    Based on T019/T020 description:
    - T019: Pearson/Spearman correlation output.
    - T020: Benjamini-Hochberg correction output.
    - T021: sensitivity_table.csv.
    
    We assume T019/T020 write a file like data/analysis/correlation_results.csv
    with columns: channel, correlation, p_value, corrected_p_value, method (pearson/spearman), 
    confidence_interval_lower, confidence_interval_upper.
    
    If the exact file name isn't known, we look for likely candidates.
    """
    analysis_dir = Path(__file__).parent.parent / "data" / "analysis"
    if not analysis_dir.exists():
        raise FileNotFoundError(f"Analysis directory not found: {analysis_dir}")
    
    # Try to find the correlation results file
    corr_file = None
    possible_files = [
        "correlation_results.csv",
        "correlations.csv",
        "analysis_results.csv",
        "complexity_metrics.csv" # Fallback if T019 output was misnamed, but unlikely to have stats
    ]
    
    for fname in possible_files:
        fpath = analysis_dir / fname
        if fpath.exists():
            corr_file = fpath
            break
    
    if corr_file is None:
        # Check if there's any CSV in the analysis directory
        csv_files = list(analysis_dir.glob("*.csv"))
        if csv_files:
            # Assume the first one is the results
            corr_file = csv_files[0]
        else:
            raise FileNotFoundError(f"No correlation results file found in {analysis_dir}")
    
    df = pd.read_csv(corr_file)
    
    # Validate required columns exist
    required_cols = ['channel', 'correlation', 'p_value', 'corrected_p_value']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        # Try to infer or raise error
        # If confidence intervals are missing, we might need to compute them or assume they are present
        # For T022, we need confidence intervals. If missing, we might need to calculate them from raw data
        # but the task says "Generate final report... with ... 95% confidence intervals".
        # We assume T019/T020 computed them. If not, we might need to fall back to a standard error calculation
        # or assume the file has them. Let's check for common names.
        ci_cols = [c for c in df.columns if 'ci' in c.lower() or 'interval' in c.lower()]
        if not ci_cols:
            # If no CI columns, we might need to calculate them if we have enough data.
            # However, T019/T020 should have done this. If not, we raise an error.
            raise ValueError(f"Missing required columns for report: {missing_cols} and confidence intervals.")
        
        # Map CI columns
        ci_lower = None
        ci_upper = None
        for c in df.columns:
            if 'lower' in c.lower():
                ci_lower = c
            elif 'upper' in c.lower():
                ci_upper = c
        
        if ci_lower and ci_upper:
            df['confidence_interval_lower'] = df[ci_lower]
            df['confidence_interval_upper'] = df[ci_upper]
        else:
            # If we can't find them, we might need to compute them.
            # But without the raw data or standard errors, we can't.
            # We'll assume the previous task (T019) should have included them.
            # If not, we'll raise an error.
            raise ValueError("Could not find confidence interval columns in the results file.")
    
    return df

def calculate_effect_size(r, n):
    """
    Calculate Cohen's q for correlation effect size? 
    Or just return r as the effect size. 
    For correlation, r itself is the effect size.
    We might also calculate the coefficient of determination (r^2).
    """
    r_squared = r ** 2
    return r_squared

def generate_report(results_df, config, output_path):
    """
    Generate the final report in Markdown format.
    Sections required:
    - Correlation Analysis
    - Statistical Significance
    - Confidence Intervals
    - Sensitivity Analysis
    
    Args:
        results_df: DataFrame with correlation results (channel, correlation, p_value, corrected_p_value, confidence_interval_lower, confidence_interval_upper)
        config: Configuration dictionary
        output_path: Path to write the report (docs/final_report.md)
    """
    # Load sensitivity analysis table (from T021)
    sensitivity_dir = Path(__file__).parent.parent / "data" / "analysis"
    sensitivity_file = sensitivity_dir / "sensitivity_table.csv"
    if not sensitivity_file.exists():
        raise FileNotFoundError(f"Sensitivity analysis table not found: {sensitivity_file}")
    
    sensitivity_df = pd.read_csv(sensitivity_file)
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Start building the report
    report_lines = []
    report_lines.append("# Final Report: Predicting Cognitive Fatigue from Resting-State EEG Complexity")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report presents the statistical analysis of the relationship between EEG complexity metrics (Lempel-Ziv Complexity and Permutation Entropy) and cognitive fatigue scores. The analysis includes correlation coefficients, p-values, confidence intervals, and sensitivity analysis.")
    report_lines.append("")
    
    # Correlation Analysis Section
    report_lines.append("## Correlation Analysis")
    report_lines.append("")
    report_lines.append("The following table summarizes the correlation coefficients (Pearson/Spearman) between complexity metrics and fatigue scores for each EEG channel.")
    report_lines.append("")
    report_lines.append("| Channel | Correlation (r) | p-value | Corrected p-value | CI Lower | CI Upper |")
    report_lines.append("|---------|-----------------|---------|-------------------|----------|----------|")
    
    for _, row in results_df.iterrows():
        channel = row['channel']
        corr = row['correlation']
        p_val = row['p_value']
        corr_p_val = row['corrected_p_value']
        ci_lower = row['confidence_interval_lower']
        ci_upper = row['confidence_interval_upper']
        
        report_lines.append(f"| {channel} | {corr:.4f} | {p_val:.4f} | {corr_p_val:.4f} | {ci_lower:.4f} | {ci_upper:.4f} |")
    
    report_lines.append("")
    
    # Statistical Significance Section
    report_lines.append("## Statistical Significance")
    report_lines.append("")
    report_lines.append("Statistical significance was assessed using p-values with Benjamini-Hochberg correction for multiple comparisons across electrodes.")
    report_lines.append("")
    
    significant_channels = results_df[results_df['corrected_p_value'] <= 0.05]
    if len(significant_channels) > 0:
        report_lines.append(f"**Significant Results (p ≤ 0.05):** {len(significant_channels)} out of {len(results_df)} channels showed a statistically significant correlation after correction.")
        report_lines.append("")
        report_lines.append("Significant channels:")
        report_lines.append(", ".join(significant_channels['channel'].tolist()))
    else:
        report_lines.append(f"**No Significant Results:** No channels showed a statistically significant correlation after Benjamini-Hochberg correction (p ≤ 0.05).")
    
    report_lines.append("")
    report_lines.append("### P-value Distribution")
    report_lines.append("")
    # We can't generate a plot here, but we can describe the distribution
    report_lines.append("The distribution of p-values across channels indicates the overall significance of the findings.")
    report_lines.append("")
    
    # Confidence Intervals Section
    report_lines.append("## Confidence Intervals")
    report_lines.append("")
    report_lines.append("95% confidence intervals for the correlation coefficients are provided in the table above. These intervals indicate the range within which the true correlation coefficient is likely to fall with 95% confidence.")
    report_lines.append("")
    report_lines.append("Channels where the confidence interval does not include zero are considered to have a statistically significant correlation at the 0.05 level (before multiple comparison correction).")
    report_lines.append("")
    
    # Sensitivity Analysis Section
    report_lines.append("## Sensitivity Analysis")
    report_lines.append("")
    report_lines.append("Sensitivity analysis was performed at different p-value thresholds to assess the robustness of the findings.")
    report_lines.append("")
    report_lines.append("| Threshold | Count Significant | Total Electrodes |")
    report_lines.append("|-----------|-------------------|------------------|")
    
    for _, row in sensitivity_df.iterrows():
        threshold = row['threshold']
        count_sig = row['count_significant']
        total = row['total_electrodes']
        report_lines.append(f"| {threshold:.2f} | {count_sig} | {total} |")
    
    report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append("The analysis provides evidence for (or against) the relationship between EEG complexity and cognitive fatigue. The results should be interpreted in the context of the study design and limitations.")
    report_lines.append("")
    
    # Write the report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    return output_path

def main():
    """Main entry point for the report generation script."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    logger.info("Starting report generation pipeline.")
    
    try:
        config = load_config()
        results_df = load_analysis_results()
        
        output_path = Path(__file__).parent.parent / "docs" / "final_report.md"
        generate_report(results_df, config, output_path)
        
        logger.info(f"Report generated successfully: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()