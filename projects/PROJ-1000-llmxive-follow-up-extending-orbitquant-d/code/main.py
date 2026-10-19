import argparse
import os
from pathlib import Path
from llmxive_toolkit import paths

def initialize_skeleton():
    """
    Creates the required project directory structure.
    """
    # Code directories
    code_dirs = [
        "analysis", "models", "quantization", "evaluation", 
        "utils", "data", "runners", "validation", "security"
    ]
    for d in code_dirs:
        dir_path = paths.code(d)
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py to make them packages
        (dir_path / "__init__.py").touch()

    # Tests directory
    paths.path("tests").mkdir(parents=True, exist_ok=True)

    # Data and Figures directories
    data_dirs = [
        "raw", 
        "processed/logs", 
        "processed/activation_stats", 
        "processed/rotation_matrices", 
        "processed/generated_images"
    ]
    for d in data_dirs:
        paths.data(d).mkdir(parents=True, exist_ok=True)
    
    paths.figures("").mkdir(parents=True, exist_ok=True)

    print("Initialization complete")

def main():
    parser = argparse.ArgumentParser(description="Project Orchestrator")
    parser.add_argument("--phase", type=str, required=True, help="Phase to execute")
    
    # Use parse_known_args to avoid crashes if the runner passes shell-piped strings as args
    args, _ = parser.parse_known_args()

    if args.phase == "init":
        initialize_skeleton()
    else:
        print(f"Phase {args.phase} not implemented in main.py")

if __name__ == "__main__":
    main()
