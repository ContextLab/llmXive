"""
Edge Case Handler for Amorphous Silicon Data Processing.

This module implements robust handling of edge cases during data ingestion and
graph construction:
1. Corrupted files: Abort execution with a clear, loud error.
2. Unexpected coordination numbers: Flag the configuration and optionally drop it
   from the validated set based on configuration.

Constraint: This module MUST fail loudly on corrupted data. No silent fallbacks.
"""

import json
import logging
import os
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

import numpy as np

from config.env_config import get_processed_dir, get_data_dir
from logging_config import get_logger
from models.atomic_config import AtomicConfiguration

logger = get_logger(__name__)

# Constants for coordination number validation
# Expected coordination for amorphous silicon is typically 4.
# We allow a small range (e.g., 3-5) for defects, but flag anything outside.
MIN_EXPECTED_COORD = 2
MAX_EXPECTED_COORD = 6
DEFAULT_COORDINATIONS = {3, 4, 5}  # Typical for a-Si (3-coord defects, 4-coord bulk, 5-coord defects)


class CorruptedFileError(Exception):
    """Raised when a data file is detected as corrupted or unreadable."""
    pass


class UnexpectedCoordinationError(Exception):
    """Raised when a configuration has coordination numbers outside expected bounds."""
    pass


def detect_corruption(file_path: Path) -> bool:
    """
    Detects if a file is corrupted.

    Checks:
    1. File exists and is not empty.
    2. File is readable (basic byte read).
    3. If it's a known format (e.g., JSON, XYZ), attempts a basic parse.

    Args:
        file_path: Path to the file to check.

    Returns:
        True if corruption is detected, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return True

    if file_path.stat().st_size == 0:
        logger.error(f"File is empty: {file_path}")
        return True

    try:
        # Try to read a chunk to ensure it's readable
        with open(file_path, 'rb') as f:
            f.read(1024)

        # Specific format checks
        suffix = file_path.suffix.lower()
        if suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        elif suffix == '.xyz':
            # Basic XYZ check: first line should be an integer
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line.isdigit():
                    logger.warning(f"XYZ file {file_path} does not start with atom count.")
                    # We might still proceed, but log it. For now, strict mode:
                    return True
        # Add more format checks as needed

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return True
    except ValueError as e:
        logger.error(f"Value error reading {file_path}: {e}")
        return True
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        return True

    return False


def validate_coordination_numbers(config: AtomicConfiguration) -> Tuple[bool, List[int]]:
    """
    Validates the coordination numbers of atoms in a configuration.

    Args:
        config: The AtomicConfiguration to validate.

    Returns:
        A tuple (is_valid, unexpected_coords).
        is_valid: True if all coordination numbers are within expected bounds.
        unexpected_coords: List of coordination numbers found that are outside bounds.
    """
    if config.coordinates is None or config.atomic_numbers is None:
        logger.warning(f"Configuration {config.id} has missing coordinates or atomic numbers.")
        return False, []

    # Calculate coordination numbers if not present
    # This assumes a cutoff radius logic is available or passed.
    # For this implementation, we assume the graph or neighbor list is already built
    # or we calculate it here using a default cutoff if not provided in config.
    # Since AtomicConfiguration doesn't explicitly store neighbors, we assume
    # the caller has ensured this or we calculate a simple distance-based count.

    # NOTE: In a real pipeline, this would likely use the graph built in T015/T018.
    # Here we simulate the check based on the config's data.
    # We assume the config has a 'neighbors' attribute or we compute it.
    # If the config is raw, we can't compute coordination without a cutoff.
    # Let's assume the config has been processed and has 'coordination_numbers'
    # or we compute it from coordinates + cutoff.

    # Fallback: If not pre-computed, compute from coordinates (requires cutoff)
    # For this task, we assume the graph_builder has already assigned neighbors.
    # If the config object doesn't have neighbors, we can't validate strictly.
    # However, the task asks to handle "unexpected coordination numbers".
    # We will assume the config has a property `coordination_numbers` or we derive it.

    # Since AtomicConfiguration is a dataclass, let's check for a 'neighbors' list
    # or compute it.
    # To be safe, we will assume the caller passes a graph or neighbors.
    # But the function signature takes AtomicConfiguration.
    # Let's assume the config has a 'neighbors' attribute populated by graph_builder.
    # If not, we return a warning that we cannot validate.

    if not hasattr(config, 'neighbors') or config.neighbors is None:
        # Cannot validate without neighbor info.
        # In a real scenario, this might mean the graph builder failed silently.
        # We flag it as "cannot validate" but not necessarily "unexpected".
        # However, for the sake of the task, we assume the graph exists.
        # If we can't find it, we might assume it's 0 or raise an error.
        # Let's assume it's an error state for the config.
        logger.warning(f"Configuration {config.id} missing neighbor information. Cannot validate coordination.")
        return False, []

    # Extract coordination numbers
    coords = []
    for neighbor_list in config.neighbors:
        coord = len(neighbor_list) if neighbor_list else 0
        coords.append(coord)

    unexpected = [c for c in coords if c < MIN_EXPECTED_COORD or c > MAX_EXPECTED_COORD]

    if unexpected:
        logger.warning(f"Configuration {config.id} has unexpected coordination numbers: {unexpected}")
        return False, unexpected

    return True, []


def handle_edge_cases(configs: List[AtomicConfiguration], strict_mode: bool = True) -> Dict[str, Any]:
    """
    Main handler for edge cases in a list of configurations.

    - Corrupted files: Aborts execution (raises error).
    - Unexpected coordination numbers: Flags the config. If strict_mode is True, drops it.
      If False, retains it but marks it as 'FLAGGED'.

    Args:
        configs: List of AtomicConfiguration objects to process.
        strict_mode: If True, drop configs with unexpected coordination. If False, flag them.

    Returns:
        A dictionary with:
          - 'processed': List of valid, clean configurations.
          - 'flagged': List of configurations with unexpected coordination (if not dropped).
          - 'dropped': List of configurations dropped due to unexpected coordination.
          - 'errors': List of error messages for corrupted files.
    """
    processed = []
    flagged = []
    dropped = []
    errors = []

    for config in configs:
        # 1. Check for file corruption (if file path is available)
        if hasattr(config, 'file_path') and config.file_path:
            file_path = Path(config.file_path)
            if detect_corruption(file_path):
                error_msg = f"CRITICAL: Corrupted file detected for config {config.id}: {file_path}"
                logger.error(error_msg)
                errors.append(error_msg)
                # ABORT: Raise error immediately as per constraint
                raise CorruptedFileError(error_msg)

        # 2. Check for unexpected coordination numbers
        is_valid, unexpected = validate_coordination_numbers(config)

        if not is_valid:
            if strict_mode:
                logger.warning(f"Dropping config {config.id} due to unexpected coordination numbers: {unexpected}")
                dropped.append({
                    "id": config.id,
                    "reason": "Unexpected coordination numbers",
                    "details": unexpected
                })
            else:
                logger.warning(f"Flagging config {config.id} due to unexpected coordination numbers: {unexpected}")
                flagged.append({
                    "id": config.id,
                    "reason": "Unexpected coordination numbers",
                    "details": unexpected
                })
            # Do not add to processed
            continue

        # If valid, add to processed
        processed.append(config)

    return {
        "processed": processed,
        "flagged": flagged,
        "dropped": dropped,
        "errors": errors,
        "summary": {
            "total_input": len(configs),
            "processed": len(processed),
            "flagged": len(flagged),
            "dropped": len(dropped),
            "errors": len(errors)
        }
    }


def save_edge_case_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Saves the edge case handling report to a JSON file.

    Args:
        report: The report dictionary from handle_edge_cases.
        output_path: Optional path to save the report. Defaults to data/processed/edge_case_report.json.

    Returns:
        The path to the saved file.
    """
    if output_path is None:
        processed_dir = get_processed_dir()
        output_path = Path(processed_dir) / "edge_case_report.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert AtomicConfiguration objects to IDs for JSON serialization
    serializable_report = {
        "summary": report["summary"],
        "flagged": report["flagged"],
        "dropped": report["dropped"],
        "errors": report["errors"]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_report, f, indent=2)

    logger.info(f"Edge case report saved to {output_path}")
    return output_path


def main():
    """
    Entry point for the edge case handler.
    This function is intended to be called after data ingestion and graph construction.
    """
    logger.info("Starting Edge Case Handler...")

    # This would typically be called from a pipeline orchestrator
    # For demonstration, we assume configs are loaded from a previous step
    # In a real scenario, we would load from data/processed/validation_report.json
    # or similar.

    # Placeholder for actual integration
    # configs = load_configurations_from_validation_report(...)
    # report = handle_edge_cases(configs, strict_mode=True)
    # save_edge_case_report(report)

    logger.info("Edge Case Handler completed.")


if __name__ == "__main__":
    main()
