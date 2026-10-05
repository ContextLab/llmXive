"""
Utility module for calculating lagged competitive pressure.

This module contains the extracted logic for calculating the number of active
runners in a time window prior to each run, used as a feature in mixed-effects
models.
"""
import logging
from datetime import timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def calculate_lagged_pressure(
    run_records: List[Dict[str, Any]],
    window_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Calculate lagged competitive pressure for each run record.
    
    For each run, this function counts the number of unique runners who submitted
    runs in the window [run_date - window_days, run_date - 1 day].
    
    Args:
        run_records: List of run record dictionaries. Each must contain:
            - 'submission_date': datetime object or ISO format string
            - 'runner_id': unique identifier for the runner
        window_days: Number of days to look back for competitive pressure.
                    Default is 30 days.
    
    Returns:
        List of run record dictionaries with an additional 'lagged_competitive_pressure'
        field containing the count of unique runners in the lookback window.
    
    Raises:
        ValueError: If run_records is empty or missing required fields.
        TypeError: If submission_date cannot be parsed.
    """
    if not run_records:
        logger.warning("Empty run_records provided to calculate_lagged_pressure")
        return []
    
    # Ensure we have datetime objects for sorting and comparison
    processed_records = []
    for record in run_records:
        if 'submission_date' not in record or 'runner_id' not in record:
            raise ValueError("Each record must contain 'submission_date' and 'runner_id'")
        
        # Parse date if it's a string
        submission_date = record['submission_date']
        if isinstance(submission_date, str):
            from datetime import datetime
            submission_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
        
        processed_records.append({
            **record,
            '_date': submission_date,
            'lagged_competitive_pressure': 0  # Placeholder
        })
    
    # Sort by date for efficient processing
    processed_records.sort(key=lambda x: x['_date'])
    
    # Calculate lagged pressure for each record
    for i, current_record in enumerate(processed_records):
        current_date = current_record['_date']
        window_start = current_date - timedelta(days=window_days)
        window_end = current_date - timedelta(days=1)
        
        # Count unique runners in the window
        # Only consider records before the current one
        unique_runners = set()
        for j in range(i):
            other_record = processed_records[j]
            other_date = other_record['_date']
            
            # Check if this record falls within the window
            if window_start <= other_date <= window_end:
                unique_runners.add(other_record['runner_id'])
            
            # Optimization: Since records are sorted, we can stop checking
            # once we go too far back
            if other_date < window_start:
                break
        
        current_record['lagged_competitive_pressure'] = len(unique_runners)
        
        # Remove the temporary date field
        del current_record['_date']
    
    logger.info(f"Calculated lagged pressure for {len(processed_records)} records "
               f"with a {window_days}-day window")
    
    return processed_records
