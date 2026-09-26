"""
T012g: Metadata Aggregation
Merges data/results/metadata_partial_e.json and data/results/metadata_partial_h.json
into the final data/results/metadata.json.

This is the ONLY task that writes to the final metadata.json.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

from config import get_path

# Configure logging
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Required input file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise

def merge_metadata_files(
    partial_e_path: Path,
    partial_h_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Merge two metadata dictionaries into one.
    
    Args:
        partial_e_path: Path to metadata_partial_e.json (low power warnings, group counts)
        partial_h_path: Path to metadata_partial_h.json (valid label proportion)
        output_path: Path to write the final metadata.json
    
    Returns:
        The merged dictionary.
    """
    logger.info(f"Loading metadata from {partial_e_path}")
    metadata_e = load_json_file(partial_e_path)
    
    logger.info(f"Loading metadata from {partial_h_path}")
    metadata_h = load_json_file(partial_h_path)
    
    # Merge dictionaries. 
    # We assume keys do not conflict based on task descriptions:
    # - metadata_partial_e contains: low_power, group_counts
    # - metadata_partial_h contains: valid_label_proportion
    merged_metadata = {**metadata_e, **metadata_h}
    
    logger.info(f"Writing merged metadata to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_metadata, f, indent=2)
    
    logger.info("Metadata aggregation complete.")
    return merged_metadata

def main():
    """Main entry point for T012g."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    
    # Input paths
    partial_e_path = get_path(project_root, "data/results/metadata_partial_e.json")
    partial_h_path = get_path(project_root, "data/results/metadata_partial_h.json")
    
    # Output path
    output_path = get_path(project_root, "data/results/metadata.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        merged = merge_metadata_files(partial_e_path, partial_h_path, output_path)
        logger.info(f"Successfully merged metadata. Output: {output_path}")
        logger.debug(f"Merged content: {merged}")
    except Exception as e:
        logger.error(f"Failed to aggregate metadata: {e}")
        raise

if __name__ == "__main__":
    # Setup basic logging if not already configured
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
