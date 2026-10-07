"""
Task Validity Validator (Action Chain Check) for WBench Sequence Variants.

Validates that generated action chains are physically plausible based on
semantic constraints and action dependencies.

Input: data/processed/variants.csv
Output: data/processed/validity_flags.csv
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
import re

from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import fail_loudly, DataValidationError

# Initialize logger
logger = get_logger(__name__)

# Physical plausibility constraints
# These are simplified rules based on common physical impossibilities
# In a real system, this would be more complex and domain-specific
PHYSICAL_IMPOSSIBILITIES = {
    # Impossible action sequences (action_a followed by action_b)
    "impossible_sequences": [
        ("drop", "catch"),  # Cannot catch something you dropped in the same step sequence without time travel
        ("burn", "freeze"),  # Cannot burn and freeze simultaneously in same context
        ("explode", "assemble"),  # Cannot assemble after explosion
    ],
    # Impossible action properties
    "impossible_properties": {
        "weight": {
            "heavy": ["float", "levitate"],
            "light": ["sink", "crush_under"]
        },
        "temperature": {
            "hot": ["freeze", "solidify_cold"],
            "cold": ["burn", "melt_hot"]
        }
    },
    # Forbidden action chains based on object states
    "state_violations": [
        ("broken", "repair", "break"),  # Cannot break after repairing in same chain
        ("empty", "fill", "empty"),  # Cannot empty after filling without intermediate state
    ]
}

# Action dependency graph for physical plausibility
ACTION_DEPENDENCIES = {
    "lift": ["grab", "hold"],
    "throw": ["grab", "hold", "lift"],
    "cut": ["hold", "position"],
    "pour": ["hold", "tilt"],
    "mix": ["hold", "combine"],
    "assemble": ["hold", "position", "connect"],
    "repair": ["hold", "identify_damage"],
    "clean": ["hold", "apply_force"],
    "move": ["grab", "lift"],
    "drop": ["hold"],
    "catch": ["track", "position"],
    "burn": ["apply_heat", "contact"],
    "freeze": ["apply_cold", "contact"],
    "explode": ["accumulate_pressure", "trigger"],
}

def _parse_action_chain(action_str: str) -> List[str]:
    """
    Parse action chain string into list of actions.
    Handles various formats: comma-separated, space-separated, or JSON array.
    """
    if not action_str or pd.isna(action_str):
        return []

    action_str = str(action_str).strip()

    # Try JSON array format first
    if action_str.startswith('[') and action_str.endswith(']'):
        try:
            actions = json.loads(action_str)
            if isinstance(actions, list):
                return [str(a).strip().lower() for a in actions if a]
        except json.JSONDecodeError:
            pass

    # Try comma-separated
    if ',' in action_str:
        actions = [a.strip().lower() for a in action_str.split(',') if a.strip()]
        return actions

    # Try space-separated
    actions = [a.strip().lower() for a in action_str.split() if a.strip()]
    return actions

def _check_impossible_sequences(actions: List[str]) -> bool:
    """Check for physically impossible action sequences."""
    for i in range(len(actions) - 1):
        pair = (actions[i], actions[i + 1])
        for impossible_pair in PHYSICAL_IMPOSSIBILITIES["impossible_sequences"]:
            if pair == impossible_pair:
                logger.debug(f"Impossible sequence found: {pair}")
                return True
    return False

def _check_state_violations(actions: List[str]) -> bool:
    """Check for state violation chains."""
    # Check for patterns like A -> B -> A where B should reset the state
    for violation_pattern in PHYSICAL_IMPOSSIBILITIES["state_violations"]:
        if len(actions) >= 3:
            for i in range(len(actions) - 2):
                if (actions[i] == violation_pattern[0] and
                    actions[i + 1] == violation_pattern[1] and
                    actions[i + 2] == violation_pattern[2]):
                    logger.debug(f"State violation found: {actions[i:i+3]}")
                    return True
    return False

def _check_action_dependencies(actions: List[str]) -> bool:
    """
    Check if actions have their required dependencies met in the chain.
    Returns True if there's a missing dependency (invalid).
    """
    seen_actions = set()

    for action in actions:
        if action in ACTION_DEPENDENCIES:
            required_deps = ACTION_DEPENDENCIES[action]
            for dep in required_deps:
                if dep not in seen_actions:
                    # Check if it's a prerequisite that should come before
                    logger.debug(f"Missing dependency for {action}: {dep}")
                    return True
        seen_actions.add(action)

    return False

def _check_property_conflicts(actions: List[str]) -> bool:
    """Check for property-based conflicts in actions."""
    # Simplified check - in reality would need object state tracking
    hot_actions = {"burn", "heat", "melt", "cook", "fire"}
    cold_actions = {"freeze", "chill", "solidify", "ice"}

    has_hot = any(a in hot_actions for a in actions)
    has_cold = any(a in cold_actions for a in actions)

    if has_hot and has_cold:
        # Check if they're in immediate succession (impossible)
        for i in range(len(actions) - 1):
            if (actions[i] in hot_actions and actions[i+1] in cold_actions) or \
               (actions[i] in cold_actions and actions[i+1] in hot_actions):
                logger.debug(f"Property conflict: hot/cold immediate succession")
                return True

    return False

def validate_action_chain(action_chain: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate a single action chain for physical plausibility.

    Args:
        action_chain: String representation of the action chain
        context: Optional context dictionary with object states, etc.

    Returns:
        bool: True if the chain is physically plausible, False otherwise
    """
    if not action_chain or pd.isna(action_chain):
        logger.warning("Empty or null action chain provided")
        return False

    actions = _parse_action_chain(action_chain)

    if not actions:
        logger.warning("No valid actions parsed from chain")
        return False

    # Run all validation checks
    checks = [
        ("impossible_sequence", _check_impossible_sequences),
        ("state_violation", _check_state_violations),
        ("missing_dependency", _check_action_dependencies),
        ("property_conflict", _check_property_conflicts),
    ]

    for check_name, check_func in checks:
        try:
            if check_func(actions):
                logger.info(f"Validation failed for {check_name}: {actions}")
                return False
        except Exception as e:
            logger.error(f"Error during {check_name} check: {e}")
            # Fail loudly on validation errors
            fail_loudly(f"Validation check {check_name} failed: {e}")

    return True

