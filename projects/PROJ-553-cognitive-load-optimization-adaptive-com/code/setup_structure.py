"""
Project Structure Setup Script

This script creates the necessary directory structure for the
Cognitive Load Optimization project.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    root = Path(__file__).parent.parent
    
    directories = [
        "data/raw",
        "data/processed",
        "data/explanation_tiers",
        "data/simulation_results",
        "code",
        "tests",
        "docs"
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(root)))
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")
    
    return 0

if __name__ == "__main__":
    exit(main())
