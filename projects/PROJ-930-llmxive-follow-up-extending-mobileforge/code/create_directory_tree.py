"""Create the required project directory tree for the MobileForge Logic Distillation study.

This script is idempotent and will create (if they do not already exist) the following
directories relative to the project root:

- code/data/raw
- code/data/processed
- code/data/evaluation
- code/models
- code/utils
- code/tests/unit
- code/tests/integration
- state

The script uses the `llmxive_toolkit.paths` helper to resolve the project root and
logs the creation of each directory. It exits with status 0 on success.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _ensure_dir(p: Path) -> None:
    """Create a directory and all parent directories if needed."""
    p.mkdir(parents=True, exist_ok=True)
    log.info(f"Ensured directory exists: {p}")

def main() -> int:
    """Create the full directory tree required for the study."""
    root = paths.root

    # Define the required directories relative to the project root.
    required_dirs = [
        root / "code" / "data" / "raw",
        root / "code" / "data" / "processed",
        root / "code" / "data" / "evaluation",
        root / "code" / "models",
        root / "code" / "utils",
        root / "code" / "tests" / "unit",
        root / "code" / "tests" / "integration",
        root / "state",
    ]

    for d in required_dirs:
        _ensure_dir(d)

    print("All required directories have been created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())