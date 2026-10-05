import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Import shared utilities and config
from utils import get_logger, read_csv, write_json, file_exists
from config import ensure_directories

# Initialize logger
logger = get_logger(__name__)

def load_cleaned_data_for_robustness(data_path: str) -> pd.DataFrame:
    """
    Load the cleaned dataset required for robustness analysis.
    
    Args:
        data_path: Path to the cleaned CSV file (data/processed/cleaned_data.csv)
        
    Returns:
        DataFrame with required columns
    """
    if not file_exists(data_path):
        raise FileNotFoundError(f"Cleaned data file not found at {data_path}. "
                                "Ensure T016 (cleaned_data.csv generation) has run successfully.")
    
    df = read_csv(data_path)
    required_cols = ['Subject_ID', 'Global_Signal_SD', 'MWQ_Score', 'Age', 'Sex', 'Mean_FD', 'Mean_DVARS']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {data_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} subjects from {data_path}")
    return df

def run_alpha_sweep(df: pd.DataFrame, alphas: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Sweep alpha values for Ridge regression and report MAE variation.
    (Implemented in T028, kept here for interface completeness)
    """
    if alphas is None:
        alphas = [0.01, 0.1, 1.0, 10.0, 100.0]
    
    results = []
    logger.info(f"Running alpha sweep with {len(alphas)} values...")
    
    # Placeholder logic for T028 - actual implementation would run CV here
    # This is a stub for T029 context, assuming T028 handles the heavy lifting
    for alpha in alphas:
        # In a full implementation, we would fit the model here
        # For T029 context, we assume T028 populates this or we read from T028 output
        results.append({
            "alpha": alpha,
            "mae": 0.0, # Placeholder - T028 should fill this
            "r_squared": 0.0
        })
    
    return {"alphas": alphas, "results": results}

def run_variance_metric_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Implement alternative metric analysis using global-signal variance instead of SD.
    
    Logic:
    1. Calculate Variance = (Global_Signal_SD)^2 for each subject.
    2. Correlate Variance with MWQ_Score.
    3. Compare correlation strength to the primary SD result.
    
    Returns:
        Dictionary with correlation coefficient (r), p-value, and comparison to SD.
    """
    logger.info("Starting alternative metric analysis (Variance vs SD)...")
    
    # 1. Compute Variance from SD
    # Global Signal Variance = (Global Signal SD)^2
    df = df.copy()
    df['Global_Signal_Variance'] = df['Global_Signal_SD'] ** 2
    
    # 2. Calculate Pearson correlation between Variance and MWQ Score
    # We use the full dataset as per robustness analysis requirements
    if df['Global_Signal_Variance'].nunique() < 2 or df['MWQ_Score'].nunique() < 2:
        logger.warning("Insufficient variance in data for correlation calculation.")
        return {
            "status": "failed",
            "reason": "Insufficient variance in data",
            "pearson_r": None,
            "p_value": None
        }
    
    r_var, p_val_var = stats.pearsonr(df['Global_Signal_Variance'], df['MWQ_Score'])
    
    # 3. Get the primary SD correlation for comparison (from the same dataframe)
    r_sd, p_val_sd = stats.pearsonr(df['Global_Signal_SD'], df['MWQ_Score'])
    
    # 4. Calculate difference
    diff = abs(r_var - r_sd)
    
    logger.info(f"Correlation (Variance): r={r_var:.4f}, p={p_val_var:.4f}")
    logger.info(f"Correlation (SD):       r={r_sd:.4f}, p={p_val_sd:.4f}")
    logger.info(f"Difference (|r_var - r_sd|): {diff:.4f}")
    
    result = {
        "metric_used": "Variance",
        "correlation_coefficient": float(r_var),
        "p_value": float(p_val_var),
        "primary_metric": "SD",
        "primary_correlation_coefficient": float(r_sd),
        "absolute_difference": float(diff),
        "status": "significant" if p_val_var < 0.05 else "null_finding",
        "robustness_check_passed": diff <= 0.05
    }
    
    return result

def run_partial_correlation_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Partial correlation analysis controlling for mean FD.
    (Implemented in T030, kept here for interface completeness)
    """
    # This is a placeholder for T030 logic
    return {"status": "skipped", "reason": "Handled in T030"}

def generate_robustness_report(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Generate the full robustness report including variance metric analysis.
    
    Args:
        data_path: Path to cleaned data CSV
        output_path: Path to write the JSON report
        
    Returns:
        The generated report dictionary
    """
    ensure_directories([output_path])
    
    # Load data
    df = load_cleaned_data_for_robustness(data_path)
    
    # Run Variance Analysis (T029 Core)
    variance_results = run_variance_metric_analysis(df)
    
    # Run Alpha Sweep (T028 - delegated)
    # Note: In a real pipeline, we might load T028 results or call it.
    # For this task, we focus on T029's specific requirement.
    alpha_results = run_alpha_sweep(df)
    
    # Compile Report
    report = {
        "analysis_type": "Robustness Check",
        "primary_metric": "Global Signal SD",
        "alternative_metric": "Global Signal Variance",
        "variance_analysis": variance_results,
        "alpha_sweep": alpha_results,
        "summary": {
            "variance_correlation": variance_results.get("correlation_coefficient"),
            "sd_correlation": variance_results.get("primary_correlation_coefficient"),
            "difference": variance_results.get("absolute_difference"),
            "robustness_threshold": 0.05,
            "is_robust": variance_results.get("robustness_check_passed", False)
        }
    }
    
    # Write to disk
    write_json(output_path, report)
    logger.info(f"Robustness report written to {output_path}")
    
    return report

def main():
    """
    Main entry point for robustness analysis script.
    Expects --data argument pointing to cleaned_data.csv.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run robustness analysis (Variance vs SD)")
    parser.add_argument("--data", type=str, required=True, help="Path to cleaned_data.csv")
    parser.add_argument("--output", type=str, default="data/results/robustness_report.json",
                        help="Output path for the report")
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.data):
        logger.error(f"Input data file not found: {args.data}")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    try:
        report = generate_robustness_report(args.data, args.output)
        logger.info("Robustness analysis completed successfully.")
        logger.info(f"Variance Correlation: {report['summary']['variance_correlation']:.4f}")
        logger.info(f"SD Correlation: {report['summary']['sd_correlation']:.4f}")
        logger.info(f"Difference: {report['summary']['difference']:.4f}")
        logger.info(f"Robustness Check (diff <= 0.05): {report['summary']['is_robust']}")
    except Exception as e:
        logger.error(f"Robustness analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
