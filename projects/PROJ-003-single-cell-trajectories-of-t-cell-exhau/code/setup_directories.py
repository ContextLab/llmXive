"""Create the required directory structure for the project.

This module provides a single public function ``setup_directories`` that
creates the standard layout under the project root and returns the root
``Path``. The function is idempotent – existing directories are left
untouched.
"""

from pathlib import Path


def setup_directories() -> Path:
    """Create the required directory structure for the project.

    The following directories are created (if they do not already exist):
    
    - ``code/``
    - ``data/raw/``
    - ``data/processed/``
    - ``data/results/``
    - ``tests/unit/``
    - ``tests/integration/``
    
    Returns
    -------
    Path
        The absolute path to the project root (the directory that contains
        the ``code`` folder).
    """
    # Resolve the directory that contains this file – that is the ``code``
    # folder. The project root is its parent.
    project_root = Path(__file__).resolve().parent.parent

    # Define the directories we need relative to the project root.
    dirs = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    return project_root
