"""
Setup script to create the required directory structure for the OPID project.
This script ensures all necessary folders exist before running experiments.
"""
import os
import sys
from typing import List

def create_directories() -> List[str]:
    """
    Create the required directory structure for the project.
    
    Returns:
        List[str]: List of paths that were created or verified.
    """
    # Define the required directories relative to the project root
    # The project root is assumed to be the parent of the 'code' directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        "src",
        "src/environment",
        "src/agent",
        "src/simulation",
        "src/analysis",
        "tests",
        "data/raw/synthetic_graphs",
        "data/processed"
    ]
    
    created_or_verified = []
    
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            created_or_verified.append(f"Created: {full_path}")
        else:
            created_or_verified.append(f"Verified: {full_path}")
    
    return created_or_verified

def main():
    """Main entry point for the directory setup script."""
    print("Setting up project directory structure...")
    results = create_directories()
    
    print("\nDirectory Setup Results:")
    print("-" * 40)
    for result in results:
        print(result)
    print("-" * 40)
    print(f"Total directories processed: {len(results)}")
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
