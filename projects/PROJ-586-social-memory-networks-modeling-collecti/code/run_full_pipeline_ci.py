"""CI Pipeline Runner with Resource Profiling.

Executes the full research pipeline on a CI runner environment and records
runtime, memory usage, and disk usage statistics.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# Ensure the project root is in the path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "results"


def get_memory_usage_mb() -> float:
    """Get current memory usage of the process in MB."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS (sometimes), check platform
        if sys.platform == "darwin":
            return usage.ru_maxrss / (1024 * 1024)
        return usage.ru_maxrss / 1024.0
    except Exception:
        # Fallback to psutil if resource module is unavailable or inconsistent
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)


def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of the specified path in MB."""
    if not path.exists():
        return 0.0
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            try:
                total_size += filepath.stat().st_size
            except (OSError, PermissionError):
                continue
    return total_size / (1024 * 1024)


def run_and_profile(
    script: str,
    args: List[str],
    output_dir: Path,
    description: str = "Pipeline Step"
) -> Dict[str, Any]:
    """Run a script and profile its resource usage.

    Args:
        script: Path to the Python script to run.
        args: List of command line arguments.
        output_dir: Directory to store output files.
        description: Description of the step for logging.

    Returns:
        Dictionary containing execution statistics.
    """
    start_time = time.time()
    start_mem = get_memory_usage_mb()
    start_disk = get_disk_usage_mb(output_dir) if output_dir.exists() else 0.0

    cmd = [sys.executable, str(script)] + args
    print(f"[CI] Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=3600  # 1 hour timeout for CI safety
    )

    end_time = time.time()
    end_mem = get_memory_usage_mb()
    end_disk = get_disk_usage_mb(output_dir) if output_dir.exists() else 0.0

    duration = end_time - start_time
    peak_mem = max(start_mem, end_mem)
    disk_delta = end_disk - start_disk

    stats = {
        "description": description,
        "command": " ".join(cmd),
        "duration_seconds": round(duration, 2),
        "start_memory_mb": round(start_mem, 2),
        "peak_memory_mb": round(peak_mem, 2),
        "start_disk_mb": round(start_disk, 2),
        "end_disk_mb": round(end_disk, 2),
        "disk_delta_mb": round(disk_delta, 2),
        "return_code": result.returncode,
        "stdout_lines": len(result.stdout.splitlines()),
        "stderr_lines": len(result.stderr.splitlines()),
        "success": result.returncode == 0
    }

    if result.returncode != 0:
        stats["error"] = result.stderr[:500]  # Truncate error message
        print(f"[CI] ERROR: {description} failed with code {result.returncode}")
        print(result.stderr)
    else:
        print(f"[CI] SUCCESS: {description} completed in {duration:.2f}s")

    return stats


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CI runner."""
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI and record metrics."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(RESULTS_DIR),
        help="Directory to store results and logs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing."
    )
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="limited",
        help="Context condition for experiments."
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents for experiments."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,  # Reduced for CI speed, real data still generated
        help="Number of games to simulate."
    )
    return parser


