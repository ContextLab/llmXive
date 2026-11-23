import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Import existing services and utilities from the project API surface
from src.lib.utils import get_logger
from src.lib.config import get_config
from src.lib.state_tracker import log_experiment_state, generate_run_id, hash_parameters
from src.cli.axis_input import read_input, process_input, verify_manual_independence_confirmation
from src.services.axis_generator import generate_axes_from_input, validate_axes_semantic_overlap
from src.services.axes_writer import write_axes_to_jsonl, ensure_derived_directory

logger = get_logger(__name__)

def display_axis_output(coarse: Dict[str, Any], fine: Dict[str, Any]) -> None:
    """
    Display the generated Coarse and Fine axis objects to the console.
    This satisfies the US-1 requirement to print two distinct JSON objects.
    """
    print("\n" + "="*60)
    print("GENERATED AXIS DEFINITIONS")
    print("="*60)
    
    print("\n[COARSE AXIS]")
    print(json.dumps(coarse, indent=2))
    
    print("\n[FINE AXIS]")
    print(json.dumps(fine, indent=2))
    
    print("\n" + "="*60 + "\n")

def initialize_axes_for_character(character_name: str, config: Dict[str, Any]) -> bool:
    """
    Initialize axes for a given character name.
    
    This function orchestrates the full US1 workflow:
    1. Reads input (simulating manual researcher input for CLI context)
    2. Validates independence
    3. Generates axes
    4. Validates semantic overlap
    5. Writes to data/derived/axes.jsonl
    6. Displays output
    
    Returns True if successful, False otherwise.
    """
    logger.info(f"Initializing axes for character: {character_name}")
    
    # Generate a run ID for this specific initialization
    run_id = generate_run_id()
    logger.info(f"Run ID: {run_id}")
    
    # Log experiment state start
    state_params = {
        "character": character_name,
        "task": "initialize_axes",
        "config_hash": hash_parameters(config)
    }
    log_experiment_state(run_id, "started", state_params)
    
    try:
        # Step 1: Read input (in a real CLI, this would be interactive)
        # For the CLI entry point, we expect the user to have provided input via args or stdin
        # We'll use the axis_input module's read_input function
        logger.info("Reading axis input...")
        coarse_input, fine_input = read_input(character_name)
        
        if not coarse_input or not fine_input:
            logger.error("Failed to read axis input.")
            log_experiment_state(run_id, "failed", {"error": "No input provided"})
            return False
        
        # Step 2: Verify manual independence confirmation
        logger.info("Verifying manual independence confirmation...")
        if not verify_manual_independence_confirmation():
            logger.error("Manual independence confirmation not provided.")
            log_experiment_state(run_id, "failed", {"error": "Independence not confirmed"})
            return False
        
        # Step 3: Process input into structured format
        logger.info("Processing input...")
        processed_coarse, processed_fine = process_input(coarse_input, fine_input)
        
        # Step 4: Generate axes
        logger.info("Generating axes from input...")
        coarse_axis, fine_axis = generate_axes_from_input(processed_coarse, processed_fine)
        
        # Step 5: Validate semantic overlap
        logger.info("Validating semantic overlap...")
        is_valid, overlap_score, distance_score = validate_axes_semantic_overlap(
            coarse_axis, fine_axis
        )
        
        if not is_valid:
            logger.warning(f"Semiatic validation failed: overlap={overlap_score}, distance={distance_score}")
            log_experiment_state(run_id, "failed", {
                "error": "Semantic validation failed",
                "overlap": overlap_score,
                "distance": distance_score
            })
            return False
        
        # Step 6: Ensure output directory exists
        ensure_derived_directory()
        
        # Step 7: Write axes to JSONL
        logger.info("Writing axes to data/derived/axes.jsonl...")
        axes_record = {
            "character": character_name,
            "run_id": run_id,
            "coarse": coarse_axis,
            "fine": fine_axis,
            "validation": {
                "overlap_score": overlap_score,
                "distance_score": distance_score,
                "is_valid": is_valid
            }
        }
        
        write_axes_to_jsonl(axes_record)
        
        # Step 8: Display output
        display_axis_output(coarse_axis, fine_axis)
        
        # Log success
        log_experiment_state(run_id, "completed", {
            "character": character_name,
            "overlap_score": overlap_score,
            "distance_score": distance_score
        })
        
        logger.info(f"Successfully initialized axes for {character_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing axes: {e}", exc_info=True)
        log_experiment_state(run_id, "failed", {"error": str(e)})
        return False

def main() -> int:
    """
    CLI entry point to initialize axes for a given character.
    
    Usage:
        python -m src.cli.run_experiment --character "Sherlock Holmes"
    
    Returns:
        0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Initialize Coarse and Fine psychological axes for a character."
    )
    parser.add_argument(
        "--character", "-c",
        type=str,
        required=True,
        help="Name of the character to initialize axes for."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to optional configuration file."
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    if args.config:
        try:
            with open(args.config, 'r') as f:
                custom_config = json.load(f)
                config.update(custom_config)
        except Exception as e:
            logger.warning(f"Failed to load custom config: {e}")
    
    success = initialize_axes_for_character(args.character, config)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())