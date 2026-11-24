"""Scaffolding script for T001.

Creates the project directory structure required by Phase 0:
    code/  (with __init__.py)
    data/raw/.gitkeep
    data/processed/.gitkeep
    data/artifacts/.gitkeep
    tests/unit/.gitkeep
    tests/contract/.gitkeep
    contracts/  (empty for now)

Idempotent: running it multiple times is safe.
"""

from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

GITKEEP_TEXT = {
    "data/raw": (
        "# This directory stores raw, unprocessed data downloaded from "
        "external sources.\n"
        "# Do not modify files in this directory manually.\n"
    ),
    "data/processed": (
        "# This directory stores processed, cleaned, and transformed data.\n"
        "# Intermediate and final artifacts for analysis should be saved here.\n"
    ),
    "data/artifacts": (
        "# This directory stores final analysis artifacts (plots, reports,\n"
        "# stability metrics) produced by the pipeline.\n"
    ),
    "tests/unit": (
        "# Placeholder file to ensure the unit tests directory is tracked "
        "by version control.\n"
    ),
    "tests/contract": (
        "# Placeholder file to ensure the contract tests directory is "
        "tracked by version control.\n"
    ),
}

CODE_INIT = '''"""
llmXive Statistical Analysis Pipeline - Main Package

This package provides tools for statistical analysis of publicly available
climate model output ensembles, including:

- Data ingestion and preprocessing (CMIP6)
- Functional representation via B-splines
- Functional Principal Component Analysis (fPCA)
- Robustness assessment via Leave-One-Out Jackknife

Submodules:
- config: Project configuration and paths
- ingestion: Data download and preprocessing
- basis: B-spline basis expansion and reconstruction
- fpca: Functional PCA implementation
- robustness: LOO Jackknife stability analysis
- visualize: Visualization utilities
- cleanup_utils: Cleanup and refactoring utilities
- refactoring_helpers: Shared helper functions
"""

from .config import get_project_root, get_data_dir, get_artifacts_dir, get_log_dir
from .logging_config import setup_logging, get_logger

__version__ = "1.0.0"
__author__ = "llmXive Research Team"

__all__ = [
    "get_project_root",
    "get_data_dir",
    "get_artifacts_dir",
    "get_log_dir",
    "setup_logging",
    "get_logger",
]
'''

def scaffold(root: Path = None) -> None:
    """Create all required directories and placeholder files."""
    root = Path(root) if root is not None else paths.root

    # Directories that only need to exist (no placeholder file).
    for d in ("contracts",):
        (root / d).mkdir(parents=True, exist_ok=True)
        log.info("Ensured directory exists: %s", root / d)

    # Directories with a .gitkeep placeholder.
    for rel, text in GITKEEP_TEXT.items():
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text(text, encoding="utf-8")
            log.info("Created %s", gitkeep)
        else:
            log.info("Already present: %s", gitkeep)

    # code/__init__.py
    code_dir = root / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    init = code_dir / "__init__.py"
    if not init.exists():
        init.write_text(CODE_INIT, encoding="utf-8")
        log.info("Created %s", init)
    else:
        log.info("Already present: %s", init)

def main() -> int:
    scaffold()
    # Verify the structure (fail loudly if anything is missing).
    root = paths.root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests/unit",
        "tests/contract",
        "contracts",
    ]
    required_files = [
        "code/__init__.py",
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "data/artifacts/.gitkeep",
        "tests/unit/.gitkeep",
        "tests/contract/.gitkeep",
    ]
    missing = [
        str(p)
        for p in required_dirs
        if not (root / p).is_dir()
    ] + [
        str(p) for p in required_files if not (root / p).is_file()
    ]
    if missing:
        raise RuntimeError(f"Scaffolding incomplete, missing: {missing}")
    print("Scaffolding complete. Project structure verified:")
    for p in required_dirs:
        print(f"  dir : {p}")
    for p in required_files:
        print(f"  file: {p}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
