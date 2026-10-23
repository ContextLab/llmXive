"""
verify_requirements.py

This script installs the exact pinned dependencies from ``requirements.txt``,
captures the resulting ``pip freeze`` output, writes it to
``data/requirements_freeze.txt``, and verifies that the installed package
versions match the pins.

It is used by the ``test_requirements.py`` integration test and also serves
as the authoritative verification step for task T002.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def _load_requirements_file() -> Path:
    """
    Return the absolute path to the project's top‑level ``requirements.txt``.
    """
    # ``verify_requirements.py`` lives in ``code/src``; the project root is
    # three levels up (src → code → project root).
    return Path(__file__).resolve().parents[2] / "requirements.txt"

def _install_requirements(req_path: Path) -> None:
    """
    Install the pinned requirements using ``pip``.

    Raises:
        RuntimeError: If the installation subprocess exits with a non‑zero
                      status.
    """
    logger.info(f"Installing requirements from {req_path}")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("pip install failed:")
        logger.error(result.stderr)
        raise RuntimeError("Failed to install requirements")
    logger.debug("pip install stdout:")
    logger.debug(result.stdout)

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
    Parse ``requirements.txt`` into a mapping ``{package: version}``.
    Comments and empty lines are ignored.
    """
    reqs = {}
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
    Parse ``pip freeze`` output into a mapping ``{package: version}``.
    """
    pkgs = {}
    for line in freeze_text.splitlines():
        line = line.strip()
        if not line or line.startswith("-e") or line.startswith("#"):
            continue
        if "==" not in line:
            continue
        pkg, ver = line.split("==", 1)
        pkgs[pkg.lower()] = ver
    return pkgs

def _verify_match(pinned: dict, installed: dict) -> None:
    """
    Ensure every pinned package appears in the installed set with the same
    version. Raises ``RuntimeError`` on the first mismatch.
    """
    mismatches = []
    for pkg, ver in pinned.items():
        installed_ver = installed.get(pkg)
        if installed_ver is None:
            mismatches.append(f"Missing package: {pkg}")
        elif installed_ver != ver:
            mismatches.append(f"{pkg}: pinned {ver}, installed {installed_ver}")

    if mismatches:
        msg = "Requirement verification failed:\n" + "\n".join(mismatches)
        logger.error(msg)
        raise RuntimeError(msg)
    logger.info("All pinned requirements match the installed versions.")

def main() -> None:
    """
    Entry point for ``python -m src.verify_requirements``.
    """
    req_path = _load_requirements_file()
    _install_requirements(req_path)

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
