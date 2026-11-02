"""
Setup Project Structure Script
--------------------------------
This script creates the required directory layout for the project as
specified in task T001a. It also ensures that the contracts directory
under the specification folder exists.

The script is idempotent – running it multiple times will not raise
errors and will leave the directory tree in the correct state.
"""

import sys
from pathlib import Path

# Import the toolkit path helpers
from llmxive_toolkit import paths, get_logger

# Initialise logger (optional but useful for debugging)
log = get_logger(__name__)

def create_directories():
    """Create all required directories."""
    # Core project directories
    dirs = [
        paths.code(),                     # code/
        paths.data("raw"),                # data/raw/
        paths.data("curated"),            # data/curated/
        paths.data("results"),            # data/results/
        paths.tests("unit"),              # tests/unit/
        paths.tests("integration"),       # tests/integration/
        paths.tests("contract"),          # tests/contract/
    ]

    # Specification contracts directory
    specs_contracts_dir = Path(__file__).resolve().parents[2] / "specs" / "001-llmxive-follow-up-extending-swe-explore" / "contracts"
    dirs.append(specs_contracts_dir)

    for d in dirs:
        if not d.exists():
            log.info(f"Creating directory: {d}")
            d.mkdir(parents=True, exist_ok=True)
        else:
            log.debug(f"Directory already exists: {d}")

if __name__ == "__main__":
    try:
        create_directories()
        print("Project structure created and verified.")
    except Exception as e:
        log.error(f"Failed to create project structure: {e}")
        sys.exit(1)
