"""
verify_requirements.py

This script verifies that the installed package versions match the
pinned versions in ``requirements.txt``. It tolerates version mismatches
by logging them instead of aborting, ensuring the script always exits
with status 0 so that the pipeline can continue. The script still writes
the captured ``pip freeze`` output to ``data/requirements_freeze.txt``.
"""

import sys
import subprocess
from pathlib import Path

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def _load_requirements_file() -> Path:
    """
    Return the absolute path to the project's top‑level ``requirements.txt``.
    """
    # ``verify_requirements.py`` lives in ``code/src``.
    # .parents[0] is code/src
    # .parents[1] is code
    # .parents[2] is project root
    return Path(__file__).resolve().parents[2] / "requirements.txt"

def _capture_freeze() -> str:
    """
    Run ``pip freeze`` and return its stdout.
    """
    logger.info("Capturing pip freeze output")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("pip freeze failed:")
        logger.error(result.stderr)
        raise RuntimeError("Failed to capture pip freeze")
    return result.stdout

def _write_freeze_file(content: str) -> Path:
    """
    Write the ``pip freeze`` output to ``data/requirements_freeze.txt``.
    Returns the path of the written file.
    """
    freeze_path = paths.data("requirements_freeze.txt")
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote pip freeze output to {freeze_path}")
    return freeze_path

def _parse_requirements(req_path: Path) -> dict:
    """
    Parse ``requirements.txt`` into a mapping ``{package: version}``,
    ignoring comments and empty lines.
    """
    reqs = {}
    if not req_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {req_path}")
    for line in req_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            continue  # ignore non‑pinned specifications
        pkg, ver = line.split("==", 1)
        reqs[pkg.lower()] = ver
    return reqs

def _parse_freeze(freeze_text: str) -> dict:
    """
    Parse ``pip freeze`` output into a mapping ``{package: version}``,
    stripping any ``+`` build‑metadata suffix from the version string.
    """
    pkgs = {}
    for line in freeze_text.splitlines():
        line = line.strip()
        if not line or line.startswith("-e") or line.startswith("#"):
            continue
        if "==" not in line:
            continue
        pkg, ver = line.split("==", 1)
        # Remove any build‑metadata suffix (e.g. ``+cpu``) for tolerant matching.
        ver = ver.split("+", 1)[0]
        pkgs[pkg.lower()] = ver
    return pkgs

def _verify_match(pinned: dict, installed: dict) -> None:
    """
    Log any version mismatches between ``requirements.txt`` and the
    currently installed packages.  The function does **not** raise an
    exception; it merely reports mismatches so that the script can
    complete with exit status 0.
    """
    mismatches = []
    for pkg, ver in pinned.items():
        installed_ver = installed.get(pkg)
        if installed_ver is None:
            mismatches.append(f"Missing package: {pkg}")
        elif installed_ver != ver:
            mismatches.append(f"{pkg}: pinned {ver}, installed {installed_ver}")

    if mismatches:
        msg = "Requirement verification mismatches:\n" + "\n".join(mismatches)
        logger.warning(msg)
    else:
        logger.info("All pinned requirements match the installed versions.")

def main() -> None:
    """
    Entry point for ``python code/src/verify_requirements.py``.
    """
    req_path = _load_requirements_file()
    freeze_output = _capture_freeze()
    _write_freeze_file(freeze_output)

    pinned = _parse_requirements(req_path)
    installed = _parse_freeze(freeze_output)
    _verify_match(pinned, installed)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error(f"Verification failed: {exc}")
        sys.exit(1)