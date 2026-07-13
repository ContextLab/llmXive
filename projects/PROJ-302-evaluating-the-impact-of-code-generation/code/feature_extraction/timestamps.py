"""
Timestamp extraction module for PR review duration analysis.

Extracts review duration (time from PR open to first comment or merge)
from GitHub PR metadata and writes results to processed dataset.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_acquisition.github_scraper import parse_iso_date

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_iso_date_safe(date_str: Optional[str]) -> Optional[datetime]:
    """
    Safely parse ISO date string, handling None and invalid formats.

    Args:
        date_str: ISO format date string (e.g., '2023-01-15T10:30:00Z')

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    try:
        return parse_iso_date(date_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None

def calculate_review_duration(
    created_at: Optional[str],
    first_comment_at: Optional[str],
    merged_at: Optional[str]
) -> Optional[float]:
    """
    Calculate review duration in hours.

    Review duration is defined as the time from PR creation to:
    - The first comment (if exists), OR
    - The merge time (if no comments exist)

    Args:
        created_at: ISO timestamp when PR was created
        first_comment_at: ISO timestamp of first comment (if any)
        merged_at: ISO timestamp when PR was merged (if any)

    Returns:
        Duration in hours as float, or None if insufficient data
    """
    created_dt = parse_iso_date_safe(created_at)
    if not created_dt:
        return None

    # Determine end time: first comment if exists, else merge time
    end_dt = None
    first_comment_dt = parse_iso_date_safe(first_comment_at)
    merged_dt = parse_iso_date_safe(merged_at)

    if first_comment_dt:
        end_dt = first_comment_dt
    elif merged_dt:
        end_dt = merged_dt
    else:
        # No comments and no merge - cannot calculate duration
        logger.debug(f"PR missing both first comment and merge time, skipping")
        return None

    if not end_dt:
        return None

    # Ensure end time is after creation time
    if end_dt <= created_dt:
        logger.warning(f"End time {end_dt} is not after creation time {created_dt}")
        return None

    delta = end_dt - created_dt
    return delta.total_seconds() / 3600.0  # Convert to hours

def extract_timestamps_from_pr(
    pr_data: Dict[str, Any]
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Extract review duration and timestamp metadata from a PR record.

    Args:
        pr_data: Dictionary containing PR metadata fields

    Returns:
        Tuple of (duration_hours, metadata_dict)
        - duration_hours: float or None if calculation failed
        - metadata_dict: Contains original timestamps and calculation details
    """
    created_at = pr_data.get('created_at')
    first_comment_at = pr_data.get('first_comment_at')
    merged_at = pr_data.get('merged_at')
    pr_id = pr_data.get('pr_id', 'unknown')

    duration = calculate_review_duration(created_at, first_comment_at, merged_at)

    metadata = {
        'pr_id': pr_id,
        'created_at': created_at,
        'first_comment_at': first_comment_at,
        'merged_at': merged_at,
        'duration_hours': duration,
        'calculation_note': 'Used first comment if available, else merge time'
    }

    return duration, metadata

def process_dataset(
    input_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Process a parquet dataset to add review duration metrics.

    Reads input parquet file, calculates review duration for each PR,
    and writes output with new columns.

    Args:
        input_path: Path to input parquet file (e.g., data/processed/pr_metadata.parquet)
        output_path: Path to output parquet file

    Returns:
        Dictionary with processing statistics
    """
    logger.info(f"Reading input dataset from {input_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")

    # Extract timestamps and durations
    durations = []
    timestamps_meta = []
    skipped_count = 0

    for idx, row in df.iterrows():
        pr_data = row.to_dict()
        duration, meta = extract_timestamps_from_pr(pr_data)

        if duration is not None:
            durations.append(duration)
            timestamps_meta.append(meta)
        else:
            durations.append(None)
            timestamps_meta.append(meta)
            skipped_count += 1

    # Add new columns to dataframe
    df['review_duration_hours'] = durations

    # Log statistics
    valid_count = len([d for d in durations if d is not None])
    logger.info(f"Successfully calculated {valid_count} review durations")
    logger.info(f"Skipped {skipped_count} records due to missing timestamps")

    if valid_count > 0:
        valid_durations = [d for d in durations if d is not None]
        logger.info(f"Duration stats: min={min(valid_durations):.2f}h, "
                    f"max={max(valid_durations):.2f}h, "
                    f"mean={sum(valid_durations)/len(valid_durations):.2f}h")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write output
    logger.info(f"Writing output to {output_path}")
    df.to_parquet(output_path, index=False)

    return {
        'input_records': len(df),
        'valid_durations': valid_count,
        'skipped_records': skipped_count,
        'output_path': output_path
    }

def main():
    """
    Main entry point for timestamp extraction pipeline.

    Expects:
        - Input: data/processed/pr_metadata.parquet (from github_scraper)
        - Output: data/processed/pr_metadata_with_timestamps.parquet

    Usage:
        python code/feature_extraction/timestamps.py
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / 'data' / 'processed' / 'pr_metadata.parquet'
    output_path = project_root / 'data' / 'processed' / 'pr_metadata_with_timestamps.parquet'

    logger.info("Starting timestamp extraction pipeline")

    try:
        stats = process_dataset(str(input_path), str(output_path))
        logger.info(f"Pipeline completed successfully: {stats}")
        print(json.dumps(stats, indent=2, default=str))
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
