"""T001 verification: the required project directory tree exists."""
from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "docs",
    "reports",
    "figures",
    "scripts",
]

REQUIRED_CODE_MODULES = [
    "ingest.py",
    "utils.py",
    "spherical_harmonics.py",
    "simulations.py",
    "analysis.py",
    "visualize.py",
    "models.py",
]


def test_required_directories_exist() -> None:
    root: Path = paths.root
    for rel in REQUIRED_DIRS:
        assert (root / rel).is_dir(), f"missing directory: {rel}"


def test_required_code_modules_exist() -> None:
    code_dir: Path = paths.root / "code"
    for name in REQUIRED_CODE_MODULES:
        assert (code_dir / name).is_file(), f"missing code module: {name}"