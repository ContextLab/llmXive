import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime

# Import logging utility from the project's existing API surface
from utils.logging_config import get_logger

# Constants
VALIDITY_THRESHOLD = 0.30  # 30% minimum valid threads required
VALIDITY_REPORT_PATH = "data/processed/validity_failure_report.json"
VALIDATED_DATASET_PATH = "data/processed/valid_threads.csv"

# Initialize logger
logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the processed dataset from data/processed/threads_processed.csv.
    Returns a DataFrame containing thread-level metrics and metadata.
    """
    input_path = Path("data/processed/threads_processed.csv")
    if not input_path.exists():
        logger.error(f"Processed data file not found at {input_path}")
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} threads from {input_path}")
    return df

def check_ground_truth_availability(thread_row: pd.Series) -> Tuple[bool, Optional[str]]:
    """
    Check if a thread has valid ground truth data for external validation.
    
    Args:
        thread_row: A single row from the processed threads DataFrame.
        
    Returns:
        Tuple of (has_ground_truth, reason_if_missing)
    """
    # Check for required ground truth columns
    gt_columns = ['ground_truth_label', 'ground_truth_source']
    missing_cols = [col for col in gt_columns if col not in thread_row.index or pd.isna(thread_row[col])]
    
    if missing_cols:
        return False, f"Missing ground truth columns: {missing_cols}"
    
    # Check if ground truth value is valid (not NaN, not empty string)
    if pd.isna(thread_row.get('ground_truth_label')) or str(thread_row.get('ground_truth_label')).strip() == '':
        return False, "Ground truth label is missing or empty"
    
    return True, None

def classify_thread(thread_row: pd.Series) -> str:
    """
    Classify a thread as 'valid' or 'excluded' based on ground truth availability.
    
    Args:
        thread_row: A single row from the processed threads DataFrame.
        
    Returns:
        'valid' if ground truth is available, 'excluded' otherwise.
    """
    has_gt, reason = check_ground_truth_availability(thread_row)
    
    if has_gt:
        return 'valid'
    else:
        # Log exclusion reason for debugging
        logger.debug(f"Thread {thread_row.get('thread_id', 'unknown')} excluded: {reason}")
        return 'excluded'

def validate_and_classify(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply classification logic to all threads in the DataFrame.
    
    Args:
        df: DataFrame of processed threads.
        
    Returns:
        DataFrame with an additional 'classification' column.
    """
    logger.info("Starting thread classification based on ground truth availability")
    
    df['classification'] = df.apply(classify_thread, axis=1)
    
    valid_count = (df['classification'] == 'valid').sum()
    excluded_count = (df['classification'] == 'excluded').sum()
    total_count = len(df)
    
    logger.info(f"Classification complete: {valid_count} valid, {excluded_count} excluded out of {total_count} threads")
    
    return df

