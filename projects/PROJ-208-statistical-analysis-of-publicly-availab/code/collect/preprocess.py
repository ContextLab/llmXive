"""
Preprocessing script for GitHub issues data.

Computes resolution_time_hours and excludes invalid issues based on:
- Missing created_at or closed_at timestamps
- Negative resolution times (closed before created)
- Zero-duration issues (optional, configurable)

Outputs:
- Cleaned issues DataFrame
- Preprocessing log (JSON format)
- Statistics on excluded issues
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config, get_path

def parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO 8601 timestamp string to datetime object.
    
    Args:
        timestamp_str: ISO 8601 formatted timestamp string
        
    Returns:
        datetime object or None if parsing fails
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
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
        logging.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return None

def compute_resolution_time(created_at: Optional[datetime], 
                            closed_at: Optional[datetime]) -> Optional[float]:
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

def is_valid_issue(issue: Dict[str, Any], 
                  log_entry: Dict[str, Any] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate an issue for preprocessing.
    
    Checks:
    - Has valid created_at timestamp
    - Has valid closed_at timestamp
    - Resolution time is non-negative
    - Resolution time is not excessively large (> 10 years)
    
    Args:
        issue: Issue dictionary
        log_entry: Optional dictionary to populate with exclusion reason
        
    Returns:
        Tuple of (is_valid, exclusion_reason)
    """
    # Check for missing timestamps
    created_at_str = issue.get('created_at')
    closed_at_str = issue.get('closed_at')
    
    if not created_at_str or not closed_at_str:
        if log_entry is not None:
            log_entry['reason'] = 'missing_timestamps'
        return False, 'missing_timestamps'
    
    created_at = parse_timestamp(created_at_str)
    closed_at = parse_timestamp(closed_at_str)
    
    if created_at is None or closed_at is None:
        if log_entry is not None:
            log_entry['reason'] = 'invalid_timestamp_format'
        return False, 'invalid_timestamp_format'
    
    # Compute resolution time
    resolution_hours = compute_resolution_time(created_at, closed_at)
    
    if resolution_hours is None:
        if log_entry is not None:
            log_entry['reason'] = 'resolution_time_calculation_failed'
        return False, 'resolution_time_calculation_failed'
    
    # Check for negative resolution time
    if resolution_hours < 0:
        if log_entry is not None:
            log_entry['reason'] = 'negative_resolution_time'
            log_entry['resolution_hours'] = resolution_hours
        return False, 'negative_resolution_time'
    
    # Check for excessively large resolution time (> 10 years = 87600 hours)
    if resolution_hours > 87600:
        if log_entry is not None:
            log_entry['reason'] = 'excessive_resolution_time'
            log_entry['resolution_hours'] = resolution_hours
        return False, 'excessive_resolution_time'
    
    return True, None

def preprocess_issues(issues: List[Dict[str, Any]], 
                     log_file: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Preprocess a list of issues:
    - Compute resolution_time_hours
    - Exclude invalid issues
    - Log excluded issues
    
    Args:
        issues: List of issue dictionaries
        log_file: Path to preprocessing log file
        
    Returns:
        Tuple of (cleaned DataFrame, statistics dictionary)
    """
    config = get_config()
    logger = logging.getLogger(__name__)
    
    valid_issues = []
    excluded_issues = []
    exclusion_counts = {
        'missing_timestamps': 0,
        'invalid_timestamp_format': 0,
        'negative_resolution_time': 0,
        'excessive_resolution_time': 0,
        'resolution_time_calculation_failed': 0
    }
    
    # Setup JSON log handler
    log_handler = None
    try:
        log_handler = logging.FileHandler(log_file, mode='w')
        log_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(log_handler)
    except Exception as e:
        logger.warning(f"Failed to create log file {log_file}: {e}")
    
    for idx, issue in enumerate(issues):
        log_entry = {
            'index': idx,
            'issue_id': issue.get('id'),
            'repository': issue.get('repository_id'),
            'title': issue.get('title', '')[:50]  # Truncate for logging
        }
        
        is_valid, reason = is_valid_issue(issue, log_entry)
        
        if is_valid:
            # Compute resolution time and add to issue
            created_at = parse_timestamp(issue.get('created_at'))
            closed_at = parse_timestamp(issue.get('closed_at'))
            resolution_hours = compute_resolution_time(created_at, closed_at)
            
            issue['resolution_time_hours'] = resolution_hours
            valid_issues.append(issue)
        else:
            excluded_issues.append(log_entry)
            exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1
            
            # Log the exclusion
            if log_handler:
                logger.info(json.dumps(log_entry))
    
    # Close log handler
    if log_handler:
        logger.removeHandler(log_handler)
        log_handler.close()
    
    # Convert to DataFrame
    df = pd.DataFrame(valid_issues)
    
    # Compute statistics
    total_issues = len(issues)
    valid_count = len(valid_issues)
    excluded_count = len(excluded_issues)
    exclusion_rate = (excluded_count / total_issues * 100) if total_issues > 0 else 0
    
    stats = {
        'total_issues': total_issues,
        'valid_issues': valid_count,
        'excluded_issues': excluded_count,
        'exclusion_rate_percent': round(exclusion_rate, 2),
        'exclusion_counts': exclusion_counts,
        'resolution_time_stats': {
            'mean_hours': float(df['resolution_time_hours'].mean()) if not df.empty else None,
            'median_hours': float(df['resolution_time_hours'].median()) if not df.empty else None,
            'std_hours': float(df['resolution_time_hours'].std()) if not df.empty else None,
            'min_hours': float(df['resolution_time_hours'].min()) if not df.empty else None,
            'max_hours': float(df['resolution_time_hours'].max()) if not df.empty else None,
            'p90_hours': float(df['resolution_time_hours'].quantile(0.90)) if not df.empty else None,
            'p95_hours': float(df['resolution_time_hours'].quantile(0.95)) if not df.empty else None,
            'p99_hours': float(df['resolution_time_hours'].quantile(0.99)) if not df.empty else None
        }
    }
    
    logger.info(f"Preprocessing complete: {valid_count}/{total_issues} issues valid ({100-exclusion_rate:.1f}% kept)")
    
    return df, stats

def main():
    """Main entry point for preprocessing script."""
    config = get_config()
    
    # Paths
    raw_data_path = get_path('raw_merged_parquet')
    cleaned_data_path = get_path('cleaned_issues_csv')
    log_path = get_path('preprocessing_log')
    
    # Ensure directories exist
    cleaned_data_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path.with_suffix('.txt'), mode='w')
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info(f"Loading raw data from {raw_data_path}")
    
    # Load raw data
    try:
        df_raw = pd.read_parquet(raw_data_path)
        logger.info(f"Loaded {len(df_raw)} issues from {raw_data_path}")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)
    
    # Convert to list of dicts for preprocessing
    issues = df_raw.to_dict('records')
    
    # Preprocess
    logger.info("Starting preprocessing...")
    df_clean, stats = preprocess_issues(issues, log_path)
    
    # Save cleaned data
    logger.info(f"Saving cleaned data to {cleaned_data_path}")
    df_clean.to_csv(cleaned_data_path, index=False)
    
    # Save statistics
    stats_path = log_path.parent / 'preprocessing_stats.json'
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    logger.info(f"Preprocessing complete. Statistics saved to {stats_path}")
    logger.info(f"Exclusion breakdown: {stats['exclusion_counts']}")
    
    return df_clean, stats

if __name__ == '__main__':
    main()