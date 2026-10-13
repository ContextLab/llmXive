"""Verify R renv environment restoration.

This script runs the R command `renv::restore()` to install the R
packages listed in `code/R/renv.lock`. It captures stdout and stderr,
logs them via the project's logger, and writes the combined output
to a log file under the `logs/` directory.

The existence of this script and its successful execution provide the
required evidence that `R -e "renv::restore()"` completes without error.
"""

import subprocess
import sys
from pathlib import Path

# Project utilities
from llmxive_toolkit import paths, get_logger

# Initialise logger
log = get_logger(__name__)

# Path for the verification log
log_path: Path = paths.logs("renv_restore.log")
log_path.parent.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Execute `R -e "renv::restore()"` and record the outcome."""
    cmd = ["R", "-e", "renv::restore()"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        # Log success and output
        log.info("R renv restore succeeded.")
        log.info(result.stdout)
        if result.stderr:
            log.warning("R renv restore produced warnings/stderr.")
            log.warning(result.stderr)

        # Write combined output to the log file for verification
        log_path.write_text(result.stdout + "\n" + result.stderr)

    except subprocess.CalledProcessError as e:
        # Log failure details
        log.error("R renv restore failed with non‑zero exit code.")
        log.error(e.stdout or "")
        log.error(e.stderr or "")
        # Write failure output to the log file
        log_path.write_text((e.stdout or "") + "\n" + (e.stderr or ""))
        # Propagate error to make the script exit with failure
        sys.exit(1)

if __name__ == "__main__":
    main()
