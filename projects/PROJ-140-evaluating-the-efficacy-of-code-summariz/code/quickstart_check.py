"""
Quickstart verification script.

This script runs the project's entry point module with the ``--mode sim``
and ``--help`` flags to ensure that the CLI is correctly defined and that
it exits with status 0. The stdout and stderr of the command are written
to ``data/quickstart_check.log`` for evidence.
"""
import subprocess
import sys
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Execute ``python -m code.main --mode sim --help`` and record its output.
    """
    cmd = [sys.executable, "-m", "code.main", "--mode", "sim", "--help"]
    log.info("Running quickstart command: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    # Log command output for debugging
    log.debug("Quickstart stdout:\n%s", result.stdout)
    log.debug("Quickstart stderr:\n%s", result.stderr)

    # Write combined output to a file under the data directory
    output_path = paths.data("quickstart_check.log")
    output_path.write_text(result.stdout + "\n" + result.stderr)

    # Exit with the same return code as the subprocess to reflect success/failure
    if result.returncode != 0:
        log.error(
            "Quickstart verification failed with exit code %d", result.returncode
        )
    else:
        log.info("Quickstart verification succeeded (exit code 0)")

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
