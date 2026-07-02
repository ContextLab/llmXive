"""Run the full experiment pipeline and record resource usage.

This script is the entry point for task **T035**.  It executes the full
pipeline (by delegating to ``run_full_pipeline.main``), measures wall‑clock
time, peak memory consumption and the size of the results directory, and
writes those measurements to the project ``results`` folder.

The implementation relies only on the Python standard library, keeping the
CI environment lightweight.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

# Import the existing pipeline entry point.
from run_full_pipeline import main as run_pipeline_main

__all__ = ["get_memory_usage_mb", "get_disk_usage_mb", "run_and_profile", "build_parser", "main"]


def get_memory_usage_mb() -> float:
    """Return the current process memory usage in megabytes.

    On Unix we can read ``/proc/self/status``; on other platforms we fall back
    to ``resource.getrusage`` which reports memory in kilobytes.
    """
    try:
        # Linux /proc
        with open("/proc/self/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    # VmRSS value is in kB
                    kb = int(parts[1])
                    return kb / 1024.0
    except FileNotFoundError:
        pass

    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux, bytes on macOS
        factor = 1 / 1024.0 if os.uname().sysname == "Linux" else 1 / (1024.0 * 1024.0)
        return usage.ru_maxrss * factor
    except Exception:
        return 0.0


def get_disk_usage_mb(path: Path) -> float:
    """Return the total size of ``path`` (including sub‑directories) in MB."""
    total_bytes = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_bytes += os.path.getsize(fp)
            except OSError:
                pass
    return total_bytes / (1024.0 * 1024.0)


def run_and_profile(output_dir: Path) -> dict:
    """Execute the full pipeline and collect resource statistics.

    The function returns a dictionary with ``runtime_s``, ``memory_mb`` and
    ``disk_mb`` keys.
    """
    start = time.time()
    # Run the full experiment pipeline.
    run_pipeline_main()
    end = time.time()

    runtime_s = end - start
    memory_mb = get_memory_usage_mb()
    disk_mb = get_disk_usage_mb(output_dir)

    return {
        "runtime_s": runtime_s,
        "memory_mb": memory_mb,
        "disk_mb": disk_mb,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full pipeline and record runtime/memory/disk usage."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parents[2] / "results",
        help="Directory where resource usage files will be written.",
    )
    return parser


def main() -> None:
    """Entry point for the CI runner."""
    parser = build_parser()
    args = parser.parse_args()

    # Ensure the output directory exists.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    stats = run_and_profile(args.output_dir)

    # Write each statistic to its own file for easy downstream consumption.
    (args.output_dir / "runtime_seconds.txt").write_text(f"{stats['runtime_s']:.2f}\\n")
    (args.output_dir / "memory_mb.txt").write_text(f"{stats['memory_mb']:.2f}\\n")
    (args.output_dir / "disk_mb.txt").write_text(f"{stats['disk_mb']:.2f}\\n")

    # Also emit a combined JSON summary (convenient for CI logs).
    summary_path = args.output_dir / "resource_usage.json"
    summary_path.write_text(json.dumps(stats, indent=2))

    print(f"Resource usage written to {args.output_dir}")


if __name__ == "__main__":
    main()