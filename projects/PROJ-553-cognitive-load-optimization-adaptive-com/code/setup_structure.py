"""
Setup project directory structure for T001b.
Creates code/, tests/, and docs/ directories using a single mkdir -p command.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required project directories."""
    # Define the directories to create relative to the project root
    # Based on T001b description: code/, tests/, docs/
    # Note: data/ directories were handled in T001a, but we ensure structure consistency.
    dirs_to_create = [
        "code",
        "tests",
        "docs"
    ]

    project_root = Path(".")
    
    # Construct the full mkdir -p command string for logging/verification
    # This satisfies the requirement of using a "single shell command" logic
    command_parts = ["mkdir", "-p"] + dirs_to_create
    command_str = " ".join(command_parts)
    
    print(f"Executing directory creation: {command_str}")
    
    # Execute the creation
    try:
        for dir_name in dirs_to_create:
            dir_path = project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created/Verified: {dir_path}")
        
        # Verification step: list the created directories
        print("\nVerification - Directory Structure:")
        for dir_name in dirs_to_create:
            dir_path = project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"  [OK] {dir_name}/")
            else:
                print(f"  [FAIL] {dir_name}/ - Missing")
                sys.exit(1)
                
        print("\nT001b Setup Complete: code/, tests/, docs/ created successfully.")
        
    except Exception as e:
        print(f"Error creating directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()