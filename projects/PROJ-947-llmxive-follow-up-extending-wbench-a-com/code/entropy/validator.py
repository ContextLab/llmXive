"""
Task Validity Validator (Action Chain Check) for WBench Sequence Variants.

This module validates that generated action chains are physically plausible.
It reads variant data from `data/processed/variants.csv`, checks the action
sequences for physical plausibility, and outputs validity flags to
`data/processed/validity_flags.csv`.

Plausibility checks include:
1. Action sequence is not empty.
2. Action types are valid (e.g., 'move', 'pick', 'place', 'push').
3. No impossible immediate sequences (e.g., 'place' before 'pick').
4. Coordinate changes are within physical bounds (if coordinates present).
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Set

# Import from project utils
from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import DataValidationError

# Constants
VALID_ACTION_TYPES: Set[str] = {"move", "pick", "place", "push", "pull", "rotate", "drop"}
REQUIRED_COLUMNS: List[str] = ["case_id", "variant_type", "action_chain"]
OUTPUT_DIR: Path = Path("data/processed")
OUTPUT_FILE: Path = OUTPUT_DIR / "validity_flags.csv"
INPUT_FILE: Path = OUTPUT_DIR / "variants.csv"

logger = get_logger(__name__)


def _parse_action_chain(action_chain_str: str) -> List[Dict[str, Any]]:
    """
    Parse the action chain string (JSON) into a list of action dictionaries.

    Args:
        action_chain_str: JSON string representing the action chain.

    Returns:
        List of action dictionaries.

    Raises:
        DataValidationError: If parsing fails or format is invalid.
    """
    if not action_chain_str or not isinstance(action_chain_str, str):
        raise DataValidationError("Action chain is empty or not a string.")

    try:
        chain = json.loads(action_chain_str)
        if not isinstance(chain, list):
            raise DataValidationError("Action chain must be a JSON list.")
        if len(chain) == 0:
            raise DataValidationError("Action chain cannot be empty.")
        return chain
    except json.JSONDecodeError as e:
        raise DataValidationError(f"Failed to parse action chain JSON: {e}")


def _validate_action_types(chain: List[Dict[str, Any]]) -> bool:
    """
    Check if all actions in the chain have valid types.

    Args:
        chain: List of action dictionaries.

    Returns:
        True if all types are valid, False otherwise.
    """
    for i, action in enumerate(chain):
        if not isinstance(action, dict):
            return False
        action_type = action.get("type")
        if action_type not in VALID_ACTION_TYPES:
            logger.warning(f"Invalid action type '{action_type}' at index {i}")
            return False
    return True


def _validate_sequence_logic(chain: List[Dict[str, Any]]) -> bool:
    """
    Check for physically impossible sequences (e.g., placing before picking).

    Args:
        chain: List of action dictionaries.

    Returns:
        True if sequence logic is valid, False otherwise.
    """
    held_object = None

    for i, action in enumerate(chain):
        action_type = action.get("type")

        if action_type == "pick":
            # Can only pick if not holding anything (simplified model)
            # or if we assume multi-object holding is not supported yet
            if held_object is not None:
                logger.warning(f"Attempted 'pick' while holding '{held_object}' at index {i}")
                return False
            # Assume pick sets held_object (simplified: just check logic flow)
            held_object = action.get("object", "unknown")

        elif action_type == "place":
            if held_object is None:
                logger.warning(f"Attempted 'place' without holding an object at index {i}")
                return False
            held_object = None

        elif action_type == "drop":
            # Drop is similar to place but implies loss of control; requires object
            if held_object is None:
                logger.warning(f"Attempted 'drop' without holding an object at index {i}")
                return False
            held_object = None

        # Other actions like 'move', 'push', 'pull' do not change held state
        # in this simplified model, or depend on specific object context.

    return True


def _validate_coordinates(chain: List[Dict[str, Any]]) -> bool:
    """
    Check if coordinates (if present) are within physical bounds.

    Args:
        chain: List of action dictionaries.

    Returns:
        True if coordinates are valid, False otherwise.
    """
    # Define bounds (example: 0 to 1000 units)
    MIN_COORD = 0.0
    MAX_COORD = 1000.0

    for i, action in enumerate(chain):
        if "position" in action:
            pos = action["position"]
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                x, y = pos[0], pos[1]
                if not (MIN_COORD <= x <= MAX_COORD and MIN_COORD <= y <= MAX_COORD):
                    logger.warning(f"Coordinates ({x}, {y}) out of bounds at index {i}")
                    return False
            elif isinstance(pos, dict):
                x = pos.get("x")
                y = pos.get("y")
                if x is not None and y is not None:
                    if not (MIN_COORD <= x <= MAX_COORD and MIN_COORD <= y <= MAX_COORD):
                        logger.warning(f"Coordinates ({x}, {y}) out of bounds at index {i}")
                        return False
    return True


def validate_action_chain(action_chain_str: str) -> bool:
    """
    Main validation function for a single action chain.

    Args:
        action_chain_str: JSON string of the action chain.

    Returns:
        True if the chain is physically plausible, False otherwise.
    """
    try:
        chain = _parse_action_chain(action_chain_str)
    except DataValidationError as e:
        log_error(f"Validation failed: {e}")
        return False

    if not _validate_action_types(chain):
        return False

    if not _validate_sequence_logic(chain):
        return False

    if not _validate_coordinates(chain):
        return False

    return True


def validate_variants(input_path: Path = INPUT_FILE, output_path: Path = OUTPUT_FILE) -> pd.DataFrame:
    """
    Load variants, validate action chains, and save validity flags.

    Args:
        input_path: Path to the input variants CSV.
        output_path: Path to the output validity flags CSV.

    Returns:
        DataFrame containing validity flags.
    """
    if not input_path.exists():
        fail_loudly(f"Input file not found: {input_path}")

    log_info(f"Loading variants from {input_path}")
    df = pd.read_csv(input_path)

    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        fail_loudly(f"Missing required columns in input: {missing_cols}")

    log_info(f"Validating {len(df)} action chains...")
    results = []

    for idx, row in df.iterrows():
        case_id = row["case_id"]
        variant_type = row["variant_type"]
        action_chain = row["action_chain"]

        is_valid = validate_action_chain(action_chain)

        results.append({
            "case_id": case_id,
            "variant_type": variant_type,
            "is_valid": is_valid
        })

        if not is_valid:
            log_warning(f"Invalid chain for case {case_id}, variant {variant_type}")

    validity_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log_info(f"Saving validity flags to {output_path}")
    validity_df.to_csv(output_path, index=False)

    return validity_df


def main():
    """Entry point for the validator script."""
    try:
        log_info("Starting Task Validity Validator (T014)")
        df = validate_variants()
        log_info(f"Validation complete. Total valid: {df['is_valid'].sum()}, invalid: {(~df['is_valid']).sum()}")
    except Exception as e:
        log_exception(e)
        fail_loudly(f"Validator failed: {e}")


if __name__ == "__main__":
    main()
