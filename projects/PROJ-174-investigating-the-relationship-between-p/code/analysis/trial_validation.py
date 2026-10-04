import os
import sys
import logging
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure parent directory is in path for imports if running as script
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from config import load_config
from logging_config import get_logger

logger = get_logger(__name__)

def validate_trial_counts(data_path: str, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Validates that each subject has sufficient trials for LME modeling.
    
    Args:
        data_path: Path to the processed features CSV.
        config: Configuration dictionary containing 'aggregation' flag and 'trial_count_threshold'.
        
    Returns:
        DataFrame with subject trial counts and validation status.
        
    Raises:
        RuntimeError: If any subject has fewer trials than the threshold 
                      and aggregation is disabled.
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    if 'subject_id' not in df.columns:
        raise ValueError("Data must contain 'subject_id' column for trial validation.")
    
    trial_counts = df.groupby('subject_id').size().reset_index(name='trial_count')
    
    threshold = config.get('trial_count_threshold', 20)
    aggregate = config.get('aggregation', False)
    
    logger.info(f"Validating trial counts (threshold={threshold}, aggregation={aggregate})")
    
    violations = trial_counts[trial_counts['trial_count'] < threshold]
    
    if not violations.empty:
        violation_details = violations['subject_id'].apply(
            lambda x: f"Subject {x} has {violations.loc[violations['subject_id'] == x, 'trial_count'].values[0]} trials"
        ).tolist()
        
        if not aggregate:
            error_msg = "Validation Failed: " + ", ".join(violation_details) + ". " + \
                        "Insufficient trials per subject and aggregation is disabled."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            logger.warning(f"Aggregation is enabled. Proceeding with subjects having < {threshold} trials: {violation_details}")
            # In aggregation mode, we might still want to log which subjects are low,
            # but we don't raise an error. The model fitting logic (T021b) handles
            # the actual aggregation or reduced model fitting.
    
    validation_status = []
    for _, row in trial_counts.iterrows():
        if row['trial_count'] >= threshold:
            validation_status.append("PASS")
        else:
            if aggregate:
                validation_status.append("LOW_COUNT_AGGREGATE")
            else:
                validation_status.append("FAIL")
                
    trial_counts['validation_status'] = validation_status
    
    return trial_counts

def run_validation_pipeline() -> None:
    """
    Main entry point for the trial validation pipeline.
    Loads config, validates data, and logs results.
    """
    config = load_config()
    data_path = config['paths']['data_processed'] + '/features.csv'
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data file not found at {data_path}. "
                                "Please ensure T015a/T015b/T016a have completed successfully.")
    
    try:
        validation_report = validate_trial_counts(data_path, config)
        logger.info("Trial validation completed successfully.")
        logger.info(f"Summary:\n{validation_report.to_string(index=False)}")
        
        # Optionally save the validation report
        report_path = config['paths']['results'] + '/trial_validation_report.csv'
        validation_report.to_csv(report_path, index=False)
        logger.info(f"Validation report saved to {report_path}")
        
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        raise

def main():
    run_validation_pipeline()

if __name__ == "__main__":
    main()