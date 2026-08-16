import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.config import get_config
from collect.setup_preprocessing_logging import setup_preprocessing_logging

def parse_timestamp(ts_value: Any) -> Optional[datetime]:
    """
    Parses a timestamp string into a datetime object.
    
    Args:
        ts_value: The timestamp value (string or None).
    
    Returns:
        A datetime object or None if parsing fails or value is None.
    """
    if ts_value is None or ts_value == "":
        return None
    
    try:
        # Handle ISO 8601 format with timezone
        dt = datetime.fromisoformat(ts_value.replace('Z', '+00:00'))
        # Ensure timezone aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None

def compute_resolution_time(created_at: datetime, closed_at: datetime) -> float:
    """
    Computes resolution time in hours between creation and closure.
    
    Args:
        created_at: Creation timestamp.
        closed_at: Closure timestamp.
    
    Returns:
        Resolution time in hours.
    """
    delta = closed_at - created_at
    return delta.total_seconds() / 3600.0

def is_valid_issue(issue: Dict[str, Any], logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """
    Validates an issue record for preprocessing.
    
    Checks:
        1. Both created_at and closed_at must be present and valid.
        2. Resolution time must be non-negative.
    
    Args:
        issue: The issue dictionary.
        logger: Logger for recording excluded issues.
    
    Returns:
        Tuple of (is_valid, reason_if_invalid).
    """
    created_at_str = issue.get("created_at")
    closed_at_str = issue.get("closed_at")
    repo_id = issue.get("repo_id", "unknown")
    issue_number = issue.get("number", "unknown")
    
    created_at = parse_timestamp(created_at_str)
    closed_at = parse_timestamp(closed_at_str)
    
    # Check for missing timestamps
    if created_at is None:
        log_data = {
            "issue_id": f"{repo_id}#{issue_number}",
            "reason": "missing_created_at",
            "created_at_value": created_at_str
        }
        logger.info("Excluded issue: missing created_at", extra={"extra_data": log_data})
        return False, "missing_created_at"
    
    if closed_at is None:
        log_data = {
            "issue_id": f"{repo_id}#{issue_number}",
            "reason": "missing_closed_at",
            "closed_at_value": closed_at_str
        }
        logger.info("Excluded issue: missing closed_at", extra={"extra_data": log_data})
        return False, "missing_closed_at"
    
    resolution_time = compute_resolution_time(created_at, closed_at)
    
    # Check for negative resolution time
    if resolution_time < 0:
        log_data = {
            "issue_id": f"{repo_id}#{issue_number}",
            "reason": "negative_resolution_time",
            "resolution_time_hours": resolution_time
        }
        logger.info("Excluded issue: negative resolution time", extra={"extra_data": log_data})
        return False, "negative_resolution_time"
    
    return True, None

def preprocess_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Preprocesses a list of issues: computes resolution time and filters invalid ones.
    
    Args:
        issues: List of raw issue dictionaries.
    
    Returns:
        List of valid issues with computed resolution_time_hours.
    """
    logger = setup_preprocessing_logging()
    processed_issues = []
    excluded_count = 0
    
    for issue in issues:
        is_valid, reason = is_valid_issue(issue, logger)
        
        if is_valid:
            created_at = parse_timestamp(issue["created_at"])
            closed_at = parse_timestamp(issue["closed_at"])
            resolution_time = compute_resolution_time(created_at, closed_at)
            
            issue["resolution_time_hours"] = resolution_time
            processed_issues.append(issue)
        else:
            excluded_count += 1
    
    logger.info(f"Preprocessing complete. Included: {len(processed_issues)}, Excluded: {excluded_count}")
    return processed_issues

def main() -> None:
    """
    Main entry point for preprocessing.
    Reads from data/processed/issues_with_metadata.json (or similar raw source),
    preprocesses, and writes to data/processed/cleaned_issues.csv (intermediate step before T011).
    Note: This task (T012) focuses on the logging aspect, which is integrated here.
    """
    # Determine input path based on project flow (T045 output)
    config = get_config()
    input_path = Path("data/processed/issues_with_metadata.json")
    
    if not input_path.exists():
        # Fallback to potential T009 output if metadata enrichment hasn't run yet
        # This is a safeguard for the specific task implementation
        input_path = Path("data/raw/github_issues_raw_hf.parquet")
        if not input_path.exists():
            input_path = Path("data/raw/github_issues_raw_api.parquet")
    
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data (handling both JSON and Parquet if needed, assuming JSON for now based on T045)
    issues = []
    if input_path.suffix == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            issues = json.load(f)
    elif input_path.suffix == '.parquet':
        try:
            import pandas as pd
            df = pd.read_parquet(input_path)
            issues = df.to_dict(orient='records')
        except ImportError:
            logging.error("pandas required for parquet reading")
            sys.exit(1)
    
    processed = preprocess_issues(issues)
    
    # Save intermediate processed data (T010 output target)
    output_path = Path("data/processed/preprocessed_issues.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed, f, indent=2, default=str)
    
    logging.info(f"Saved preprocessed issues to {output_path}")

if __name__ == "__main__":
    main()