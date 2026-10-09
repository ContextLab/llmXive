"""Validate the Quickstart script.

This script runs the project's CI sanity‑check script (`scripts/run-ci.sh`)
end‑to‑end, captures its exit code and output, and writes a concise log
file to `logs/quickstart_validation.log`.  The log contains a timestamp,
the exit code, and the combined stdout/stderr of the CI run.

The script is intended to be invoked directly (e.g. `python
scripts/validate_quickstart.py`).  It exits with the same status as the
underlying `run-ci.sh` so that CI pipelines can treat a failure as a
hard error.
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def main() -> int:
    # Resolve paths relative to the repository root
    repo_root = Path(__file__).resolve().parent.parent
    run_ci_path = repo_root / "scripts" / "run-ci.sh"
    log_path = repo_root / "logs" / "quickstart_validation.log"

    # Ensure the log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Execute the CI script
    try:
        result = subprocess.run(
            ["bash", str(run_ci_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except Exception as exc:  # pragma: no cover – unexpected failure
        log_path.write_text(
            f"{datetime.utcnow().isoformat()}Z - Exception while running run-ci.sh: {exc}\n"
        )
        return 1

    # Write detailed log
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_content = (
        f"{timestamp} - run-ci.sh exit code: {result.returncode}\n"
        f"{'-'*80}\n"
        f"{result.stdout}\n"
        f"{'-'*80}\n"
    )
    log_path.write_text(log_content)

    # Propagate the exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())