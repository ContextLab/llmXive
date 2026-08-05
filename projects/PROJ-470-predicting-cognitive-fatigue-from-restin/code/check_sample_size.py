import os
import sys
import json
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.warning(f"Could not load config.yaml: {e}. Using defaults.")
        return {"min_sample_size": 30}

def write_validation_report(status, message, details):
    """Write validation report to data/analysis/validation_report.json."""
    report_dir = Path("data/analysis")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    
    report_path = report_dir / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Validation report written to {report_path}")
    return report_path

def check_sample_size(metrics_file, alt_metrics_file=None, min_n=30):
    """
    Check if the sample size meets the minimum requirement.
    
    Args:
        metrics_file: Path to primary metrics CSV (lzc_metrics.csv)
        alt_metrics_file: Path to alternative metrics CSV (pe_metrics.csv)
        min_n: Minimum required number of unique participants
        
    Returns:
        Tuple (success: bool, count: int, message: str)
    """
    # Try primary file first
    if os.path.exists(metrics_file):
        try:
            df = pd.read_csv(metrics_file)
            if 'participant_id' not in df.columns:
                msg = f"File {metrics_file} missing required column 'participant_id'"
                write_validation_report("FAIL", msg, {
                    "file": metrics_file,
                    "min_required": min_n
                })
                return False, 0, msg
            
            count = df['participant_id'].nunique()
            if count >= min_n:
                msg = f"Sample size OK: N={count} >= {min_n}"
                write_validation_report("PASS", msg, {
                    "file": metrics_file,
                    "participant_count": count,
                    "min_required": min_n
                })
                return True, count, msg
            else:
                msg = f"Insufficient sample size: N={count} < {min_n}"
                write_validation_report("FAIL", msg, {
                    "file": metrics_file,
                    "participant_count": count,
                    "min_required": min_n
                })
                return False, count, msg
        except Exception as e:
            msg = f"Error reading {metrics_file}: {str(e)}"
            logging.error(msg)
            # Fall through to try alternative file
    
    # Try alternative file if primary failed or doesn't exist
    if alt_metrics_file and os.path.exists(alt_metrics_file):
        try:
            df = pd.read_csv(alt_metrics_file)
            if 'participant_id' not in df.columns:
                msg = f"File {alt_metrics_file} missing required column 'participant_id'"
                write_validation_report("FAIL", msg, {
                    "file": alt_metrics_file,
                    "min_required": min_n
                })
                return False, 0, msg
            
            count = df['participant_id'].nunique()
            if count >= min_n:
                msg = f"Sample size OK (via {Path(alt_metrics_file).name}): N={count} >= {min_n}"
                write_validation_report("PASS", msg, {
                    "file": alt_metrics_file,
                    "participant_count": count,
                    "min_required": min_n
                })
                return True, count, msg
            else:
                msg = f"Insufficient sample size: N={count} < {min_n}"
                write_validation_report("FAIL", msg, {
                    "file": alt_metrics_file,
                    "participant_count": count,
                    "min_required": min_n
                })
                return False, count, msg
        except Exception as e:
            msg = f"Error reading {alt_metrics_file}: {str(e)}"
            logging.error(msg)
    
    # Neither file worked
    msg = f"Metrics file not found: {metrics_file}"
    if alt_metrics_file:
        msg += f" (alt: {alt_metrics_file})"
    write_validation_report("FAIL", msg, {
        "files_checked": [metrics_file, alt_metrics_file] if alt_metrics_file else [metrics_file],
        "min_required": min_n
    })
    return False, 0, msg

def main():
    """Main entry point for sample size validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config = load_config()
    min_n = config.get("min_sample_size", 30)
    
    metrics_file = Path("data/processed/lzc_metrics.csv")
    alt_metrics_file = Path("data/processed/pe_metrics.csv")
    
    logging.info(f"Checking sample size (min required: {min_n})")
    logging.info(f"Primary file: {metrics_file}")
    logging.info(f"Alternative file: {alt_metrics_file}")
    
    success, count, message = check_sample_size(
        metrics_file=str(metrics_file),
        alt_metrics_file=str(alt_metrics_file),
        min_n=min_n
    )
    
    if success:
        logging.info(message)
        sys.exit(0)
    else:
        logging.error(message)
        sys.exit(1)

if __name__ == "__main__":
    main()
