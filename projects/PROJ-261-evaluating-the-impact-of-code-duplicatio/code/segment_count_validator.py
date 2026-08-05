from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_min_valid_segments, get_processed_dir, get_data_root

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(get_data_root()) / 'segment_validation.log')
    ]
)
logger = logging.getLogger(__name__)


def load_processed_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file and return rows as a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def validate_segment_count(
    file_path: Path,
    min_segments: Optional[int] = None,
    segment_id_column: str = 'segment_id'
) -> bool:
    """
    Validate that the number of segments in a CSV file meets the minimum threshold.
    
    Args:
        file_path: Path to the CSV file to validate
        min_segments: Minimum number of segments required (defaults to config)
        segment_id_column: Column name representing unique segment ID
        
    Returns:
        True if segment count meets threshold, False otherwise
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the segment_id column is not found
    """
    if min_segments is None:
        min_segments = get_min_valid_segments()
    
    logger.info(f"Validating segment count in {file_path} (min: {min_segments})")
    
    try:
        data = load_processed_csv(file_path)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    
    if not data:
        logger.error(f"File {file_path} is empty or contains no data rows")
        return False
    
    # Check if segment_id column exists
    if segment_id_column not in data[0]:
        available_cols = list(data[0].keys())
        logger.error(f"Column '{segment_id_column}' not found in {file_path}. Available: {available_cols}")
        raise ValueError(f"Column '{segment_id_column}' not found in {file_path}")
    
    # Count unique segment IDs
    unique_segments = set(row[segment_id_column] for row in data if row[segment_id_column])
    segment_count = len(unique_segments)
    
    logger.info(f"Found {segment_count} unique segments in {file_path}")
    
    if segment_count >= min_segments:
        logger.info(f"SUCCESS: Segment count {segment_count} >= {min_segments}")
        return True
    else:
        logger.error(f"FAILURE: Segment count {segment_count} < {min_segments}")
        return False


def validate_all_required_files() -> bool:
    """
    Validate segment counts for all required processed files.
    
    Returns:
        True if all files meet the threshold, False otherwise
    """
    processed_dir = get_processed_dir()
    min_segments = get_min_valid_segments()
    
    required_files = [
        processed_dir / 'clone_metrics.csv',
        processed_dir / 'perplexity_scores.csv',
        processed_dir / 'bug_detection_results.csv'
    ]
    
    all_valid = True
    
    for file_path in required_files:
        try:
            if validate_segment_count(file_path, min_segments):
                logger.info(f"✓ {file_path.name} passed validation")
            else:
                logger.error(f"✗ {file_path.name} failed validation")
                all_valid = False
        except FileNotFoundError:
            logger.error(f"✗ {file_path.name} not found")
            all_valid = False
        except ValueError as e:
            logger.error(f"✗ {file_path.name} validation error: {e}")
            all_valid = False
    
    return all_valid


def main():
    """Main entry point for segment count validation."""
    logger.info("Starting segment count validation for SC-003")
    
    min_segments = get_min_valid_segments()
    logger.info(f"Minimum required segments: {min_segments}")
    
    success = validate_all_required_files()
    
    if success:
        logger.info("All segment count validations passed")
        sys.exit(0)
    else:
        logger.error("Segment count validation failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
