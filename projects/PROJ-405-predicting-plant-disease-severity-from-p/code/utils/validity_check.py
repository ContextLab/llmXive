import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from config import get_path, ensure_dirs
from utils.logging_config import get_logger
from utils.reporting import load_results, save_results

logger = get_logger("validity_check")

def run_validity_check(sample_size: int = 50) -> Dict[str, Any]:
    """
    Check for non-null values in image features and weather variables on a random subset.
    
    This function validates the integrity of the unified dataset by ensuring that
    critical columns (image features and weather variables) contain non-null values.
    It operates on a random sample to minimize overhead while providing statistical
    confidence in the data quality.
    
    Args:
        sample_size: Number of records to sample for the check. Defaults to 50.
    
    Returns:
        Dictionary with validity results including status, sample size, null counts,
        and observational status flag.
    """
    # Ensure output directories exist
    ensure_dirs(["data_processed", "artifacts"])
    
    input_path = get_path("data_processed") / "unified_analysis.csv"
    
    if not input_path.exists():
        error_msg = f"Input file {input_path} not found. Cannot run validity check."
        logger.error(error_msg)
        return {"status": "failed", "reason": "Input file missing", "observational_status": True}
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        error_msg = f"Failed to read input file {input_path}: {str(e)}"
        logger.error(error_msg)
        return {"status": "failed", "reason": f"File read error: {str(e)}", "observational_status": True}
    
    if df.empty:
        error_msg = "Input DataFrame is empty. Cannot perform validity check."
        logger.error(error_msg)
        return {"status": "failed", "reason": "Empty dataset", "observational_status": True}
    
    logger.info(f"Loaded dataset with {len(df)} records. Sampling {min(sample_size, len(df))} records.")
    
    # Random sample for validation
    if len(df) > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42)
    else:
        df_sample = df
        logger.info(f"Dataset size ({len(df)}) is less than sample size ({sample_size}). Using full dataset.")
    
    # Define required columns based on the data model
    required_cols = [
        "lesion_area_ratio", "necrosis_color_index", "texture_entropy",
        "mean_temp", "mean_humidity", "total_precipitation"
    ]
    
    # Check for missing columns
    missing_cols = [c for c in required_cols if c not in df_sample.columns]
    if missing_cols:
        error_msg = f"Missing required columns in sample: {missing_cols}"
        logger.error(error_msg)
        return {
            "status": "failed", 
            "reason": f"Missing columns: {missing_cols}",
            "sample_size": len(df_sample),
            "observational_status": True
        }
    
    # Check for null values in required columns
    null_counts = {}
    valid = True
    total_nulls = 0
    
    for col in required_cols:
        null_count = int(df_sample[col].isna().sum())
        null_counts[col] = null_count
        total_nulls += null_count
        
        if null_count > 0:
            valid = False
            warning_msg = f"Found {null_count} null values in {col} ({null_count/len(df_sample)*100:.2f}% of sample)."
            logger.warning(warning_msg)
    
    # Calculate null rate
    null_rate = total_nulls / (len(df_sample) * len(required_cols)) if len(required_cols) > 0 else 0.0
    
    result = {
        "status": "passed" if valid else "failed",
        "sample_size": len(df_sample),
        "null_counts": null_counts,
        "total_nulls": total_nulls,
        "null_rate": null_rate,
        "observational_status": True,
        "message": "Data contains non-null values for key features." if valid else f"Data contains {total_nulls} null values across required columns."
    }
    
    logger.info(f"Validity check completed: {result['status']}")
    logger.info(f"Null rate: {null_rate:.4f} ({null_rate*100:.2f}%)")
    
    return result

def generate_validity_report() -> Dict[str, Any]:
    """
    Generate a validity report stating the study is 'Observational' (no ground truth).
    
    This function creates a JSON report file documenting the observational nature of the study.
    It does NOT perform correlation checks or block execution.
    
    Returns:
        Dictionary containing the validity report data.
    """
    ensure_dirs(["artifacts"])
    
    report_data = {
        "study_type": "Observational",
        "ground_truth_available": False,
        "methodology_note": "No expert-labeled severity scores or simulated ground truth exist. "
                            "Findings are framed as associational based on metadata presence and non-null feature values.",
        "validation_scope": "Data integrity check only (non-null values in image features and weather variables).",
        "correlation_checks_performed": False,
        "blocking_execution": False,
        "generated_by": "T019b: generate_validity_report",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    output_path = get_path("artifacts") / "validity_report.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Validity report generated at {output_path}")
    except Exception as e:
        error_msg = f"Failed to write validity report to {output_path}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    
    return report_data

def update_results_with_validity_flag(validity_result: Dict[str, Any]) -> None:
    """
    Update results.json with the validity check outcome.
    
    This function merges the validity check results into the main results file,
    ensuring the observational status is properly flagged.
    
    Args:
        validity_result: Dictionary containing the validity check results.
    """
    results = load_results()
    results["validity_check"] = validity_result
    
    # Always set observational status to true as per study design
    results["observational_status"] = True
    
    save_results(results)
    logger.info("Results updated with validity check flag.")

def main():
    """
    Entry point for validity check.
    
    Runs the validity check on a random subset of the unified dataset,
    generates the validity report, and updates the results file with the findings.
    """
    logger.info("Starting validity check process...")
    
    # Run the validity check
    check_result = run_validity_check(sample_size=50)
    
    # Generate the validity report
    report_result = generate_validity_report()
    
    # Update results with validity flag
    update_results_with_validity_flag(check_result)
    
    logger.info("Validity check process completed.")
    return check_result, report_result

if __name__ == "__main__":
    main()