"""
Full‑pipeline performance recorder.

This script orchestrates the execution of the project's primary
experiment scripts, measures runtime, peak memory usage and disk
consumption, and writes a JSON summary to the project's ``results``
directory.

It is deliberately lightweight and relies only on the Python
standard library (``resource`` for memory, ``subprocess`` for
invoking other scripts, and ``os``/``pathlib`` for filesystem
operations) so that it can run on the CI runner without additional
dependencies.
"""

import argparse
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_command(cmd: List[str]) -> None:
    """Execute a command via ``subprocess.run`` and raise on failure."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print("STDOUT:", result.stdout, file=sys.stderr)
        print("STDERR:", result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

def _measure_disk_usage(path: Path) -> float:
    """Return total disk usage of ``path`` in megabytes."""
    total_bytes = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total_bytes / (1024 * 1024)

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full experiment pipeline and record performance metrics."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
        ),
        help="Directory where performance JSON will be written.",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Record start time and baseline memory usage
    start_time = time.time()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)

    # ------------------------------------------------------------------
    # Step 1: Run full‑context experiment (baseline)
    # ------------------------------------------------------------------
    _run_command([sys.executable, "code/run_experiment.py",
                  "--context", "full",
                  "--agents", "5",
                  "--games", "200"])  # reduced games for CI speed

    # ------------------------------------------------------------------
    # Step 2: Run limited‑context experiment
    # ------------------------------------------------------------------
    _run_command([sys.executable, "code/run_experiment.py",
                  "--context", "limited",
                  "--agents", "5",
                  "--games", "200"])

    # ------------------------------------------------------------------
    # Step 3: Run scaling analysis (agent counts 3,5,7)
    # ------------------------------------------------------------------
    _run_command([sys.executable, "code/run_experiment.py",
                  "--context", "full",
                  "--agents", "3,5,7",
                  "--games", "100",
                  "--plot", "scaling"])

    # ------------------------------------------------------------------
    # Step 4: Run statistical analyses (ANOVA, power, scaling)
    # ------------------------------------------------------------------
    _run_command([sys.executable, "code/analysis/anova.py"])
    _run_command([sys.executable, "code/analysis/power.py"])
    _run_command([sys.executable, "code/analysis/scaling.py"])

    # Record end time and memory usage
    end_time = time.time()
    usage_end = resource.getrusage(resource.RUSAGE_SELF)

    # Compute metrics
    runtime_seconds = end_time - start_time
    # Peak memory (max resident set size) is given in kilobytes on Linux
    peak_memory_kb = max(usage_start.ru_maxrss, usage_end.ru_maxrss)
    peak_memory_mb = peak_memory_kb / 1024.0

    disk_usage_mb = _measure_disk_usage(args.output_dir)

    performance = {
        "runtime_seconds": round(runtime_seconds, 2),
        "peak_memory_mb": round(peak_memory_mb, 2),
        "disk_usage_mb": round(disk_usage_mb, 2),
    }

    # Write JSON file
    out_path = args.output_dir / "pipeline_performance.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(performance, f, indent=2)

    print(f"Pipeline performance written to {out_path}")

if __name__ == "__main__":
    main()
