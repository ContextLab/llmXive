"""
Export Manifest Generator for Code Smell Comparison Study.

This module generates a unified CSV manifest linking all collected samples
(both human-written and LLM-generated) to their source metadata.

Output: data/raw/manifest.csv
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path to allow imports from utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_project_root
from utils.logger import get_logger

logger = get_logger(__name__)

def load_samples_from_dir(directory: Path, sample_type: str) -> List[Dict[str, Any]]:
    """
    Load all sample metadata from a directory containing .py/.java files
    and their corresponding .json sidecars.

    Args:
        directory: Path to the samples directory (e.g., data/raw/human_samples)
        sample_type: 'human' or 'llm' to tag the source

    Returns:
        List of dictionaries containing sample metadata.
    """
    samples = []
    if not directory.exists():
        logger.warning(f"Directory not found: {directory}. Skipping.")
        return samples

    # Iterate through files looking for .json sidecars
    for json_file in directory.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Validate required fields exist
            required_fields = ['sample_id', 'repository_id', 'issue_id', 'commit_sha', 'file_path']
            missing = [field for field in required_fields if field not in metadata]
            if missing:
                logger.warning(f"Skipping {json_file.name}: missing fields {missing}")
                continue

            # Add source type
            metadata['source_type'] = sample_type
            samples.append(metadata)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON sidecar {json_file.name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing {json_file.name}: {e}")

    logger.info(f"Loaded {len(samples)} samples from {directory}")
    return samples

def generate_manifest(human_dir: Path, llm_dir: Path, output_path: Path) -> bool:
    """
    Generate a CSV manifest file combining human and LLM samples.

    Args:
        human_dir: Path to human samples directory
        llm_dir: Path to LLM samples directory
        output_path: Path where the manifest CSV will be written

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Generating manifest for {human_dir} and {llm_dir}")

    # Load samples
    human_samples = load_samples_from_dir(human_dir, 'human')
    llm_samples = load_samples_from_dir(llm_dir, 'llm')

    all_samples = human_samples + llm_samples

    if not all_samples:
        logger.error("No samples found to include in manifest.")
        return False

    # Define CSV columns based on task requirements
    # Note: 'language' is added as per task description requirements
    fieldnames = [
        'sample_id',
        'source_type',
        'repository_id',
        'issue_id',
        'task_id',
        'commit_sha',
        'file_path',
        'language'
    ]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for sample in all_samples:
                row = {field: sample.get(field, '') for field in fieldnames}
                writer.writerow(row)

        logger.info(f"Manifest successfully written to {output_path}")
        logger.info(f"Total samples in manifest: {len(all_samples)} (Human: {len(human_samples)}, LLM: {len(llm_samples)})")
        return True

    except IOError as e:
        logger.error(f"Failed to write manifest file: {e}")
        return False

def main():
    """Main entry point for manifest generation."""
    project_root = get_project_root()
    
    human_samples_dir = project_root / "data" / "raw" / "human_samples"
    llm_samples_dir = project_root / "data" / "raw" / "llm_samples"
    output_file = project_root / "data" / "raw" / "manifest.csv"

    logger.info("Starting manifest generation...")
    
    success = generate_manifest(human_samples_dir, llm_samples_dir, output_file)
    
    if success:
        logger.info("Manifest generation completed successfully.")
        return 0
    else:
        logger.error("Manifest generation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
