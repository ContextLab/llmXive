"""
init_r_environment.py

This module provides utilities to bootstrap an R environment for the
project using **renv** and to install the required Bioconductor packages.
It is used by the unit‑tests in `tests/test_r_environment.py` and by the
CI pipeline.

The implementation follows the public API defined in the project's
specification:

* ``run_command`` – thin wrapper around ``subprocess.run`` that raises on
  failure.
* ``initialize_renv`` – creates a fresh ``renv`` environment and writes a
  ``renv.lock`` file.
* ``install_bioc_packages`` – installs the list of required Bioconductor
  packages inside the ``renv`` project.
* ``main`` – orchestrates the full initialization when the script is run
  directly.

All commands are executed via ``Rscript``; the functions raise a
``subprocess.CalledProcessError`` on failure so that the test suite can
verify error handling.
"""

import subprocess
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------
def run_command(command: List[str]) -> subprocess.CompletedProcess:
    """
    Execute a command using ``subprocess.run`` with ``check=True`` so that
    failures raise ``CalledProcessError``.

    Parameters
    ----------
    command: List[str]
        The command and its arguments, e.g. ``["Rscript", "-e", "..."]``.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object (stdout, stderr, returncode).
    """
    # ``text=True`` provides ``stdout``/``stderr`` as strings.
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return result

# ----------------------------------------------------------------------
# renv initialization
# ----------------------------------------------------------------------
def initialize_renv() -> None:
    """
    Initialise a *renv* project in the current working directory.

    The function performs the following steps:

    1. Ensures the ``renv`` package is installed (via CRAN).
    2. Calls ``renv::init(bare = TRUE)`` which creates a minimal ``renv``
       environment and writes a ``renv.lock`` file.
    """
    # Install renv if missing
    install_renv_cmd = [
        "Rscript",
        "-e",
        (
            "if (!requireNamespace('renv', quietly = TRUE)) "
            "install.packages('renv', repos = 'https://cloud.r-project.org')"
        ),
    ]
    run_command(install_renv_cmd)

    # Initialise renv (bare = TRUE creates the lockfile without installing any packages yet)
    init_cmd = [
        "Rscript",
        "-e",
        "renv::init(bare = TRUE)",
    ]
    run_command(init_cmd)

    # Verify that the lockfile was created
    lock_path = Path("renv.lock")
    if not lock_path.is_file():
        raise FileNotFoundError("renv.lock was not created by renv::init()")

# ----------------------------------------------------------------------
# Bioconductor package installation
# ----------------------------------------------------------------------
REQUIRED_BIOC_PACKAGES = [
    "DESeq2",
    "org.At.tair.db",
    "biomaRt",
    "sva",
    "GEOquery",
]

def install_bioc_packages() -> None:
    """
    Install the required Bioconductor packages inside the *renv* project.

    The function ensures that the ``BiocManager`` package is available and
    then calls ``BiocManager::install()`` with ``ask = FALSE`` to avoid
    interactive prompts.
    """
    # Install BiocManager if missing
    install_biocmanager_cmd = [
        "Rscript",
        "-e",
        (
            "if (!requireNamespace('BiocManager', quietly = TRUE)) "
            "install.packages('BiocManager', repos = 'https://cloud.r-project.org')"
        ),
    ]
    run_command(install_biocmanager_cmd)

    # Install the required Bioconductor packages
    packages_str = ", ".join(f'"{pkg}"' for pkg in REQUIRED_BIOC_PACKAGES)
    install_cmd = [
        "Rscript",
        "-e",
        (
            f"BiocManager::install(c({packages_str}), ask = FALSE, update = FALSE, "
            "checkBuilt = FALSE, force = FALSE)"
        ),
    ]
    run_command(install_cmd)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Initialise the R environment and install the Bioconductor dependencies.
    This function is used by the CI step and can also be invoked manually:

    ``python code/init_r_environment.py``
    """
    print("Initializing renv environment...")
    initialize_renv()
    print("Installing required Bioconductor packages...")
    install_bioc_packages()
    print("R environment ready. renv.lock created at:", Path("renv.lock").resolve())

if __name__ == "__main__":
    main()
