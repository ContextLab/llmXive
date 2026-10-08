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
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input data file not found: {data_path}")
        
    df = pd.read_csv(data_path)
    
    if 'subject_id' not in df.columns:
        raise ValueError("Data must contain 'subject_id' column for trial validation.")
    
    # Count trials per subject
    trial_counts = df.groupby('subject_id').size().reset_index(name='trial_count')
    
    # Get configuration values
    threshold = config.get('trial_count_threshold', 20)
    aggregate = config.get('aggregation', False)
    
    logger.info(f"Validating trial counts (threshold={threshold}, aggregation={aggregate})")
    
    # Identify subjects with insufficient trials
    violations = trial_counts[trial_counts['trial_count'] < threshold]
    
    if not violations.empty:
        violation_details = []
        for _, row in violations.iterrows():
            sub_id = row['subject_id']
            count = row['trial_count']
            violation_details.append(f"Subject {sub_id} has {count} trials")
        
        if not aggregate:
            error_msg = "Validation Failed: " + ", ".join(violation_details) + ". " + \
                        "Insufficient trials per subject and aggregation is disabled."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            logger.warning(f"Aggregation is enabled. Proceeding with subjects having < {threshold} trials: {violation_details}")
    
    # Generate validation status column
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
    # Verify config.yaml exists
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    if not config_path.exists():
        logger.warning("config.yaml not found in project root. Creating default config with aggregation=false.")
        # Create a minimal default config to allow the script to run or fail gracefully
        default_config = {
            "seeds": 42,
            "thresholds": {"low": 0.40, "mid": 0.50, "high": 0.60},
            "paths": {
                "data_raw": "data/raw",
                "data_processed": "data/processed",
                "results": "results"
            },
            "aggregation": False,
            "trial_count_threshold": 20
        }
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
        logger.warning(f"Default config written to {config_path}")
        config = default_config
    else:
        config = load_config()

    # Check aggregation flag specifically
    if 'aggregation' not in config:
        logger.warning("'aggregation' key missing in config.yaml. Defaulting to false.")
        config['aggregation'] = False

    # Construct path to processed features
    data_dir = config.get('paths', {}).get('data_processed', 'data/processed')
    data_path = os.path.join(data_dir, 'features.csv')
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data file not found at {data_path}. "
                                "Please ensure T015a/T015b/T016a have completed successfully.")
    
    try:
        validation_report = validate_trial_counts(data_path, config)
        logger.info("Trial validation completed successfully.")
        logger.info(f"Summary:\n{validation_report.to_string(index=False)}")
        
        # Write validation log
        results_dir = config.get('paths', {}).get('results', 'results')
        # Ensure results directory exists
        os.makedirs(results_dir, exist_ok=True)
        
        log_path = os.path.join(results_dir, 'trial_validation.log')
        
        with open(log_path, 'w') as f:
            f.write("Trial Validation Log\n")
            f.write("=" * 40 + "\n")
            f.write(f"Timestamp: {pd.Timestamp.now()}\n")
            f.write(f"Input file: {data_path}\n")
            f.write(f"Threshold: {config.get('trial_count_threshold', 20)}\n")
            f.write(f"Aggregation: {config.get('aggregation', False)}\n")
            f.write("\n")
            f.write("Validation Results:\n")
            f.write(validation_report.to_string(index=False))
            f.write("\n")
            
        logger.info(f"Validation log saved to {log_path}")
        
        # Also save CSV report for downstream tasks
        csv_report_path = os.path.join(results_dir, 'trial_validation_report.csv')
        validation_report.to_csv(csv_report_path, index=False)
        logger.info(f"Validation report saved to {csv_report_path}")
        
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        raise

def main():
    run_validation_pipeline()

if __name__ == "__main__":
    main()
