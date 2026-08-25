"""
T030: Inject Disclaimer into Result Files

Injects a mandatory disclaimer string into the metadata section of every JSON
result file found in the results directory (baseline and augmented).
"""
import os
import json
import logging
import glob
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = "DISCLAIMER: Findings are associational and do not imply causation. Results are specific to the simulation parameters and datasets used."
DISCLAIMER_KEY = "metadata"
DISCLAIMER_FIELD = "disclaimer"

def inject_disclaimer_into_file(file_path: str) -> bool:
    """
    Loads a JSON file, injects the disclaimer into metadata, and saves it back.

    Args:
        file_path: Path to the JSON file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ensure metadata key exists
        if DISCLAIMER_KEY not in data:
            data[DISCLAIMER_KEY] = {}
            logger.info(f"Created '{DISCLAIMER_KEY}' key in {file_path}")

        # Inject disclaimer
        data[DISCLAIMER_KEY][DISCLAIMER_FIELD] = DISCLAIMER_TEXT

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Injected disclaimer into {file_path}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def main():
    """
    Main entry point: discovers all JSON files in results/ and injects the disclaimer.
    """
    project_root = Path(__file__).parent.parent
    results_dir = project_root / "results"

    if not results_dir.exists():
        logger.warning(f"Results directory not found at {results_dir}. Nothing to process.")
        return

    # Glob pattern for all JSON files recursively
    pattern = str(results_dir / "**" / "*.json")
    json_files = glob.glob(pattern, recursive=True)

    if not json_files:
        logger.warning("No JSON files found in results directory.")
        return

    logger.info(f"Found {len(json_files)} JSON files to process.")

    success_count = 0
    fail_count = 0

    for file_path in json_files:
        if inject_disclaimer_into_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    logger.info(f"Disclaimer injection complete. Success: {success_count}, Failed: {fail_count}")

    if fail_count > 0:
        logger.error("Some files failed to process.")
        raise RuntimeError(f"Failed to process {fail_count} files.")

if __name__ == "__main__":
    main()