"""
T012g: Metadata Aggregation

Implements function aggregate_metadata() to merge:
- data/results/raw_record_count.json
- data/results/group_counts.json
- data/interim/exclusions.log

Calculates valid_label_proportion and writes to data/results/metadata.json.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_valid_lines_from_exclusions_log(exclusions_log_path: Path) -> int:
    """
    Count the number of records excluded based on the exclusions log.
    The log format is expected to be: 'participant_id|reason_code'
    We count the number of lines to determine excluded records.
    """
    if not exclusions_log_path.exists():
        logger.warning(f"Exclusions log not found at {exclusions_log_path}. Assuming 0 exclusions.")
        return 0
    
    excluded_count = 0
    with open(exclusions_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                excluded_count += 1
    return excluded_count

def merge_metadata_files() -> Dict[str, Any]:
    """
    Merge metadata from raw_record_count.json, group_counts.json, and exclusions.log.
    Calculate valid_label_proportion and return the aggregated metadata.
    """
    # Define paths
    raw_count_path = get_path("data/results/raw_record_count.json")
    group_counts_path = get_path("data/results/group_counts.json")
    exclusions_log_path = get_path("data/interim/exclusions.log")
    
    # Load raw record count
    try:
        raw_count_data = load_json_file(raw_count_path)
        raw_count = raw_count_data.get("raw_count", 0)
    except FileNotFoundError as e:
        logger.error(f"Failed to load raw record count: {e}")
        raise

    # Load group counts
    try:
        group_counts_data = load_json_file(group_counts_path)
        group_counts = {
            "Control": group_counts_data.get("Control", 0),
            "MCI": group_counts_data.get("MCI", 0),
            "AD": group_counts_data.get("AD", 0)
        }
    except FileNotFoundError as e:
        logger.error(f"Failed to load group counts: {e}")
        raise

    # Count exclusions from log
    excluded_count = count_valid_lines_from_exclusions_log(exclusions_log_path)
    
    # Calculate filtered count (raw - excluded)
    filtered_count = raw_count - excluded_count
    
    # Calculate valid_label_proportion
    # This is the proportion of raw records that made it through filtering
    if raw_count > 0:
        valid_label_proportion = filtered_count / raw_count
    else:
        valid_label_proportion = 0.0
    
    # Aggregate metadata
    aggregated_metadata = {
        "raw_count": raw_count,
        "filtered_count": filtered_count,
        "valid_label_proportion": valid_label_proportion,
        "group_counts": group_counts
    }
    
    return aggregated_metadata

def save_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Save the aggregated metadata to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to {output_path}")

def main() -> None:
    """Main entry point for T012g metadata aggregation."""
    logger.info("Starting metadata aggregation (T012g)")
    
    try:
        # Merge metadata files
        metadata = merge_metadata_files()
        
        # Define output path
        output_path = get_path("data/results/metadata.json")
        
        # Save metadata
        save_metadata(metadata, output_path)
        
        logger.info("Metadata aggregation completed successfully")
    except Exception as e:
        logger.error(f"Metadata aggregation failed: {e}")
        raise

if __name__ == "__main__":
    main()