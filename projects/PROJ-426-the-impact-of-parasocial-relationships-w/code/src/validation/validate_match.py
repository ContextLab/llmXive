import logging
import sys
from pathlib import Path
from typing import Dict, Any
import yaml
import pandas as pd

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context

# Constants
MIN_MATCHED_USERS = 500
MIN_MATCH_RATE = 0.80
MATCHED_USERS_PATH = project_root / "data" / "processed" / "matched_users.parquet"
LONELINESS_USERS_PATH = project_root / "data" / "raw" / "loneliness_dataset.parquet"
OUTPUT_REPORT_PATH = project_root / "data" / "validation" / "match_report.yaml"

logger = get_logger(__name__)

def load_data(path: Path) -> pd.DataFrame:
    """Load a parquet file and return a DataFrame."""
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    logger.info(f"Loading data from {path}")
    return pd.read_parquet(path)

def calculate_match_rate(total_users: int, matched_users: int) -> float:
    """Calculate the match rate."""
    if total_users == 0:
        return 0.0
    return matched_users / total_users

def validate_match() -> Dict[str, Any]:
    """
    Validate the match between loneliness dataset and Pushshift logs.
    
    Returns:
        Dict containing match statistics and validation status.
    """
    log_stage_start(logger, "validate_match")
    
    try:
        # Load datasets
        loneliness_df = load_data(LONELINESS_USERS_PATH)
        matched_df = load_data(MATCHED_USERS_PATH)
        
        total_users = len(loneliness_df)
        matched_count = len(matched_df)
        
        match_rate = calculate_match_rate(total_users, matched_count)
        
        logger.info(f"Total loneliness users: {total_users}")
        logger.info(f"Matched users: {matched_count}")
        logger.info(f"Match rate: {match_rate:.2%}")
        
        # Validation checks
        status = "pass"
        errors = []
        
        if matched_count < MIN_MATCHED_USERS:
            errors.append(f"Matched users ({matched_count}) is below minimum threshold ({MIN_MATCHED_USERS})")
            status = "fail"
        
        if match_rate < MIN_MATCH_RATE:
            errors.append(f"Match rate ({match_rate:.2%}) is below minimum threshold ({MIN_MATCH_RATE:.2%})")
            status = "fail"
        
        if status == "fail":
            error_msg = "Power Insufficient: " + "; ".join(errors)
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Generate report
        report = {
            "match_rate": round(match_rate, 4),
            "total_users": total_users,
            "matched_users": matched_count,
            "status": status,
            "thresholds": {
                "min_matched_users": MIN_MATCHED_USERS,
                "min_match_rate": MIN_MATCH_RATE
            }
        }
        
        # Ensure output directory exists
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report to YAML
        with open(OUTPUT_REPORT_PATH, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Match report written to {OUTPUT_REPORT_PATH}")
        log_stage_end(logger, "validate_match", success=True)
        
        return report
        
    except FileNotFoundError as e:
        log_error_context(logger, "validate_match", str(e))
        raise
    except RuntimeError as e:
        log_error_context(logger, "validate_match", str(e))
        raise
    except Exception as e:
        log_error_context(logger, "validate_match", f"Unexpected error: {str(e)}")
        raise

def main():
    """Main entry point for the validation script."""
    try:
        validate_match()
        print("Validation passed successfully.")
        return 0
    except Exception as e:
        print(f"Validation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
