"""
Script to create the required 'artifacts/' and 'artifacts/models/' directories
for the project. This fulfills task T001d.
"""

import sys
from pathlib import Path

# llmxive_toolkit provides convenient path helpers
from llmxive_toolkit import paths


def main() -> int:
    """
    Create the 'artifacts' directory and its 'models' subdirectory.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    # Resolve the project root and construct the required paths
    project_root: Path = Path(paths.root)

    artifacts_dir = project_root / "artifacts"
    models_dir = artifacts_dir / "models"

    try:
        # Ensure both directories exist
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        # Inform the user (useful when run manually)
        print(f"Created directory: {artifacts_dir}")
        print(f"Created directory: {models_dir}")

    except Exception as exc:
        print(f"Failed to create artifact directories: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())