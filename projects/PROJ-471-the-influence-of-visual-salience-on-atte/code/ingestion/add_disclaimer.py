import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import get_paths, load_config
from utils.logging import get_logger

logger = get_logger(__name__)

def process_json_file(file_path: Path, disclaimer: str) -> bool:
    """
    Load a JSON file, append a disclaimer field if it doesn't exist,
    and write it back.

    Args:
        file_path: Path to the JSON file.
        disclaimer: The disclaimer text to append.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        disclaimer_key = "disclaimer"
        if disclaimer_key in data:
            logger.info(f"Disclaimer already exists in {file_path}, skipping update.")
            # Optionally update the timestamp if desired, but strictly we just ensure it exists
            data["disclaimer_updated_at"] = datetime.now().isoformat()
        else:
            data[disclaimer_key] = disclaimer
            data["disclaimer_updated_at"] = datetime.now().isoformat()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Successfully updated {file_path} with disclaimer.")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        return False

def main():
    """
    Main entry point for T016.
    Appends "correlational only" disclaimer to data/processed/salience_maps/metadata.json.
    """
    config = load_config()
    paths = get_paths()

    # Target file as specified in T016
    metadata_file = paths["processed"] / "salience_maps" / "metadata.json"

    if not metadata_file.exists():
        logger.error(f"Target metadata file not found: {metadata_file}. "
                     "Ensure T016a (metadata_writer.py) has been run successfully.")
        return 1

    disclaimer_text = (
        "CORRELATIONAL ONLY: This study observes associations between visual salience "
        "and attentional bias. No causal claims are made regarding the influence of "
        "visual features on moral judgments. Results are preliminary and require "
        "further validation with controlled experimental designs."
    )

    success = process_json_file(metadata_file, disclaimer_text)

    if not success:
        logger.error("Failed to update metadata file with disclaimer.")
        return 1

    logger.info("Task T016 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())