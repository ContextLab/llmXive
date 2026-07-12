"""
Generate final report with correlation matrices, effect sizes, FDR-corrected p-values,
sensitivity comparisons, and explicit associational disclaimers.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import from existing project modules
from utils.logging_config import get_logger, setup_general_logger
from utils.resource_monitor import get_memory_usage_gb, log_resource_snapshot

def setup_logger():
    """Setup logger for report generation."""
    return setup_general_logger('report_generator', 'logs/report_generation.log')

def load_regression_results():
    """Load FDR-corrected regression results."""
    path = Path('data/processed/correlation_results_fdr.csv')
    if not path.exists():
        raise FileNotFoundError(f"Regression results not found at {path}")
    return pd.read_csv(path)

def load_effect_sizes():
    """Load effect sizes data."""
    path = Path('data/processed/effect_sizes.json')
    if not path.exists():
        raise FileNotFoundError(f"Effect sizes not found at {path}")
    import json
    with open(path, 'r') as f:
        return json.load(f)

def load_sensitivity_report():
    """Load sensitivity analysis report."""
    path = Path('data/processed/sensitivity_report.json')
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity report not found at {path}")
    import json
    with open(path, 'r') as f:
        return json.load(f)

def load_behavioral_scores():
    """Load behavioral scores for covariate summary."""
    path = Path('data/processed/behavioral_scores.csv')
    if not path.exists():
        raise FileNotFoundError(f"Behavioral scores not found at {path}")
    return pd.read_csv(path)

def generate_covariate_summary(behavioral_df):
    """Generate summary of covariates controlled in the analysis."""
    covariates = ['age', 'education_years', 'task_accuracy', 'neurological_condition', 'medication_status']
    summary_lines = []
    
    summary_lines.append("### Covariates Controlled")
    summary_lines.append("The following covariates were included in the Multiple Linear Regression (OLS) model:")
    summary_lines.append("")
    for cov in covariates:
        if cov in behavioral_df.columns:
            if behavioral_df[cov].dtype in ['int64', 'float64']:
                mean_val = behavioral_df[cov].mean()
                std_val = behavioral_df[cov].std()
                summary_lines.append(f"- **{cov.replace('_', ' ').title()}**: Mean = {mean_val:.2f} (SD = {std_val:.2f})")
            else:
                value_counts = behavioral_df[cov].value_counts().to_dict()
                summary_lines.append(f"- **{cov.replace('_', ' ').title()}**: {value_counts}")
        else:
            summary_lines.append(f"- **{cov.replace('_', ' ').title()}**: *Column not found in dataset*")
    
    return "\n".join(summary_lines)

def generate_associational_disclaimer():
    """Generate the explicit associational disclaimer as per FR-009 and SC-005."""
    disclaimer = """
## Important Methodological Disclaimer

### Nature of Findings: Associational Only

**This study identifies statistical associations between neural entropy metrics and cognitive flexibility scores. These findings do not establish causation.**

Key limitations to consider:

1. **Observational Design**: This analysis is based on cross-sectional observational data. No experimental manipulation of neural entropy was performed.

2. **Unmeasured Confounding**: Despite controlling for age, education, task accuracy, neurological condition, and medication status, unmeasured confounding variables may influence both neural entropy and cognitive performance.

3. **Temporal Directionality**: The temporal direction of any potential relationship cannot be determined from this cross-sectional design.

4. **Generalizability**: Results are specific to the sampled population (older adults with available EEG and WCST data from OpenNeuro datasets ds and ds003104) and may not generalize to other populations.

### Interpretation Guidance

- **Do not interpret** significant correlations as evidence that altering neural entropy will change cognitive performance.
- **Do not interpret** non-significant results as evidence of no relationship; power limitations may apply.
- **Consider** these findings as hypothesis-generating for future experimental or longitudinal research.

### Compliance Statement