def save_validated_dataset(df: pd.DataFrame) -> Path:
    """
    Save the classified dataset to the output file.
    
    Args:
        df: DataFrame with classification column.
        
    Returns:
        Path to the saved file.
    """
    output_path = Path(VALIDATED_DATASET_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validated dataset to {output_path}")
    
    return output_path

def generate_failure_report(valid_percentage: float, total_threads: int, valid_threads: int, excluded_threads: int) -> Dict[str, Any]:
    """
    Generate a formal failure report when valid threads < 30%.
    
    Args:
        valid_percentage: Percentage of valid threads.
        total_threads: Total number of threads analyzed.
        valid_threads: Number of valid threads.
        excluded_threads: Number of excluded threads.
        
    Returns:
        Dictionary containing the failure report data.
    """
    report = {
        "report_type": "validity_failure_report",
        "timestamp": datetime.now().isoformat(),
        "specification_reference": "SC-006",
        "threshold": VALIDITY_THRESHOLD,
        "result": "FAILED",
        "statistics": {
            "total_threads": total_threads,
            "valid_threads": valid_threads,
            "excluded_threads": excluded_threads,
            "valid_percentage": valid_percentage,
            "excluded_percentage": 100.0 - valid_percentage
        },
        "reason": f"Valid threads ({valid_percentage:.2f}%) are below the required threshold of {VALIDITY_THRESHOLD * 100:.0f}%.",
        "implications": "The study cannot proceed with statistical modeling as per SC-006. This is a valid research outcome indicating insufficient ground truth data availability.",
        "recommendations": [
            "Investigate data sources for ground truth labels",
            "Consider expanding data collection to include more threads with ground truth",
            "Review ground truth annotation protocol for completeness",
            "Document this limitation in the final research paper"
        ]
    }
    
    return report

def run_validation_pipeline() -> Dict[str, Any]:
    """
    Run the complete validation pipeline:
    1. Load processed data
    2. Classify threads
    3. Save validated dataset
    4. Check SC-006 threshold and generate failure report if needed
    
    Returns:
        Dictionary containing pipeline results and status.
    """
    logger.info("Starting validation pipeline")
    
    try:
        # Load data
        df = load_processed_data()
        
        # Classify threads
        df_classified = validate_and_classify(df)
        
        # Save validated dataset
        save_validated_dataset(df_classified)
        
        # Calculate statistics
        valid_count = (df_classified['classification'] == 'valid').sum()
        total_count = len(df_classified)
        excluded_count = total_count - valid_count
        
        if total_count == 0:
            valid_percentage = 0.0
        else:
            valid_percentage = (valid_count / total_count) * 100.0
        
        logger.info(f"Valid threads: {valid_count}/{total_count} ({valid_percentage:.2f}%)")
        
        # Check SC-006 threshold
        status = "PASSED"
        failure_report = None
        
        if valid_percentage < (VALIDITY_THRESHOLD * 100):
            status = "FAILED"
            logger.warning(f"SC-006 check FAILED: {valid_percentage:.2f}% < {VALIDITY_THRESHOLD * 100:.0f}%")
            
            # Generate and save failure report
            failure_report = generate_failure_report(
                valid_percentage, total_count, valid_count, excluded_count
            )
            
            report_path = Path(VALIDITY_REPORT_PATH)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(failure_report, f, indent=2)
            
            logger.info(f"Generated failure report at {report_path}")
        else:
            logger.info(f"SC-006 check PASSED: {valid_percentage:.2f}% >= {VALIDITY_THRESHOLD * 100:.0f}%")
        
        return {
            "status": status,
            "total_threads": total_count,
            "valid_threads": int(valid_count),
            "excluded_threads": int(excluded_count),
            "valid_percentage": valid_percentage,
            "threshold": VALIDITY_THRESHOLD,
            "failure_report_path": str(Path(VALIDITY_REPORT_PATH)) if failure_report else None,
            "validated_dataset_path": str(Path(VALIDATED_DATASET_PATH))
        }
        
    except Exception as e:
        logger.error(f"Validation pipeline failed: {str(e)}", exc_info=True)
        raise

def main():
    """
    Main entry point for the validation script.
    """
    logger.info("Running validation.py main")
    
    try:
        results = run_validation_pipeline()
        
        print("\n=== Validation Pipeline Results ===")
        print(f"Status: {results['status']}")
        print(f"Total Threads: {results['total_threads']}")
        print(f"Valid Threads: {results['valid_threads']} ({results['valid_percentage']:.2f}%)")
        print(f"Excluded Threads: {results['excluded_threads']}")
        print(f"Threshold: {results['threshold'] * 100:.0f}%")
        
        if results['status'] == 'FAILED':
            print(f"\n⚠ SC-006 FAILURE DETECTED")
            print(f"Valid threads ({results['valid_percentage']:.2f}%) are below the required threshold.")
            print(f"Failure report generated at: {results['failure_report_path']}")
        else:
            print(f"\n✓ SC-006 PASSED")
            print(f"Valid threads meet the required threshold.")
        
        print(f"\nValidated dataset saved to: {results['validated_dataset_path']}")
        
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()