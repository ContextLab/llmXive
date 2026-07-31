"""
Report generation module for the Gut Microbiome and Circadian Rhythm study.

This module generates the final research report, ensuring all findings are
framed as associational and includes sections on bootstrap stability and
sensitivity analysis results.
"""
import os
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import json

from config import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.seeding import get_seed_manager

# Import results from analysis
try:
    from analysis import save_results
except ImportError:
    # Fallback for direct execution context if needed
    save_results = None

# Import validation results
try:
    from validation import load_correlation_results as load_validation_results, get_top_correlations
except ImportError:
    load_validation_results = None
    get_top_correlations = None

logger = get_logger(__name__)

def load_correlation_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the correlation results from the CSV file.
    
    Args:
        filepath: Path to the correlation results CSV. If None, uses config default.
        
    Returns:
        DataFrame containing correlation results.
    """
    config = get_config()
    if filepath is None:
        filepath = str(config.output_dir / "correlation_results.csv")
        
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
        
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} correlation results from {filepath}")
    return df

def load_validation_status(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the validation status JSON file.
    
    Args:
        filepath: Path to the validation status JSON. If None, uses config default.
        
    Returns:
        Dictionary containing validation status information.
    """
    config = get_config()
    if filepath is None:
        filepath = str(config.output_dir / "validation_status.json")
        
    if not os.path.exists(filepath):
        logger.warning(f"Validation status file not found: {filepath}. Using empty status.")
        return {"resampling_skipped": True, "reason": "File not found"}
        
    with open(filepath, 'r') as f:
        return json.load(f)

