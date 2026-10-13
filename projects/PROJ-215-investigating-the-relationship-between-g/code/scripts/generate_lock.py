"""
generate_lock.py

This script generates a `requirements.lock` file that records the exact
versions of the packages listed in `requirements.txt` as they are installed
in the current environment. The lock file can be used to reproduce the
environment precisely.

Usage:
    python code/scripts/generate_lock.py
"""

import os
from pathlib import Path
from importlib import metadata

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def parse_requirements(requirements_path: Path):
    """
    Parse a requirements.txt file and return a set of package names
    (case‑insensitive, without version specifiers).

    Parameters
    ----------
    requirements_path : Path
        Path to the requirements.txt file.

    Returns
    -------
    Set[str]
        Normalised package names.
    """
    packages = set()
    with requirements_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Remove any environment markers or extras
            # Example formats:
            #   pandas==2.2.2
            #   scikit-learn>=1.0; python_version < "3.12"
            #   package[extra]==1.0
            # Split on ';' first to drop markers
            line = line.split(";", 1)[0].strip()
            # Split on '==' or '>=' or '<=' or '~=' or '>'
            for sep in ["==", ">=", "<=", "~=", ">", "<"]:
                if sep in line:
                    line = line.split(sep, 1)[0]
                    break
            # Remove extras in brackets
            if "[" in line:
                line = line.split("[", 1)[0]
            packages.add(line.lower())
    return packages

def generate_lock(requirements_txt: Path, lock_path: Path):
    """
    Generate a lock file that pins the exact installed versions for all
    packages listed in ``requirements.txt``.

    Parameters
    ----------
    requirements_txt : Path
        Path to the source ``requirements.txt``.
    lock_path : Path
        Destination path for ``requirements.lock``.
    """
    log.info(f"Reading requirements from {requirements_txt}")
    required_packages = parse_requirements(requirements_txt)

    log.info(f"Resolving installed versions for {len(required_packages)} packages")
    locked_lines = []
    for pkg in sorted(required_packages):
        try:
            version = metadata.version(pkg)
            locked_lines.append(f"{pkg}=={version}")
        except metadata.PackageNotFoundError:
            log.error(f"Package '{pkg}' not found in the current environment.")
            raise

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(locked_lines) + "\n")

    log.info(f"Lock file written to {lock_path}")

def main():
    """
    Entry point for the script.
    """
    # Resolve paths using llmxive_toolkit helpers
    requirements_path = paths.root / "requirements.txt"
    lock_path = paths.root / "requirements.lock"

    if not requirements_path.is_file():
        log.error(f"requirements.txt not found at {requirements_path}")
        raise FileNotFoundError(f"{requirements_path} does not exist")

    generate_lock(requirements_path, lock_path)

if __name__ == "__main__":
    main()
