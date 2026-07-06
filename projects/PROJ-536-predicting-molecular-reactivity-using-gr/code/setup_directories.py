import os
import sys

def create_directories():
    """
    Creates the project directory structure for the Molecular Reactivity prediction pipeline.
    Executes the equivalent of:
    mkdir -p src/data src/models src/analysis src/config src/utils tests/contract tests/integration tests/unit
    """
    # Define the root directory (assuming the script is run from the project root)
    # The task description implies creating these relative to the project root.
    # We will create them in the current working directory.
    
    base_dirs = [
        "src/data",
        "src/models",
        "src/analysis",
        "src/config",
        "src/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]

    created = []
    skipped = []

    for dir_path in base_dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                created.append(dir_path)
            else:
                skipped.append(dir_path)
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)

    print(f"Directories created: {len(created)}")
    for d in created:
        print(f"  - {d}")
    
    if skipped:
        print(f"Directories already existing: {len(skipped)}")
        for d in skipped:
            print(f"  - {d}")

    return created + skipped

if __name__ == "__main__":
    create_directories()