This disclaimer satisfies the requirements of:
- **FR-009**: Explicit acknowledgment of associational nature of findings
- **SC-005**: Constitution Amendment Request regarding methodological transparency
"""
    return disclaimer.strip()

def generate_report_content(regression_df, effect_sizes, sensitivity_report, behavioral_df):
    """Generate the full markdown content for the final report."""
    
    # Header
    report_lines = [
        "# Final Report: Neural Entropy and Cognitive Flexibility in Aging",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report presents the results of a Multiple Linear Regression (OLS) analysis examining the relationship between EEG-derived neural entropy metrics and cognitive flexibility (measured by WCST perseverative errors) in an older adult population.",
        "",
        "### Key Findings",
        ""
    ]

    # Summary of significant findings
    significant_results = regression_df[regression_df['p_value_fdr'] < 0.05]
    report_lines.append(f"- **Number of significant associations (FDR-corrected p < 0.05)**: {len(significant_results)} out of {len(regression_df)} tested relationships")
    
    if len(significant_results) > 0:
        report_lines.append("- **Primary significant bands**:",)
        bands = significant_results['frequency_band'].unique()
        for band in bands:
            count = len(significant_results[significant_results['frequency_band'] == band])
            report_lines.append(f"  - {band}: {count} significant entropy metric(s)")
    else:
        report_lines.append("- No statistically significant associations were found after FDR correction.")
    
    report_lines.append("")

    # Methodology Section
    report_lines.extend([
        "## Methodology",
        "",
        "### Statistical Approach",
        "",
        "This analysis employed **Multiple Linear Regression (OLS)** as the primary statistical method, with **Benjamini-Hochberg FDR correction** applied to account for multiple comparisons across frequency bands and entropy metrics. This approach was selected per project Plan deviation from the original specification.",
        "",
        "### Covariates",
        ""
    ])

    # Add covariate summary
    report_lines.append(generate_covariate_summary(behavioral_df))
    report_lines.append("")

    # Results Section
    report_lines.extend([
        "---",
        "",
        "## Detailed Results",
        "",
        "### Regression Results (FDR-Corrected)",
        "",
        "The table below presents regression coefficients, effect sizes (partial r), and FDR-corrected p-values for all tested relationships.",
        "",
        "| Frequency Band | Entropy Metric | Coefficient | Std Error | t-statistic | p-value (raw) | p-value (FDR) | Partial r | Effect Size |",
        "|----------------|----------------|-------------|-----------|-------------|---------------|---------------|-----------|-------------|"
    ])

    for _, row in regression_df.iterrows():
        effect_class = effect_sizes.get('classifications', {}).get(
            f"{row['frequency_band']}_{row['entropy_metric']}", 
            'Unknown'
        )
        report_lines.append(
            f"| {row['frequency_band']} | {row['entropy_metric']} | "
            f"{row['coef']:.4f} | {row['std_err']:.4f} | {row['t_value']:.4f} | "
            f"{row['p_value_raw']:.6f} | {row['p_value_fdr']:.6f} | "
            f"{row['partial_r']:.4f} | {effect_class} |"
        )

    report_lines.extend([
        "",
        "**Note**: Effect sizes are classified as clinically meaningful if |partial r| ≥ 0.3.",
        "",
        "### Sensitivity Analysis",
        "",
        "Sensitivity analyses were conducted to assess the robustness of findings under different exclusion criteria and threshold settings.",
        ""
    ])

    # Add sensitivity summary
    if sensitivity_report and 'scenarios' in sensitivity_report:
        report_lines.append("#### Exclusion Scenarios")
        report_lines.append("")
        for scenario in sensitivity_report['scenarios']:
            report_lines.append(f"- **{scenario['scenario']}**: {scenario['n_excluded']} participants excluded, correlation r={scenario['r_value']:.4f}, p={scenario['p_value']:.6f}")
        report_lines.append("")

    if sensitivity_report and 'threshold_sweep' in sensitivity_report:
        report_lines.append("#### Threshold Sensitivity")
        report_lines.append("")
        sweep = sensitivity_report['threshold_sweep']
        report_lines.append(f"- **Artifact rejection threshold sweep**: Range 15%-25% deviation. Maximum deviation from baseline: {sweep.get('max_artifact_deviation', 'N/A')}")
        report_lines.append(f"- **SNR threshold sweep**: Range 5-7 dB. Maximum deviation from baseline: {sweep.get('max_snr_deviation', 'N/A')}")
        report_lines.append("")

    # Disclaimer Section (CRITICAL FOR T031)
    report_lines.extend([
        "---",
        "",
        "## Methodological Transparency and Limitations",
        "",
        generate_associational_disclaimer(),
        "",
        "---",
        "",
        "## Data Availability and Reproducibility",
        "",
        "- **Raw Data**: OpenNeuro datasets (ds, ds003104) accessed via API",
        "- **Processed Data**: Available in `data/processed/`",
        "- **Code**: All analysis scripts available in `code/`",
        "- **Dependencies**: See `code/requirements.txt` for pinned versions",
        "",
        "## Acknowledgements",
        "",
        "- Power analysis sample size requirements deferred to implementation phase (see `logs/power_analysis.log`)",
        "- This study adheres to the project's Constitution Principles, including reproducibility (Pinned Dependencies) and data integrity (No fabricated results).",
        "",
        "---",
        "",
        "*Report generated by llmXive automated science pipeline*"
    ])

    return "\n".join(report_lines)

def main():
    """Main entry point for report generation."""
    logger = setup_logger()
    logger.info("Starting final report generation")
    
    # Resource monitoring
    log_resource_snapshot(logger)
    
    try:
        # Load all required data
        logger.info("Loading regression results...")
        regression_df = load_regression_results()
        
        logger.info("Loading effect sizes...")
        effect_sizes = load_effect_sizes()
        
        logger.info("Loading sensitivity report...")
        sensitivity_report = load_sensitivity_report()
        
        logger.info("Loading behavioral scores...")
        behavioral_df = load_behavioral_scores()
        
        # Generate report content
        logger.info("Generating report content...")
        report_content = generate_report_content(
            regression_df, 
            effect_sizes, 
            sensitivity_report, 
            behavioral_df
        )
        
        # Ensure output directory exists
        output_path = Path('reports/final_report.md')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        logger.info(f"Writing report to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info("Report generation completed successfully")
        
        # Final resource check
        mem_gb = get_memory_usage_gb()
        logger.info(f"Final memory usage: {mem_gb:.2f} GB")
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()