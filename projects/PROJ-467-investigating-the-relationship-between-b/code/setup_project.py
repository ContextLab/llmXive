import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-467.
    Ensures all required directories exist under the project root.
    """
    # Determine project root (assuming this script is in code/, root is parent)
    # If run as module or script, we assume execution context is project root or code/
    # To be safe, we define paths relative to the script's location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define the required directory structure
    required_dirs = [
        "src/brainnet",
        "tests/unit",
        "tests/contract",
        "data/processed",
        "data/raw",
        "results/figures",
        "metadata",
        "contracts"
    ]

    created_count = 0
    existing_count = 0

    print(f"Initializing project structure at: {project_root}")

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"  Created: {full_path}")
        else:
            existing_count += 1
            print(f"  Exists:  {full_path}")

    print(f"Project structure ready. Created {created_count} new directories.")
    print(f"Verification: Listing 'src/brainnet' contents...")
    
    brainnet_path = project_root / "src" / "brainnet"
    if brainnet_path.exists():
        # Ensure the package is importable by creating an __init__.py if missing
        init_file = brainnet_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"  Created: {init_file} (empty)")
        
        # List contents
        contents = list(brainnet_path.iterdir())
        if not contents:
            print("  (Directory is empty)")
        else:
            for item in contents:
                print(f"  - {item.name}")
    else:
        print("  ERROR: src/brainnet directory not found after creation!")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
