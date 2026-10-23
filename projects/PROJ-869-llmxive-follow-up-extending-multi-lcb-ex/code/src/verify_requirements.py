"""
verify_requirements.py

This script verifies that the project's ``requirements.txt`` can be installed
in a fresh environment and that the installed package versions exactly match
the pinned versions declared in the file.

It performs the following steps:
1. Runs ``pip install -r requirements.txt``.
2. Captures the output of ``pip freeze``.
3. Compares the frozen versions against the pins.
4. Writes the full ``pip freeze`` output to ``data/requirements_freeze.txt``.
5. Exits with status 0 on success or 1 on any version mismatch.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def _load_pinned_versions(req_path: Path) -> dict:
    """Parse ``requirements.txt`` and return a dict of {package: version}."""
    pinned = {}
    with req_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                pkg, ver = line.split("==", 1)
                pinned[pkg.lower()] = ver
    return pinned

def main() -> None:
    # Resolve the path to the repository‑root ``requirements.txt``.
    repo_root = Path(__file__).resolve().parents[2]
    req_path = repo_root / "requirements.txt"

    logger.info(f"Installing requirements from {req_path}")

    # Install the exact pinned requirements into the current environment.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])

    # Capture the frozen environment.
    logger.info("Running ``pip freeze`` to capture installed versions")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    freeze_lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]

    # Load the pins and compare.
    pinned = _load_pinned_versions(req_path)
    mismatches = []

    for line in freeze_lines:
        if "==" not in line:
            continue
        pkg, ver = line.split("==", 1)
        pkg_l = pkg.lower()
        if pkg_l in pinned and pinned[pkg_l] != ver:
            mismatches.append(f"{pkg} {ver} != {pinned[pkg_l]}")

    if mismatches:
        logger.error("Version mismatches detected:")
        for msg in mismatches:
            logger.error(f"  {msg}")
        sys.exit(1)

    # Write the full freeze output for audit purposes.
    freeze_path = paths.data("requirements_freeze.txt")
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text("\n".join(freeze_lines) + "\n")
    logger.info(f"Wrote pip freeze output to {freeze_path}")

    logger.info("All pinned versions match the installed environment.")
    # Successful exit.
    sys.exit(0)

if __name__ == "__main__":
    main()
