"""Setup script for project directory structure.

T001-Setup-Dirs-Code: creates code-related directories:
code/, code/data/, code/models/, code/eval/, code/utils/,
tests/contract/, tests/unit/, tests/integration/, logs/

T001-Setup-Dirs-Data: creates data-related directories:
data/raw/, data/processed/, data/splits/, data/schemas/

T001-Setup-Dirs-Results: creates results-related directories:
results/reports/, results/plots/, results/baseline/, results/predictions/

Run from the repository root:
    python scripts/setup_dirs.py
"""

import sys
from pathlib import Path

CODE_DIRS = [
    "code",
    "code/data",
    "code/models",
    "code/eval",
    "code/utils",
    "tests/contract",
    "tests/unit",
    "tests/integration",
    "logs",
]

DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/splits",
    "data/schemas",
]

RESULTS_DIRS = [
    "results/reports",
    "results/plots",
    "results/baseline",
    "results/predictions",
]

ALL_DIRS = CODE_DIRS + DATA_DIRS + RESULTS_DIRS


def _resolve_base(base: Path = None) -> Path:
    if base is None:
        return Path(__file__).resolve().parent.parent
    return base


def create_directories(base: Path = None) -> list:
    """Create all code-related directories under the given base path.

    Args:
        base: Base path (defaults to repository root, i.e. parent of scripts/).

    Returns:
        List of Path objects for the created directories.
    """
    base = _resolve_base(base)
    created = []
    for rel in CODE_DIRS:
        d = base / rel
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)
    return created


def create_data_directories(base: Path = None) -> list:
    """Create all data-related directories under the given base path.

    Args:
        base: Base path (defaults to repository root, i.e. parent of scripts/).

    Returns:
        List of Path objects for the created directories.
    """
    base = _resolve_base(base)
    created = []
    for rel in DATA_DIRS:
        d = base / rel
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)
    return created


def create_results_directories(base: Path = None) -> list:
    """Create all results-related directories under the given base path.

    T001-Setup-Dirs-Results: results/reports/, results/plots/,
    results/baseline/, results/predictions/

    Args:
        base: Base path (defaults to repository root, i.e. parent of scripts/).

    Returns:
        List of Path objects for the created directories.
    """
    base = _resolve_base(base)
    created = []
    for rel in RESULTS_DIRS:
        d = base / rel
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)
    return created


def verify_directories(base: Path = None) -> bool:
    """Verify that all code-related directories exist.

    Returns:
        True if all directories exist, False otherwise.
    """
    base = _resolve_base(base)
    return all((base / rel).is_dir() for rel in CODE_DIRS)


def verify_data_directories(base: Path = None) -> bool:
    """Verify that all data-related directories exist.

    Returns:
        True if all directories exist, False otherwise.
    """
    base = _resolve_base(base)
    return all((base / rel).is_dir() for rel in DATA_DIRS)


def verify_results_directories(base: Path = None) -> bool:
    """Verify that all results-related directories exist.

    Returns:
        True if all directories exist, False otherwise.
    """
    base = _resolve_base(base)
    return all((base / rel).is_dir() for rel in RESULTS_DIRS)


def verify_all_directories(base: Path = None) -> bool:
    """Verify that all project directories (code + data + results) exist."""
    return (
        verify_directories(base)
        and verify_data_directories(base)
        and verify_results_directories(base)
    )


def main() -> int:
    # Code-related directories (T001-Setup-Dirs-Code)
    created = create_directories()
    for d in created:
        print(f"OK: {d}")

    # Data-related directories (T001-Setup-Dirs-Data)
    data_created = create_data_directories()
    for d in data_created:
        print(f"OK: {d}")

    # Results-related directories (T001-Setup-Dirs-Results)
    results_created = create_results_directories()
    for d in results_created:
        print(f"OK: {d}")

    if verify_all_directories():
        print("All code-, data-, and results-related directories created and verified.")
        return 0
    print("ERROR: directory verification failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())