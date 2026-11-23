"""
T017: Write processing summary JSON.

This script reads the state file (which tracks downloaded/processed subjects),
calculates statistics, and writes a summary to data/results/processing_summary.json.
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent))

from checksums import load_state
from logging_config import get_logger, setup_logging

def calculate_summary_stats(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate summary statistics from the state data.

    Args:
        state_data: Dictionary containing project state including subject info.

    Returns:
        Dictionary with target, processed, skipped, and proportion.
    """
    # Extract subject information from state
    # The state file should contain a 'subjects' key with a list of subject records
    subjects = state_data.get("subjects", [])
    
    if not subjects:
        # If no subjects in state, try to infer from checksums or other metadata
        checksums = state_data.get("checksums", {})
        if checksums:
            # Count subjects that have both SC and FC matrices recorded
            processed_count = sum(
                1 for sub_id, data in checksums.items()
                if isinstance(data, dict) and "structural_matrix" in data and "functional_matrix" in data
            )
            total_count = len(checksums)
        else:
            processed_count = 0
            total_count = 0
    else:
        # Count processed vs skipped from subject records
        processed_count = sum(
            1 for sub in subjects 
            if sub.get("status") == "processed" or (
                "structural_matrix" in sub and "functional_matrix" in sub
            )
        )
        total_count = len(subjects)
        skipped_count = total_count - processed_count
    
    # Calculate proportion
    proportion = processed_count / total_count if total_count > 0 else 0.0
    
    # Determine target (total expected subjects)
    # If we have a total count, that's our target. Otherwise, use processed + skipped.
    target = total_count if total_count > 0 else processed_count
    
    return {
        "target": target,
        "processed": processed_count,
        "skipped": total_count - processed_count,
        "proportion": round(proportion, 4)
    }

def write_summary(summary_data: Dict[str, Any], output_path: Path) -> None:
    """
    Write the summary data to a JSON file.

    Args:
        summary_data: Dictionary containing summary statistics.
        output_path: Path to the output JSON file.
    """
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

def main() -> int:
    """
    Main entry point for the processing summary script.

    Returns:
        0 on success, non-zero on failure.
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Define paths
    project_root = Path(__file__).parent.parent
    state_file = project_root / "state" / "projects" / "PROJ-268-the-impact-of-network-centrality-on-neur.yaml"
    output_file = project_root / "data" / "results" / "processing_summary.json"

    logger.info(f"Loading state from: {state_file}")
    
    if not state_file.exists():
        logger.error(f"State file not found: {state_file}")
        return 1

    try:
        state_data = load_state(str(state_file))
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return 1

    logger.info("Calculating summary statistics...")
    summary = calculate_summary_stats(state_data)

    logger.info(f"Writing summary to: {output_file}")
    try:
        write_summary(summary, output_file)
    except Exception as e:
        logger.error(f"Failed to write summary file: {e}")
        return 1

    logger.info(f"Processing summary written successfully:")
    logger.info(f"  Target: {summary['target']}")
    logger.info(f"  Processed: {summary['processed']}")
    logger.info(f"  Skipped: {summary['skipped']}")
    logger.info(f"  Proportion: {summary['proportion']:.2%}")

    return 0

if __name__ == "__main__":
    sys.exit(main())