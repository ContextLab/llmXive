import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path

from config import get_config_dict, ensure_directories

def load_metrics_data(metrics_path: str) -> pd.DataFrame:
    """Load aggregated structural and dynamic metrics."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    return pd.read_csv(metrics_path)

def load_correlation_results(results_path: str) -> pd.DataFrame:
    """Load correlation analysis results."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Correlation results file not found: {results_path}")
    return pd.read_csv(results_path)

def load_exclusion_log(log_path: str) -> List[Dict]:
    """Load exclusion log if it exists."""
    if not os.path.exists(log_path):
        return []
    with open(log_path, 'r') as f:
        return json.load(f)

def calculate_sensitivity_metrics(
    correlation_results: pd.DataFrame,
    baseline_window: int = 30,
    sensitivity_window: int = 20
) -> Dict[str, Any]:
    """
    Calculate sensitivity metrics for the report.
    
    Specifically handles the edge case where FDR correction yields zero 
    significant findings by ensuring the report explicitly states this.
    
    Also calculates the absolute difference between 30 TR and 20 TR 
    correlation coefficients if sensitivity data exists.
    """
    summary = {
        "total_correlations_tested": len(correlation_results),
        "significant_findings_fdr_q005": 0,
        "fdr_correction_result": "No significant findings",
        "absolute_difference_30_20_tr": None,
        "notes": []
    }

    if correlation_results.empty:
        summary["notes"].append("No correlation results available for analysis.")
        return summary

    # Count significant findings after FDR correction
    # Assuming 'fdr_corrected_p' column exists from T027
    if 'fdr_corrected_p' in correlation_results.columns:
        sig_mask = correlation_results['fdr_corrected_p'] < 0.05
        sig_count = sig_mask.sum()
        summary["significant_findings"] = int(sig_count)

        if sig_count == 0:
            summary["fdr_correction_result"] = (
                "Zero significant findings after Benjamini-Hochberg FDR correction (q=0.05). "
                "This indicates no statistically significant correlations between structural "
                "topological metrics and dynamic functional metrics in this cohort."
            )
            summary["notes"].append(
                "Explicitly reported zero significant findings as per T028 requirements."
            )
        else:
            summary["fdr_correction_result"] = (
                f"Found {sig_count} significant correlation(s) after FDR correction."
            )

    # Calculate absolute difference between 30 TR and 20 TR if data exists
    # This assumes the correlation_results or a separate sensitivity file 
    # contains columns like 'r_30tr' and 'r_20tr' or similar structure.
    # For T028, the primary focus is the zero-findings message, but we 
    # prepare the structure for the absolute difference if data is present.
    if 'r_30tr' in correlation_results.columns and 'r_20tr' in correlation_results.columns:
        diff_col = (correlation_results['r_30tr'] - correlation_results['r_20tr']).abs()
        summary["absolute_difference_30_20_tr"] = float(diff_col.mean())
        summary["notes"].append(
            f"Average absolute difference between 30 TR and 20 TR correlation coefficients: "
            f"{summary['absolute_difference_30_20_tr']:.4f}"
        )
    else:
        summary["notes"].append(
            "Sensitivity analysis (20 TR vs 30 TR) data not found in correlation results. "
            "Skipping absolute difference calculation."
        )

    return summary

def generate_summary_statistics(
    metrics_df: pd.DataFrame,
    exclusion_log: List[Dict]
) -> Dict[str, Any]:
    """Generate summary statistics for the report."""
    summary = {
        "cohort_size": len(metrics_df),
        "excluded_subjects": len(exclusion_log),
        "structural_metrics": {},
        "dynamic_metrics": {}
    }

    if not metrics_df.empty:
        # Structural metrics summary
        struct_cols = [c for c in metrics_df.columns if c.startswith('struct_')]
        for col in struct_cols:
            summary["structural_metrics"][col] = {
                "mean": float(metrics_df[col].mean()),
                "std": float(metrics_df[col].std()),
                "min": float(metrics_df[col].min()),
                "max": float(metrics_df[col].max())
            }

        # Dynamic metrics summary
        dyn_cols = [c for c in metrics_df.columns if c.startswith('dyn_')]
        for col in dyn_cols:
            summary["dynamic_metrics"][col] = {
                "mean": float(metrics_df[col].mean()),
                "std": float(metrics_df[col].std()),
                "min": float(metrics_df[col].min()),
                "max": float(metrics_df[col].max())
            }

    return summary

def generate_final_report(
    metrics_path: str,
    correlation_results_path: str,
    exclusion_log_path: str,
    output_path: str
) -> None:
    """
    Generate the final comprehensive report.
    
    Ensures that if FDR correction yields zero significant findings, 
    the report explicitly states this rather than omitting results.
    """
    ensure_directories()
    
    # Load data
    metrics_df = load_metrics_data(metrics_path)
    correlation_results = load_correlation_results(correlation_results_path)
    exclusion_log = load_exclusion_log(exclusion_log_path)

    # Generate components
    cohort_summary = generate_summary_statistics(metrics_df, exclusion_log)
    sensitivity_summary = calculate_sensitivity_metrics(correlation_results)

    # Assemble report
    report = {
        "title": "Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns",
        "version": "1.0",
        "cohort_summary": cohort_summary,
        "correlation_analysis": {
            "total_tests": sensitivity_summary["total_correlations_tested"],
            "significant_findings": sensitivity_summary.get("significant_findings", 0),
            "fdr_result_statement": sensitivity_summary["fdr_correction_result"],
            "sensitivity_analysis": {
                "absolute_difference_30_20_tr": sensitivity_summary["absolute_difference_30_20_tr"],
                "notes": sensitivity_summary["notes"]
            }
        },
        "exclusions": exclusion_log,
        "methodological_notes": [
            "All structural metrics derived from dMRI using NetworkX.",
            "Dynamic metrics derived from fMRI using LOO K-Means (k=5) with 30 TR window.",
            "Correlations tested with FDR correction (Benjamini-Hochberg, q=0.05).",
            "Associational framing maintained throughout."
        ]
    }

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Final report generated: {output_path}")
    
    # Explicitly print the FDR result to console for immediate verification
    print(f"\nFDR Correction Result: {report['correlation_analysis']['fdr_result_statement']}")

def main():
    """Entry point for report generation."""
    config = get_config_dict()
    
    metrics_path = config.get('paths', {}).get('processed_metrics', 'data/processed/structural_metrics.csv')
    # Assuming correlation results are saved here by T027
    correlation_results_path = config.get('paths', {}).get('correlation_results', 'data/processed/correlation_results.csv')
    exclusion_log_path = config.get('paths', {}).get('exclusion_log', 'data/logs/exclusion_log.json')
    output_path = config.get('paths', {}).get('final_report', 'data/reports/final_report.json')

    generate_final_report(
        metrics_path=metrics_path,
        correlation_results_path=correlation_results_path,
        exclusion_log_path=exclusion_log_path,
        output_path=output_path
    )

if __name__ == "__main__":
    main()