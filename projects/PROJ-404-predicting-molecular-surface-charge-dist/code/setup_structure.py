"""
Script to create the required project directory hierarchy and ensure that each
sub‑package under `code/` contains an `__init__.py` file. After creation it
verifies the existence of the directories and the `__init__.py` files,
exiting with a non‑zero status if any check fails.
"""
import os
import sys
import pathlib
import logging

# Configure a simple logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def create_dir(path: pathlib.Path) -> None:
    """Create a directory (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory: {path}")

def ensure_init_py(package_path: pathlib.Path) -> None:
    """Ensure an __init__.py file exists in the given package directory."""
    init_file = package_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        logger.info(f"Created __init__.py in: {package_path}")
    else:
        logger.info(f"__init__.py already present in: {package_path}")

def main() -> None:
    """
    Create the directory tree required by the implementation plan and verify
    that every `code/*` subdirectory contains an `__init__.py` file.
    """
    # Determine the project root (the directory that contains this script's `code/` folder)
    script_path = pathlib.Path(__file__).resolve()
    code_dir = script_path.parent  # <project_root>/code
    project_root = code_dir.parent  # <project_root>

    # Directories to create (relative to the project root)
    dirs_to_create = [
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "utils",
        project_root / "tests",
        project_root / "artifacts" / "reports",
        project_root / "artifacts" / "models",
        project_root / "artifacts" / "splits",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
    ]

    # Create directories
    for d in dirs_to_create:
        create_dir(d)

    # Packages under `code/` that must contain __init__.py
    package_dirs = [
        code_dir,                       # code/
        code_dir / "data",              # code/data/
        code_dir / "models",            # code/models/
        code_dir / "utils",             # code/utils/
    ]

    # Ensure __init__.py exists in each package directory
    for pkg in package_dirs:
        ensure_init_py(pkg)

    # Verification step
    missing = []
    for d in dirs_to_create:
        if not d.is_dir():
            missing.append(str(d))
    for pkg in package_dirs:
        init_file = pkg / "__init__.py"
        if not init_file.is_file():
            missing.append(str(init_file))

    if missing:
        logger.error("Verification failed. Missing items:")
        for m in missing:
            logger.error(f"  - {m}")
        sys.exit(1)
    else:
        logger.info("All required directories and __init__.py files are present.")

if __name__ == "__main__":
    main()