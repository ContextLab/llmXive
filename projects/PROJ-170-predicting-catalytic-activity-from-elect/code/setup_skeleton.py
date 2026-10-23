"""
Skeleton Setup Script
---------------------

This script creates the required directory hierarchy for the project and
places a tiny ``README.txt`` file in each of the key data directories to
confirm their creation. The directories are created using the
``llmxive_toolkit.paths`` helpers which guarantee that they are placed
inside the project root and that the parent folders are created as needed.

Required directories:
  - data/raw/
  - data/processed/
  - outputs/
  - code/
  - code/utils/
  - code/models/
  - tests/contract/
  - tests/integration/
  - tests/unit/

Verification (used by the integration test suite):
  * All directories exist.
  * ``README.txt`` exists inside ``data/raw``, ``data/processed`` and
    ``outputs`` and contains a short confirmation message.
"""

from llmxive_toolkit import paths
import os

def _write_readme(dir_path):
    """Write a tiny README.txt confirming directory creation."""
    readme_path = dir_path / "README.txt"
    # Use a deterministic short message; the content is not important for
    # downstream analysis but satisfies the verification step.
    readme_path.write_text("This directory was created by setup_skeleton.\n")
    print(f"Created README at {readme_path}")

def main():
    """
    Create the required directory structure and README files.
    """
    # Define the directories to be created.
    required_dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.path("outputs"),
        paths.code(),
        paths.code("utils"),
        paths.code("models"),
        paths.path("tests/contract"),
        paths.path("tests/integration"),
        paths.path("tests/unit"),
    ]

    # Create directories and confirm creation.
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Verified directory: {d}")

    # Write README files in the three top-level data directories.
    _write_readme(paths.data("raw"))
    _write_readme(paths.data("processed"))
    _write_readme(paths.path("outputs"))

    # No return value needed; exit code 0 indicates success.

if __name__ == "__main__":
    main()