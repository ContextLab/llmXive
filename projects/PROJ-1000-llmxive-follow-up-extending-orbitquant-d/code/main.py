import argparse
import os
from pathlib import Path
from llmxive_toolkit import paths

def initialize_skeleton():
    """
    Creates the required project directory structure.
    """
    # Required sub-directories under code/
    subdirs = [
        "analysis",
        "models",
        "quantization",
        "evaluation",
        "utils",
        "runners",
        "data",
        "validation"
    ]
    
    code_root = paths.code("")
    
    for sd in subdirs:
        dir_path = code_root / sd
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py to make it a package
        (dir_path / "__init__.py").touch()
    
    # Create tests directory
    tests_dir = paths.root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").touch()
    
    print("Initialization complete")

def main():
    parser = argparse.ArgumentParser(description="Project Orchestrator")
    parser.add_argument("--phase", type=str, required=True, help="Phase to execute")
    args = parser.parse_args()
    
    if args.phase == "init":
        initialize_skeleton()
    else:
        print(f"Unknown phase: {args.phase}")
        exit(1)

if __name__ == "__main__":
    main()
