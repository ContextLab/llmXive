"""
Script to create required test directories for the project.
This satisfies task T001c: Create test directories `tests/unit/`,
`tests/integration/`, and `tests/contract/`.
"""

from llmxive_toolkit import paths, get_logger
import os

def main() -> None:
    """
    Create the three test sub‑directories under the project ``tests`` folder.
    Uses the ``paths`` helper to ensure the correct project‑root location.
    """
    log = get_logger(__name__)
    subdirs = ["unit", "integration", "contract"]
    for sub in subdirs:
        dir_path = paths.tests(sub)  # e.g., <project>/tests/unit
        # ``mkdir`` with ``parents=True`` creates any missing parents.
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created test directory: {dir_path}")

if __name__ == "__main__":
    main()