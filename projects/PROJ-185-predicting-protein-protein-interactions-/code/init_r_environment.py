"""
init_r_environment.py
---------------------

This module provides a small helper to bootstrap an R environment for the
project using **renv**.  It creates a ``renv.lock`` file (if one does not
already exist) that pins the Bioconductor packages required by the
pipeline and then runs a short R script that:

1. Installs the ``renv`` package (if missing).
2. Initializes a bare renv project.
3. Installs the required Bioconductor packages.
4. Writes a snapshot to ``renv.lock`` so that the environment can be
   reproduced later.

The helper is deliberately lightweight – it only invokes R via
``subprocess``.  If R is not available on the system the call will raise a
``FileNotFoundError`` which is propagated to the caller; this is the
preferred behaviour because the pipeline must fail loudly when the real R
environment cannot be created.

The module is used by the CI and by developers who wish to set up the R
side of the project locally:

    $ python -m code.init_r_environment --project-dir .

The ``--project-dir`` argument defaults to the current working directory.
"""

import json
import subprocess
from pathlib import Path
from typing import List

__all__ = ["initialize_renv", "main"]


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _default_lock_content() -> dict:
    """
    Return the default ``renv.lock`` content that pins the required
    Bioconductor packages.  Versions are taken from the Bioconductor
    3.18 release (the most recent stable release at the time of writing).

    The structure follows the format produced by ``renv::snapshot()``.
    """
    return {
        "R": {"Version": "4.3.0"},
        "BiocVersion": "3.18",
        "Packages": {
            "DESeq2": {
                "Package": "DESeq2",
                "Version": "1.38.0",
                "Source": "Bioconductor",
                "Repository": "Bioc"
            },
            "org.At.tair.db": {
                "Package": "org.At.tair.db",
                "Version": "3.15.0",
                "Source": "Bioconductor",
                "Repository": "Bioc"
            },
            "biomaRt": {
                "Package": "biomaRt",
                "Version": "2.56.0",
                "Source": "Bioconductor",
                "Repository": "Bioc"
            },
            "sva": {
                "Package": "sva",
                "Version": "3.44.0",
                "Source": "Bioconductor",
                "Repository": "Bioc"
            },
            "GEOquery": {
                "Package": "GEOquery",
                "Version": "2.68.0",
                "Source": "Bioconductor",
                "Repository": "Bioc"
            }
        }
    }


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def initialize_renv(project_dir: Path = Path.cwd()) -> None:
    """
    Initialise an R ``renv`` environment in *project_dir*.

    Steps performed:

    1. Create ``renv.lock`` with the default content if it does not already
       exist.
    2. Run an R one‑liner that installs ``renv`` (if missing), creates a
       bare renv project, installs the required Bioconductor packages and
       snapshots the environment.

    Parameters
    ----------
    project_dir:
        Path to the root of the project.  ``renv.lock`` will be placed
        directly inside this directory.
    """
    project_dir = project_dir.resolve()
    renv_lock_path = project_dir / "renv.lock"

    # 1️⃣ Write a default lock file if necessary
    if not renv_lock_path.is_file():
        lock_content = _default_lock_content()
        renv_lock_path.write_text(json.dumps(lock_content, indent=2))
        print(f"[init_r_environment] Created default renv.lock at {renv_lock_path}")

    # 2️⃣ Build the R bootstrap script
    r_commands: List[str] = [
        # Install renv if it is not available
        'if (!requireNamespace("renv", quietly = TRUE)) {',
        '  install.packages("renv", repos = "https://cloud.r-project.org")',
        '}',
        # Initialise a bare renv project (no automatic package detection)
        'renv::init(bare = TRUE, restore = FALSE)',
        # Install the required Bioconductor packages
        'pkgs <- c("DESeq2", "org.At.tair.db", "biomaRt", "sva", "GEOquery")',
        'renv::install(pkgs)',
        # Snapshot the environment so that renv.lock is up‑to‑date
        'renv::snapshot()',
    ]

    # Join commands with semicolons so they can be passed as a single -e argument
    r_script = "; ".join(r_commands)

    # Run the R script
    try:
        subprocess.run(
            ["R", "--vanilla", "-e", r_script],
            cwd=str(project_dir),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print("[init_r_environment] renv environment initialised successfully.")
    except subprocess.CalledProcessError as exc:
        # Propagate a clear error that includes R's output for debugging
        raise RuntimeError(
            f"R script failed with exit code {exc.returncode}\\n"
            f"STDOUT:\\n{exc.stdout}\\nSTDERR:\\n{exc.stderr}"
        ) from exc
    except FileNotFoundError as exc:
        # ``R`` binary not found – give a helpful message
        raise FileNotFoundError(
            "The R executable was not found on the PATH. "
            "Please install R (>= 4.3) before running init_r_environment."
        ) from exc


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Command‑line interface for ``init_r_environment``.

    Usage
    -----
    python -m code.init_r_environment [--project-dir PATH]

    Options
    -------
    --project-dir PATH   Path to the project root (default: current working directory)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialise an R renv environment with the required Bioconductor packages."
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="Path to the project root (default: current working directory).",
    )
    args = parser.parse_args()
    project_path = Path(args.project_dir)
    initialize_renv(project_path)


if __name__ == "__main__":
    main()
