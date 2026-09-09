import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-285.
    This script ensures all required directories exist relative to the project root.
    """
    # Define the base directory for this project
    base_dir = Path("projects/PROJ-285-assessing-the-impact-of-data-filtering-o")
    
    # Define the required directory tree
    required_dirs = [
        "code",
        "code/src",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    print(f"Creating project structure at: {base_dir.absolute()}")
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    
    # Verify the structure by printing the tree
    print("\n--- Project Structure Verification ---")
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(str(base_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{sub_indent}{file}')
        for d in dirs:
             # Just listing directories to keep output clean, though os.walk handles them
             pass

if __name__ == "__main__":
    main()
