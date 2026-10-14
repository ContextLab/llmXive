#!/usr/bin/env python
"""
Project layout and dependency verification script for T001.

Creates the authoritative directory structure under the project root,
checks that all pinned dependencies declared in ``code/pyproject.toml``
are importable, and writes a JSON install log to ``docs/install_log.txt``.

The script is idempotent – running it multiple times will not error
and will simply ensure the directories exist.
"""

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Mapping from package names (in pyproject.toml) to import names
IMPORT_MAPPING = {
    "pyyaml": "yaml",
    "scikit-learn": "sklearn",
}

def _load_pyproject_dependencies() -> list[str]:
    """Parse ``code/pyproject.toml`` and return the raw dependency strings."""
    import tomllib

    # The pyproject file lives directly inside the ``code`` directory.
    pyproject_path = Path(__file__).resolve().parent / "pyproject.toml"
    if not pyproject_path.is_file():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    if not isinstance(deps, list):
        raise ValueError("Invalid dependencies format in pyproject.toml")
    return deps

def _verify_dependencies(deps: list[str]) -> dict[str, str]:
    """
    Attempt to import each declared package and record its installed version.

    Raises:
        RuntimeError: If any package cannot be imported.
    """
    missing = []
    versions: dict[str, str] = {}

    for dep in deps:
        # Strip version specifiers; we only need the package name.
        pkg = (
            dep.split("[", 1)[0]
            .split("==", 1)[0]
            .split(">=", 1)[0]
            .split("<=", 1)[0]
            .split("~=", 1)[0]
            .strip()
        )

        # Resolve package name to import name (e.g., scikit-learn -> sklearn)
        import_name = IMPORT_MAPPING.get(pkg.lower(), pkg)

        try:
            module = importlib.import_module(import_name)
            ver = getattr(module, "__version__", "unknown")
            versions[pkg] = ver
        except Exception:  # pragma: no cover – import failure is fatal
            missing.append(pkg)

    if missing:
        raise RuntimeError(f"Missing required dependencies: {', '.join(missing)}")
    return versions

def _create_directories() -> None:
    """Create all required project folders (idempotent)."""
    dirs = [
        Path("code/data"),
        Path("code/analysis"),
        Path("code/viz"),
        Path("code/lib"),
        Path("code/utils"),
        Path("code/reporting"),
        Path("data/raw"),
        Path("data/processed"),
        Path("data/results"),
        Path("docs"),
        Path("contracts"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("tests/contract"),
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {d}")

def _cleanup_corrupted_paths() -> None:
    """Remove any files that should be files but were created as directories."""
    # Fix for reported IsADirectoryError: data/processed/cleaned_studies.csv
    corrupted = Path("data/processed/cleaned_studies.csv")
    if corrupted.is_dir():
        log.warning(f"Removing corrupted directory: {corrupted}")
        import shutil
        shutil.rmtree(corrupted)

def _write_install_log(versions: dict[str, str]) -> None:
    """Write a JSON log documenting the install timestamp and package versions."""
    log_path = Path("docs/install_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": versions,
    }

    with log_path.open("w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)

    log.info(f"Install log written to {log_path}")

def main() -> None:
    """Entry point for the setup script."""
    log.info("Starting project layout creation and dependency verification")

    # 0. Cleanup potential corrupted paths from previous failed runs
    _cleanup_corrupted_paths()

    # 1. Create the directory tree
    _create_directories()

    # 2. Load and verify pinned dependencies
    deps = _load_pyproject_dependencies()
    versions = _verify_dependencies(deps)

    # 3. Record the successful verification
    _write_install_log(versions)

    log.info("Project setup completed successfully")

if __name__ == "__main__":
    main()
