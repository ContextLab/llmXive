"""Run the full experiment pipeline in a CI‑like environment and record
performance statistics (runtime, memory, disk usage).

The script executes the full‑context and limited‑context experiments,
measures the elapsed wall‑clock time, maximum resident set size (memory),
and disk usage of the project directory, then writes a JSON report to the
results folder.
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

from utils.logging import get_logger, log_operation


LOGGER = get_logger(__name__)


@log_operation
def run_experiment_cli(context: str, agents: str, games: int, output_dir: Path) -> Path:
    """Invoke `run_experiment.py` via a subprocess and return the path to the CSV."""
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_experiment.py"),
        "--context",
        context,
        "--agents",
        agents,
        "--games",
        str(games),
        "--output-dir",
        str(output_dir),
    ]
    subprocess.check_call(cmd)
    return output_dir / f"results_{context}.csv"


def gather_performance(start_time: float, start_mem: resource.struct_rusage) -> dict:
    """Collect runtime, memory, and disk usage."""
    elapsed = time.time() - start_time
    end_mem = resource.getrusage(resource.RUSAGE_SELF)
    # Maximum resident set size (in kilobytes on Linux)
    max_rss_kb = max(start_mem.ru_maxrss, end_mem.ru_maxrss)
    # Disk usage of the project root
    total, used, free = shutil.disk_usage(str(Path.cwd()))
    return {
        "runtime_seconds": elapsed,
        "max_rss_kb": max_rss_kb,
        "disk_total_gb": total / (1024 ** 3),
        "disk_used_gb": used / (1024 ** 3),
        "disk_free_gb": free / (1024 ** 3),
    }


def main() -> int:
    results_dir = Path(
        "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
    )
    results_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    start_mem = resource.getrusage(resource.RUSAGE_SELF)

    # Run full‑context experiment
    run_experiment_cli(
        context="full",
        agents="5",
        games=100,
        output_dir=results_dir,
    )

    # Run limited‑context experiment
    run_experiment_cli(
        context="limited",
        agents="5",
        games=100,
        output_dir=results_dir,
    )

    performance = gather_performance(start_time, start_mem)

    report_path = results_dir / "pipeline_performance.json"
    with report_path.open("w") as f:
        json.dump(performance, f, indent=2)

    LOGGER.info("Pipeline performance written to %s", report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
