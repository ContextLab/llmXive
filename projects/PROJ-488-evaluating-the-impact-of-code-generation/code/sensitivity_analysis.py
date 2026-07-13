"""
Sensitivity analysis for statistical significance thresholds.

This module performs sensitivity analysis across significance thresholds {0.01, 0.05, 0.1}
to record how headline rates (number of significant findings) vary.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import from project modules
from logging_config import setup_logger, get_logger
from state_tracker import load_state_file, save_state_file, update_state_with_artifact
from statistical_analysis import run_mann_whitney_u_test, apply_benjamini_hochberg_correction

# Constants
SIGNIFICANCE_THRESHOLDS = [0.01, 0.05, 0.1]
OUTPUT_DIR = Path("results")
OUTPUT_FILE = OUTPUT_DIR / "sensitivity.md"
METRICS_DIR = Path("data/metrics")

def load_metric_data(metric_name: str) -> pd.DataFrame:
    """Load metric data for both groups from CSV files."""
    human_file = METRICS_DIR / f"human_{metric_name}.csv"
    lmm_file = METRICS_DIR / f"codegen_{metric_name}.csv"
    
    if not human_file.exists() or not lmm_file.exists():
        logger = get_logger(__name__)
        logger.warning(f"Missing metric files for {metric_name}: {human_file}, {lmm_file}")
        return None
    
    human_df = pd.read_csv(human_file)
    lmm_df = pd.read_csv(lmm_file)
    
    # Extract scores column (assuming column name is 'score' or first numeric column)
    score_col = 'score' if 'score' in human_df.columns else human_df.select_dtypes(include=[np.number]).columns[0]
    
    return {
        'human': human_df[score_col].dropna().values,
        'codegen': lmm_df[score_col].dropna().values
    }

def perform_sensitivity_test(
    human_scores: np.ndarray, 
    codegen_scores: np.ndarray,
    alpha: float
) -> Tuple[bool, float, float]:
    """
    Perform Mann-Whitney U test and BH correction for a specific alpha.
    
    Returns:
      Tuple of (is_significant, p_value, adjusted_p_value)
    """
    # Run Mann-Whitney U test
    u_stat, p_value = run_mann_whitney_u_test(human_scores, codegen_scores)
    
    # Apply Benjamini-Hochberg correction (for single test, it's the same)
    # But we simulate the correction process for consistency
    adjusted_p_value = apply_benjamini_hochberg_correction([p_value], alpha=alpha)[0] if p_value is not None else None
    
    is_significant = (p_value is not None) and (adjusted_p_value is not None) and (adjusted_p_value < alpha)
    
    return is_significant, p_value, adjusted_p_value

def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Run sensitivity analysis across all significance thresholds.
    
    Returns:
      Dictionary containing analysis results
    """
    logger = get_logger(__name__)
    logger.info("Starting sensitivity analysis across significance thresholds")
    
    # Load all metric files
    metric_files = list(METRICS_DIR.glob("human_*.csv"))
    metrics = [f.name.replace("human_", "").replace(".csv", "") for f in metric_files]
    
    results = {
        "thresholds": SIGNIFICANCE_THRESHOLDS,
        "metrics": metrics,
        "analysis": {}
    }
    
    for metric in metrics:
        logger.info(f"Analyzing metric: {metric}")
        data = load_metric_data(metric)
        
        if data is None:
            logger.warning(f"Skipping {metric} due to missing data")
            continue
        
        human_scores = data['human']
        codegen_scores = data['codegen']
        
        if len(human_scores) == 0 or len(codegen_scores) == 0:
            logger.warning(f"Skipping {metric} due to empty data")
            continue
        
        metric_results = {
            "human_n": len(human_scores),
            "codegen_n": len(codegen_scores),
            "thresholds": {}
        }
        
        for alpha in SIGNIFICANCE_THRESHOLDS:
            is_sig, p_val, adj_p_val = perform_sensitivity_test(
                human_scores, codegen_scores, alpha
            )
            
            metric_results["thresholds"][str(alpha)] = {
                "is_significant": is_sig,
                "p_value": float(p_val) if p_val is not None else None,
                "adjusted_p_value": float(adj_p_val) if adj_p_val is not None else None
            }
        
        results["analysis"][metric] = metric_results
    
    return results

