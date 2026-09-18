"""
Report generation module for the Cognitive Fatigue EEG Analysis Pipeline.
Agingates all analysis results into a final markdown report.
"""
import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np

# Import logging utility from the shared module
# Note: The API surface shows `code/utils/logging.py` defines `get_logger`
# and `log_operation`. We import them to ensure consistency.
try:
    from utils.logging import get_logger, log_operation
except ImportError:
    # Fallback for direct execution if path is not set up correctly
    # In a real pipeline, utils.logging should be on the path
    import logging
    def get_logger(name, *args, **kwargs):
        return logging.getLogger(name)
    def log_operation(op, **kwargs):
        return None

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(file_path):
    """Load a CSV file containing analysis results."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Analysis results file not found: {file_path}")
    return pd.read_csv(file_path)

def load_sensitivity_table(file_path):
    """Load the sensitivity analysis table."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Sensitivity table not found: {file_path}")
    return pd.read_csv(file_path)

def calculate_effect_size(coef, std_err):
    """Calculate Cohen's d-like effect size (simplified for regression context)."""
    if std_err is None or std_err == 0:
        return 0.0
    return float(coef) / float(std_err)

def render_markdown_table(df):
    """
    Render a pandas DataFrame as a Markdown table.
    Handles potential pandas version issues gracefully.
    """
    # Avoid deprecated options that might cause errors in newer pandas versions
    try:
        # Only set if the option exists, otherwise ignore
        if hasattr(pd.options, 'mode') and hasattr(pd.options.mode, 'future_infer_string'):
            pd.options.mode.future_infer_string = False
    except (AttributeError, pd.errors.OptionError):
        # Option does not exist or is deprecated; proceed without setting it
        pass

    # Convert to markdown string
    return df.to_markdown(index=False)

def generate_report(
    correlation_df,
    ancova_df,
    bh_df,
    sensitivity_df,
    vif_log_path,
    complexity_metrics_path,
    output_path
):
    """
    Generate the final markdown report.
    """
    report_lines = []
    report_lines.append("# Final Report: Predicting Cognitive Fatigue from Resting-State EEG Complexity")
    report_lines.append("")
    report_lines.append("This report summarizes the statistical analysis of EEG complexity metrics (Lempel-Ziv Complexity) ")
    report_lines.append("correlated with cognitive fatigue ratings.")
    report_lines.append("")

    # 1. Correlation Results
    report_lines.append("## Correlation Results")
    report_lines.append("")
    report_lines.append("Pearson and Spearman correlation coefficients between complexity deltas and fatigue deltas.")
    report_lines.append("")
    if correlation_df is not None and not correlation_df.empty:
        report_lines.append(render_markdown_table(correlation_df))
        report_lines.append("")
    else:
        report_lines.append("*No correlation data available.*")
        report_lines.append("")

    # 2. ANCOVA Results
    report_lines.append("## ANCOVA Results")
    report_lines.append("")
    report_lines.append("Analysis of Covariance controlling for pre-fatigue complexity and other covariates.")
    report_lines.append("")
    if ancova_df is not None and not ancova_df.empty:
        report_lines.append(render_markdown_table(ancova_df))
        report_lines.append("")
    else:
        report_lines.append("*No ANCOVA data available.*")
        report_lines.append("")

    # 3. Benjamini-Hochberg Correction
    report_lines.append("## Multiple Comparison Correction (Benjamini-Hochberg)")
    report_lines.append("")
    report_lines.append("Corrected p-values for multiple comparisons across electrodes.")
    report_lines.append("")
    if bh_df is not None and not bh_df.empty:
        report_lines.append(render_markdown_table(bh_df))
        report_lines.append("")
    else:
        report_lines.append("*No BH correction data available.*")
        report_lines.append("")

    # 4. Sensitivity Analysis
    report_lines.append("## Sensitivity Analysis")
    report_lines.append("")
    report_lines.append("Count of significant electrodes at p ≤ 0.05 and p ≤ 0.01 thresholds.")
    report_lines.append("")
    if sensitivity_df is not None and not sensitivity_df.empty:
        report_lines.append(render_markdown_table(sensitivity_df))
        report_lines.append("")
    else:
        report_lines.append("*No sensitivity analysis data available.*")
        report_lines.append("")

    # 5. VIF Diagnostics
    report_lines.append("## VIF Diagnostics")
    report_lines.append("")
    report_lines.append("Variance Inflation Factor (VIF) diagnostics for collinearity checks.")
    report_lines.append("Target: VIF < 5 for all predictors.")
    report_lines.append("")
    if vif_log_path and os.path.exists(vif_log_path):
        with open(vif_log_path, 'r') as f:
            log_content = f.read()
        report_lines.append("```")
        report_lines.append(log_content)
        report_lines.append("```")
        report_lines.append("")
    else:
        report_lines.append("*VIF diagnostics log not found.*")
        report_lines.append("")

    # 6. Data Sources
    report_lines.append("## Data Sources")
    report_lines.append("")
    report_lines.append(f"- **Complexity Metrics**: {complexity_metrics_path}")
    report_lines.append(f"- **Correlation Results**: `data/analysis/correlation_results.csv`")
    report_lines.append(f"- **BH Corrected P-values**: `data/analysis/bh_corrected_pvalues.csv`")
    report_lines.append(f"- **Sensitivity Table**: `data/analysis/sensitivity_table.csv`")
    report_lines.append(f"- **VIF Diagnostics**: `data/analysis/vif_diagnostics.log`")
    report_lines.append("")

    # Write to file
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"Report generated successfully: {output_path}")

def main():
    """Main entry point for report generation."""
    logger = get_logger("report")
    log_operation("start_report_generation")

    try:
        config = load_config()
        output_path = "docs/final_report.md"

        # Define paths based on task requirements
        correlation_path = "data/analysis/correlation_results.csv"
        ancova_path = "data/analysis/ancova_results.csv"
        bh_path = "data/analysis/bh_corrected_pvalues.csv"
        sensitivity_path = "data/analysis/sensitivity_table.csv"
        vif_log_path = "data/analysis/vif_diagnostics.log"
        complexity_path = "data/analysis/complexity_metrics.csv"

        # Load data
        correlation_df = None
        if os.path.exists(correlation_path):
            correlation_df = load_analysis_results(correlation_path)

        ancova_df = None
        if os.path.exists(ancova_path):
            ancova_df = load_analysis_results(ancova_path)

        bh_df = None
        if os.path.exists(bh_path):
            bh_df = load_analysis_results(bh_path)

        sensitivity_df = None
        if os.path.exists(sensitivity_path):
            sensitivity_df = load_sensitivity_table(sensitivity_path)

        # Generate report
        generate_report(
            correlation_df=correlation_df,
            ancova_df=ancova_df,
            bh_df=bh_df,
            sensitivity_df=sensitivity_df,
            vif_log_path=vif_log_path,
            complexity_metrics_path=complexity_path,
            output_path=output_path
        )

        log_operation("report_generation_complete", output_file=output_path)

    except Exception as e:
        log_operation("report_generation_failed", error=str(e))
        raise

if __name__ == "__main__":
    main()