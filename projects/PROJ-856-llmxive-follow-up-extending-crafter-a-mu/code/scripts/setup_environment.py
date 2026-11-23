"""Setup script for the llmXive follow-up project.

This script performs two essential steps required by task T000:

1. Installs the exact, pinned Python dependencies defined in
   ``requirements.txt`` using the current Python interpreter.
2. Generates SHA‑256 checksums for all raw data files under the
   ``data/`` directory (excluding the checksum manifest itself) and
   writes them to ``data/checksums.txt``.

The script is intended to be executed as part of the reproducible
environment setup and is invoked by the quick‑start workflow:

    python -m code.scripts.setup_environment

It exits with status 0 on success; any failure (e.g., missing
``pip`` or a broken requirement) propagates as a non‑zero exit code,
causing the CI gate to fail loudly.
"""

import subprocess
import sys
from pathlib import Path

# The llmxive_toolkit provides convenient path helpers that create the
# required directories if they do not already exist.
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _install_requirements() -> None:
    """Install the exact dependencies pinned in ``requirements.txt``."""
    req_path: Path = paths.root / "requirements.txt"
    if not req_path.is_file():
        log.error("requirements.txt not found at %s", req_path)
        sys.exit(1)

    # Use the current interpreter to invoke pip in a subprocess.
    log.info("Installing dependencies from %s", req_path)
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        log.error("Dependency installation failed:\n%s", exc.stdout)
        sys.exit(exc.returncode)

def _generate_checksums() -> None:
    """Run the project's checksum generator."""
    # Import inside the function to avoid import‑time side effects.
    from src.utils import checksums

    log.info("Generating SHA‑256 checksums for raw data files")
    try:
        checksums.main()
    except Exception as exc:
        log.exception("Checksum generation failed: %s", exc)
        sys.exit(1)

def main() -> None:
    _install_requirements()
    _generate_checksums()
    log.info("Environment setup completed successfully")

if __name__ == "__main__":
    main()