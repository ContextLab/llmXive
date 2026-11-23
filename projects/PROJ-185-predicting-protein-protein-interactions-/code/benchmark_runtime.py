"""
Benchmark Runtime Script
========================

This script runs the full pipeline using the ``make all`` target,
measures the wall‑clock execution time, and writes the result to
``results/benchmark_report.txt``.  If the total runtime exceeds the
allowed maximum of six hours (21600 seconds) the script exits with a
non‑zero status code, causing CI to fail.

The script is intended to be used as a CI step (e.g. in a GitHub
Actions workflow) but can also be executed locally for quick checks.
"""

import subprocess
import sys
import time
from pathlib import Path

# Maximum allowed runtime in seconds (6 hours)
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 21600

def run_make_all() -> float:
    """Execute ``make all`` and return the elapsed time in seconds.

    Returns
    -------
    float
        Elapsed wall‑clock time.
    """
    start = time.time()
    # ``make`` may produce a lot of output; capture it to avoid cluttering CI logs.
    # ``check=True`` will raise a CalledProcessError if the command fails.
    subprocess.run(
        ["make", "all"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = time.time() - start
    return elapsed

def write_report(elapsed: float) -> None:
    """Write the benchmark report to ``results/benchmark_report.txt``."""
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "benchmark_report.txt"
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"runtime_seconds: {elapsed:.2f}\\n")
    # Also print to stdout for visibility in CI logs.
    print(f"Benchmark runtime: {elapsed:.2f} seconds (written to {report_path})")

def main() -> None:
    try:
        elapsed = run_make_all()
    except subprocess.CalledProcessError as e:
        print("Error: ``make all`` failed.", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)

    write_report(elapsed)

    if elapsed > MAX_RUNTIME_SECONDS:
        print(
            f"Error: Runtime {elapsed:.2f}s exceeds the maximum allowed "
            f"{MAX_RUNTIME_SECONDS}s (6 hours).",
            file=sys.stderr,
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
