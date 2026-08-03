import os
import sys
import json
import pandas as pd
import logging
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def check_sample_size(features_file_path, min_n=30):
    logger = setup_logger("sample_size_check")
    logger.info(f"Checking sample size in {features_file_path}")

    if not os.path.exists(features_file_path):
        logger.error(f"Features file not found: {features_file_path}")
        write_validation_report("fail", "File not found", features_file_path)
        return False

    try:
        df = pd.read_csv(features_file_path)
        if 'participant_id' not in df.columns:
            logger.error(f"Column 'participant_id' not found in {features_file_path}")
            write_validation_report("fail", "Missing column 'participant_id'", features_file_path)
            return False

        unique_participants = df['participant_id'].nunique()
        logger.info(f"Found {unique_participants} unique participants")

        if unique_participants < min_n:
            logger.error(f"Insufficient sample size: N={unique_participants} < {min_n}")
            write_validation_report("fail", f"Insufficient sample size: N={unique_participants} < {min_n}", features_file_path)
            return False

        logger.info(f"Sample size check passed: N={unique_participants} >= {min_n}")
        write_validation_report("pass", f"Sample size sufficient: N={unique_participants}", features_file_path)
        return True

    except Exception as e:
        logger.error(f"Error reading features file: {e}")
        write_validation_report("fail", str(e), features_file_path)
        return False

def write_validation_report(status, message, source_file):
    report = {
        "status": status,
        "message": message,
        "source_file": source_file,
        "min_required": 30
    }
    report_path = Path(__file__).parent.parent / "data" / "processed" / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Validation report written to {report_path}")

def main():
    config = load_config()
    # Default to lzc_metrics.csv as per task description, but could be configurable
    features_file = Path(__file__).parent.parent / "data" / "processed" / "lzc_metrics.csv"
    
    if not check_sample_size(str(features_file)):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
