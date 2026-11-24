"""
Create the required project directory hierarchy and placeholder README files.

This script is idempotent – it will not overwrite an existing README.
After execution, the following directories (and any intermediate parents)
will exist:

- src
- src/environment
- src/agent
- src/simulation
- src/analysis
- src/utils
- tests
- data/raw/synthetic_graphs
- data/processed

A minimal ``README.md`` placeholder is written into each new directory.
The script then runs ``tree -L 2`` and captures its output to
``data/processed/dir_structure.txt`` for verification (Task T001a).
"""

import os
import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: ensure a directory exists and contains a placeholder README
# ----------------------------------------------------------------------
def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    readme = path / "README.md"
    if not readme.exists():
        readme.write_text(f"# {path.name}\n\nPlaceholder README for the {path} directory.\n")
    logger.debug("Ensured %s exists with README", path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    # List of required top‑level directories
    required_dirs = [
        Path("src"),
        Path("src/environment"),
        Path("src/agent"),
        Path("src/simulation"),
        Path("src/analysis"),
        Path("src/utils"),
        Path("tests"),
        Path("data/raw/synthetic_graphs"),
        Path("data/processed"),
    ]

    logger.info("Creating required project hierarchy...")
    for d in required_dirs:
        _ensure_dir(d)

    # Capture directory tree output
    try:
        result = subprocess.run(
            ["tree", "-L", "2"],
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        tree_output = result.stdout
    except FileNotFoundError:
        raise RuntimeError(
            "`tree` command not found. Install it (e.g., `sudo apt-get install tree`) "
            "or run the script on a system where it is available."
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"`tree` command failed: {e.stderr}") from e

    # Write the captured output to the designated file
    output_path = paths.data("processed", "dir_structure.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tree_output)
    logger.info("Directory structure written to %s", output_path)

if __name__ == "__main__":
    main()