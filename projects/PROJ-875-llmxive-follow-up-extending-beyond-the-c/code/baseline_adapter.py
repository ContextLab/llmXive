"""
Baseline Adapter Module for llmXive Follow-up Project.

This module implements the adapter to parse Baseline MLLM (Visual) output
into structured JSON mental maps compatible with the Text Agent's schema.

Target Schema: Matches state_snapshot.schema.yaml (defined in specs/contracts/)
Fields:
  - action: str (move_up, move_down, move_left, move_right, wait)
  - mental_map: str (JSON string representing the agent's internal state)

Validation: Ensures output matches the masked ground-truth format used by the Text Agent.
"""
import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple

# Import logging configuration from existing project module
from logger import get_logger

# Define valid action types to enforce schema compliance
VALID_ACTIONS = {
    "move_up",
    "move_down",
    "move_left",
    "move_right",
    "wait"
}

# Initialize logger
logger = get_logger(__name__)


class BaselineAdapterError(Exception):
    """Custom exception for baseline adapter parsing failures."""
    pass


def parse_baseline_output(
    raw_output: str,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse raw Baseline MLLM output into structured JSON mental map.

    Args:
        raw_output: Raw JSON string from the Baseline MLLM (Visual) model.
                    Expected format: {"action": "...", "mental_map": "..."}
        run_id: Optional identifier for the run, used in error logging.

    Returns:
        Dict containing:
            - action: str (validated against VALID_ACTIONS)
            - mental_map: str (JSON string of the state snapshot)

    Raises:
        BaselineAdapterError: If parsing fails, schema is invalid, or fields are missing.
    """
    run_context = f"Run {run_id}: " if run_id else ""

    try:
        # Attempt to parse the raw JSON string
        parsed_data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        msg = f"{run_context}Failed to parse raw output as JSON: {e}"
        logger.error(msg)
        raise BaselineAdapterError(msg) from e

    if not isinstance(parsed_data, dict):
        msg = f"{run_context}Parsed output is not a dictionary: {type(parsed_data)}"
        logger.error(msg)
        raise BaselineAdapterError(msg)

    # Extract and validate 'action' field
    action = parsed_data.get("action")
    if action is None:
        msg = f"{run_context}Missing required field 'action' in baseline output"
        logger.error(msg)
        raise BaselineAdapterError(msg)

    if not isinstance(action, str):
        msg = f"{run_context}Field 'action' must be a string, got {type(action)}"
        logger.error(msg)
        raise BaselineAdapterError(msg)

    if action not in VALID_ACTIONS:
        msg = f"{run_context}Invalid action '{action}'. Must be one of {VALID_ACTIONS}"
        logger.error(msg)
        raise BaselineAdapterError(msg)

    # Extract and validate 'mental_map' field
    mental_map = parsed_data.get("mental_map")
    if mental_map is None:
        msg = f"{run_context}Missing required field 'mental_map' in baseline output"
        logger.error(msg)
        raise BaselineAdapterError(msg)

    if not isinstance(mental_map, str):
        msg = f"{run_context}Field 'mental_map' must be a string, got {type(mental_map)}"
        logger.error(msg)
        raise BaselineAdapterError(msg)

    # Validate that mental_map is itself valid JSON (as per schema)
    try:
        mental_map_obj = json.loads(mental_map)
        if not isinstance(mental_map_obj, dict):
            msg = f"{run_context}Field 'mental_map' content must be a JSON object, got {type(mental_map_obj)}"
            logger.error(msg)
            raise BaselineAdapterError(msg)
    except json.JSONDecodeError as e:
        msg = f"{run_context}Field 'mental_map' is not valid JSON: {e}"
        logger.error(msg)
        raise BaselineAdapterError(msg) from e

    # Construct the final structured output matching state_snapshot.schema.yaml
    # The schema requires: ascii_grid, event_log, ground_truth_state, masked_ground_truth
    # However, the adapter's primary role here is to normalize the *agent's* output
    # which consists of the action taken and the mental_map string.
    # The mental_map string itself is expected to contain the state representation
    # compatible with the masked ground truth format (e.g., containing ascii_grid, etc.)
    # We return the normalized dict.

    result = {
        "action": action,
        "mental_map": mental_map
    }

    logger.debug(f"{run_context}Successfully parsed baseline output: action={action}")
    return result


def validate_against_masked_ground_truth(
    adapter_output: Dict[str, Any],
    masked_ground_truth: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that the adapter's output matches the masked ground-truth format.

    This ensures the Baseline agent's mental map is structured consistently
    with the Text Agent's input format for fair comparison.

    Args:
        adapter_output: The parsed output from parse_baseline_output().
        masked_ground_truth: The reference masked ground truth state (from data/processed).

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []

    # Check required top-level keys in mental_map
    required_keys = {"ascii_grid", "event_log", "ground_truth_state", "masked_ground_truth"}
    mental_map_str = adapter_output.get("mental_map")
    if not mental_map_str:
        errors.append("Missing 'mental_map' in adapter output")
        return False, errors

    try:
        mental_map_obj = json.loads(mental_map_str)
    except json.JSONDecodeError:
        errors.append("'mental_map' is not valid JSON")
        return False, errors

    # Verify presence of required keys in the mental map object
    missing_keys = required_keys - set(mental_map_obj.keys())
    if missing_keys:
        errors.append(f"Mental map missing required keys: {missing_keys}")

    # Verify 'action' is present in the original adapter output
    if "action" not in adapter_output:
        errors.append("Missing 'action' in adapter output")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Validation failed: {errors}")
    else:
        logger.debug("Baseline output successfully validated against masked ground truth format.")

    return is_valid, errors


def process_baseline_run_file(
    input_path: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a baseline run file (JSON) and save the normalized output.

    Args:
        input_path: Path to the raw baseline output JSON file.
        output_path: Optional path to save the normalized JSON. If None, returns dict only.

    Returns:
        The normalized dictionary.
    """
    run_id = os.path.basename(input_path).replace(".json", "")

    with open(input_path, "r", encoding="utf-8") as f:
        raw_content = f.read().strip()

    try:
        normalized = parse_baseline_output(raw_content, run_id=run_id)
    except BaselineAdapterError as e:
        logger.error(f"Failed to process {input_path}: {e}")
        raise

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2)
        logger.info(f"Saved normalized output to {output_path}")

    return normalized


def main():
    """
    CLI entry point for testing the adapter on a specific file.
    Usage: python code/baseline_adapter.py --input <path> --output <path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Baseline Adapter CLI")
    parser.add_argument("--input", required=True, help="Path to raw baseline JSON output")
    parser.add_argument("--output", required=True, help="Path to save normalized JSON")
    args = parser.parse_args()

    try:
        process_baseline_run_file(args.input, args.output)
        print(f"Success: Normalized output saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
