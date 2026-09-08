"""
Main orchestration entry point for the llmXive pipeline.

This script initializes the project structure and can be extended
to run the full benchmark generation and evaluation pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Entry point for the llmXive pipeline.
    Currently performs a sanity check on the directory structure.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    required_subdirs = [
        "data_generation",
        "agents",
        "retrieval",
        "evaluation",
        "utils"
    ]
    
    print(f"Project Root: {project_root}")
    print(f"Code Directory: {code_dir}")
    
    for subdir in required_subdirs:
        target_path = code_dir / subdir
        if target_path.exists():
            print(f"✓ Found: {target_path}")
        else:
            print(f"✗ Missing: {target_path}")
            return 1
    
    print("\nProject structure verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
