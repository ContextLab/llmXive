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
        # Strip version specifiers; we only need the import name.
        # Handles ``pkg==x.y.z`` and simple extras like ``pkg[extra]==x.y``.
        pkg = (
            dep.split("[", 1)[0]
            .split("==", 1)[0]
            .split(">=", 1)[0]
            .split("<=", 1)[0]
            .split("~=", 1)[0]
            .strip()
        )

        try:
            module = importlib.import_module(pkg)
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
