import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.config import get_config


def parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO 8601 timestamp string into a datetime object.

    Args:
        timestamp_str: ISO 8601 formatted timestamp string

    Returns:
        datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None

    try:
        # Handle 'Z' suffix for UTC
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'

        # Parse the timestamp
        dt = datetime.fromisoformat(timestamp_str)

        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except (ValueError, TypeError) as e:
        logging.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return None


def compute_resolution_time(created_at: datetime, closed_at: datetime) -> Optional[float]:
    """
    Compute resolution time in hours between creation and closure.

    Args:
        created_at: Issue creation datetime
        closed_at: Issue closure datetime

    Returns:
        Resolution time in hours, or None if invalid
    """
    if created_at is None or closed_at is None:
        return None

    delta = closed_at - created_at
    hours = delta.total_seconds() / 3600.0

    return hours


def is_valid_issue(
    issue: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate an issue record for preprocessing.

    Checks:
    - created_at and closed_at timestamps are present and valid
    - Resolution time is non-negative

    Args:
        issue: Issue dictionary from the dataset
        logger: Optional logger for recording excluded issues

    Returns:
        Tuple of (is_valid, reason_for_exclusion)
    """
    created_at_str = issue.get("created_at")
    closed_at_str = issue.get("closed_at")

    # Check for missing timestamps
    if not created_at_str:
        if logger:
            logger.info(
                "Excluded issue: missing created_at",
                extra={"extra_data": {"issue_id": issue.get("id"), "reason": "missing_created_at"}}
            )
        return False, "missing_created_at"

    if not closed_at_str:
        if logger:
            logger.info(
                "Excluded issue: missing closed_at",
                extra={"extra_data": {"issue_id": issue.get("id"), "reason": "missing_closed_at"}}
            )
        return False, "missing_closed_at"

    # Parse timestamps
    created_at = parse_timestamp(created_at_str)
    closed_at = parse_timestamp(closed_at_str)

    if created_at is None:
        if logger:
            logger.info(
                "Excluded issue: invalid created_at format",
                extra={"extra_data": {"issue_id": issue.get("id"), "reason": "invalid_created_at_format"}}
            )
        return False, "invalid_created_at"

    if closed_at is None:
        if logger:
            logger.info(
                "Excluded issue: invalid closed_at format",
                extra={"extra_data": {"issue_id": issue.get("id"), "reason": "invalid_closed_at_format"}}
            )
        return False, "invalid_closed_at"

    # Compute resolution time
    resolution_time = compute_resolution_time(created_at, closed_at)

    if resolution_time is None:
        if logger:
            logger.info(
                "Excluded issue: could not compute resolution time",
                extra={"extra_data": {"issue_id": issue.get("id"), "reason": "resolution_time_compute_failed"}}
            )
        return False, "resolution_time_failed"

    if resolution_time < 0:
        if logger:
            logger.info(
                "Excluded issue: negative resolution time",
                extra={"extra_data": {
                    "issue_id": issue.get("id"),
                    "reason": "negative_resolution_time",
                    "resolution_time_hours": resolution_time
                }}
            )
        return False, "negative_resolution_time"

    return True, None


def preprocess_issues(
    issues: List[Dict[str, Any]],
    logger: Optional[logging.Logger] = None,
) -> List[Dict[str, Any]]:
    """
    Preprocess a list of issues: filter invalid ones and compute resolution time.

    Args:
        issues: List of issue dictionaries
        logger: Optional logger for recording excluded issues

    Returns:
        List of valid issues with computed resolution_time_hours
    """
    valid_issues = []
    excluded_count = 0

    for issue in issues:
        is_valid, reason = is_valid_issue(issue, logger)

        if is_valid:
            # Add resolution time to the issue
            created_at = parse_timestamp(issue["created_at"])
            closed_at = parse_timestamp(issue["closed_at"])
            resolution_time = compute_resolution_time(created_at, closed_at)

            issue["resolution_time_hours"] = resolution_time
            valid_issues.append(issue)
        else:
            excluded_count += 1

    if logger:
        logger.info(f"Preprocessing complete. Valid: {len(valid_issues)}, Excluded: {excluded_count}")

    return valid_issues


def main() -> None:
    """
    Main entry point for preprocessing.

    Expected inputs:
    - data/raw/github_issues_raw_api.parquet (from T009)

    Expected outputs:
    - data/processed/cleaned_issues.csv (from T011)
    - data/logs/preprocessing.log (from T012)
    """
    import pandas as pd

    config = get_config()
    raw_path = config.get_path("raw_issues_parquet")
    processed_path = config.get_path("cleaned_issues_csv")
    log_path = config.get_path("preprocessing_log")

    # Ensure directories exist
    Path(processed_path).parent.mkdir(parents=True, exist_ok=True)
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = logging.getLogger("preprocessing")
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.INFO)

    # JSON Formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            if hasattr(record, "extra_data"):
                log_data["data"] = record.extra_data
            return json.dumps(log_data)

    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    logger.info("Starting preprocessing pipeline")

    # Load raw data
    logger.info(f"Loading data from {raw_path}")
    try:
        df = pd.read_parquet(raw_path)
        issues = df.to_dict(orient='records')
        logger.info(f"Loaded {len(issues)} issues")
    except FileNotFoundError:
        logger.error(f"Raw data file not found: {raw_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading raw data: {e}")
        raise

    # Preprocess
    valid_issues = preprocess_issues(issues, logger)

    # Save cleaned data
    logger.info(f"Saving {len(valid_issues)} valid issues to {processed_path}")
    df_clean = pd.DataFrame(valid_issues)
    df_clean.to_csv(processed_path, index=False)

    logger.info("Preprocessing pipeline completed successfully")


if __name__ == "__main__":
    main()