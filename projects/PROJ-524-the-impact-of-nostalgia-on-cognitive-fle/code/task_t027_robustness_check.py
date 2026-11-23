import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import from project modules using the provided API surface
from config import get_config, get_mmse_threshold, get_data_source_url
from utils import setup_logging, log_info, log_warning, log_error
from analysis import run_analysis, welch_t_test, calculate_cohen_d

def load_cleaned_dataset() -> Optional[pd.DataFrame]:
    """Load the cleaned dataset from data/processed/cleaned_dataset.csv."""
    config = get_config()
    dataset_path = Path(config["paths"]["processed"]) / "cleaned_dataset.csv"
    
    if not dataset_path.exists():
        log_error(f"Cleaned dataset not found at {dataset_path}")
        return None
    
    try:
        df = pd.read_csv(dataset_path)
        log_info(f"Loaded cleaned dataset with {len(df)} records")
        return df
    except Exception as e:
        log_error(f"Failed to load cleaned dataset: {e}")
        return None

def load_statistical_report() -> Optional[Dict[str, Any]]:
    """Load the existing statistical report from data/results/statistical_report.json."""
    config = get_config()
    report_path = Path(config["paths"]["results"]) / "statistical_report.json"
    
    if not report_path.exists():
        log_warning(f"Statistical report not found at {report_path}. Starting fresh.")
        return {}
    
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Failed to load statistical report: {e}")
        return {}

def load_mmse_flag() -> bool:
    """
    Load the has_mmse flag from the processed dataset metadata.
    We check if the cleaned dataset actually contains an 'MMSE' column.
    """
    config = get_config()
    dataset_path = Path(config["paths"]["processed"]) / "cleaned_dataset.csv"
    
    if not dataset_path.exists():
        log_warning("Cleaned dataset not found, assuming MMSE flag is False")
        return False
    
    try:
        # Read just the header to check for column existence
        df_header = pd.read_csv(dataset_path, nrows=0)
        has_mmse = 'MMSE' in df_header.columns
        return has_mmse
    except Exception as e:
        log_error(f"Error checking MMSE column: {e}")
        return False

def filter_by_mmse(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """
    Filter the dataframe to exclude participants with MMSE < threshold.
    Returns the filtered dataframe and the count of excluded participants.
    """
    if 'MMSE' not in df.columns:
        log_error("MMSE column not found in dataset. Cannot filter.")
        return df, 0
    
    total_before = len(df)
    filtered_df = df[df['MMSE'] >= threshold].copy()
    total_after = len(filtered_df)
    excluded_count = total_before - total_after
    
    log_info(f"MMSE Filter: Excluded {excluded_count} participants with MMSE < {threshold}")
    log_info(f"Remaining participants: {total_after}")
    
    return filtered_df, excluded_count

def run_robustness_analysis(original_results: Dict[str, Any], robust_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Re-run the statistical analysis on the MMSE-filtered dataset.
    Returns the robust analysis results.
    """
    if len(robust_df) < 2:
        log_error("Not enough data points for analysis after MMSE filtering.")
        return {"error": "Insufficient data after filtering"}

    # Group by stimulus type
    nostalgia_group = robust_df[robust_df['stimulus_type'] == 'nostalgia']
    control_group = robust_df[robust_df['stimulus_type'] == 'control']

    if len(nostalgia_group) == 0 or len(control_group) == 0:
        log_error("One of the groups is empty after MMSE filtering.")
        return {"error": "Empty group after filtering"}

    # Run Welch's t-test on perseverative_errors
    try:
        t_stat, p_val = welch_t_test(
            nostalgia_group['perseverative_errors'].dropna(),
            control_group['perseverative_errors'].dropna()
        )
        cohens_d = calculate_cohen_d(
            nostalgia_group['perseverative_errors'].dropna(),
            control_group['perseverative_errors'].dropna()
        )
        
        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "cohens_d": float(cohens_d),
            "nostalgia_n": len(nostalgia_group),
            "control_n": len(control_group),
            "metric": "perseverative_errors"
        }
    except Exception as e:
        log_error(f"Error running robustness analysis: {e}")
        return {"error": str(e)}

def save_robustness_report(report: Dict[str, Any], original_results: Dict[str, Any], mmse_excluded_count: int):
    """Save the robustness check report to data/results/robustness_report.json."""
    config = get_config()
    output_path = Path(config["paths"]["results"]) / "robustness_report.json"
    
    # Merge original results with robustness findings
    final_report = {
        "original_analysis": original_results,
        "robustness_check": {
            "mmse_threshold": get_mmse_threshold(),
            "participants_excluded": mmse_excluded_count,
            "results": report
        },
        "status": "completed"
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        log_info(f"Robustness report saved to {output_path}")
    except Exception as e:
        log_error(f"Failed to save robustness report: {e}")

def main():
    """Main entry point for T027: Robustness Check."""
    setup_logging(level=logging.INFO)
    log_info("Starting T027: Robustness Check (MMSE Filter)")

    # 1. Load the cleaned dataset
    df = load_cleaned_dataset()
    if df is None:
        log_error("Cannot proceed without cleaned dataset.")
        return

    # 2. Check if MMSE column exists (T013b dependency)
    has_mmse = load_mmse_flag()
    
    if not has_mmse:
        log_warning("ERR_MMSE_MISSING_SKIPPED: MMSE column not found in dataset. Skipping robustness filter.")
        # Load existing report if any and just add a note that this step was skipped
        original_report = load_statistical_report()
        if "robustness_check" not in original_report:
            original_report["robustness_check"] = {
                "status": "skipped",
                "reason": "ERR_MMSE_MISSING_SKIPPED"
            }
            # Save back to ensure the skip is recorded
            config = get_config()
            output_path = Path(config["paths"]["results"]) / "robustness_report.json"
            with open(output_path, 'w') as f:
                json.dump(original_report, f, indent=2)
        return

    log_info("MMSE column found. Proceeding with robustness check.")

    # 3. Load existing statistical report
    original_results = load_statistical_report()

    # 4. Filter by MMSE threshold
    threshold = get_mmse_threshold()
    filtered_df, excluded_count = filter_by_mmse(df, threshold)

    # 5. Re-run analysis on filtered data
    robust_results = run_robustness_analysis(original_results, filtered_df)

    # 6. Save the report
    save_robustness_report(robust_results, original_results, excluded_count)

    log_info("T027 Robustness Check completed successfully.")

if __name__ == "__main__":
    main()