def generate_markdown_report(results: Dict[str, Any]) -> str:
    """Generate a Markdown report of the sensitivity analysis."""
    lines = [
        "# Sensitivity Analysis Report",
        "",
        "This report presents the results of sensitivity analysis across significance thresholds",
        "{0.01, 0.05, 0.1} to examine how headline rates (number of significant findings) vary.",
        "",
        "## Summary",
        "",
        f"- **Thresholds tested**: {', '.join(map(str, results['thresholds']))}",
        f"- **Metrics analyzed**: {len(results['metrics'])}",
        "",
        "## Detailed Results",
        ""
    ]
    
    for metric, data in results["analysis"].items():
        lines.append(f"### {metric}")
        lines.append("")
        lines.append(f"- Human snippets: {data['human_n']}")
        lines.append(f"- CodeGen snippets: {data['codegen_n']}")
        lines.append("")
        lines.append("| Threshold | Significant | P-value | Adjusted P-value |")
        lines.append("|-----------|-------------|---------|------------------|")
        
        for threshold, values in data["thresholds"].items():
            sig_str = "Yes" if values["is_significant"] else "No"
            p_val_str = f"{values['p_value']:.4f}" if values['p_value'] is not None else "N/A"
            adj_p_val_str = f"{values['adjusted_p_value']:.4f}" if values['adjusted_p_value'] is not None else "N/A"
            
            lines.append(f"| {threshold} | {sig_str} | {p_val_str} | {adj_p_val_str} |")
        
        lines.append("")
    
    # Calculate headline rates
    lines.append("## Headline Rates Analysis")
    lines.append("")
    
    rate_summary = {str(alpha): 0 for alpha in SIGNIFICANCE_THRESHOLDS}
    total_metrics = len(results["analysis"])
    
    for metric, data in results["analysis"].items():
        for threshold in SIGNIFICANCE_THRESHOLDS:
            if data["thresholds"][str(threshold)]["is_significant"]:
                rate_summary[str(threshold)] += 1
    
    lines.append("| Threshold | Significant Findings | Headline Rate |")
    lines.append("|-----------|---------------------|---------------|")
    
    for threshold in SIGNIFICANCE_THRESHOLDS:
        count = rate_summary[str(threshold)]
        rate = (count / total_metrics * 100) if total_metrics > 0 else 0
        lines.append(f"| {threshold} | {count}/{total_metrics} | {rate:.1f}% |")
    
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append("The sensitivity analysis demonstrates how the number of significant findings varies")
    lines.append("across different significance thresholds. This helps assess the robustness of")
    lines.append("statistical conclusions to the choice of alpha level.")
    lines.append("")
    
    return "\n".join(lines)

def write_report(report: str, output_path: Path):
    """Write the Markdown report to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger = get_logger(__name__)
    logger.info(f"Sensitivity analysis report written to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    logger = setup_logger(__name__, level=logging.INFO)
    
    try:
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Run sensitivity analysis
        results = run_sensitivity_analysis()
        
        if not results["analysis"]:
            logger.error("No metrics were analyzed. Check if metric data files exist in data/metrics/")
            sys.exit(1)
        
        # Generate and write report
        report = generate_markdown_report(results)
        write_report(report, OUTPUT_FILE)
        
        # Save JSON results for programmatic access
        json_path = OUTPUT_DIR / "sensitivity_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Update state tracker
        try:
            update_state_with_artifact(
                artifact_path=str(OUTPUT_FILE),
                artifact_type="sensitivity_analysis",
                description="Sensitivity analysis across significance thresholds"
            )
        except Exception as e:
            logger.warning(f"Could not update state tracker: {e}")
        
        logger.info("Sensitivity analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
