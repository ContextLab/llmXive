import os
import sys
import json
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Import shared utilities from the project's API surface
# These names are guaranteed to exist in code/utils/logging.py and code/config.yaml handling
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback if utils.logging is not fully set up in this specific execution context
    # We define a minimal local logger to ensure this script runs standalone
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def load_config():
    """Loads configuration from code/config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        # Return defaults if config is missing, though it should exist per T005
        return {
            "min_sample_size": 30,
            "lzc_file": "data/processed/lzc_metrics.csv",
            "pe_file": "data/processed/pe_metrics.csv"
        }
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure defaults for this specific task's keys if not present
    config.setdefault("min_sample_size", 30)
    # Define paths relative to project root (where this script is run from)
    # The task description implies running from project root
    config.setdefault("lzc_file", "data/processed/lzc_metrics.csv")
    config.setdefault("pe_file", "data/processed/pe_metrics.csv")
    
    return config

def write_validation_report(message: str, status: str = "FAIL", details: dict = None):
    """Writes the validation report to data/analysis/validation_report.json."""
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / "validation_report.json"
    
    report = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_path

def check_sample_size():
    """
    Enforces N >= 30 constraint as a blocking gate before analysis.
    Reads lzc_metrics.csv (or pe_metrics.csv) and counts unique participants.
    Exits with code 1 if count < 30.
    """
    logger = get_logger("check_sample_size")
    config = load_config()
    
    min_n = config.get("min_sample_size", 30)
    lzc_path = Path(config.get("lzc_file", "data/processed/lzc_metrics.csv"))
    pe_path = Path(config.get("pe_file", "data/processed/pe_metrics.csv"))
    
    # Determine which file to use
    target_file = None
    if lzc_path.exists():
        target_file = lzc_path
        logger.info(f"Using LZC metrics file: {target_file}")
    elif pe_path.exists():
        target_file = pe_path
        logger.info(f"LZC file missing, using PE metrics file: {target_file}")
    else:
        error_msg = "Insufficient sample size: N < 30. Missing both LZC and PE metrics files."
        logger.error(error_msg)
        write_validation_report(error_msg, status="FAIL", details={"missing_files": [str(lzc_path), str(pe_path)]})
        return False, error_msg
    
    try:
        # Read the CSV
        df = pd.read_csv(target_file)
        
        # Check for required column
        if "participant_id" not in df.columns:
            error_msg = f"Insufficient sample size: N < 30. File {target_file} missing 'participant_id' column."
            logger.error(error_msg)
            write_validation_report(error_msg, status="FAIL", details={"columns_found": list(df.columns)})
            return False, error_msg
        
        # Count unique participants
        unique_participants = df["participant_id"].nunique()
        
        if unique_participants < min_n:
            error_msg = f"Insufficient sample size: N = {unique_participants} < {min_n}. Analysis cannot proceed."
            logger.error(error_msg)
            write_validation_report(error_msg, status="FAIL", details={"n_found": unique_participants, "n_required": min_n})
            return False, error_msg
        
        success_msg = f"Sample size check passed: N = {unique_participants} >= {min_n}."
        logger.info(success_msg)
        write_validation_report(success_msg, status="PASS", details={"n_found": unique_participants, "n_required": min_n})
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Error reading metrics file {target_file}: {str(e)}"
        logger.error(error_msg)
        write_validation_report(error_msg, status="FAIL", details={"error": str(e)})
        return False, error_msg

def main():
    """Main entry point for the sample size check."""
    logger = get_logger("check_sample_size")
    logger.info("Starting sample size validation gate.")
    
    passed, message = check_sample_size()
    
    if not passed:
        logger.error("Sample size validation FAILED. Exiting with code 1.")
        sys.exit(1)
    else:
        logger.info("Sample size validation PASSED. Exiting with code 0.")
        sys.exit(0)

if __name__ == "__main__":
    main()
