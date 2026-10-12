"""
Script to create the required data sub‑directories for the project.
This implements task T001a2: create `data/` with sub‑folders
`raw`, `synthetic`, `processed`, and `validation`.
It uses the llmxive_toolkit path helpers which ensure the directories
are created under the project root.
"""
import sys
from pathlib import Path

# Import the toolkit helpers
try:
    from llmxive_toolkit import paths
except ImportError as e:
    sys.stderr.write(f"Failed to import llmxive_toolkit: {e}\\n")
    sys.exit(1)

def create_subdirs():
    """
    Create the required data sub‑directories.
    The `paths.data` helper creates the folder if it does not exist.
    """
    # Base data directory (ensured by the helper)
    base = paths.data()
    # Sub‑directories
    subdirs = ["raw", "synthetic", "processed", "validation"]
    for sub in subdirs:
        # This creates the sub‑directory inside the base `data/` folder.
        paths.data(sub)

    # Simple verification output
    print("Created data sub‑directories:")
    for sub in subdirs:
        print(f" - {Path(base, sub)}")

if __name__ == "__main__":
    create_subdirs()
    # Exit with success code
    sys.exit(0)