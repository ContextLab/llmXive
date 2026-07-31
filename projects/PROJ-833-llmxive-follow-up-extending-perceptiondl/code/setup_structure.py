"""
Task T001: Create project structure per implementation plan.

This script creates the required directory hierarchy for the llmXive
follow-up project. It ensures all necessary folders exist and are
ready for subsequent code and data artifacts.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-833-llmxive-follow-up-extending-perceptiondl"
    
    # Ensure we are operating in the correct project root context
    if project_root.name != "projects":
        # Fallback if run from a different context, assume relative to script
        project_root = Path(__file__).resolve().parent.parent
    
    base_path = project_root / project_name
    
    # Define directory structure
    directories = [
        "code/synthetic",
        "code/models",
        "code/metrics",
        "code/analysis",
        "tests/unit",
        "tests/contract",
        "data/raw",
        "data/synthetic",
        "data/processed",
        "state",
    ]
    
    created_count = 0
    for d in directories:
        dir_path = base_path / d
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            # Verify creation by listing (basic check)
            if not dir_path.exists():
                raise RuntimeError(f"Failed to create {dir_path}")
            created_count += 1
            print(f"Created: {dir_path.relative_to(project_root)}")
        except Exception as e:
            print(f"Error creating {dir_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    print(f"\nSuccessfully created {created_count} directories under {project_root}/{project_name}")
    
    # Verify final structure
    print("\nVerifying structure...")
    for d in directories:
        if not (base_path / d).is_dir():
            print(f"ERROR: Missing directory {d}", file=sys.stderr)
            sys.exit(1)
    print("Verification complete: All directories exist.")

if __name__ == "__main__":
    main()
