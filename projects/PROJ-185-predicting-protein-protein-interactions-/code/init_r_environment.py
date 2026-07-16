"""Initialize an R environment with renv and install required Bioconductor packages.

This script performs the following steps:
1. Ensures the `renv` package is available in R.
2. Initializes a renv project in the repository root (if not already initialized).
3. Installs the Bioconductor packages required for the pipeline:
   - DESeq2
   - org.At.tair.db
   - biomaRt
   - sva
   - GEOquery
4. Snapshots the environment, producing a `renv.lock` file.

The script is intentionally minimal and relies on the system having R (>=4.0) and
internet access. It will raise an exception if any step fails, ensuring that
downstream tasks can detect a missing or incomplete R environment.
"""

import subprocess
import sys
from pathlib import Path
import json

# List of Bioconductor packages required by the project
REQUIRED_PACKAGES = [
    "DESeq2",
    "org.At.tair.db",
    "biomaRt",
    "sva",
    "GEOquery",
]


def _run_r_command(command: str) -> None:
    """Execute an R command via subprocess.

    Args:
        command: The R expression to evaluate (passed to `R -e`).

    Raises:
        RuntimeError: If the R subprocess exits with a non‑zero status.
    """
    # Use `Rscript` for better handling of non‑interactive sessions
    proc = subprocess.run(
        ["Rscript", "-e", command],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"R command failed with exit code {proc.returncode}\\n"
            f"STDOUT:\\n{proc.stdout}\\nSTDERR:\\n{proc.stderr}"
        )
    # Optionally, print R output for debugging (can be silenced later)
    print(proc.stdout)


def initialize_renv(project_root: Path) -> None:
    """Initialize renv in the given directory and install required packages.

    Args:
        project_root: Path to the repository root where `renv.lock` will live.

    Raises:
        RuntimeError: If any step of the initialization fails.
    """
    # Step 1: Ensure renv is installed
    _run_r_command(
        "if (!requireNamespace('renv', quietly = TRUE)) "
        "install.packages('renv', repos = 'https://cloud.r-project.org')"
    )

    # Step 2: Initialize renv (creates renv folder and renv.lock if missing)
    _run_r_command(
        f"setwd('{project_root.as_posix()}'); "
        "if (!file.exists('renv.lock')) renv::init(bare = TRUE) else renv::load()"
    )

    # Step 3: Install required Bioconductor packages
    packages_str = ', '.join([f'\"{pkg}\"' for pkg in REQUIRED_PACKAGES])
    _run_r_command(
        f"setwd('{project_root.as_posix()}'); "
        f"renv::install(c({packages_str}), repos = BiocManager::repositories())"
    )

    # Step 4: Snapshot the environment to update renv.lock
    _run_r_command(
        f"setwd('{project_root.as_posix()}'); renv::snapshot(prompt = FALSE)"
    )

    # Verify that renv.lock now contains the required packages
    lock_path = project_root / "renv.lock"
    if not lock_path.is_file():
        raise RuntimeError("renv.lock was not created after snapshot.")
    try:
        with lock_path.open() as f:
            lock_data = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse renv.lock: {exc}") from exc

    missing = [
        pkg for pkg in REQUIRED_PACKAGES if pkg not in lock_data.get("Packages", {})
    ]
    if missing:
        raise RuntimeError(
            f"The following required packages are missing from renv.lock: {missing}"
        )
    print(f"renv environment successfully initialized at {project_root}")


def main() -> None:
    """Entry point for the script.

    The repository root is assumed to be two levels up from this file
    (i.e., `code/` -> project root).
    """
    project_root = Path(__file__).resolve().parents[1]
    try:
        initialize_renv(project_root)
    except Exception as exc:
        print(f"Error initializing R environment: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
