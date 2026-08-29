"""
Main CLI entry point for running experiments.

Includes display_axis_output function for User Story 1 to print
the two distinct JSON objects (Coarse and Fine axes) to the console.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Import from local project structure
from src.lib.config import get_config
from src.lib.utils import get_logger
from src.services.axis_generator import main as axis_generator_main

logger = get_logger(__name__)

def display_axis_output(coarse: Dict[str, Any], fine: Dict[str, Any]):
    """
    Print the two distinct JSON objects (Coarse and Fine axes) to the console.
    
    Args:
        coarse: Coarse axis dictionary
        fine: Fine axis dictionary
    """
    print("\n" + "="*60)
    print("AXIS OUTPUT (User Story 1)")
    print("="*60)
    
    print("\n--- COARSE AXIS ---")
    print(json.dumps(coarse, indent=2))
    
    print("\n--- FINE AXIS ---")
    print(json.dumps(fine, indent=2))
    
    print("="*60 + "\n")

def run_axis_generation():
    """
    Wrapper to run axis generation and display output.
    """
    # Call the axis generator main which handles input parsing
    # We capture the result and display it
    import subprocess
    import sys
    
    # Re-run the axis generator module to get the output
    # In a real scenario, we would refactor to import the function directly
    # but for CLI consistency we call the main
    ret = axis_generator_main()
    
    if ret == 0:
        # If successful, we assume the user already saw the output
        # from axis_generator.py's print statements
        return 0
    else:
        return ret

def main():
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description="llmXive Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Axis Generation Command
    axis_parser = subparsers.add_parser(
        "generate-axes",
        help="Generate Coarse and Fine axes for a character"
    )
    axis_parser.add_argument("--config", type=str, help="Config file path (CI/CD)")
    axis_parser.add_argument("--character", type=str, help="Character name")
    axis_parser.add_argument("--coarse", type=str, help="Coarse axis text")
    axis_parser.add_argument("--fine", type=str, help="Fine axis text")
    axis_parser.add_argument("--output", type=str, help="Output JSONL path")
    
    args = parser.parse_args()
    
    if args.command == "generate-axes":
        # Delegate to axis_generator module
        sys.argv = [
            "run_experiment.py",
            "--config" if args.config else "",
            args.config if args.config else "",
            "--character" if args.character else "",
            args.character if args.character else "",
            "--coarse" if args.coarse else "",
            args.coarse if args.coarse else "",
            "--fine" if args.fine else "",
            args.fine if args.fine else "",
            "--output" if args.output else "",
            args.output if args.output else ""
        ]
        # Filter empty strings
        sys.argv = [arg for arg in sys.argv if arg]
        
        # Import and run the specific function
        from src.services.axis_generator import main as gen_main
        return gen_main()
    
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
