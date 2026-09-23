"""
T051: Validate Manual Update

Implements the validation logic for manually injected dataset entries.
This script checks if a manual update to data/README.md has successfully
cleared a critical blocker (data/blocked_status.json).

It does NOT inject data; it only validates the state of the README and
the presence of the blocker file.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing utilities from the project
from config import get_data_dir
from read_ids import read_dataset_ids
from update_readme import update_readme

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("validate_manual_update")


def parse_verified_datasets_block(readme_path: Path) -> List[Dict[str, Any]]:
    """
    Parses the 'Verified datasets' YAML block from data/README.md.
    Returns a list of dictionaries with keys: id, source, url.
    
    Note: This is a simplified parser assuming the YAML block is formatted
    as a list of objects with specific keys.
    """
    if not readme_path.exists():
        raise FileNotFoundError(f"README file not found: {readme_path}")

    content = readme_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Find the start of the 'Verified datasets' block
    start_idx = None
    for i, line in enumerate(lines):
        if "Verified datasets" in line and line.strip().startswith("#"):
            start_idx = i + 1
            break
    
    if start_idx is None:
        logger.warning("No 'Verified datasets' section found in README.")
        return []

    # Extract lines until the next section or end of file
    block_lines = []
    in_block = False
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        if line.startswith("-"):
            in_block = True
            block_lines.append(line)
        elif in_block:
            # Check if we hit a new section header
            if line.startswith("#"):
                break
            if line.startswith("-"):
                block_lines.append(line)
            else:
                # Likely a continuation of the previous item or a new property
                # For simplicity, we assume the block ends at the next section header
                # or if the line is not indented and not a list item (heuristic)
                if not line.startswith(" ") and not line.startswith("-"):
                    break
                block_lines.append(line)

    # Parse the extracted block
    datasets = []
    current_item = {}
    for line in block_lines:
        line = line.strip()
        if line.startswith("-"):
            if current_item:
                datasets.append(current_item)
            current_item = {}
            # Parse the first key-value pair on the same line as '-'
            # Format: - id: <ID>, source: <Source>, url: <URL>
            parts = line[1:].split(",")
            for part in parts:
                part = part.strip()
                if ":" in part:
                    key, value = part.split(":", 1)
                    current_item[key.strip()] = value.strip()
        else:
            # Handle multi-line items if any (not expected in this format)
            if ":" in line:
                key, value = line.split(":", 1)
                current_item[key.strip()] = value.strip()

    if current_item:
        datasets.append(current_item)

    return datasets


def validate_manual_update() -> bool:
    """
    Validates if a manual update has cleared the blocker.
    
    Returns:
        bool: True if the blocker was cleared successfully, False otherwise.
    """
    data_dir = get_data_dir()
    readme_path = data_dir / "README.md"
    blocked_status_path = data_dir / "blocked_status.json"

    logger.info(f"Checking for blocked_status.json at: {blocked_status_path}")

    if not blocked_status_path.exists():
        logger.info("No blocked_status.json found. The system is not in a blocked state.")
        return True

    logger.warning("blocked_status.json exists. Checking for manual update...")

    # Re-parse the README to verify new dataset entries
    try:
        datasets = parse_verified_datasets_block(readme_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to parse README: {e}")
        return False

    if not datasets:
        logger.error("No valid dataset entries found in 'Verified datasets' block.")
        logger.error("Manual update failed: No datasets added.")
        return False

    # Validate each dataset entry using existing logic from read_ids
    # read_dataset_ids expects a path to the README and returns a list of dicts
    # We can reuse the logic that T012a uses to ensure consistency
    try:
        # read_dataset_ids returns a list of dicts
        validated_datasets = read_dataset_ids(readme_path)
        if not validated_datasets:
            logger.error("Dataset IDs validation failed. No valid datasets found.")
            return False
        
        logger.info(f"Found {len(validated_datasets)} valid dataset(s) after manual update.")
    except Exception as e:
        logger.error(f"Error validating dataset IDs: {e}")
        return False

    # If we reach here, the manual update is valid
    logger.info("Manual update validated successfully. Clearing blocker...")

    # Remove the blocked_status.json
    try:
        blocked_status_path.unlink()
        logger.info(f"Removed {blocked_status_path}")
    except Exception as e:
        logger.error(f"Failed to remove blocked_status.json: {e}")
        return False

    # Update README to reflect the change (optional but good practice)
    # We can call update_readme to refresh the status, but it might be heavy.
    # For T051, we just log the success.
    logger.info("Blocker cleared by manual update.")

    return True


def main():
    """Main entry point for the validation script."""
    success = validate_manual_update()
    if success:
        logger.info("Validation successful. The pipeline can proceed.")
        sys.exit(0)
    else:
        logger.error("Validation failed. Manual intervention required or fix the README.")
        sys.exit(1)


if __name__ == "__main__":
    main()