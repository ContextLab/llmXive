"""
VIF Report Generator for Multicollinearity Analysis.

This module generates a comprehensive markdown report visualizing the correlation
matrix of predictors and documenting the VIF-based exclusion steps taken during
the logistic regression model selection process.

Dependencies:
- pandas, numpy, scipy (for statistical calculations)
- Existing outputs from statistical_analysis.py (logistic_regression.json)
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from scipy import stats

from config import get_results_path, setup_logging
from statistical_analysis import load_static_baseline, load_semantic_results, merge_datasets

# Setup logging
logger = setup_logging(__name__)

def load_regression_results() -> Dict[str, Any]:
    """Load the logistic regression results from the JSON file."""
    results_path = get_results_path() / "logistic_regression.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Regression results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_merged_dataset() -> pd.DataFrame:
    """Load and merge the static and semantic datasets for correlation analysis."""
    try:
        df = merge_datasets()
        return df
    except Exception as e:
        logger.error(f"Failed to load merged dataset: {e}")
        raise

def calculate_correlation_matrix(df: pd.DataFrame, predictor_cols: List[str]) -> pd.DataFrame:
    """
    Calculate the correlation matrix for the specified predictors.
    
    Args:
        df: The merged dataframe containing all predictors
        predictor_cols: List of column names to include in the correlation matrix
        
    Returns:
        A pandas DataFrame containing the correlation matrix
    """
    # Filter to only numeric columns that exist in the dataframe
    available_cols = [col for col in predictor_cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(available_cols) < 2:
        logger.warning(f"Not enough numeric predictors found. Available: {available_cols}")
        return pd.DataFrame()
    
    return df[available_cols].corr()

def format_correlation_table(corr_matrix: pd.DataFrame) -> str:
    """
    Format the correlation matrix as a Markdown table.
    
    Args:
        corr_matrix: The correlation matrix DataFrame
        
    Returns:
        A Markdown-formatted string representation of the table
    """
    if corr_matrix.empty:
        return "No correlation matrix available."
    
    # Round values to 3 decimal places
    corr_rounded = corr_matrix.round(3)
    
    # Convert to markdown table string
    md_lines = []
    headers = ["Variable"] + list(corr_rounded.columns)
    
    # Header row
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    # Data rows
    for idx in corr_rounded.index:
        row_values = [idx] + [f"{val:.3f}" for val in corr_rounded.loc[idx]]
        md_lines.append("| " + " | ".join(row_values) + " |")
    
    return "\n".join(md_lines)

def generate_exclusion_documentation(regression_results: Dict[str, Any]) -> str:
    """
    Generate documentation of the VIF exclusion steps taken.
    
    Args:
        regression_results: The dictionary containing regression results including VIF scores
        
    Returns:
        A Markdown-formatted string documenting the exclusion process
    """
    lines = []
    
    # Section: VIF Analysis Summary
    lines.append("### VIF Analysis and Exclusion Process")
    lines.append("")
    
    if "vif_scores" not in regression_results or not regression_results["vif_scores"]:
        lines.append("*No VIF scores were calculated or recorded in this run.*")
        lines.append("")
        return "\n".join(lines)
    
    vif_scores = regression_results["vif_scores"]
    lines.append("**Initial VIF Scores:**")
    lines.append("")
    lines.append("| Predictor | VIF Score | Status |")
    lines.append("|-----------|-----------|--------|")
    
    for predictor, vif in vif_scores.items():
        status = "Excluded" if vif >= 5.0 else "Retained"
        lines.append(f"| {predictor} | {vif:.3f} | {status} |")
    
    lines.append("")
    
    # Section: Exclusion Steps
    lines.append("**Exclusion Steps Taken:**")
    lines.append("")
    
    excluded_predictors = [p for p, v in vif_scores.items() if v >= 5.0]
    if not excluded_predictors:
        lines.append("No predictors exceeded the VIF threshold of 5.0. All predictors were retained in the model.")
    else:
        lines.append(f"The following predictors were excluded due to VIF ≥ 5.0: {', '.join(excluded_predictors)}")
        lines.append("")
        
        # Document the iterative exclusion process if available
        if "exclusion_history" in regression_results and regression_results["exclusion_history"]:
            lines.append("The following iterative exclusion process was performed:")
            lines.append("")
            
            for step, step_data in enumerate(regression_results["exclusion_history"], 1):
                lines.append(f"**Step {step}:**")
                lines.append(f"- Highest VIF predictor: {step_data.get('excluded_predictor', 'N/A')}")
                lines.append(f"- VIF value: {step_data.get('vif_value', 'N/A'):.3f}")
                lines.append(f"- Remaining predictors: {', '.join(step_data.get('remaining_predictors', []))}")
                lines.append("")
        
        # Document residualization if applicable
        if "residualization_applied" in regression_results and regression_results["residualization_applied"]:
            lines.append("**Residualization Details:**")
            lines.append("")
            lines.append("Residualization was applied to the following predictors to address multicollinearity:")
            lines.append("")
            for pred_info in regression_results["residualization_applied"]:
                lines.append(f"- **{pred_info['predictor']}**: Residualized against {pred_info['against']}")
            lines.append("")
    
    # Section: Final Model Predictors
    lines.append("**Final Model Predictors:**")
    lines.append("")
    if "final_predictors" in regression_results:
        lines.append(", ".join(regression_results["final_predictors"]))
    else:
        lines.append("Predictors not available in results.")
    lines.append("")
    
    return "\n".join(lines)

def generate_recommendations(correlation_matrix: pd.DataFrame, regression_results: Dict[str, Any]) -> str:
    """
    Generate recommendations based on the multicollinearity analysis.
    
    Args:
        correlation_matrix: The correlation matrix of predictors
        regression_results: The regression results dictionary
        
    Returns:
        A Markdown-formatted string with recommendations
    """
    lines = []
    lines.append("### Recommendations and Interpretation")
    lines.append("")
    
    # Check for high correlations
    high_corr_pairs = []
    if not correlation_matrix.empty:
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                col_i = correlation_matrix.columns[i]
                col_j = correlation_matrix.columns[j]
                corr_val = abs(correlation_matrix.iloc[i, j])
                if corr_val > 0.7:
                    high_corr_pairs.append((col_i, col_j, corr_val))
    
    if high_corr_pairs:
        lines.append("**High Correlation Detected:**")
        lines.append("")
        lines.append("The following predictor pairs show high correlation (|r| > 0.7), which may contribute to multicollinearity:")
        lines.append("")
        for p1, p2, val in high_corr_pairs:
            lines.append(f"- {p1} and {p2} (r = {val:.3f})")
        lines.append("")
        lines.append("Recommendation: Consider combining these variables or using one as a proxy for the other in future models.")
    else:
        lines.append("No extreme pairwise correlations (|r| > 0.7) were detected in the predictor set.")
    
    lines.append("")
    
    # VIF-based recommendations
    if "vif_scores" in regression_results:
        max_vif = max(regression_results["vif_scores"].values()) if regression_results["vif_scores"] else 0
        if max_vif >= 5.0:
            lines.append("**VIF Concerns:**")
            lines.append("")
            lines.append("Some predictors exhibited VIF scores ≥ 5.0, indicating potential multicollinearity issues.")
            lines.append("The exclusion process documented above was applied to mitigate this.")
            lines.append("Future studies should consider collecting more diverse data or using dimensionality reduction techniques.")
        else:
            lines.append("**VIF Status:**")
            lines.append("")
            lines.append("All predictors in the final model have VIF scores below the threshold of 5.0, indicating acceptable multicollinearity levels.")
    
    lines.append("")
    return "\n".join(lines)

def generate_vif_report() -> str:
    """
    Generate the complete VIF report in Markdown format.
    
    Returns:
        A complete Markdown string representing the VIF report
    """
    logger.info("Starting VIF report generation...")
    
    # Load data
    try:
        regression_results = load_regression_results()
        df = load_merged_dataset()
    except Exception as e:
        logger.error(f"Failed to load required data: {e}")
        return f"# VIF Report Generation Failed\n\nError: {str(e)}"
    
    # Define predictors of interest based on the study design
    # These are the typical predictors used in the statistical analysis
    predictor_cols = ['loc', 'cyclomatic_complexity', 'semantic_mean']
    
    # Calculate correlation matrix
    corr_matrix = calculate_correlation_matrix(df, predictor_cols)
    
    # Build the report
    report_lines = [
        "# VIF Report: Multicollinearity Analysis",
        "",
        "## Overview",
        "",
        "This report documents the multicollinearity analysis performed on the predictors used in the logistic regression model for code smell detection.",
        "The analysis includes a correlation matrix visualization and a detailed account of the Variable Inflation Factor (VIF) exclusion process.",
        "",
        "## Correlation Matrix",
        "",
        "The following table shows the pairwise Pearson correlation coefficients between the predictors:",
        "",
        format_correlation_table(corr_matrix),
        "",
        generate_exclusion_documentation(regression_results),
        generate_recommendations(corr_matrix, regression_results),
        "",
        "---",
        "",
        "*Report generated automatically by the VIF Report Generator.*"
    ]
    
    report_content = "\n".join(report_lines)
    logger.info("VIF report generated successfully.")
    
    return report_content

def save_vif_report(content: str) -> Path:
    """
    Save the VIF report to a Markdown file.
    
    Args:
        content: The Markdown content of the report
        
    Returns:
        The path to the saved file
    """
    results_path = get_results_path()
    report_path = results_path / "vif_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"VIF report saved to {report_path}")
    return report_path

def main():
    """Main entry point for the VIF report generator."""
    logger.info("Running VIF Report Generator...")
    
    try:
        # Generate the report
        report_content = generate_vif_report()
        
        # Save the report
        report_path = save_vif_report(report_content)
        
        logger.info(f"VIF Report successfully generated at: {report_path}")
        print(f"VIF Report generated: {report_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate VIF report: {e}")
        print(f"Error generating VIF report: {e}")
        raise

if __name__ == "__main__":
    main()
