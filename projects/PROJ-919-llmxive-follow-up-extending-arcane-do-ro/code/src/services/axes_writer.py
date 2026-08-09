import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.lib.config import get_config
from src.lib.utils import get_logger
from src.lib.state_tracker import log_experiment_state, hash_parameters, generate_run_id

logger = get_logger(__name__)

def ensure_derived_directory() -> Path:
    """Ensure the data/derived directory exists."""
    config = get_config()
    derived_path = Path(config.data_dir) / "derived"
    derived_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured derived directory exists: {derived_path}")
    return derived_path

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_axes_to_jsonl(
    axes_data: List[Dict[str, Any]],
    output_filename: str = "axes.jsonl",
    run_id: Optional[str] = None,
) -> Path:
    """
    Write validated axis definitions to a JSONL file.

    Args:
        axes_data: List of dictionaries containing 'coarse' and 'fine' axis definitions.
        output_filename: Name of the output file (default: axes.jsonl).
        run_id: Optional run ID for state tracking.

    Returns:
        Path to the written file.
    """
    output_dir = ensure_derived_directory()
    output_path = output_dir / output_filename

    logger.info(f"Writing {len(axes_data)} axis entries to {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in axes_data:
            # Ensure each entry has metadata
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "character": entry.get("character", "unknown"),
                "coarse": entry.get("coarse", {}),
                "fine": entry.get("fine", {}),
                "validation_passed": entry.get("validation_passed", True),
            }
            f.write(json.dumps(record) + "\n")

    # Compute checksum for reproducibility (Constitution Principle III)
    checksum = compute_file_checksum(output_path)
    logger.info(f"Computed checksum for {output_path}: {checksum}")

    # Log experiment state if run_id is provided
    if run_id:
        state_params = {
            "output_file": str(output_path),
            "entry_count": len(axes_data),
            "checksum": checksum,
        }
        log_experiment_state(run_id, "axes_written", state_params)
    else:
        # Generate a run ID if not provided for state tracking
        gen_run_id = generate_run_id()
        state_params = {
            "output_file": str(output_path),
            "entry_count": len(axes_data),
            "checksum": checksum,
        }
        log_experiment_state(gen_run_id, "axes_written", state_params)

    return output_path

def read_axes_from_jsonl(input_path: Path) -> List[Dict[str, Any]]:
    """
    Read axis definitions from a JSONL file.

    Args:
        input_path: Path to the JSONL file.

    Returns:
        List of dictionaries containing axis data.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Axis file not found: {input_path}")

    axes_data = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                axes_data.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")

    logger.info(f"Read {len(axes_data)} axis entries from {input_path}")
    return axes_data

def verify_axes_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the checksum of an axes file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 checksum.

    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        return False

    actual_checksum = compute_file_checksum(file_path)
    match = actual_checksum == expected_checksum

    if match:
        logger.info(f"Checksum verification passed for {file_path}")
    else:
        logger.error(
            f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, "
            f"Actual: {actual_checksum}"
        )

    return match

def get_axes_summary(file_path: Path) -> Dict[str, Any]:
    """
    Generate a summary of the axes file.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        Dictionary containing summary statistics.
    """
    axes_data = read_axes_from_jsonl(file_path)

    if not axes_data:
        return {
            "file_path": str(file_path),
            "total_entries": 0,
            "characters": [],
            "checksum": None,
        }

    characters = [entry.get("character", "unknown") for entry in axes_data]
    unique_characters = list(set(characters))

    checksum = compute_file_checksum(file_path)

    return {
        "file_path": str(file_path),
        "total_entries": len(axes_data),
        "unique_characters": unique_characters,
        "character_count": len(unique_characters),
        "checksum": checksum,
    }

def main():
    """
    Main entry point for writing axes to JSONL.
    Demonstrates the writer functionality.
    """
    logger.info("Starting axes writer demonstration")

    # Sample data simulating validated axes from T011/T012
    sample_axes = [
        {
            "character": "TestCharacter1",
            "coarse": {
                "axis_name": "Moral Compass",
                "description": "Tendency towards altruism vs. selfishness",
                "scale": "1-10",
            },
            "fine": {
                "axis_name": "Conflict Resolution Style",
                "description": "Preference for confrontation vs. avoidance",
                "scale": "Direct to Passive",
            },
            "validation_passed": True,
        },
        {
            "character": "TestCharacter2",
            "coarse": {
                "axis_name": "Emotional Stability",
                "description": "Consistency of emotional responses under stress",
                "scale": "Low to High",
            },
            "fine": {
                "axis_name": "Social Engagement",
                "description": "Preference for group interaction vs. solitude",
                "scale": "Extroverted to Introverted",
            },
            "validation_passed": True,
        },
    ]

    try:
        output_path = write_axes_to_jsonl(sample_axes, "axes.jsonl")
        logger.info(f"Successfully wrote axes to {output_path}")

        # Verify the write
        summary = get_axes_summary(output_path)
        logger.info(f"Axes summary: {json.dumps(summary, indent=2)}")

        # Verify checksum
        is_valid = verify_axes_checksum(output_path, summary["checksum"])
        if is_valid:
            logger.info("Checksum verification successful")
        else:
            logger.error("Checksum verification failed")

    except Exception as e:
        logger.error(f"Error during axes writing: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
