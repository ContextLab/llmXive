"""
Directory structure setup for the llmXive project.
Creates the required directory hierarchy as specified in T001.
"""
import os
import sys
from typing import List

def create_project_structure(root_dir: str = ".") -> None:
    """
    Creates the required directory structure for the project.
    
    Required directories:
    - data/raw
    - data/results
    - code
    - tests/unit
    - tests/contract
    - contracts
    - projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/
    
    Args:
        root_dir: The root directory where the structure will be created.
                 Defaults to current working directory.
    """
    # Define the required directory paths relative to root
    required_dirs: List[str] = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts",
        "projects/PROJ-975-llmxive-follow-up-extending-from-chatbot",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in required_dirs:
        full_path = os.path.join(root_dir, dir_path)
        
        if os.path.exists(full_path):
            skipped_count += 1
            print(f"Skipped (exists): {full_path}")
        else:
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
    
    print(f"\nDirectory setup complete.")
    print(f"  Created: {created_count}")
    print(f"  Skipped (already existed): {skipped_count}")
    print(f"  Total required: {len(required_dirs)}")

def main() -> None:
    """Main entry point for directory setup."""
    print("Initializing llmXive project directory structure...")
    create_project_structure()
    print("Done.")

if __name__ == "__main__":
    main()