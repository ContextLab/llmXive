import os
from pathlib import Path
from llmxive_toolkit import paths

def main():
    """
    Creates the required directory layout for the project and writes
    a plain-text manifest of the structure.
    """
    # The nine required directories as specified in T001
    required_dirs = [
        "code",
        "code/simulation",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/processed/plots",
    ]

    # Create directories
    for d in required_dirs:
        # Use pathlib for robust directory creation
        Path(d).mkdir(parents=True, exist_ok=True)

    # Write the manifest file to data/dir_structure.txt
    # paths.data creates the 'data' folder if it doesn't exist
    manifest_path = paths.data("dir_structure.txt")
    with open(manifest_path, "w") as f:
        f.write("\n".join(required_dirs) + "\n")

if __name__ == "__main__":
    main()