def main() -> int:
    """Main entry point for CI pipeline execution."""
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"ci_run_report_{timestamp}.json"
    log_path = output_dir / f"ci_run_log_{timestamp}.txt"

    all_stats: List[Dict[str, Any]] = []
    overall_start = time.time()
    overall_start_mem = get_memory_usage_mb()
    overall_start_disk = get_disk_usage_mb(output_dir)

    print(f"[CI] Starting pipeline run at {datetime.utcnow().isoformat()}")
    print(f"[CI] Output directory: {output_dir}")

    # Step 1: Run Full Context Experiment (US-1)
    # Note: Reduced game count for CI efficiency while maintaining real measurement
    stats_full = run_and_profile(
        script=str(PROJECT_ROOT / "code" / "run_experiment.py"),
        args=[
            "--context", "full",
            "--agents", str(args.agents),
            "--games", str(args.games),
            "--output-dir", str(output_dir)
        ],
        output_dir=output_dir,
        description="Full Context Experiment (US-1)"
    )
    all_stats.append(stats_full)

    # Step 2: Run Limited Context Experiment (US-2)
    stats_limited = run_and_profile(
        script=str(PROJECT_ROOT / "code" / "run_experiment.py"),
        args=[
            "--context", "limited",
            "--agents", str(args.agents),
            "--games", str(args.games),
            "--output-dir", str(output_dir)
        ],
        output_dir=output_dir,
        description="Limited Context Experiment (US-2)"
    )
    all_stats.append(stats_limited)

    # Step 3: Run Scaling Analysis (US-3) - reduced agent counts for CI
    stats_scaling = run_and_profile(
        script=str(PROJECT_ROOT / "code" / "run_scaling_experiment.py"),
        args=[
            "--agent-counts", "3,5",  # Reduced from 3,5,7 for CI speed
            "--games", str(args.games),
            "--output-dir", str(output_dir)
        ],
        output_dir=output_dir,
        description="Scaling Analysis (US-3)"
    )
    all_stats.append(stats_scaling)

    # Step 4: Run ANOVA Analysis
    stats_anova = run_and_profile(
        script=str(PROJECT_ROOT / "code" / "analysis" / "anova.py"),
        args=[
            "--input-dir", str(output_dir),
            "--output-dir", str(output_dir)
        ],
        output_dir=output_dir,
        description="ANOVA Analysis (US-2)"
    )
    all_stats.append(stats_anova)

    overall_end = time.time()
    overall_end_mem = get_memory_usage_mb()
    overall_end_disk = get_disk_usage_mb(output_dir)

    total_duration = overall_end - overall_start
    total_disk_delta = overall_end_disk - overall_start_disk

    # Compile final report
    report = {
        "run_metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
            "python_version": sys.version,
            "platform": sys.platform,
            "ci_environment": os.environ.get("CI", "false"),
            "arguments": vars(args)
        },
        "summary": {
            "total_duration_seconds": round(total_duration, 2),
            "peak_memory_mb": max(s.get("peak_memory_mb", 0) for s in all_stats),
            "total_disk_delta_mb": round(total_disk_delta, 2),
            "steps_executed": len(all_stats),
            "steps_successful": sum(1 for s in all_stats if s.get("success")),
            "steps_failed": sum(1 for s in all_stats if not s.get("success"))
        },
        "steps": all_stats
    }

    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Write log
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"CI Pipeline Run Log\n")
        f.write(f"Timestamp: {report['run_metadata']['timestamp']}\n")
        f.write(f"Total Duration: {total_duration:.2f}s\n")
        f.write(f"Peak Memory: {report['summary']['peak_memory_mb']:.2f} MB\n")
        f.write(f"Disk Delta: {total_disk_delta:.2f} MB\n")
        f.write(f"Steps: {report['summary']['steps_executed']} (Success: {report['summary']['steps_successful']}, Failed: {report['summary']['steps_failed']})\n")
        f.write("-" * 80 + "\n")
        for step in all_stats:
            f.write(f"\nStep: {step['description']}\n")
            f.write(f"  Command: {step['command']}\n")
            f.write(f"  Duration: {step['duration_seconds']}s\n")
            f.write(f"  Peak Memory: {step['peak_memory_mb']} MB\n")
            f.write(f"  Status: {'SUCCESS' if step['success'] else 'FAILED'}\n")
            if "error" in step:
                f.write(f"  Error: {step['error']}\n")

    print(f"[CI] Report written to: {report_path}")
    print(f"[CI] Log written to: {log_path}")
    print(f"[CI] Total Duration: {total_duration:.2f}s")
    print(f"[CI] Peak Memory: {report['summary']['peak_memory_mb']:.2f} MB")
    print(f"[CI] Disk Usage Delta: {total_disk_delta:.2f} MB")

    return 0 if report['summary']['steps_failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
