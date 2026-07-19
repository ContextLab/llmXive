"""
Preprocessing module for GitHub issue data.

This module handles:
- Timestamp parsing and validation
- Resolution time computation
- Issue validation (excluding invalid issues)
- Logging of excluded issues
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import shared utilities
from utils.config import get_config, get_path

def setup_logging(log_file: Path) -> logging.Logger:
    """
    Setup logging configuration for preprocessing.
    
    Args:
        log_file: Path to the log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('preprocessing')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    
    # JSON formatter for structured logging
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
            }
            
            # Add extra fields if present
            if hasattr(record, 'issue_id'):
                log_record['issue_id'] = record.issue_id
            if hasattr(record, 'repo'):
                log_record['repo'] = record.repo
            if hasattr(record, 'reason'):
                log_record['reason'] = record.reason
            if hasattr(record, 'created_at'):
                log_record['created_at'] = record.created_at
            if hasattr(record, 'closed_at'):
                log_record['closed_at'] = record.closed_at
                
            return json.dumps(log_record)
    
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Also add a console handler for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)
    
    return logger

def parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO 8601 timestamp string to datetime object.
    
    Args:
        timestamp_str: ISO 8601 formatted timestamp string
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None
    
    try:
        # Handle various ISO 8601 formats
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        # Try parsing with timezone
        dt = datetime.fromisoformat(timestamp_str)
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
    except (ValueError, TypeError) as e:
        logging.getLogger('preprocessing').warning(
            f"Failed to parse timestamp: {timestamp_str}. Error: {e}"
        )
        return None

def compute_resolution_time(created_at: datetime, closed_at: datetime) -> float:
    """
    Compute resolution time in hours between creation and closure.
    
    Args:
        created_at: Issue creation datetime
        closed_at: Issue closure datetime
        
    Returns:
        Resolution time in hours (can be negative if closed before created)
    """
    delta = closed_at - created_at
    return delta.total_seconds() / 3600.0

def is_valid_issue(issue: Dict[str, Any], logger: Optional[logging.Logger] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate an issue for inclusion in the cleaned dataset.
    
    Checks:
    - Both created_at and closed_at timestamps exist and are valid
    - Resolution time is non-negative
    
    Args:
        issue: Issue dictionary from GitHub API
        logger: Optional logger for recording exclusion reasons
        
    Returns:
        Tuple of (is_valid, exclusion_reason)
    """
    repo = issue.get('repository_url', 'unknown')
    issue_id = issue.get('id', 'unknown')
    created_at_str = issue.get('created_at')
    closed_at_str = issue.get('closed_at')
    
    # Parse timestamps
    created_at = parse_timestamp(created_at_str)
    closed_at = parse_timestamp(closed_at_str)
    
    # Check for missing timestamps
    if created_at is None or closed_at is None:
        reason = "Missing or invalid timestamp (created_at or closed_at)"
        if logger:
            logger.warning(
                f"Issue excluded: {reason}",
                extra={
                    'issue_id': issue_id,
                    'repo': repo,
                    'reason': reason,
                    'created_at': created_at_str,
                    'closed_at': closed_at_str
                }
            )
        return False, reason
    
    # Compute resolution time
    resolution_time = compute_resolution_time(created_at, closed_at)
    
    # Check for negative resolution time
    if resolution_time < 0:
        reason = f"Negative resolution time: {resolution_time:.2f} hours"
        if logger:
            logger.warning(
                f"Issue excluded: {reason}",
                extra={
                    'issue_id': issue_id,
                    'repo': repo,
                    'reason': reason,
                    'created_at': created_at.isoformat(),
                    'closed_at': closed_at.isoformat()
                }
            )
        return False, reason
    
    return True, None

def preprocess_issues(issues: List[Dict[str, Any]], logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Preprocess a list of issues, computing resolution times and filtering invalid entries.
    
    Args:
        issues: List of issue dictionaries from GitHub API
        logger: Logger instance for recording exclusions
        
    Returns:
        List of valid issues with computed resolution_time_hours
    """
    valid_issues = []
    excluded_count = 0
    
    for issue in issues:
        is_valid, reason = is_valid_issue(issue, logger)
        
        if is_valid:
            # Compute resolution time
            created_at = parse_timestamp(issue['created_at'])
            closed_at = parse_timestamp(issue['closed_at'])
            resolution_time = compute_resolution_time(created_at, closed_at)
            
            # Add computed fields
            processed_issue = issue.copy()
            processed_issue['resolution_time_hours'] = resolution_time
            processed_issue['created_at_parsed'] = created_at.isoformat()
            processed_issue['closed_at_parsed'] = closed_at.isoformat()
            
            valid_issues.append(processed_issue)
        else:
            excluded_count += 1
    
    logger.info(f"Preprocessing complete: {len(valid_issues)} valid, {excluded_count} excluded")
    return valid_issues

def main():
    """
    Main entry point for preprocessing script.
    
    Loads preprocessed issues from raw data, validates them, and saves cleaned dataset.
    Also generates a JSON log of excluded issues.
    """
    # Get configuration
    config = get_config()
    data_dir = get_path('data_dir')
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    logs_dir = data_dir / 'logs'
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    log_file = logs_dir / 'preprocessing.log'
    logger = setup_logging(log_file)
    
    logger.info("Starting preprocessing pipeline")
    
    # Load raw issues
    raw_file = raw_dir / 'issues.json'
    if not raw_file.exists():
        logger.error(f"Raw issues file not found: {raw_file}")
        sys.exit(1)
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        issues = json.load(f)
    
    logger.info(f"Loaded {len(issues)} issues from {raw_file}")
    
    # Preprocess issues
    valid_issues = preprocess_issues(issues, logger)
    
    # Save cleaned dataset
    cleaned_file = processed_dir / 'cleaned_issues.csv'
    
    if valid_issues:
        import csv
        
        # Get all unique keys from issues
        fieldnames = set()
        for issue in valid_issues:
            fieldnames.update(issue.keys())
        
        # Remove parsed timestamps from CSV (keep ISO strings)
        fieldnames.discard('created_at_parsed')
        fieldnames.discard('closed_at_parsed')
        
        # Sort fieldnames for consistency
        fieldnames = sorted(fieldnames)
        
        with open(cleaned_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(valid_issues)
        
        logger.info(f"Saved {len(valid_issues)} issues to {cleaned_file}")
    else:
        logger.warning("No valid issues to save")
    
    logger.info("Preprocessing pipeline completed")

if __name__ == '__main__':
    main()
