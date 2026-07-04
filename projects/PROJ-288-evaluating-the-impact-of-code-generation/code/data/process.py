import os
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from data.logging_config import get_logger

logger = get_logger(__name__)

# Constants for outlier exclusion
MAX_REVIEW_DAYS = 30
SECONDS_IN_DAY = 86400
MAX_REVIEW_SECONDS = MAX_REVIEW_DAYS * SECONDS_IN_DAY

def load_sampled_prs(input_path: str) -> List[Dict[str, Any]]:
    """Load the sampled PRs dataset from a CSV file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO format datetime string."""
    if not dt_str or dt_str.strip() == '':
        return None
    try:
        # Handle common ISO formats
        if 'T' in dt_str:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        logger.warning(f"Could not parse datetime '{dt_str}': {e}")
        return None

def calculate_review_times(row: Dict[str, Any]) -> tuple:
    """
    Calculate review times in minutes.
    Returns (first_review_time, total_review_time).
    Returns (-1, -1) if data is invalid (negative time or missing).
    """
    created_at_str = row.get('created_at')
    first_review_at_str = row.get('first_review_at')
    merged_at_str = row.get('merged_at')
    
    created_at = parse_datetime(created_at_str)
    first_review_at = parse_datetime(first_review_at_str)
    merged_at = parse_datetime(merged_at_str)
    
    # If any required time is missing, mark as invalid
    if not created_at or not first_review_at or not merged_at:
        return -1.0, -1.0
    
    # Calculate durations in seconds
    first_review_sec = (first_review_at - created_at).total_seconds()
    total_review_sec = (merged_at - created_at).total_seconds()
    
    # Check for negative times (data inconsistency)
    if first_review_sec < 0 or total_review_sec < 0:
        return -1.0, -1.0
    
    # Convert to minutes
    first_review_min = first_review_sec / 60.0
    total_review_min = total_review_sec / 60.0
    
    return first_review_min, total_review_min

def apply_outlier_exclusion(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out PRs based on outlier criteria:
    1. Negative review times (data errors)
    2. Total review duration > MAX_REVIEW_DAYS (30 days)
    
    Returns the filtered list of PRs.
    """
    filtered_data = []
    excluded_count = {
        'negative_time': 0,
        'too_long': 0,
        'missing_data': 0,
        'kept': 0
    }
    
    for row in data:
        # Ensure time columns exist and are calculated
        if 'first_review_time' not in row or 'total_review_time' not in row:
            # Calculate if not present (should already be present from T021)
            first_min, total_min = calculate_review_times(row)
            row['first_review_time'] = first_min
            row['total_review_time'] = total_min
        
        try:
            first_time = float(row.get('first_review_time', -1))
            total_time = float(row.get('total_review_time', -1))
        except (ValueError, TypeError):
            excluded_count['missing_data'] += 1
            logger.debug(f"Excluded PR {row.get('pr_number')}: invalid time values")
            continue
        
        # Check exclusion criteria
        if first_time < 0 or total_time < 0:
            excluded_count['negative_time'] += 1
            logger.debug(f"Excluded PR {row.get('pr_number')}: negative time ({first_time}, {total_time})")
            continue
        
        if total_time > MAX_REVIEW_SECONDS / 60.0: # Convert days to minutes
            excluded_count['too_long'] += 1
            logger.debug(f"Excluded PR {row.get('pr_number')}: duration {total_time} min > {MAX_REVIEW_DAYS} days")
            continue
        
        filtered_data.append(row)
        excluded_count['kept'] += 1
    
    logger.info(f"Outlier Exclusion Summary: Kept={excluded_count['kept']}, "
                f"Negative={excluded_count['negative_time']}, "
                f"TooLong={excluded_count['too_long']}, "
                f"Missing={excluded_count['missing_data']}")
    
    return filtered_data

def save_processed_prs(data: List[Dict[str, Any]], output_path: str) -> None:
    """Save the filtered dataset to a CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        logger.warning("No data to save.")
        return
    
    fieldnames = list(data[0].keys())
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} rows to {output_path}")

def main():
    """Main entry point for outlier exclusion."""
    # Define paths relative to project root
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_file = base_dir / "data" / "processed" / "pr_data_cleaned.csv"
    output_file = base_dir / "data" / "processed" / "pr_data_filtered.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T021 (process.py: calculate_review_times) has been run first.")
        sys.exit(1)
    
    logger.info(f"Starting outlier exclusion. Input: {input_file}")
    
    # Load data
    data = load_sampled_prs(str(input_file))
    
    # Apply exclusion logic
    filtered_data = apply_outlier_exclusion(data)
    
    # Save results
    save_processed_prs(filtered_data, str(output_file))
    
    logger.info(f"Outlier exclusion complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()