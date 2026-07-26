"""
Task T022: Generate data/results/statistical_report.json
Contains p-values, corrected p-values, effect sizes, power, MDES, and power analysis results.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Import from existing API surface
from config import get_config, get_env_bool, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error
from analysis import (
    welch_t_test,
    calculate_cohen_d,
    calculate_effect_size_ci,
    bonferroni_correction,
    calculate_power_and_mdes,
    run_analysis,
    run_full_analysis
)

# Constants
RESULTS_DIR = "data/results"
REPORT_FILE = "statistical_report.json"

def load_cleaned_dataset():
    """Load the cleaned dataset from data/processed/cleaned_dataset.csv"""
    config = get_config()
    data_path = Path(config["data_processed_dir"]) / "cleaned_dataset.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}. Run T014a first.")
    
    df = pd.read_csv(data_path)
    log_info(f"Loaded cleaned dataset with {len(df)} records from {data_path}")
    return df

def load_statistical_analysis_results():
    """
    Load statistical analysis results (t-tests, effect sizes, corrections).
    Assumes T018/T019/T020 have run and produced intermediate results or
    we compute them directly here for the final report.
    """
    # For T022, we run the analysis pipeline to ensure we have the latest results
    # This mirrors what T018/T019/T020 do but aggregates for the final report
    return run_full_analysis()

def load_power_analysis_results():
    """
    Load power analysis results (power, MDES).
    Assumes T021 has run or we compute it directly.
    """
    # Run power analysis pipeline
    return calculate_power_and_mdes()

def run_analysis_pipeline(df):
    """Run the full statistical analysis pipeline."""
    log_info("Running full statistical analysis pipeline...")
    results = run_full_analysis()
    return results

def run_power_pipeline(df):
    """Run the power analysis pipeline."""
    log_info("Running power and MDES analysis...")
    power_results = calculate_power_and_mdes()
    return power_results

def compile_final_report(analysis_results, power_results):
    """
    Compile the final statistical report combining:
    - p-values
    - corrected p-values
    - effect sizes (Cohen's d)
    - confidence intervals
    - power analysis (power, MDES)
    """
    log_info("Compiling final statistical report...")
    
    report = {
        "report_metadata": {
            "task_id": "T022",
            "description": "Statistical Report: p-values, effect sizes, power, MDES",
            "analysis_method": "Welch's independent samples t-test",
            "correction_method": "Bonferroni"
        },
        "comparisons": []
    }
    
    # Process each comparison from analysis results
    comparisons = analysis_results.get("comparisons", [])
    for comp in comparisons:
        comparison_entry = {
            "metric": comp.get("metric"),
            "group_nostalgia": {
                "n": comp.get("n_nostalgia"),
                "mean": comp.get("mean_nostalgia"),
                "std": comp.get("std_nostalgia")
            },
            "group_control": {
                "n": comp.get("n_control"),
                "mean": comp.get("mean_control"),
                "std": comp.get("std_control")
            },
            "t_statistic": comp.get("t_statistic"),
            "p_value_raw": comp.get("p_value_raw"),
            "p_value_corrected": comp.get("p_value_corrected"),
            "effect_size": {
                "cohen_d": comp.get("cohen_d"),
                "ci_95_lower": comp.get("ci_lower"),
                "ci_95_upper": comp.get("ci_upper")
            },
            "power_analysis": {
                "statistical_power": comp.get("power"),
                "minimum_detectable_effect_size": comp.get("mdes"),
                "alpha": comp.get("alpha", 0.05),
                "sample_size_nostalgia": comp.get("n_nostalgia"),
                "sample_size_control": comp.get("n_control")
            }
        }
        report["comparisons"].append(comparison_entry)
    
    # Add summary statistics
    report["summary"] = {
        "total_comparisons": len(comparisons),
        "significant_at_alpha_05": sum(1 for c in comparisons if c.get("p_value_corrected", 1.0) < 0.05),
        "significant_at_alpha_01": sum(1 for c in comparisons if c.get("p_value_corrected", 1.0) < 0.01),
        "average_power": np.mean([c.get("power", 0) for c in comparisons]) if comparisons else 0,
        "average_mdes": np.mean([c.get("mdes", 0) for c in comparisons]) if comparisons else 0
    }
    
    return report

def save_report(report):
    """Save the final report to data/results/statistical_report.json"""
    output_path = Path(RESULTS_DIR) / REPORT_FILE
    ensure_dirs()
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    log_info(f"Statistical report saved to {output_path}")
    return output_path

def main():
    """Main entry point for T022."""
    # Setup logging
    log_level = logging.INFO
    setup_logging(level=log_level)
    
    log_info("Starting Task T022: Generate Statistical Report")
    
    try:
        # Ensure output directory exists
        ensure_dirs()
        
        # Load cleaned dataset
        df = load_cleaned_dataset()
        
        # Run analysis pipeline
        analysis_results = run_analysis_pipeline(df)
        
        # Run power analysis pipeline
        power_results = run_power_pipeline(df)
        
        # Compile final report
        final_report = compile_final_report(analysis_results, power_results)
        
        # Save report
        output_path = save_report(final_report)
        
        log_info(f"Task T022 completed successfully. Report: {output_path}")
        return 0
        
    except Exception as e:
        log_error(f"Task T022 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
