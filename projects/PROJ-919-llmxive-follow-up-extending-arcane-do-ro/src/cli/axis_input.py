"""
CLI module for independent input validation of Character Axes.

This module implements the input validation logic for User Story 1 (US1).
It requires two separate text blocks for Coarse and Fine axes, prevents
copy-paste between fields, and validates that Fine axes originate from
independent narrative observations via manual researcher confirmation.
"""
import argparse
import json
import sys
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np
import re

# Import shared utilities
from src.lib.config import get_config
from src.lib.utils import get_logger
from src.lib.state_tracker import log_experiment_state, hash_parameters, generate_run_id

# Initialize logger
logger = get_logger(__name__)


def read_input(prompt: str, allow_empty: bool = False) -> str:
    """
    Read a single line of input from the user with a specific prompt.
    
    Args:
        prompt: The prompt text to display.
        allow_empty: If True, allow empty input.
        
    Returns:
        The user's input string.
        
    Raises:
        ValueError: If input is empty and allow_empty is False.
    """
    while True:
        try:
            user_input = input(prompt).strip()
            if user_input or allow_empty:
                return user_input
            print("Input cannot be empty. Please try again.")
        except EOFError:
            logger.error("EOF encountered during input.")
            sys.exit(1)


def get_hash(text: str) -> str:
    """Generate a SHA-256 hash of the input text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def validate_coarse_fine_independence(coarse: str, fine: str) -> Tuple[bool, str]:
    """
    Validate that Coarse and Fine axes are distinct.
    
    This performs a basic check to ensure the strings are not identical
    or trivially similar (e.g., one is a substring of the other).
    
    Args:
        coarse: The Coarse axis definition.
        fine: The Fine axis definition.
        
    Returns:
        A tuple (is_valid, message).
    """
    if not coarse or not fine:
        return False, "Both Coarse and Fine axes must be provided."
    
    if coarse == fine:
        return False, "Coarse and Fine axes cannot be identical."
    
    # Check for trivial substring inclusion (case-insensitive)
    c_lower = coarse.lower()
    f_lower = fine.lower()
    if c_lower in f_lower or f_lower in c_lower:
        return False, "Coarse and Fine axes appear to be trivially related (substring match)."
    
    return True, "Axes appear distinct."


def validate_fine_independence_from_source(fine: str) -> Tuple[bool, str]:
    """
    Validate that Fine axes originate from independent narrative observations.
    
    FR-001 Requirement: The validation MUST require the researcher to 
    manually confirm independence before proceeding. No automated threshold
    is used here; this function enforces the manual confirmation step.
    
    Args:
        fine: The Fine axis definition (used for logging/context).
        
    Returns:
        A tuple (is_valid, message).
    """
    logger.info("Requesting manual confirmation of independence for Fine axis.")
    print("\n" + "="*60)
    print("INDEPENDENCE CONFIRMATION REQUIRED")
    print("="*60)
    print("You have entered the following Fine Axis definition:")
    print(f"  '{fine}'")
    print("\nAccording to FR-001, Fine axes must originate from")
    print("independent narrative observations, not derived from")
    print("the Coarse axis definition.")
    print("-"*60)
    print("Please confirm: Did you derive this Fine axis definition")
    print("from a SEPARATE, INDEPENDENT observation of the character")
    print("(e.g., a different scene, a different trait analysis)?")
    print("-"*60)
    
    while True:
        response = input("Type 'YES' to confirm independence: ").strip().upper()
        if response == "YES":
            logger.info("Researcher confirmed independence of Fine axis.")
            return True, "Independence confirmed by researcher."
        elif response == "NO":
            print("Independence not confirmed. Please revise your input.")
            return False, "Independence not confirmed."
        else:
            print("Invalid response. Please type 'YES' to confirm.")


def prevent_copy_paste_coarse_fine(coarse_hash: str, fine_hash: str) -> bool:
    """
    Prevent copy-paste between fields by comparing hashes.
    
    If the hashes are identical, the user likely copied the same text
    into both fields.
    
    Args:
        coarse_hash: Hash of the Coarse input.
        fine_hash: Hash of the Fine input.
        
    Returns:
        True if distinct, False if identical.
    """
    return coarse_hash != fine_hash


def process_input(character_name: str) -> Optional[Dict[str, Any]]:
    """
    Main interaction loop to collect and validate axis inputs.
    
    Args:
        character_name: The name of the character being analyzed.
        
    Returns:
        A dictionary containing the validated axes and metadata, or None if validation fails.
    """
    print(f"\n--- Defining Axes for Character: {character_name} ---\n")
    
    # 1. Collect Coarse Axis
    print("Step 1: Define Coarse Axis")
    print("(High-level psychological dimensions, e.g., 'Extraversion vs Introversion')")
    coarse_input = read_input("Enter Coarse Axis definition: ")
    coarse_hash = get_hash(coarse_input)
    
    # 2. Collect Fine Axis
    print("\nStep 2: Define Fine Axis")
    print("(Specific, nuanced narrative observations, e.g., 'Nervous tic when lying')")
    fine_input = read_input("Enter Fine Axis definition: ")
    fine_hash = get_hash(fine_input)
    
    # 3. Validation: Prevent Copy-Paste
    if not prevent_copy_paste_coarse_fine(coarse_hash, fine_hash):
        logger.warning("Copy-paste detected: Coarse and Fine inputs are identical.")
        print("\nERROR: Coarse and Fine inputs are identical. Please provide distinct definitions.")
        return None
    
    # 4. Validation: Distinctness
    is_distinct, distinct_msg = validate_coarse_fine_independence(coarse_input, fine_input)
    if not is_distinct:
        logger.warning(f"Distinctness check failed: {distinct_msg}")
        print(f"\nERROR: {distinct_msg}")
        return None
    
    # 5. Validation: Manual Independence Confirmation (FR-001)
    is_independent, indep_msg = validate_fine_independence_from_source(fine_input)
    if not is_independent:
        logger.warning(f"Independence confirmation failed: {indep_msg}")
        print(f"\nERROR: {indep_msg}")
        return None
    
    # All validations passed
    logger.info("Axis input validation successful.")
    return {
        "character": character_name,
        "coarse": coarse_input,
        "fine": fine_input,
        "coarse_hash": coarse_hash,
        "fine_hash": fine_hash,
        "validated": True
    }


def main():
    """CLI entry point for axis input validation."""
    parser = argparse.ArgumentParser(
        description="Interactive CLI for defining and validating Character Axes (US1)."
    )
    parser.add_argument(
        "--character", 
        type=str, 
        default="TestCharacter",
        help="Name of the character to analyze."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/axes_input.json",
        help="Path to save the validated axis definitions."
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting axis input process for character: {args.character}")
    
    result = process_input(args.character)
    
    if result:
        # Log state
        run_id = generate_run_id()
        params_hash = hash_parameters({"character": args.character})
        log_experiment_state(
            run_id=run_id,
            task="axis_input",
            status="completed",
            parameters={"character": args.character},
            parameter_hash=params_hash
        )
        
        # Save result
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nSUCCESS: Validated axes saved to {output_path}")
        print(f"Run ID: {run_id}")
        return 0
    else:
        print("\nFAILED: Validation failed. No output generated.")
        return 1


if __name__ == "__main__":
    sys.exit(main())