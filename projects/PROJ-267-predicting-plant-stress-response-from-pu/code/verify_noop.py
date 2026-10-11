"""
Script to verify that the project skeleton's noop stage executes successfully.
It runs `python -m code.main --stage noop`, captures the output,
writes a log file under the logs directory, and exits with a non‑zero
status if the command fails. This provides the required execution
evidence for task T001.
"""
import sys
import subprocess
from pathlib import Path

# Import the toolkit's path helper and logger
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Execute the noop stage of the pipeline and record the result.
    """
    # Build the command to run the main module with the noop stage
    cmd = [sys.executable, "-m", "code.main", "--stage", "noop"]
    log.info(f"Running command: {' '.join(cmd)}")

    # Run the command, capturing stdout and stderr
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    # Determine the log file path inside the project logs directory
    log_file = paths.logs("noop_test.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Write detailed information about the execution
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Return code: {result.returncode}\\n")
        f.write("=== STDOUT ===\\n")
        f.write(result.stdout or "")
        f.write("\\n=== STDERR ===\\n")
        f.write(result.stderr or "")

    # Log a summary
    if result.returncode == 0:
        log.info("Noop stage completed successfully (exit code 0).")
    else:
        log.error(
            f"Noop stage failed with exit code {result.returncode}. "
            "See logs/noop_test.log for details."
        )
        # Propagate the failure to the caller
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()