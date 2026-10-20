"""
Verify that the project's requirements are correctly pinned and can be installed.

This script is invoked by the quickstart (`python -m code.verify_requirements`).
It performs two checks:

1. **Installation check** – runs ``pip install -r requirements.txt`` in a
   subprocess.  The command is executed with the current Python interpreter
   and silences stdout/stderr to keep CI output clean.  If the installation
   fails, the script raises an exception so the CI step fails.

2. **Regex pinning check** – ensures every non‑empty line in
   ``requirements.txt`` matches the pattern
   ``^[a-zA-Z0-9_-]+==[0-9]+\.[0-9]+\.\*$`` (package name, major.minor.\*).

Upon success a ``results/requirements_install.log`` file containing the
word ``success`` is written.  The existence and content of this file are
used by the verifier as proof that the task completed successfully.
"""

import re
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

LOG = get_logger(__name__)

REQUIREMENTS_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+==[0-9]+\.[0-9]+\.\*$')


def _install_requirements(req_path: Path) -> None:
    """Run ``pip install -r <requirements.txt>``."""
    LOG.info("Installing requirements from %s", req_path)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        LOG.error("pip install failed with exit code %s", exc.returncode)
        raise


def _validate_pinning(req_path: Path) -> None:
    """Check that each requirement line matches the pinning regex."""
    LOG.info("Validating requirement pinning patterns")
    bad_lines = []
    with req_path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue  # ignore comments / blanks
            if not REQUIREMENTS_PATTERN.fullmatch(line):
                bad_lines.append((line_no, line))

    if bad_lines:
        for ln, txt in bad_lines:
            LOG.error("Invalid requirement at line %d: %s", ln, txt)
        raise ValueError("One or more requirement lines do not match the required pattern")


def _write_success_log() -> None:
    """Write a minimal success indicator for the CI verifier."""
    log_path = paths.results("requirements_install.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as fh:
        fh.write("success\n")
    LOG.info("Wrote success log to %s", log_path)


def main() -> None:
    """Entry point for ``python -m code.verify_requirements``."""
    req_path = paths.root / "requirements.txt"
    if not req_path.is_file():
        LOG.error("requirements.txt not found at %s", req_path)
        raise FileNotFoundError(req_path)

    _install_requirements(req_path)
    _validate_pinning(req_path)
    _write_success_log()
    LOG.info("Requirements verification completed successfully")


if __name__ == "__main__":
    main()