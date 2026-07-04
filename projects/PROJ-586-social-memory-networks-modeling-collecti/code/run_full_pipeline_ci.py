"""Full pipeline CI runner with resource metrics.

Executes the complete research pipeline on a CI runner (CPU or GPU) and records
runtime, memory usage, and disk usage for reproducibility and performance analysis.
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
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger


@dataclass
class ResourceMetrics:
    """Resource usage metrics for a single run."""
    wall_clock_seconds: float
    peak_memory_mb: float
    disk_usage_mb: float
    cpu_percent: float
    timestamp: str
    script_name: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class PipelineReport:
    """Aggregated report for the full pipeline."""
    runs: List[Dict[str, Any]]
    total_wall_clock_seconds: float
    max_memory_mb: float
    total_disk_usage_mb: float
    timestamp: str
    ci_environment: str
    python_version: str
    platform: str


def get_memory_usage_mb() -> float:
    """Get current peak memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, bytes on macOS
    # On Linux, it's KB; on macOS, it's bytes
    if sys.platform == "darwin":
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024.0


def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of a directory in MB."""
    total = 0
    if path.exists():
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except OSError:
                    pass
    return total / (1024 * 1024)


def run_experiment_script(
    script_path: Path,
    args: List[str],
    logger: Any,
    timeout_seconds: Optional[int] = None
) -> ResourceMetrics:
    """Run a single experiment script and collect metrics."""
    start_time = time.time()
    start_mem = get_memory_usage_mb()
    start_disk = get_disk_usage_mb(PROJECT_ROOT / "results")

    logger.info(f"Starting: {script_path.name} {' '.join(args)}")

    success = False
    error_msg = None

    try:
        cmd = [sys.executable, str(script_path)] + args
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT / "code"),
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        if result.returncode != 0:
            error_msg = f"Script failed with code {result.returncode}: {result.stderr}"
            logger.error(error_msg)
        else:
            success = True
            logger.info(f"Completed: {script_path.name}")

    except subprocess.TimeoutExpired:
        error_msg = f"Script timed out after {timeout_seconds} seconds"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        logger.error(error_msg)

    end_time = time.time()
    end_mem = get_memory_usage_mb()
    end_disk = get_disk_usage_mb(PROJECT_ROOT / "results")

    # Use peak memory if available, otherwise delta
    peak_mem = max(end_mem, start_mem)
    if hasattr(resource, 'getrusage'):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        if sys.platform == "darwin":
            peak_mem = max(peak_mem, usage.ru_maxrss / (1024 * 1024))
        else:
            peak_mem = max(peak_mem, usage.ru_maxrss / 1024.0)

    wall_clock = end_time - start_time
    disk_delta = end_disk - start_disk
    if disk_delta < 0:
        disk_delta = end_disk

    return ResourceMetrics(
        wall_clock_seconds=wall_clock,
        peak_memory_mb=peak_mem,
        disk_usage_mb=disk_delta,
        cpu_percent=100.0,  # Placeholder for CI runner
        timestamp=datetime.utcnow().isoformat(),
        script_name=script_path.name,
        success=success,
        error_message=error_msg
    )


def run_full_pipeline(
    scripts: List[Dict[str, Any]],
    logger: Any
) -> List[ResourceMetrics]:
    """Run the full pipeline of scripts."""
    results = []

    for step in scripts:
        script_name = step["script"]
        args = step.get("args", [])
        timeout = step.get("timeout", 3600)

        script_path = PROJECT_ROOT / "code" / script_name
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            results.append(ResourceMetrics(
                wall_clock_seconds=0,
                peak_memory_mb=0,
                disk_usage_mb=0,
                cpu_percent=0,
                timestamp=datetime.utcnow().isoformat(),
                script_name=script_name,
                success=False,
                error_message=f"Script not found: {script_path}"
            ))
            continue

        metrics = run_experiment_script(script_path, args, logger, timeout)
        results.append(metrics)

        # Stop if a critical step fails
        if not metrics.success and step.get("critical", True):
            logger.error("Critical step failed, stopping pipeline")
            break

    return results


def save_results(
    report: PipelineReport,
    output_path: Path
) -> None:
    """Save the pipeline report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)
    logger.info(f"Report saved to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI and record metrics"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="pipeline_metrics_report.json",
        help="Output path for the metrics report"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Default timeout per script in seconds"
    )
    return parser


def main() -> int:
    """Main entry point."""
    logger = get_logger(__name__)
    parser = build_parser()
    args = parser.parse_args()

    logger.info("Starting full pipeline CI run")
    logger.info(f"Project root: {PROJECT_ROOT}")

    # Define the pipeline steps
    # These scripts must exist and be runnable
    pipeline_scripts = [
        {
            "script": "run_experiment.py",
            "args": ["--context", "full", "--agents", "5", "--games", "100", "--seed", "42"],
            "timeout": args.timeout,
            "critical": True
        },
        {
            "script": "run_experiment.py",
            "args": ["--context", "limited", "--agents", "5", "--games", "100", "--seed", "42"],
            "timeout": args.timeout,
            "critical": True
        },
        {
            "script": "run_scaling_experiment.py",
            "args": ["--agents", "3", "5", "7", "--games", "200", "--seed", "42"],
            "timeout": args.timeout,
            "critical": True
        },
        {
            "script": "analysis/anova.py",
            "args": [],
            "timeout": args.timeout,
            "critical": False
        },
        {
            "script": "analysis/power.py",
            "args": [],
            "timeout": args.timeout,
            "critical": False
        },
        {
            "script": "analysis/scaling.py",
            "args": [],
            "timeout": args.timeout,
            "critical": False
        }
    ]

    # Run the pipeline
    results = run_full_pipeline(pipeline_scripts, logger)

    # Aggregate results
    total_wall_clock = sum(r.wall_clock_seconds for r in results)
    max_memory = max((r.peak_memory_mb for r in results), default=0)
    total_disk = sum(r.disk_usage_mb for r in results)

    report = PipelineReport(
        runs=[asdict(r) for r in results],
        total_wall_clock_seconds=total_wall_clock,
        max_memory_mb=max_memory,
        total_disk_usage_mb=total_disk,
        timestamp=datetime.utcnow().isoformat(),
        ci_environment=os.environ.get("CI", "local"),
        python_version=sys.version,
        platform=sys.platform
    )

    # Save report
    output_path = PROJECT_ROOT / "results" / args.output
    save_results(report, output_path)

    # Summary
    logger.info(f"Pipeline complete. Total time: {total_wall_clock:.2f}s, "
               f"Peak memory: {max_memory:.2f}MB, Disk: {total_disk:.2f}MB")

    success_count = sum(1 for r in results if r.success)
    logger.info(f"Successful runs: {success_count}/{len(results)}")

    if success_count < len(results):
        logger.warning("Some pipeline steps failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())