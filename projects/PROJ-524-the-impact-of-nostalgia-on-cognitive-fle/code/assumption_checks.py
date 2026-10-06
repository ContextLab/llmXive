"""
Statistical Assumption Checks Module (Task T052).

Implements checks for normality (Shapiro-Wilk) and homogeneity of variance (Levene's test)
prior to running Welch's t-test. Logs results to data/results/assumption_checks.json.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

from config import get_config
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()

def load_cleaned_dataset() -> pd.DataFrame:
    """
    Loads the final cleaned dataset from data/processed/final_cleaned_dataset.csv.
    
    Returns:
        pd.DataFrame: The cleaned dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    config = get_config()
    file_path = config['paths']['processed'] / 'final_cleaned_dataset.csv'
    
    if not file_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {file_path}")
    
    logger.info(f"Loading cleaned dataset from {file_path}")
    return pd.read_csv(file_path)

def check_normality_shapiro(df: pd.DataFrame, column: str, group_col: str = 'stimulus_type') -> dict:
    """
    Performs Shapiro-Wilk test for normality on each group for a specific column.
    
    Args:
        df: The dataframe containing the data.
        column: The column to test (e.g., 'perseverative_errors').
        group_col: The column defining the groups (default: 'stimulus_type').
        
    Returns:
        dict: A dictionary with test results for each group.
    """
    results = {}
    groups = df[group_col].unique()
    
    for group in groups:
        group_data = df[df[group_col] == group][column].dropna()
        
        if len(group_data) < 3:
            # Shapiro-Wilk requires at least 3 samples
            results[group] = {
                "status": "skipped",
                "reason": "Sample size < 3",
                "statistic": None,
                "p_value": None
            }
            log_warning(f"Shapiro-Wilk skipped for {group} on {column}: n={len(group_data)}")
            continue
        
        try:
            stat, p_value = stats.shapiro(group_data)
            results[group] = {
                "status": "passed" if p_value > 0.05 else "failed",
                "statistic": float(stat),
                "p_value": float(p_value)
            }
            if p_value <= 0.05:
                log_warning(f"Normality assumption VIOLATED for {group} on {column} (p={p_value:.4f})")
            else:
                log_info(f"Normality assumption holds for {group} on {column} (p={p_value:.4f})")
        except Exception as e:
            log_error(f"Error running Shapiro-Wilk for {group} on {column}: {e}")
            results[group] = {
                "status": "error",
                "reason": str(e),
                "statistic": None,
                "p_value": None
            }
    
    return results

def check_homogeneity_levene(df: pd.DataFrame, column: str, group_col: str = 'stimulus_type') -> dict:
    """
    Performs Levene's test for homogeneity of variance between groups.
    
    Args:
        df: The dataframe containing the data.
        column: The column to test (e.g., 'perseverative_errors').
        group_col: The column defining the groups (default: 'stimulus_type').
        
    Returns:
        dict: A dictionary with the test result.
    """
    groups = df[group_col].unique()
    if len(groups) < 2:
        log_error("Levene's test requires at least 2 groups.")
        return {
            "status": "skipped",
            "reason": "Less than 2 groups found",
            "statistic": None,
            "p_value": None
        }
    
    # Prepare data for Levene's test
    data_arrays = [df[df[group_col] == g][column].dropna() for g in groups]
    
    # Check if all arrays have enough data
    if any(len(arr) < 2 for arr in data_arrays):
        log_warning("Levene's test skipped: one or more groups have < 2 samples.")
        return {
            "status": "skipped",
            "reason": "Insufficient samples in one or more groups",
            "statistic": None,
            "p_value": None
        }
    
    try:
        stat, p_value = stats.levene(*data_arrays)
        result = {
            "status": "passed" if p_value > 0.05 else "failed",
            "statistic": float(stat),
            "p_value": float(p_value)
        }
        
        if p_value <= 0.05:
            log_warning(f"Homogeneity of variance VIOLATED for {column} (p={p_value:.4f}). Welch's t-test is appropriate.")
        else:
            log_info(f"Homogeneity of variance holds for {column} (p={p_value:.4f}).")
            
        return result
    except Exception as e:
        log_error(f"Error running Levene's test for {column}: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "statistic": None,
            "p_value": None
        }

def run_assumption_checks() -> dict:
    """
    Runs all assumption checks on the final cleaned dataset.
    
    Returns:
        dict: A complete report of assumption check results.
    """
    try:
        df = load_cleaned_dataset()
    except FileNotFoundError as e:
        log_error(str(e))
        return {"error": str(e)}
    
    report = {
        "timestamp": get_timestamp(),
        "dataset_path": "data/processed/final_cleaned_dataset.csv",
        "total_records": len(df),
        "groups": list(df['stimulus_type'].unique()),
        "checks": {}
    }
    
    # Columns to check based on T018 requirements
    metrics = ['perseverative_errors', 'categories_completed']
    
    for metric in metrics:
        if metric not in df.columns:
            log_warning(f"Metric {metric} not found in dataset, skipping checks.")
            continue
        
        report["checks"][metric] = {
            "normality": check_normality_shapiro(df, metric),
            "homogeneity": check_homogeneity_levene(df, metric)
        }
    
    # Determine if assumptions are severely violated
    # For Welch's t-test, we specifically care about homogeneity. 
    # Normality is less critical for Welch's with large N, but we log it.
    violations = []
    for metric, checks in report["checks"].items():
        if checks["homogeneity"]["status"] == "failed":
            violations.append(f"{metric}_homogeneity")
    
    if violations:
        log_warning(f"Assumptions severely violated for: {violations}. Proceeding with Welch's t-test (robust).")
        report["summary"] = {
            "assumptions_met": False,
            "violations": violations,
            "recommendation": "Proceed with Welch's t-test as planned."
        }
    else:
        log_info("Assumptions generally met or no critical violations found.")
        report["summary"] = {
            "assumptions_met": True,
            "violations": [],
            "recommendation": "Standard parametric tests are appropriate."
        }
        
    return report

def save_report(report: dict, output_path: str = None):
    """
    Saves the assumption check report to a JSON file.
    
    Args:
        report: The report dictionary.
        output_path: Path to save the JSON file. Defaults to config path.
    """
    config = get_config()
    if output_path is None:
        output_path = config['paths']['results'] / 'assumption_checks.json'
    else:
        output_path = Path(output_path)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    log_info(f"Assumption checks report saved to {output_path}")

def main():
    """Main entry point for T052."""
    log_info("Starting Statistical Assumption Checks (T052)...")
    
    report = run_assumption_checks()
    
    if "error" in report:
        log_error(f"Failed to run checks: {report['error']}")
        # Save error report to ensure artifact exists even on failure
        save_report(report)
        return 1
        
    save_report(report)
    log_info("Statistical Assumption Checks completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