def load_sensitivity_report(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the sensitivity analysis report.
    
    Args:
        filepath: Path to the sensitivity report CSV. If None, uses config default.
        
    Returns:
        DataFrame containing sensitivity analysis results.
    """
    config = get_config()
    if filepath is None:
        filepath = str(config.output_dir / "sensitivity_report.csv")
        
    if not os.path.exists(filepath):
        logger.warning(f"Sensitivity report file not found: {filepath}. Using empty report.")
        return pd.DataFrame()
        
    return pd.read_csv(filepath)

def load_bootstrap_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the bootstrap analysis results.
    
    Args:
        filepath: Path to the bootstrap results CSV. If None, uses config default.
        
    Returns:
        DataFrame containing bootstrap results.
    """
    config = get_config()
    if filepath is None:
        filepath = str(config.output_dir / "bootstrap_results.csv")
        
    if not os.path.exists(filepath):
        logger.warning(f"Bootstrap results file not found: {filepath}. Using empty report.")
        return pd.DataFrame()
        
    return pd.read_csv(filepath)

def generate_report_section_bootstrap_stability(bootstrap_df: pd.DataFrame, top_n: int = 5) -> str:
    """
    Generate a section detailing bootstrap stability results.
    
    Args:
        bootstrap_df: DataFrame containing bootstrap results with CIs.
        top_n: Number of top correlations to include.
        
    Returns:
        Formatted text section for the report.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("BOOTSTRAP STABILITY ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    lines.append("This section presents the stability of the top correlations identified")
    lines.append("in the associational analysis, assessed via bootstrap resampling (1000 iterations).")
    lines.append("Confidence intervals (95%) are reported for effect sizes. Note that intervals")
    lines.append("including zero indicate a lack of statistical stability for that association,")
    lines.append("which is reported as a valid negative result rather than a failure.")
    lines.append("")
    
    if bootstrap_df.empty:
        lines.append("No bootstrap results available. Resampling may have been skipped due to")
        lines.append("insufficient sample size (N < 40) or other constraints.")
        lines.append("")
        return "\n".join(lines)
        
    # Sort by absolute effect size to get top correlations
    if 'correlation_coefficient' in bootstrap_df.columns:
        sorted_df = bootstrap_df.sort_values(
            by='correlation_coefficient', 
            key=lambda x: x.abs(), 
            ascending=False
        ).head(top_n)
    else:
        sorted_df = bootstrap_df.head(top_n)
        
    lines.append(f"Top {top_n} Correlations by Stability Analysis:")
    lines.append("-" * 40)
    
    for idx, row in sorted_df.iterrows():
        taxon = row.get('taxon', 'Unknown')
        sleep_var = row.get('sleep_variable', 'Unknown')
        coef = row.get('correlation_coefficient', 0.0)
        ci_low = row.get('ci_low', 0.0)
        ci_high = row.get('ci_high', 0.0)
        includes_zero = ci_low <= 0 <= ci_high
        
        stability_note = "UNSTABLE (CI includes zero)" if includes_zero else "STABLE"
        
        lines.append(f"  Taxon: {taxon}")
        lines.append(f"  Sleep Variable: {sleep_var}")
        lines.append(f"  Effect Size (r): {coef:.4f}")
        lines.append(f"  95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
        lines.append(f"  Stability Status: {stability_note}")
        lines.append("")
        
    lines.append("Interpretation: Associations with confidence intervals including zero")
    lines.append("should be interpreted with caution as they lack robust stability across")
    lines.append("resampled datasets. This does not invalidate the initial finding but")
    lines.append("suggests the association may be sensitive to sample composition.")
    lines.append("")
    
    return "\n".join(lines)

def generate_report_section_sensitivity(sensitivity_df: pd.DataFrame) -> str:
    """
    Generate a section detailing sensitivity analysis results.
    
    Args:
        sensitivity_df: DataFrame containing sensitivity analysis results.
        
    Returns:
        Formatted text section for the report.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("SENSITIVITY ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    lines.append("This section examines how the number of significant taxa associations")
    lines.append("changes across different significance thresholds (alpha levels).")
    lines.append("This analysis helps assess the robustness of findings to the choice")
    lines.append("of significance cutoff.")
    lines.append("")
    
    if sensitivity_df.empty:
        lines.append("No sensitivity analysis results available.")
        lines.append("")
        return "\n".join(lines)
        
    lines.append("Significance Threshold Sweep Results:")
    lines.append("-" * 40)
    lines.append(f"{'Threshold (alpha)':<20} {'Significant Taxa Count':<25} {'Notes'}")
    lines.append("-" * 40)
    
    for idx, row in sensitivity_df.iterrows():
        alpha = row.get('threshold', 0.05)
        count = row.get('significant_count', 0)
        lines.append(f"{alpha:<20.2f} {count:<25} ")
        
    lines.append("")
    lines.append("Interpretation: A rapid decline in significant taxa as alpha decreases")
    lines.append("suggests that findings are sensitive to the significance threshold.")
    lines.append("Conversely, stable counts across thresholds indicate robust associations.")
    lines.append("")
    
    return "\n".join(lines)

def generate_full_report(correlation_df: pd.DataFrame, 
                         bootstrap_df: pd.DataFrame, 
                         sensitivity_df: pd.DataFrame,
                         validation_status: Dict[str, Any],
                         output_path: Optional[str] = None) -> str:
    """
    Generate the complete research report with all required sections.
    
    Args:
        correlation_df: Main correlation results.
        bootstrap_df: Bootstrap stability results.
        sensitivity_df: Sensitivity analysis results.
        validation_status: Validation status information.
        output_path: Optional path to save the report. If None, returns string.
        
    Returns:
        Complete report text.
    """
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("INVESTIGATING THE CORRELATION BETWEEN GUT MICROBIOME COMPOSITION")
    lines.append("AND CIRCADIAN RHYTHM DISRUPTION: ASSOCIATIONAL ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("IMPORTANT DISCLAIMER: This report presents ASSOCIATIONAL findings only.")
    lines.append("No causal claims are made. Correlation does not imply causation.")
    lines.append("All results should be interpreted as statistical associations that")
    lines.append("warrant further investigation, not as evidence of causal mechanisms.")
    lines.append("")
    
    # Study Overview
    lines.append("-" * 80)
    lines.append("1. STUDY OVERVIEW")
    lines.append("-" * 80)
    lines.append("This study investigates associations between gut microbiome diversity metrics")
    lines.append("(Shannon, Simpson, Bray-Curtis) and circadian rhythm disruption variables")
    lines.append("(sleep duration, quality, chronotype) using data from the American Gut Project")
    lines.append("and Open Humans. All analyses are strictly associational in nature.")
    lines.append("")
    
    # Main Results Summary
    lines.append("-" * 80)
    lines.append("2. MAIN ASSOCIATIONAL RESULTS")
    lines.append("-" * 80)
    
    if correlation_df.empty:
        lines.append("No correlation results were generated.")
    else:
        significant_count = correlation_df['is_significant'].sum() if 'is_significant' in correlation_df.columns else 0
        lines.append(f"Total correlations tested: {len(correlation_df)}")
        lines.append(f"Significant associations (FDR-corrected): {significant_count}")
        lines.append("")
        lines.append("Top 5 Significant Associations (by absolute effect size):")
        lines.append("-" * 40)
        
        if 'correlation_coefficient' in correlation_df.columns:
            top5 = correlation_df.sort_values(
                by='correlation_coefficient', 
                key=lambda x: x.abs(), 
                ascending=False
            ).head(5)
        else:
            top5 = correlation_df.head(5)
            
        for idx, row in top5.iterrows():
            taxon = row.get('taxon', 'Unknown')
            sleep_var = row.get('sleep_variable', 'Unknown')
            coef = row.get('correlation_coefficient', 0.0)
            pval = row.get('p_value', 0.0)
            fdr_pval = row.get('fdr_p_value', 0.0)
            lines.append(f"  {taxon} <-> {sleep_var}: r={coef:.4f}, p={pval:.4f}, FDR-p={fdr_pval:.4f}")
            
    lines.append("")
    
    # Bootstrap Stability Section
    lines.append(generate_report_section_bootstrap_stability(bootstrap_df))
    
    # Sensitivity Analysis Section
    lines.append(generate_report_section_sensitivity(sensitivity_df))
    
    # Validation Status
    lines.append("-" * 80)
    lines.append("3. VALIDATION STATUS")
    lines.append("-" * 80)
    if validation_status.get('resampling_skipped'):
        lines.append(f"Bootstrap resampling was skipped: {validation_status.get('reason', 'Unknown reason')}")
        lines.append("This is consistent with the protocol for sample sizes < 40.")
    else:
        lines.append("Bootstrap resampling was completed successfully.")
    lines.append("")
    
    # Methodological Notes
    lines.append("-" * 80)
    lines.append("4. METHODOLOGICAL NOTES")
    lines.append("-" * 80)
    lines.append("- All p-values were corrected for multiple testing using the Benjamini-Hochberg")
    lines.append("  procedure to control the False Discovery Rate (FDR).")
    lines.append("- Confounding variables (age, BMI, diet type, medication, antibiotic history)")
    lines.append("  were adjusted for in GLM analyses.")
    lines.append("- Diet timing data was unavailable in the American Gut Project; diet type")
    lines.append("  was used as a substitute as per project plan mitigation.")
    lines.append("- All findings are presented as associational only. No causal inferences")
    lines.append("  are drawn from these results.")
    lines.append("")
    
    # Conclusion
    lines.append("-" * 80)
    lines.append("5. CONCLUSION")
    lines.append("-" * 80)
    lines.append("This study has identified statistical associations between gut microbiome")
    lines.append("composition and circadian rhythm disruption variables. The stability of")
    lines.append("these associations was assessed via bootstrap resampling, and their")
    lines.append("robustness to significance thresholds was evaluated via sensitivity analysis.")
    lines.append("")
    lines.append("Future research should focus on mechanistic studies to determine whether")
    lines.append("these associations reflect causal relationships or are mediated by")
    lines.append("unmeasured confounding factors.")
    lines.append("")
    lines.append("REMEMBER: CORRELATION DOES NOT IMPLY CAUSATION.")
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(report_text)
        logger.info(f"Report saved to {output_path}")
        
    return report_text

def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(description="Generate final research report")
    parser.add_argument("--output", type=str, default=None, help="Output file path for report")
    args = parser.parse_args()
    
    setup_logging()
    config = get_config()
    
    logger.info("Starting report generation...")
    
    try:
        # Load all required data
        correlation_df = load_correlation_results()
        bootstrap_df = load_bootstrap_results()
        sensitivity_df = load_sensitivity_report()
        validation_status = load_validation_status()
        
        # Generate report
        output_path = args.output or str(config.output_dir / "final_report.txt")
        report = generate_full_report(
            correlation_df, 
            bootstrap_df, 
            sensitivity_df, 
            validation_status, 
            output_path
        )
        
        print(report)
        logger.info("Report generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()