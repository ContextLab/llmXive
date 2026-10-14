"""Verify R renv environment restoration.

This script ensures that the R environment can be restored using the
project's `renv.lock` file. It identifies the available R executable,
installs the `renv` package if missing, and executes `renv::restore()`.
"""

import subprocess
import sys
import shutil
from pathlib import Path
from llmxive_toolkit import paths, get_logger

# Initialise logger
log = get_logger(__name__)

# Path for the verification log
log_path: Path = paths.logs("renv_restore.log")

def main() -> None:
    """Execute R renv restoration and record the outcome."""
    # 1. Find the R executable (try 'R' then 'Rscript')
    r_exec = shutil.which("R") or shutil.which("Rscript")
    if not r_exec:
        msg = "R executable not found in PATH. Please ensure R is installed."
        log.error(msg)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(msg)
        sys.exit(1)
    
    # 2. Ensure renv.lock exists at the project root (where renv::restore looks)
    lock_file = Path("renv.lock")
    if not lock_file.exists():
        # Fallback: if it's in code/R/, copy it to root
        alt_lock = Path("code/R/renv.lock")
        if alt_lock.exists():
            shutil.copy(alt_lock, lock_file)
        else:
            msg = "renv.lock not found at root or code/R/."
            log.error(msg)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(msg)
            sys.exit(1)

    # 3. Run the restoration command
    # We install renv first if it's not available, then call restore()
    # prompt = FALSE is critical for non-interactive CI environments
    r_cmd = "if (!require('renv', quietly = TRUE)) install.packages('renv', repos='https://cloud.r-project.org'); renv::restore(prompt = FALSE)"
    cmd = [r_exec, "-e", r_cmd]
    
    try:
        log.info(f"Attempting R renv restoration using {r_exec}...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=550
        )
        # Log success
        log.info("R renv restore succeeded.")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(result.stdout + "\n" + result.stderr)

    except subprocess.CalledProcessError as e:
        log.error(f"R renv restore failed with exit code {e.returncode}.")
        log.error(e.stderr or "")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text((e.stdout or "") + "\n" + (e.stderr or ""))
        sys.exit(1)
    except subprocess.TimeoutExpired:
        log.error("R renv restore timed out.")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("Error: Timeout expired during renv::restore()")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error during R restoration: {e}")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()