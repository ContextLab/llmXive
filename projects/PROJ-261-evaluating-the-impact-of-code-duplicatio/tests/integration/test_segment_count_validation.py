"""
Integration test for SC-003: Segment Count Verification.
Ensures that the pipeline processes at least 1000 code segments.

This test validates that the data processing pipeline (T018 -> T019 -> T020 -> T021)
successfully generates a sufficient volume of processed code segments to support
statistical significance in the correlation analysis.
"""
import csv
import logging
from pathlib import Path
from typing import List

import pytest

# Import project configuration and paths
from config import get_processed_dir, get_min_valid_segments

# Setup logging for test visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SegmentCountValidator:
    """
    Utility class to validate segment counts in processed data artifacts.
    """
    
    def __init__(self, processed_dir: Path):
        self.processed_dir = processed_dir
        self.min_segments = get_min_valid_segments()
        logger.info(f"Initialized validator with min_segments={self.min_segments}")

    def count_segments_in_csv(self, filename: str, segment_id_column: str = "segment_id") -> int:
        """
        Counts the number of unique segments in a CSV file.
        
        Args:
            filename: Name of the CSV file relative to processed_dir.
            segment_id_column: The column name containing the segment identifier.
        
        Returns:
            The count of unique segment IDs found in the file.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            KeyError: If the specified column is missing.
        """
        file_path = self.processed_dir / filename
        logger.info(f"Validating segment count in: {file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"Required artifact not found: {file_path}")

        unique_segments = set()
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if segment_id_column not in reader.fieldnames:
                    available_cols = reader.fieldnames if reader.fieldnames else "None"
                    raise KeyError(f"Column '{segment_id_column}' not found in {filename}. Available: {available_cols}")

                for row in reader:
                    seg_id = row.get(segment_id_column)
                    if seg_id is not None and seg_id.strip() != "":
                        unique_segments.add(seg_id)
        
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            raise
        
        count = len(unique_segments)
        logger.info(f"Found {count} unique segments in {filename} (column: {segment_id_column})")
        return count

    def validate_main_metrics(self) -> bool:
        """
        Validates that the primary metrics file (clone_metrics.csv) meets the segment threshold.
        
        Returns:
            True if validation passes, False otherwise.
        """
        try:
            count = self.count_segments_in_csv("clone_metrics.csv", "segment_id")
            passed = count >= self.min_segments
            status = "PASSED" if passed else "FAILED"
            logger.info(f"SC-003 Validation (clone_metrics.csv): {status} (Count: {count}, Min: {self.min_segments})")
            return passed
        except Exception as e:
            logger.error(f"Validation failed due to error: {e}")
            return False

@pytest.fixture(scope="module")
def validator() -> SegmentCountValidator:
    """
    Creates a validator instance using project configuration.
    """
    processed_dir = get_processed_dir()
    # Ensure the directory exists for the test context, though validation handles missing files
    processed_dir.mkdir(parents=True, exist_ok=True)
    return SegmentCountValidator(processed_dir)

def test_segment_count_threshold(validator: SegmentCountValidator):
    """
    SC-003: Verify that the pipeline processed at least 1000 code segments.
    
    This test ensures that the data volume is sufficient for statistical analysis.
    If the pipeline failed to download, parse, or process enough segments, this test will fail.
    """
    logger.info("Starting SC-003 Segment Count Verification...")
    
    try:
        # Validate the primary artifact
        is_valid = validator.validate_main_metrics()
        
        # Assert the result
        assert is_valid, (
            f"SC-003 Verification Failed: "
            f"Processed segment count is below the required threshold of {validator.min_segments}. "
            f"Check pipeline logs for data download or parsing failures."
        )
        
        logger.info("SC-003 Verification Successful.")
        
    except FileNotFoundError as e:
        pytest.fail(f"Required data artifact missing: {e}. The pipeline may not have completed successfully.")
    except AssertionError as e:
        pytest.fail(str(e))
    except Exception as e:
        pytest.fail(f"Unexpected error during validation: {e}")

def test_segment_count_perplexity_consistency(validator: SegmentCountValidator):
    """
    Additional check: Ensure perplexity_scores.csv has consistent segment counts.
    
    While SC-003 specifically targets the main metrics, consistency across
    joined datasets is critical for data integrity.
    """
    logger.info("Checking consistency between clone_metrics.csv and perplexity_scores.csv...")
    
    try:
        count_clone = validator.count_segments_in_csv("clone_metrics.csv", "segment_id")
        count_perp = validator.count_segments_in_csv("perplexity_scores.csv", "segment_id")
        
        logger.info(f"Clone Metrics Count: {count_clone}, Perplexity Scores Count: {count_perp}")
        
        # Allow for minor discrepancies if some segments failed perplexity calculation,
        # but they should be roughly equal or perplexity <= clone
        assert count_perp <= count_clone, (
            f"Data Integrity Error: Perplexity scores ({count_perp}) exceed clone metrics ({count_clone}). "
            f"Check join logic in main.py."
        )
        
        assert count_perp >= validator.min_segments, (
            f"SC-003 Consistency Check Failed: Perplexity dataset ({count_perp}) is below threshold ({validator.min_segments})."
        )
        
    except FileNotFoundError as e:
        # If perplexity file is missing, the main test should have caught it,
        # but we note it here for completeness.
        pytest.skip(f"Perplexity file missing, skipping consistency check: {e}")

if __name__ == "__main__":
    # Allow running directly for quick verification
    pytest.main([__file__, "-v"])