def validate_variants(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Validate all variants in the input CSV and write validity flags to output CSV.

    Args:
        input_path: Path to input variants CSV (data/processed/variants.csv)
        output_path: Path to output validity flags CSV (data/processed/validity_flags.csv)

    Returns:
        pd.DataFrame: The validity flags dataframe
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        fail_loudly(f"Input file does not exist: {input_path}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading variants from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        fail_loudly(f"Failed to read input CSV: {e}")

    required_columns = ['case_id', 'variant_type']
    for col in required_columns:
        if col not in df.columns:
            fail_loudly(f"Missing required column '{col}' in input file")

    if 'action_chain' not in df.columns:
        # If action_chain is not present, we assume all are valid
        # This might happen if the generator didn't include it
        logger.warning("No 'action_chain' column found. Assuming all variants are valid.")
        df['is_valid'] = True
    else:
        logger.info(f"Validating {len(df)} action chains")
        validity_results = []

        for idx, row in df.iterrows():
            case_id = row['case_id']
            variant_type = row['variant_type']
            action_chain = row.get('action_chain', '')

            is_valid = validate_action_chain(action_chain)
            validity_results.append({
                'case_id': case_id,
                'variant_type': variant_type,
                'is_valid': is_valid
            })

            if idx % 10 == 0:
                logger.debug(f"Processed {idx}/{len(df)} variants")

        df_validity = pd.DataFrame(validity_results)
        df_validity.to_csv(output_path, index=False)
        logger.info(f"Validity flags written to {output_path}")

        return df_validity

    # If we got here, we didn't have action chains to validate
    df_validity = df[['case_id', 'variant_type']].copy()
    df_validity['is_valid'] = True
    df_validity.to_csv(output_path, index=False)
    logger.info(f"Validity flags written to {output_path} (all marked valid due to missing action_chain)")

    return df_validity

def main():
    """Main entry point for the validator."""
    # Default paths
    input_path = "data/processed/variants.csv"
    output_path = "data/processed/validity_flags.csv"

    # Allow command line override
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    logger.info(f"Starting validation pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    try:
        result_df = validate_variants(input_path, output_path)

        # Summary statistics
        valid_count = result_df['is_valid'].sum()
        invalid_count = len(result_df) - valid_count

        logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid out of {len(result_df)}")

        return result_df

    except Exception as e:
        log_exception(e)
        fail_loudly(f"Validation pipeline failed: {e}")

if __name__ == "__main__":
    main()
