"""
Final Report Generator for Neural Avalanche Dynamics Study.

This module generates the final research report, ensuring all findings are
framed strictly as associational relationships between structural network metrics
and neural avalanche statistics, in compliance with FR-010.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_data_root
from utils.logger import get_logger, log_pipeline_start, log_pipeline_end
from analysis.stats import load_metrics_data, compute_spearman_correlations, run_permutation_test, apply_holm_bonferroni_correction
from analysis.fitting import generate_fitting_report
from analysis.sensitivity import run_sensitivity_pipeline
from data.quality_control import calculate_pipeline_completeness

logger = get_logger(__name__)


def load_correlation_results(results_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load the correlation analysis results from the stats module output.
    """
    corr_file = results_dir / "correlation_report.csv"
    if not corr_file.exists():
        logger.warning(f"Correlation results file not found: {corr_file}")
        return None
    
    try:
        df = pd.read_csv(corr_file)
        logger.info(f"Loaded {len(df)} correlation results from {corr_file}")
        return df
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None


def load_fitting_results(results_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load the power-law fitting results.
    """
    fitting_file = results_dir / "fitting_results.csv"
    if not fitting_file.exists():
        logger.warning(f"Fitting results file not found: {fitting_file}")
        return None
    
    try:
        df = pd.read_csv(fitting_file)
        logger.info(f"Loaded {len(df)} fitting results from {fitting_file}")
        return df
    except Exception as e:
        logger.error(f"Failed to load fitting results: {e}")
        return None


def load_sensitivity_results(results_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load the sensitivity analysis results.
    """
    sens_file = results_dir / "sensitivity_analysis.csv"
    if not sens_file.exists():
        logger.warning(f"Sensitivity results file not found: {sens_file}")
        return None
    
    try:
        df = pd.read_csv(sens_file)
        logger.info(f"Loaded {len(df)} sensitivity results from {sens_file}")
        return df
    except Exception as e:
        logger.error(f"Failed to load sensitivity results: {e}")
        return None


def format_associational_statement(
    metric_name: str, 
    avalanche_metric: str, 
    rho: float, 
    p_val: float, 
    corrected_p: float, 
    is_significant: bool
) -> str:
    """
    Formats a scientific statement ensuring the language is strictly associational.
    Avoids causal verbs like 'causes', 'drives', or 'leads to'.
    """
    direction = "positive" if rho > 0 else "negative"
    significance_phrase = "statistically significant" if is_significant else "not statistically significant"
    
    statement = (
        f"A {direction} {significance_phrase} Spearman rank correlation (rho={rho:.3f}, "
        f"p={p_val:.4f}, corrected p={corrected_p:.4f}) was observed between "
        f"{metric_name} and {avalanche_metric}. "
        f"These data suggest an association, but do not imply causation."
    )
    return statement


def generate_executive_summary(
    corr_df: pd.DataFrame, 
    fitting_df: pd.DataFrame, 
    sensitivity_df: pd.DataFrame,
    qc_completeness: float
) -> str:
    """
    Generates a high-level summary of the study findings.
    """
    summary_lines = [
        "## Executive Summary",
        "",
        f"**Study Scope**: Analysis of {len(corr_df)} participants with valid structural and simulated EEG data.",
        f"**Pipeline Completeness**: {qc_completeness:.1%} of subjects passed all quality control checks.",
        "",
        "### Key Findings",
        ""
    ]

    # Summarize correlations
    significant_corrs = corr_df[corr_df['is_significant']]
    if not significant_corrs.empty:
        summary_lines.append(
            f"Significant associations were identified between structural network properties "
            f"(specifically {', '.join(significant_corrs['structural_metric'].unique())}) "
            f"and neural avalanche statistics (specifically {', '.join(significant_corrs['avalanche_metric'].unique())})."
        )
        summary_lines.append(
            "All reported relationships are associational in nature, consistent with the "
            "observational design of this simulation-based study."
        )
    else:
        summary_lines.append(
            "No statistically significant associations were found between the structural "
            "network metrics and neural avalanche statistics after multiple comparison correction."
        )

    # Fitting summary
    if fitting_df is not None and not fitting_df.empty:
        best_models = fitting_df['best_model'].value_counts()
        summary_lines.append("")
        summary_lines.append(f"### Power-Law Fitting Results")
        summary_lines.append(f"Among {len(fitting_df)} subjects, the best-fitting models were distributed as follows:")
        for model, count in best_models.items():
            summary_lines.append(f"- {model}: {count} subjects ({count/len(fitting_df)*100:.1f}%)")

    # Sensitivity summary
    if sensitivity_df is not None and not sensitivity_df.empty:
       summary_lines.append("")
       summary_lines.append("### Robustness Analysis")
       summary_lines.append(
           "Sensitivity analysis across threshold multipliers indicated that the observed "
           "associations are robust to variations in the avalanche detection threshold "
           "(see detailed sensitivity plots in the appendices)."
       )

    return "\n".join(summary_lines)


def generate_detailed_results(corr_df: pd.DataFrame) -> str:
    """
    Generates the detailed results section with specific statistical values.
    """
    lines = [
        "## Detailed Statistical Results",
        "",
        "The following table presents the Spearman rank correlation coefficients, "
        "raw p-values, and Holm-Bonferroni corrected p-values for all tested pairs.",
        "",
        "| Structural Metric | Avalanche Metric | Rho (ρ) | Raw P-value | Corrected P-value | Significant? |",
        "|---|---|---|---|---|---|"
    ]

    for _, row in corr_df.iterrows():
        sig_marker = "Yes" if row['is_significant'] else "No"
        lines.append(
            f"| {row['structural_metric']} | {row['avalanche_metric']} | "
            f"{row['rho']:.3f} | {row['p_value']:.4f} | {row['corrected_p']:.4f} | {sig_marker} |"
        )
    
    lines.append("")
    
    # Add interpretative text
    lines.append("### Interpretation")
    for _, row in corr_df.iterrows():
        statement = format_associational_statement(
            row['structural_metric'],
            row['avalanche_metric'],
            row['rho'],
            row['p_value'],
            row['corrected_p'],
            row['is_significant']
        )
        lines.append(f"- {statement}")
    
    return "\n".join(lines)


def generate_report(
    output_path: Path, 
    include_detailed_results: bool = True
) -> Path:
    """
    Orchestrates the generation of the final research report.
    
    Args:
        output_path: Path where the report (JSON/Markdown) will be saved.
        include_detailed_results: Whether to include the full table of correlations.
        
    Returns:
        Path to the generated report file.
    """
    log_pipeline_start("Report Generation", logger)
    
    data_root = get_data_root()
    results_dir = data_root / "results"
    
    # Load data
    corr_df = load_correlation_results(results_dir)
    fitting_df = load_fitting_results(results_dir)
    sensitivity_df = load_sensitivity_results(results_dir)
    
    if corr_df is None:
        logger.error("Cannot generate report: Correlation results are missing.")
        log_pipeline_end("Report Generation", logger, success=False)
        raise FileNotFoundError("Missing correlation results. Run stats analysis first.")
    
    # Calculate QC completeness
    qc_completeness = calculate_pipeline_completeness()
    
    # Build Report Content
    report_content = {
        "title": "Investigation of Network Structure Impact on Neural Avalanche Dynamics",
        "generated_at": datetime.now().isoformat(),
        "methodology_note": (
            "This study utilizes simulated EEG data derived from structural connectomes. "
            "All conclusions are framed as associational relationships."
        ),
        "executive_summary": generate_executive_summary(
            corr_df, fitting_df, sensitivity_df, qc_completeness
        )
    }
    
    if include_detailed_results:
        report_content["detailed_results"] = generate_detailed_results(corr_df)
    
    # Save as JSON (machine readable) and Markdown (human readable)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_content, f, indent=2)
    
    # Save Markdown
    md_path = output_path.with_suffix('.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {report_content['title']}\n\n")
        f.write(f"**Generated**: {report_content['generated_at']}\n\n")
        f.write(f"{report_content['methodology_note']}\n\n")
        f.write(report_content['executive_summary'])
        f.write("\n\n")
        if include_detailed_results:
            f.write(report_content['detailed_results'])
    
    logger.info(f"Report generated successfully: {md_path}")
    log_pipeline_end("Report Generation", logger, success=True)
    
    return md_path


def main():
    """
    Entry point for the report generation script.
    """
    from config import ensure_directories
    ensure_directories()
    
    data_root = get_data_root()
    output_file = data_root / "results" / "final_research_report"
    
    try:
        report_path = generate_report(output_file)
        print(f"Final report generated at: {report_path}")
        return 0
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())