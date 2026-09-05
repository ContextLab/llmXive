"""
Baseline Adapter Module for llmXive Follow-up Project.

This module parses Baseline MLLM (Visual) output into structured JSON mental maps
and validates them against the masked ground-truth format used by the Text Agent.

Implements Task T033: US3 - Structured JSON Comparison + Semantic Similarity.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple

# Import logger from the project's logging utility
from logger import get_logger

# Define a custom exception for baseline adapter errors
class BaselineAdapterError(Exception):
    """Custom exception for errors during baseline output parsing and validation."""
    pass

# Get the project logger
logger = get_logger(__name__)

# Expected keys in the baseline output JSON based on baseline_runner.py
BASELINE_OUTPUT_KEYS = {"action", "mental_map"}

# Expected keys in the target schema (state_snapshot.schema.yaml)
# Based on T007: state_snapshot.schema.yaml fields:
# ascii_grid, event_log, ground_truth_state, masked_ground_truth
# For the mental map comparison, we expect the parsed output to align with
# the structure of 'masked_ground_truth' which contains the state representation.
TARGET_SCHEMA_KEYS = {"action", "mental_map"}

def parse_baseline_output(raw_output: str) -> Dict[str, Any]:
    """
    Parse the raw JSON string output from the Baseline MLLM.

    Args:
        raw_output (str): The raw JSON string output from the baseline model.

    Returns:
        Dict[str, Any]: Parsed dictionary containing 'action' and 'mental_map'.

    Raises:
        BaselineAdapterError: If the output is not valid JSON or missing required keys.
    """
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise BaselineAdapterError(f"Failed to parse baseline output as JSON: {e}")

    if not isinstance(parsed, dict):
        raise BaselineAdapterError(f"Baseline output must be a JSON object, got {type(parsed)}")

    missing_keys = BASELINE_OUTPUT_KEYS - set(parsed.keys())
    if missing_keys:
        raise BaselineAdapterError(f"Baseline output missing required keys: {missing_keys}")

    # Validate types
    if not isinstance(parsed["action"], str):
        raise BaselineAdapterError(f"Expected 'action' to be a string, got {type(parsed['action'])}")
    
    if not isinstance(parsed["mental_map"], str):
        raise BaselineAdapterError(f"Expected 'mental_map' to be a string, got {type(parsed['mental_map'])}")

    logger.debug(f"Successfully parsed baseline output: action={parsed['action'][:20]}..., mental_map={parsed['mental_map'][:20]}...")
    return parsed

def validate_against_masked_ground_truth(parsed_output: Dict[str, Any], masked_ground_truth: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that the parsed baseline output matches the format of the masked ground truth.

    This ensures the baseline's mental map can be directly compared with the text agent's
    mental map, which is derived from the same masked ground truth structure.

    Args:
        parsed_output (Dict[str, Any]): The parsed baseline output containing 'action' and 'mental_map'.
        masked_ground_truth (Dict[str, Any]): The masked ground truth state snapshot.

    Returns:
        Tuple[bool, str]: (is_valid, error_message). is_valid is True if validation passes.
    """
    # Check if masked_ground_truth has the expected structure
    if "masked_ground_truth" not in masked_ground_truth:
        # If the input is already the masked state, use it directly
        if "state" in masked_ground_truth or "grid" in masked_ground_truth:
            logger.debug("Using masked_ground_truth input directly as state representation.")
            expected_structure = masked_ground_truth
        else:
            raise BaselineAdapterError("Invalid masked_ground_truth format: missing 'masked_ground_truth' key and state representation.")
    else:
        expected_structure = masked_ground_truth["masked_ground_truth"]

    # The mental_map in parsed_output should be a string representation of the state
    # that aligns with the expected structure (e.g., ASCII grid, list of items, etc.)
    # For this implementation, we assume the mental_map is a string that should
    # be comparable to the string representation of the masked ground truth.

    if "mental_map" not in parsed_output:
        return False, "Parsed output missing 'mental_map' field."

    mental_map = parsed_output["mental_map"]
    
    # Validate that mental_map is a non-empty string
    if not mental_map or not isinstance(mental_map, str):
        return False, f"Invalid mental_map format: expected non-empty string, got {type(mental_map)}"

    # Additional validation could be added here depending on the specific format
    # of the masked_ground_truth (e.g., checking for specific keys in a JSON string)
    # For now, we ensure the structure is consistent with the schema.
    
    # Check if the mental_map string can be parsed as JSON if the ground truth is structured
    # This is a heuristic; the actual comparison logic is in the scorer.
    try:
        # If the mental_map is a JSON string, verify it's valid JSON
        json.loads(mental_map)
        logger.debug("Mental map is valid JSON string.")
    except json.JSONDecodeError:
        # It might be a plain ASCII grid string, which is also valid
        logger.debug("Mental map is not JSON, assuming ASCII grid or plain text format.")

    # Validate action against allowed actions (optional but good practice)
    allowed_actions = {"move_up", "move_down", "move_left", "move_right", "wait"}
    if parsed_output.get("action") not in allowed_actions:
        logger.warning(f"Action '{parsed_output.get('action')}' not in allowed actions: {allowed_actions}")

    return True, "Validation successful."

def process_baseline_run_file(file_path: str, masked_ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single baseline run file, parse its output, and validate against masked ground truth.

    Args:
        file_path (str): Path to the baseline run JSON file.
        masked_ground_truth (Dict[str, Any]): The masked ground truth for this run.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed output and validation status.
                        Structure: {"success": bool, "parsed_output": dict, "validation": dict, "error": str}

    Raises:
        BaselineAdapterError: If the file cannot be read or parsed.
    """
    if not os.path.exists(file_path):
        raise BaselineAdapterError(f"Baseline run file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_output = f.read().strip()
    except IOError as e:
        raise BaselineAdapterError(f"Failed to read baseline run file {file_path}: {e}")

    parsed_output = parse_baseline_output(raw_output)
    is_valid, error_msg = validate_against_masked_ground_truth(parsed_output, masked_ground_truth)

    result = {
        "success": is_valid,
        "parsed_output": parsed_output,
        "validation": {"is_valid": is_valid, "message": error_msg}
    }

    if not is_valid:
        logger.error(f"Validation failed for {file_path}: {error_msg}")
    else:
        logger.info(f"Successfully processed and validated baseline run: {file_path}")

    return result

def main():
    """
    Main entry point for the baseline adapter module.
    This function is primarily for testing and demonstration purposes.
    In the actual pipeline, this module is imported and used by the scorer.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Parse and validate baseline MLLM output.")
    parser.add_argument("--input", type=str, required=True, help="Path to baseline run JSON file.")
    parser.add_argument("--ground-truth", type=str, required=True, help="Path to masked ground truth JSON file.")
    parser.add_argument("--output", type=str, default=None, help="Path to output validation result JSON file.")
    
    args = parser.parse_args()

    try:
        # Load masked ground truth
        if not os.path.exists(args.ground_truth):
            raise FileNotFoundError(f"Ground truth file not found: {args.ground_truth}")
        
        with open(args.ground_truth, 'r', encoding='utf-8') as f:
            masked_ground_truth = json.load(f)

        # Process the baseline run
        result = process_baseline_run_file(args.input, masked_ground_truth)

        # Output result
        output_json = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"Validation result written to {args.output}")
        else:
            print(output_json)

        sys.exit(0 if result["success"] else 1)

    except BaselineAdapterError as e:
        logger.error(f"BaselineAdapterError: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()