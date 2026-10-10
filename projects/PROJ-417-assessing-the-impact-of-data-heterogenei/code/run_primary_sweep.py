"""
Run the Primary Simulation Sweep.

This script invokes the main pipeline with the full
configuration (5 heterogeneity levels, 500 replicates each)
and records basic runtime information. The resulting
`data/results/simulation_raw.json` must contain at least
2 500 replicate records, satisfying the verification
requirement for task T006.

The script is deliberately lightweight: it spawns the
existing `code/main.py` entry‑point via a subprocess, so
all pipeline logic remains unchanged. After the subprocess
finishes, the script writes a simple runtime log containing
the wall‑clock duration and an approximate peak memory
usage (via the `resource` module on Unix platforms). This
log is stored at `data/results/runtime_logs.txt`, which
can be inspected to confirm the < 6 h and < 7 GB RAM
constraints.
"""

import subprocess
import sys
import time
import json
import os
from pathlib import Path

# Standard library `resource` works on Unix; on non‑Unix platforms we
# fall back to a placeholder (the CI runner is Linux‑based).
try:
    import resource
except ImportError:  # pragma: no cover
    resource = None

def _run_main() -> int:
    """
    Execute the pipeline's main entry point with full‑sweep arguments.

    Returns the subprocess exit code.
    """
    cmd = [
        sys.executable,
        str(Path("code") / "main.py"),
        "--mode",
        "full",
        "--seed",
        "42",
    ]
    # Inherit stdout/stderr so any errors are visible in CI logs.
    result = subprocess.run(cmd, check=False)
    return result.returncode

def _record_runtime(start: float, end: float) -> None:
    """
    Write a minimal runtime log.

    The log contains:
      - start time (ISO‑8601)
      - end time (ISO‑8601)
      - elapsed seconds
      - peak memory (RSS in MB) if available
    """
    log_path = Path("data") / "results" / "runtime_logs.txt"
    elapsed = end - start

    log = {
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(start)),
        "end_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(end)),
        "elapsed_seconds": elapsed,
    }

    if resource is not None:
        # ru_maxrss is in kilobytes on Linux.
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        log["peak_memory_mb"] = mem_kb / 1024.0

    # Ensure the output directory exists.
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    print(f"Runtime log written to {log_path}")

def main() -> None:
    """
    Orchestrate the primary sweep execution and verification.
    """
    start_time = time.time()
    exit_code = _run_main()
    end_time = time.time()

    _record_runtime(start_time, end_time)

    if exit_code != 0:
        sys.exit(
            f"Primary sweep failed with exit code {exit_code}. "
            "Check the pipeline output for details."
        )

    # Verify that the simulation output has the expected minimum size.
    sim_path = Path("data") / "results" / "simulation_raw.json"
    if not sim_path.exists():
        sys.exit("ERROR: simulation_raw.json was not created.")

    try:
        with open(sim_path, "r", encoding="utf-8") as f:
            sim_data = json.load(f)
    except Exception as exc:  # pragma: no cover
        sys.exit(f"ERROR: Failed to load simulation_raw.json: {exc}")

    replicates = sim_data.get("replicates", [])
    if len(replicates) < 2500:
        sys.exit(
            f"ERROR: Expected at least 2500 replicates, found {len(replicates)}."
        )

    print(
        f"Primary sweep completed successfully with {len(replicates)} replicates."
    )

if __name__ == "__main__":
    main()
