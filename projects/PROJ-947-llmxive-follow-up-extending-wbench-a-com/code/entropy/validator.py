import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Set

from utils.logging import get_logger, log_info, log_error, fail_loudly
from utils.errors import DataValidationError

logger = get_logger(__name__)

# Pre-defined set of physically plausible actions based on WBench ontology.
# This serves as the reference for the "Action Chain Check".
# In a real-world scenario, this might be loaded from a spec file or ontology.
VALID_ACTION_SET: Set[str] = {
    "move", "grab", "release", "place", "push", "pull",
    "lift", "lower", "rotate", "tilt", "open", "close",
    "stack", "unstack", "pour", "scoop", "cut", "join",
    "wait", "idle", "navigate", "approach", "retreat"
}

# Invalid or physically impossible action sequences (examples)
# Used to detect obvious logical breaks if we were doing sequence logic.
# For this task, we focus on: 1. Valid action tokens, 2. Non-empty chains.
INVALID_PATTERNS = [
    "grab release",  # Grabbing without moving usually invalid in sequence context unless immediate
    "move move move", # Redundant moves might be valid but we check for semantic breaks
]

def validate_action_chain(chain: str, case_id: str) -> Dict[str, Any]:
    """
    Validates a single action chain string for physical plausibility.

    Algorithm:
    1. Split chain into individual actions (assuming space-separated or comma-separated).
    2. Check if every action exists in the VALID_ACTION_SET.
    3. Check if the chain is non-empty.
    4. (Optional) Check for obvious invalid patterns (e.g., "release" before "grab").

    Args:
        chain: The action chain string (e.g., "move grab place release").
        case_id: Identifier for the case being validated (for logging).

    Returns:
        Dict with keys:
            - is_valid (bool): True if chain passes all checks.
            - error_reason (str or None): Explanation if invalid.
    """
    if not chain or not isinstance(chain, str):
        return {"is_valid": False, "error_reason": "Chain is empty or not a string"}

    # Normalize: split by space or comma
    tokens = [t.strip() for t in chain.replace(",", " ").split() if t.strip()]

    if not tokens:
        return {"is_valid": False, "error_reason": "No valid tokens found in chain"}

    invalid_tokens = []
    for token in tokens:
        if token not in VALID_ACTION_SET:
            invalid_tokens.append(token)

    if invalid_tokens:
        return {
            "is_valid": False,
            "error_reason": f"Invalid action tokens found: {invalid_tokens}"
        }

    # Basic sequence logic check: "release" cannot happen before "grab"
    # unless there was a "move" to an object first? Simplified:
    # We enforce that 'release' must be preceded by 'grab' or 'lift' or 'place'
    # within the chain context.
    # For strict physical plausibility:
    # - 'release' requires a prior 'grab' or 'lift' that hasn't been released.
    # - 'place' requires 'grab' or 'lift'.

    has_grabbed = False
    for i, token in enumerate(tokens):
        if token in ["grab", "lift", "scoop"]:
            has_grabbed = True
        elif token == "release":
            if not has_grabbed:
                return {
                    "is_valid": False,
                    "error_reason": f"Action 'release' at index {i} without prior grab/lift"
                }
            has_grabbed = False # Released, so no longer holding
        elif token == "place":
            if not has_grabbed:
                return {
                    "is_valid": False,
                    "error_reason": f"Action 'place' at index {i} without prior grab/lift"
                }
            has_grabbed = False

    return {"is_valid": True, "error_reason": None}

def validate_variants(input_path: str, output_path: str) -> None:
    """
    Reads variants.csv, validates each action chain, and writes validity_flags.csv.

    Input CSV Expected Columns:
        - case_id: Unique identifier
        - variant_type: Low, Medium, High
        - generated_chain: The action chain string (mapped from task description's 'action_chain' concept)

    Output CSV Columns:
        - case_id
        - variant_type
        - is_valid (boolean)

    Args:
        input_path: Path to data/processed/variants.csv
        output_path: Path to data/processed/validity_flags.csv
    """
    logger.info(f"Starting validation for {input_path}")

    if not os.path.exists(input_path):
        fail_loudly(f"Input file not found: {input_path}. Run generation pipeline first.")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        fail_loudly(f"Failed to read CSV: {e}")

    # Identify the column containing the action chain.
    # Task T013 output 'variants.csv' has 'generated_chain'.
    # Task T014 description mentions 'action_chain' column.
    # We check for 'generated_chain' first, then 'action_chain'.
    chain_col = None
    if 'generated_chain' in df.columns:
        chain_col = 'generated_chain'
    elif 'action_chain' in df.columns:
        chain_col = 'action_chain'
    else:
        fail_loudly(
            f"Input CSV missing required chain column. "
            f"Expected 'generated_chain' or 'action_chain'. "
            f"Found columns: {list(df.columns)}"
        )

    logger.info(f"Using chain column: {chain_col}")

    results = []
    failed_count = 0

    for _, row in df.iterrows():
        case_id = row['case_id']
        variant_type = row['variant_type']
        chain_str = str(row[chain_col])

        validation_result = validate_action_chain(chain_str, case_id)
        is_valid = validation_result['is_valid']

        if not is_valid:
            failed_count += 1
            log_error(f"Validation failed for {case_id} ({variant_type}): {validation_result['error_reason']}")

        results.append({
            "case_id": case_id,
            "variant_type": variant_type,
            "is_valid": is_valid
        })

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    output_df.to_csv(output_path, index=False)
    logger.info(f"Validation complete. Wrote {len(output_df)} rows to {output_path}")
    logger.info(f"Total valid: {output_df['is_valid'].sum()}, Invalid: {failed_count}")

def main():
    """Main entry point for the validator script."""
    # Default paths relative to project root
    # We assume running from project root or setting CWD correctly
    base_dir = Path(__file__).resolve().parent.parent
    input_file = base_dir / "data" / "processed" / "variants.csv"
    output_file = base_dir / "data" / "processed" / "validity_flags.csv"

    # Allow override via command line args
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    validate_variants(str(input_file), str(output_file))

if __name__ == "__main__":
    main()
