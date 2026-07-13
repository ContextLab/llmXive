import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.config import get_config, get_path
from utils.validators import validate_dataset_schema, ValidationError


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging configuration for the preprocessing step."""
    logger = logging.getLogger("preprocess")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO 8601 timestamp string into a timezone-aware datetime object.
    
    Args:
        ts_str: ISO 8601 timestamp string (e.g., "2023-01-15T10:30:00Z")
        
    Returns:
        timezone-aware datetime object or None if input is None/empty
    """
    if not ts_str:
        return None
    
    try:
        # Handle 'Z' suffix by replacing with '+00:00' for fromisoformat
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(ts_str)
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        return dt
    except (ValueError, TypeError) as e:
        logging.warning(f"Failed to parse timestamp '{ts_str}': {e}")
        return None


def compute_resolution_time(created_at: Optional[datetime], 
                            closed_at: Optional[datetime]) -> Optional[float]:
    """
    Compute the resolution time in hours between creation and closure.
    
    Args:
        created_at: The creation datetime
        closed_at: The closure datetime
        
    Returns:
        Resolution time in hours (float) or None if either timestamp is missing
    """
    if created_at is None or closed_at is None:
        return None
    
    if closed_at < created_at:
        return None  # Invalid: closed before created
    
    delta = closed_at - created_at
    return delta.total_seconds() / 3600.0


def is_valid_issue(issue: Dict[str, Any], logger: Optional[logging.Logger] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate an issue record for inclusion in the cleaned dataset.
    
    Validation rules (FR-002, FR-003):
    1. Must have both created_at and closed_at timestamps
    2. Resolution time must be non-negative (closed_at >= created_at)
    3. Resolution time must be finite (not NaN or Inf)
    4. Must have a non-empty 'state' field indicating 'closed'
    
    Args:
        issue: The issue dictionary from the API
        logger: Optional logger for recording exclusion reasons
        
    Returns:
        Tuple of (is_valid, reason_for_exclusion)
    """
    # Check for required fields
    if not issue.get("state") or issue.get("state") != "closed":
        if logger:
            logger.debug(f"Issue #{issue.get('number', 'unknown')} excluded: state is not 'closed'")
        return False, "state_not_closed"
    
    created_at = parse_timestamp(issue.get("created_at"))
    closed_at = parse_timestamp(issue.get("closed_at"))
    
    if created_at is None:
        if logger:
            logger.debug(f"Issue #{issue.get('number', 'unknown')} excluded: missing created_at")
        return False, "missing_created_at"
    
    if closed_at is None:
        if logger:
            logger.debug(f"Issue #{issue.get('number', 'unknown')} excluded: missing closed_at")
        return False, "missing_closed_at"
    
    if closed_at < created_at:
        if logger:
            logger.debug(f"Issue #{issue.get('number', 'unknown')} excluded: closed_at < created_at")
        return False, "negative_resolution_time"
    
    resolution_time = compute_resolution_time(created_at, closed_at)
    if resolution_time is None or resolution_time < 0:
        if logger:
            logger.debug(f"Issue #{issue.get('number', 'unknown')} excluded: invalid resolution time")
        return False, "invalid_resolution_time"
    
    if not (resolution_time == resolution_time and resolution_time != float('inf')):  # Check for NaN/Inf
        if logger:
            logger.debug(f"Issue #{issue.get('number', 'unknown')} excluded: resolution time is NaN or Inf")
        return False, "invalid_resolution_value"
    
    return True, None


def preprocess_issues(issues: List[Dict[str, Any]], 
                     log_file: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Preprocess a list of raw issue records.
    
    This function:
    1. Validates each issue using is_valid_issue
    2. Computes resolution_time_hours for valid issues
    3. Excludes invalid issues and logs reasons
    4. Returns cleaned dataset and exclusion statistics
    
    Args:
        issues: List of raw issue dictionaries from GitHub API
        log_file: Optional path to write exclusion logs
        
    Returns:
        Tuple of (cleaned_issues, exclusion_stats)
        - cleaned_issues: List of valid issues with resolution_time_hours computed
        - exclusion_stats: Dict with counts of excluded issues by reason
    """
    logger = setup_logging(log_file)
    
    cleaned_issues = []
    exclusion_stats = {
        "total_input": len(issues),
        "total_valid": 0,
        "total_excluded": 0,
        "reasons": {}
    }
    
    for issue in issues:
        is_valid, reason = is_valid_issue(issue, logger)
        
        if is_valid:
            created_at = parse_timestamp(issue.get("created_at"))
            closed_at = parse_timestamp(issue.get("closed_at"))
            resolution_time = compute_resolution_time(created_at, closed_at)
            
            # Create cleaned record with computed field
            cleaned_record = issue.copy()
            cleaned_record["resolution_time_hours"] = resolution_time
            cleaned_record["created_at_parsed"] = created_at.isoformat()
            cleaned_record["closed_at_parsed"] = closed_at.isoformat()
            
            cleaned_issues.append(cleaned_record)
            exclusion_stats["total_valid"] += 1
        else:
            exclusion_stats["total_excluded"] += 1
            exclusion_stats["reasons"][reason] = exclusion_stats["reasons"].get(reason, 0) + 1
    
    logger.info(f"Preprocessing complete: {exclusion_stats['total_valid']} valid, "
               f"{exclusion_stats['total_excluded']} excluded out of {exclusion_stats['total_input']}")
    
    return cleaned_issues, exclusion_stats


def main():
    """
    Main entry point for the preprocessing script.
    
    Reads raw issues from data/raw/fetched_issues.json,
    preprocesses them, and writes cleaned data to data/processed/cleaned_issues.csv.
    Also logs exclusion details to data/logs/preprocessing.log.
    """
    config = get_config()
    
    # Define paths
    raw_input_path = get_path("raw_fetched_issues", "data/raw/fetched_issues.json")
    output_path = get_path("cleaned_issues", "data/processed/cleaned_issues.csv")
    log_path = get_path("preprocessing_log", "data/logs/preprocessing.log")
    
    logger = setup_logging(log_path)
    logger.info("Starting preprocessing pipeline...")
    
    # Validate input file exists
    if not Path(raw_input_path).exists():
        logger.error(f"Input file not found: {raw_input_path}")
        sys.exit(1)
    
    # Load raw issues
    try:
        with open(raw_input_path, 'r', encoding='utf-8') as f:
            raw_issues = json.load(f)
        logger.info(f"Loaded {len(raw_issues)} raw issues from {raw_input_path}")
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load raw issues: {e}")
        sys.exit(1)
    
    # Preprocess issues
    cleaned_issues, stats = preprocess_issues(raw_issues, log_path)
    
    if not cleaned_issues:
        logger.warning("No valid issues found after preprocessing. Check exclusion logs.")
    
    # Save cleaned dataset
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        import pandas as pd
        df = pd.DataFrame(cleaned_issues)
        
        # Ensure resolution_time_hours column exists and is numeric
        if "resolution_time_hours" in df.columns:
            df["resolution_time_hours"] = pd.to_numeric(df["resolution_time_hours"], errors='coerce')
        
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Saved {len(cleaned_issues)} cleaned issues to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save cleaned issues: {e}")
        sys.exit(1)
    
    # Save exclusion statistics
    stats_path = output_path_obj.parent / "preprocessing_stats.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved preprocessing statistics to {stats_path}")
    
    # Validate schema
    try:
        validate_dataset_schema(cleaned_issues, logger=logger)
        logger.info("Schema validation passed")
    except ValidationError as e:
        logger.warning(f"Schema validation warning: {e}")
    
    logger.info("Preprocessing pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())