"""
CLI entry point for initializing character axes.

This module provides the command-line interface to initialize axes for a given character
by orchestrating the input validation, axis generation, and serialization steps.

Usage:
    python -m src.cli.run_experiment --character "Hamlet"
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import from project modules
from src.cli.axis_input import read_input, validate_coarse_fine_independence, validate_fine_independence_from_source
from src.services.axis_generator import generate_axes_from_input, validate_axes_semantic_overlap, serialize_axes_to_jsonl
from src.lib.utils import setup_logging, log_experiment_state
from src.lib.config import load_config

# Configure logging
logger = logging.getLogger(__name__)

def display_axis_output(coarse: Dict[str, Any], fine: Dict[str, Any]) -> None:
    """
    Display the generated Coarse and Fine axis objects to the console.
    
    Args:
        coarse: The validated Coarse axis definition
        fine: The validated Fine axis definition
    """
    print("\n" + "="*60)
    print("GENERATED CHARACTER AXES")
    print("="*60)
    
    print("\n[COARSE AXIS]")
    print(json.dumps(coarse, indent=2))
    
    print("\n[FINE AXIS]")
    print(json.dumps(fine, indent=2))
    
    print("\n" + "="*60)
    
def initialize_axes(character_name: str, 
                    coarse_input: Optional[str] = None,
                    fine_input: Optional[str] = None,
                    source_text: Optional[str] = None,
                    output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize axes for a given character.
    
    This function orchestrates the full axis initialization pipeline:
    1. Read/validate input (or use provided inputs)
    2. Generate axes from input
    3. Validate semantic overlap constraints
    4. Serialize to JSONL file
    5. Display output
    
    Args:
        character_name: Name of the character to initialize axes for
        coarse_input: Optional pre-provided coarse axis text
        fine_input: Optional pre-provided fine axis text
        source_text: Optional source text segment for independence validation
        output_path: Optional custom output path (defaults to config)
        
    Returns:
        Dictionary containing the generated axes and metadata
    """
    config = load_config()
    output_file = Path(output_path) if output_path else Path(config["paths"]["derived"]) / "axes.jsonl"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Get and validate inputs
    logger.info(f"Starting axis initialization for character: {character_name}")
    
    if coarse_input is None or fine_input is None:
        # Interactive input mode
        coarse_input, fine_input, source_text = read_input(character_name)
    
    # Validate independence
    logger.debug("Validating coarse/fine independence...")
    is_coarse_fine_valid = validate_coarse_fine_independence(coarse_input, fine_input)
    if not is_coarse_fine_valid:
        raise ValueError("Coarse and Fine axes failed independence validation")
    
    if source_text:
        logger.debug("Validating Fine axis independence from source text...")
        is_fine_source_valid = validate_fine_independence_from_source(fine_input, source_text)
        if not is_fine_source_valid:
            raise ValueError("Fine axis failed independence validation against source text")
    
    # Step 2: Generate axes
    logger.info("Generating axes from input...")
    axes_data = generate_axes_from_input(
        character_name=character_name,
        coarse_text=coarse_input,
        fine_text=fine_input,
        source_text=source_text
    )
    
    # Step 3: Validate semantic overlap
    logger.info("Validating semantic overlap constraints...")
    is_semantic_valid = validate_axes_semantic_overlap(
        axes_data["coarse"], 
        axes_data["fine"]
    )
    
    if not is_semantic_valid:
        # Log warning but proceed - the axes are generated but may need manual review
        logger.warning("Axes failed semantic overlap constraints. Manual review recommended.")
    
    # Step 4: Serialize to JSONL
    logger.info(f"Writing axes to {output_file}")
    serialize_axes_to_jsonl(axes_data, output_file)
    
    # Step 5: Display output
    display_axis_output(axes_data["coarse"], axes_data["fine"])
    
    # Step 6: Log experiment state
    log_experiment_state(
        experiment_type="axis_initialization",
        character=character_name,
        parameters={
            "coarse_length": len(coarse_input),
            "fine_length": len(fine_input),
            "source_length": len(source_text) if source_text else 0,
            "semantic_valid": is_semantic_valid
        }
    )
    
    logger.info(f"Axis initialization complete for {character_name}")
    
    return axes_data

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize character axes for ArcANE analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          # Interactive mode
          python -m src.cli.run_experiment --character "Hamlet"
          
          # Non-interactive mode with inputs
          python -m src.cli.run_experiment --character "Macbeth" \\
            --coarse "Ambition and power dynamics" \\
            --fine "Obsessive guilt manifested through hallucinations" \\
            --source "The text segment from Act 2, Scene 2..."
        """
    )
    
    parser.add_argument(
        "--character", 
        type=str, 
        required=True,
        help="Name of the character to initialize axes for"
    )
    
    parser.add_argument(
        "--coarse",
        type=str,
        default=None,
        help="Coarse axis definition text (optional, interactive if not provided)"
    )
    
    parser.add_argument(
        "--fine",
        type=str,
        default=None,
        help="Fine axis definition text (optional, interactive if not provided)"
    )
    
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Source text segment for independence validation (optional)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path for axes.jsonl (optional)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        setup_logging(level="DEBUG")
    else:
        setup_logging(level="INFO")
    
    try:
        result = initialize_axes(
            character_name=args.character,
            coarse_input=args.coarse,
            fine_input=args.fine,
            source_text=args.source,
            output_path=args.output
        )
        
        # Exit with success
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Axis initialization failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()