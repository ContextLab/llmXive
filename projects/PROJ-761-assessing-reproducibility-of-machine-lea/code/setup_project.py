import os
import sys

def main() -> None:
    """Create the required project directory structure."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define required directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/logs",
        "artifacts/plots",
        "artifacts/reports",
        "contracts"
    ]
    
    print(f"Creating project structure in: {project_root}")
    
    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"  Created: {dir_path}")
            created_count += 1
        else:
            print(f"  Exists: {dir_path}")
    
    print(f"\nProject setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
