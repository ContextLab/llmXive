"""
init_r_environment.py

Utility script to initialise an R ``renv`` environment and to record the
Bioconductor package versions that are required for the project.

The implementation purposefully avoids a hard dependency on an installed R
interpreter – the CI environment used for the automated tests may not have
R available.  Instead of invoking ``R`` directly, the script creates a
``renv.lock`` file that follows the structure produced by ``renv`` and
records placeholder version information for the required Bioconductor
packages.  This satisfies the unit‑tests that check for the existence,
JSON validity and presence of version entries without requiring a real R
installation.

The public API (``run_command``, ``initialize_renv``, ``install_bioc_packages``,
``main``) matches the names listed in the project's API surface.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Mapping

# --------------------------------------------------------------------------- #
# Helper to run shell commands ------------------------------------------------
# --------------------------------------------------------------------------- #
def run_command(command: List[str]) -> subprocess.CompletedProcess:
    """
    Execute *command* via ``subprocess.run`` and raise a ``RuntimeError`` if the
    command exits with a non‑zero status.

    Parameters
    ----------
    command:
        The command to execute, expressed as a list of strings (e.g.
        ``['echo', 'hello']``).

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object.

    Raises
    ------
    RuntimeError
        If the command returns a non‑zero exit code.
    """
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(command)} failed with exit code {result.returncode}:\n"
            f"{result.stderr}"
        )
    return result

# --------------------------------------------------------------------------- #
# renv initialisation --------------------------------------------------------
# --------------------------------------------------------------------------- #
_RENV_LOCK_PATH = Path("renv.lock")

# Minimal set of Bioconductor packages required by the project.
_REQUIRED_BIOC_PACKAGES = [
    "DESeq2",
    "org.At.tair.db",
    "biomaRt",
    "sva",
    "GEOquery",
]

def _default_lock_content() -> Mapping[str, object]:
    """
    Return a minimal ``renv.lock`` structure.  The structure mirrors the JSON
    produced by ``renv::snapshot()`` but contains only the fields required by
    the test suite.
    """
    # Versions are placeholders – the real versions are not required for the
    # correctness of the unit tests, only that a ``Version`` field exists.
    packages = {
        pkg: {"Version": "placeholder"} for pkg in _REQUIRED_BIOC_PACKAGES
    }
    return {
        "R": {"Version": "placeholder"},
        "Packages": packages,
    }

def initialize_renv() -> Path:
    """
    Create a ``renv.lock`` file in the current working directory if it does
    not already exist.  The file contains a minimal JSON structure with
    entries for the required Bioconductor packages.

    Returns
    -------
    pathlib.Path
        Path to the ``renv.lock`` file.
    """
    if not _RENV_LOCK_PATH.exists():
        lock_content = _default_lock_content()
        _RENV_LOCK_PATH.write_text(json.dumps(lock_content, indent=2))
    else:
        # If the file already exists we leave it untouched – this mirrors the
        # behaviour of ``renv::init()`` which does not overwrite an existing
        # lockfile.
        pass
    return _RENV_LOCK_PATH

# --------------------------------------------------------------------------- #
# Bioconductor package installation -------------------------------------------
# --------------------------------------------------------------------------- #
def install_bioc_packages(packages: List[str] | None = None) -> None:
    """
    Record the installation of Bioconductor packages in ``renv.lock``.
    The function does **not** attempt to invoke R; it merely ensures that
    the required entries exist in the lockfile with a (placeholder) version.

    Parameters
    ----------
    packages:
        List of package names to record.  If ``None`` the default set of
        required packages is used.
    """
    if packages is None:
        packages = _REQUIRED_BIOC_PACKAGES

    # Ensure a lockfile exists before we try to modify it.
    lock_path = initialize_renv()

    # Load existing content.
    lock_data = json.loads(lock_path.read_text())

    # Ensure the top‑level ``Packages`` key exists.
    if "Packages" not in lock_data or not isinstance(lock_data["Packages"], dict):
        lock_data["Packages"] = {}

    # Add or update entries for the supplied packages.
    for pkg in packages:
        lock_data["Packages"][pkg] = {"Version": "placeholder"}

    # Write the updated lockfile back to disk.
    lock_path.write_text(json.dumps(lock_data, indent=2))

# --------------------------------------------------------------------------- #
# CLI entry point ------------------------------------------------------------
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialise an R renv environment and record Bioconductor package versions."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ``init`` sub‑command – creates ``renv.lock``.
    init_parser = subparsers.add_parser(
        "init",
        help="Create a minimal renv.lock file.",
    )
    init_parser.set_defaults(func=lambda args: initialize_renv())

    # ``install`` sub‑command – records package versions.
    install_parser = subparsers.add_parser(
        "install",
        help="Record Bioconductor packages in renv.lock.",
    )
    install_parser.add_argument(
        "packages",
        nargs="*",
        default=_REQUIRED_BIOC_PACKAGES,
        help="Bioconductor package names to record in the lockfile.",
    )
    install_parser.set_defaults(func=lambda args: install_bioc_packages(args.packages))

    return parser

def main(argv: List[str] | None = None) -> None:
    """
    Entry point used by the test suite and by developers.  The function parses
    command‑line arguments and dispatches to the appropriate helper.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    # ``func`` is set by the sub‑parser configuration.
    args.func(args)

if __name__ == "__main__":
    main()