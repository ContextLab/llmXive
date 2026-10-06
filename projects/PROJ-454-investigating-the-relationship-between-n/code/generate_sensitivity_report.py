"""
T029: Generate sensitivity_report.json comparing results across exclusion scenarios and threshold sweeps.

Inputs:
  - data/processed/sensitivity_exclusion_results.csv
  - data/processed/sensitivity_threshold_results.csv
Output:
  - data/processed/sensitivity_report.json

Required fields in report:
  - scenario
  - r_value
  - p_value
  - n_excluded
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_general_logger

def setup_logger(name):
    return setup_general_logger(name)

def load_sensitivity_data(logger):
    """
    Load the sensitivity analysis results from CSV files.
    
    Returns:
        tuple: (exclusion_df, threshold_df)
    """
    data_path = project_root / "data" / "processed"
    
    exclusion_file = data_path / "sensitivity_exclusion_results.csv"
    threshold_file = data_path / "sensitivity_threshold_results.csv"
    
    if not exclusion_file.exists():
        logger.error(f"Exclusion results file not found: {exclusion_file}")
        raise FileNotFoundError(f"Missing file: {exclusion_file}")
    
    if not threshold_file.exists():
        logger.error(f"Threshold results file not found: {exclusion_file}")
        raise FileNotFoundError(f"Missing file: {threshold_file}")
    
    exclusion_df = pd.read_csv(exclusion_file)
    threshold_df = pd.read_csv(threshold_file)
    
    logger.info(f"Loaded {len(exclusion_df)} exclusion scenarios")
    logger.info(f"Loaded {len(threshold_df)} threshold sweep results")
    
    return exclusion_df, threshold_df

def build_report(exclusion_df, threshold_df, logger):
    """
    Construct the sensitivity report dictionary.
    
    The report compares results across exclusion scenarios and threshold sweeps.
    Each entry must contain: scenario, r_value, p_value, n_excluded.
    
    Args:
        exclusion_df: DataFrame from sensitivity_exclusion_results.csv
        threshold_df: DataFrame from sensitivity_threshold_results.csv
        logger: Logger instance
        
    Returns:
        dict: The sensitivity report structure
    """
    report = {
        "summary": {
            "total_exclusion_scenarios": len(exclusion_df),
            "total_threshold_scenarios": len(threshold_df),
            "analysis_type": "sensitivity_analysis",
            "methodology": "OLS regression with FDR correction across exclusion and threshold variations"
        },
        "exclusion_scenarios": [],
        "threshold_scenarios": []
    }
    
    # Process exclusion scenarios
    # Expected columns: scenario_name, r_value, p_value, n_excluded, n_total, metric_name
    for _, row in exclusion_df.iterrows():
        scenario_entry = {
            "scenario": row.get("scenario_name", row.get("scenario", "unknown")),
            "r_value": float(row["r_value"]) if pd.notna(row["r_value"]) else None,
            "p_value": float(row["p_value"]) if pd.notna(row["p_value"]) else None,
            "n_excluded": int(row["n_excluded"]) if pd.notna(row["n_excluded"]) else 0,
            "n_total": int(row.get("n_total", 0)),
            "metric": row.get("metric_name", row.get("metric", "all")),
            "description": row.get("description", "")
        }
        report["exclusion_scenarios"].append(scenario_entry)
    
    # Process threshold sweep scenarios
    # Expected columns: scenario_name, threshold_type, threshold_value, r_value, p_value, n_excluded
    for _, row in threshold_df.iterrows():
        scenario_entry = {
            "scenario": row.get("scenario_name", row.get("scenario", "unknown")),
            "threshold_type": row.get("threshold_type", "unknown"),
            "threshold_value": float(row["threshold_value"]) if pd.notna(row["threshold_value"]) else None,
            "r_value": float(row["r_value"]) if pd.notna(row["r_value"]) else None,
            "p_value": float(row["p_value"]) if pd.notna(row["p_value"]) else None,
            "n_excluded": int(row["n_excluded"]) if pd.notna(row["n_excluded"]) else 0,
            "n_total": int(row.get("n_total", 0)),
            "metric": row.get("metric_name", row.get("metric", "all")),
            "description": row.get("description", "")
        }
        report["threshold_scenarios"].append(scenario_entry)
    
    # Add comparison summary
    if len(exclusion_df) > 0 and len(threshold_df) > 0:
        # Calculate stability metrics
        exclusion_r_values = [e["r_value"] for e in report["exclusion_scenarios"] if e["r_value"] is not None]
        threshold_r_values = [t["r_value"] for t in report["threshold_scenarios"] if t["r_value"] is not None]
        
        if exclusion_r_values:
            report["comparison"] = {
                "exclusion_r_range": {
                    "min": min(exclusion_r_values),
                    "max": max(exclusion_r_values),
                    "mean": sum(exclusion_r_values) / len(exclusion_r_values)
                },
                "threshold_r_range": {
                    "min": min(threshold_r_values),
                    "max": max(threshold_r_values),
                    "mean": sum(threshold_r_values) / len(threshold_r_values)
                },
                "stability_note": "Lower variance indicates more robust findings across scenarios"
            }
        else:
            report["comparison"] = {
                "stability_note": "No valid r-values found in sensitivity analysis"
            }
    
    logger.info(f"Built report with {len(report['exclusion_scenarios'])} exclusion and {len(report['threshold_scenarios'])} threshold scenarios")
    
    return report

def main():
    """Main entry point for generating the sensitivity report."""
    logger = setup_logger("generate_sensitivity_report")
    logger.info("Starting sensitivity report generation (T029)")
    
    try:
        # Load data
        exclusion_df, threshold_df = load_sensitivity_data(logger)
        
        # Build report
        report = build_report(exclusion_df, threshold_df, logger)
        
        # Save report
        output_path = project_root / "data" / "processed" / "sensitivity_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Sensitivity report saved to: {output_path}")
        logger.info(f"Report contains {report['summary']['total_exclusion_scenarios']} exclusion scenarios and {report['summary']['total_threshold_scenarios']} threshold scenarios")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error generating sensitivity report: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())