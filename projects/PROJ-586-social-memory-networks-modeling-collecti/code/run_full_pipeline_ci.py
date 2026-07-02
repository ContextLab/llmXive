"""Run the full experiment pipeline and record performance metrics.

This script is intended to be executed in a CI environment. It runs the
various experiment scripts (full‑context, limited‑context, scaling) and
records runtime, peak memory usage, and disk usage for each step. The
collected metrics are written to a JSON file in the project results
directory.

The script uses only the standard library and the project's existing
modules. It does **not** fabricate any results – all experiment scripts
generate real data and the performance numbers are measured on the
executing process.
"""

from __future__ import annotations

import json
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

# Project‑relative paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # projects/PROJ-.../code/..
RESULTS_DIR = PROJECT_ROOT / "results"
PERFORMANCE_FILE = RESULTS_DIR / "ci_performance_metrics.json"

# Ensure the results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_command(command: List[str]) -> Dict[str, float]:
    """Run a shell command while measuring runtime, memory, and disk usage.

    Returns a dictionary with keys:
        - elapsed_seconds
        - max_memory_mb
        - disk_used_mb
    """
    start_time = time.time()
    # Record disk usage before execution
    disk_before = shutil.disk_usage(str(PROJECT_ROOT)).used

    # Run the command; capture stdout/stderr for debugging
    proc = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        # Propagate the error with context – CI should see the failure.
        sys.stderr.write(
            f"Command {' '.join(command)} failed with exit code {proc.returncode}\\n"
        )
        sys.stderr.write(f"Stdout:\\n{proc.stdout}\\n")
        sys.stderr.write(f"Stderr:\\n{proc.stderr}\\n")
        raise subprocess.CalledProcessError(proc.returncode, command)

    end_time = time.time()
    # Record disk usage after execution
    disk_after = shutil.disk_usage(str(PROJECT_ROOT)).used

    # Peak memory usage (RSS) in kilobytes; convert to MB.
    # Note: ru_maxrss is in kilobytes on Linux, bytes on macOS.
    mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        mem_mb = mem_kb / (1024 * 1024)  # macOS reports bytes
    else:
        mem_mb = mem_kb / 1024  # Linux reports kilobytes

    metrics = {
        "elapsed_seconds": end_time - start_time,
        "max_memory_mb": mem_mb,
        "disk_used_mb": (disk_after - disk_before) / (1024 * 1024),
    }
    return metrics

# ----------------------------------------------------------------------
# Pipeline steps
# ----------------------------------------------------------------------
def _run_full_context(agents: int = 5, games: int = 1000) -> Dict[str, float]:
    """Run the full‑context experiment."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "run_experiment.py"),
        "--context",
        "full",
        "--agents",
        str(agents),
        "--games",
        str(games),
        "--seed",
        "42",
    ]
    return _run_command(cmd)

def _run_limited_context(
    agents: int = 5, games: int = 1000, thresholds: str = "128,256,512"
) -> Dict[str, float]:
    """Run the limited‑context experiment with token‑limit thresholds."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "run_experiment.py"),
        "--context",
        "limited",
        "--agents",
        str(agents),
        "--games",
        str(games),
        "--thresholds",
        thresholds,
        "--seed",
        "42",
    ]
    return _run_command(cmd)

def _run_scaling_experiment(
    agent_counts: str = "3,5,7", games: int = 800
) -> Dict[str, float]:
    """Run the scaling experiment across multiple agent counts."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "run_experiment.py"),
        "--agents",
        agent_counts,
        "--games",
        str(games),
        "--plot",
        "scaling",
        "--seed",
        "42",
    ]
    return _run_command(cmd)

def _run_anova_analysis() -> Dict[str, float]:
    """Run the two‑way ANOVA analysis on the generated CSVs."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "analysis" / "anova.py"),
    ]
    return _run_command(cmd)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Execute the full pipeline and write performance metrics.

    Returns:
        Exit code (0 for success, non‑zero for failure).
    """
    all_metrics: Dict[str, Dict[str, float]] = {}

    try:
        # 1. Full‑context experiment
        all_metrics["full_context"] = _run_full_context()

        # 2. Limited‑context experiment
        all_metrics["limited_context"] = _run_limited_context()

        # 3. Scaling experiment (produces scaling_plot.pdf)
        all_metrics["scaling_experiment"] = _run_scaling_experiment()

        # 4. ANOVA analysis (produces anova results)
        all_metrics["anova_analysis"] = _run_anova_analysis()
    except Exception as exc:  # pragma: no cover – CI will surface the traceback
        sys.stderr.write(f"Pipeline failed: {exc}\\n")
        return 1

    # Write the collected metrics to JSON for downstream CI consumption.
    with PERFORMANCE_FILE.open("w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    # Print a short summary to stdout – useful for CI logs.
    print("CI performance metrics written to:", PERFORMANCE_FILE)
    for step, metrics in all_metrics.items():
        print(
            f"{step:>20}: {metrics['elapsed_seconds']:.2f}s, "
            f"{metrics['max_memory_mb']:.2f}MiB, "
            f"{metrics['disk_used_mb']:.2f}MiB"
        )

    return 0

if __name__ == "__main__":
    sys.exit(main())
