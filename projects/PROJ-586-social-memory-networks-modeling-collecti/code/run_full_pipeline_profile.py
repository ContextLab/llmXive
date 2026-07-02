"""Run the complete experiment pipeline while profiling runtime, memory and disk usage.

The script orchestrates the three experiment configurations required by the
project:

* Full‑context simulation (default)
* Limited‑context simulation
* Scaling analysis across agent counts (3, 5, 7)

After each sub‑run the script records:

* Wall‑clock time (seconds)
* Peak resident memory (MiB)
* Disk usage of the project directory (MiB)

All measurements are written to a CSV file in the project‑level
``results/`` directory so that the CI job can inspect them.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def get_memory_usage_mb() -> float:
    """Return the current resident set size (RSS) in megabytes."""
    # ``resource`` is Unix‑only; fall back to ``psutil`` if available.
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux ru_maxrss is in KiB, on macOS it is in bytes.
        if sys.platform.startswith("linux"):
            return usage / 1024.0
        return usage / (1024.0 * 1024.0)
    except Exception:
        try:
            import psutil

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024.0 * 1024.0)
        except Exception:
            # As a last resort return 0 – the caller can still record runtime.
            return 0.0


def get_disk_usage_mb(path: Path) -> float:
    """Return the total disk usage (in MiB) of *path*."""
    usage = shutil.disk_usage(str(path))
    total_bytes = usage.total
    return total_bytes / (1024.0 * 1024.0)


def run_experiment_script(args: List[str]) -> Tuple[float, float]:
    """Run ``code/run_experiment.py`` with *args* and return (runtime, mem)."""
    start = time.time()
    # Use the same Python interpreter that is executing this script.
    cmd = [sys.executable, "code/run_experiment.py"] + args
    subprocess.run(cmd, check=True)
    elapsed = time.time() - start
    mem = get_memory_usage_mb()
    return elapsed, mem


# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #

def run_full_pipeline() -> List[dict]:
    """Execute all experiment configurations and collect profiling data."""
    results: List[dict] = []

    # 1. Full‑context baseline (5 agents, 1000 games)
    elapsed, mem = run_experiment_script(
        ["--context", "full", "--agents", "5", "--games", "1000"]
    )
    results.append(
        {
            "step": "full_context",
            "runtime_seconds": round(elapsed, 2),
            "peak_memory_mb": round(mem, 2),
        }
    )

    # 2. Limited‑context baseline (5 agents, 1000 games)
    elapsed, mem = run_experiment_script(
        ["--context", "limited", "--agents", "5", "--games", "1000"]
    )
    results.append(
        {
            "step": "limited_context",
            "runtime_seconds": round(elapsed, 2),
            "peak_memory_mb": round(mem, 2),
        }
    )

    # 3. Scaling analysis (agent counts 3,5,7; 800 games each)
    elapsed, mem = run_experiment_script(
        [
            "--context",
            "full",
            "--agents",
            "3,5,7",
            "--games",
            "800",
            "--plot",
            "scaling",
        ]
    )
    results.append(
        {
            "step": "scaling_analysis",
            "runtime_seconds": round(elapsed, 2),
            "peak_memory_mb": round(mem, 2),
        }
    )

    # Record overall disk usage once at the end.
    project_root = Path(__file__).parents[1]  # projects/PROJ-586-...
    disk_mb = round(get_disk_usage_mb(project_root), 2)
    for entry in results:
        entry["disk_usage_mb"] = disk_mb

    return results


def save_results_csv(results: List[dict], output_path: Path) -> None:
    """Write the profiling data to ``results/profile_summary.csv``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["step", "runtime_seconds", "peak_memory_mb", "disk_usage_mb"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        import csv

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full experiment pipeline and record resource usage."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/profile_summary.csv",
        help="Path to the CSV file that will contain the profiling summary.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    results = run_full_pipeline()
    save_results_csv(results, Path(args.output))
    # Also emit a JSON version for easier downstream consumption.
    json_path = Path(str(args.output)).with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(results, indent=2))
    print(f"Profiling results written to {args.output} (and {json_path})")


if __name__ == "__main__":
    main()
