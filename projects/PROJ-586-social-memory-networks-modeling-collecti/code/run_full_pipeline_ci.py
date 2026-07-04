"""CI Pipeline Runner with Resource Metrics.

Runs the full experiment pipeline on a CI runner and records runtime, memory,
and disk usage metrics for reproducibility and resource profiling.
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
from typing import Dict, Any, List, Optional

from utils.logging import get_logger


@dataclass
class ResourceMetrics:
    """Resource usage metrics for a single pipeline run."""
    timestamp: str
    script_name: str
    exit_code: int
    duration_seconds: float
    memory_max_mb: float
    memory_current_mb: float
    disk_usage_mb: float
    output_files: List[str]
    error_message: Optional[str] = None


@dataclass
class PipelineReport:
    """Aggregated report for the full pipeline execution."""
    timestamp: str
    total_duration_seconds: float
    runs: List[ResourceMetrics]
    summary: Dict[str, Any]


def get_memory_usage_mb() -> Dict[str, float]:
    """Get current and max memory usage in MB.

    Uses resource module for Unix-like systems.
    Returns dict with 'current' and 'max' keys in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, but in bytes on macOS
    # We normalize to MB
    maxrss_kb = usage.ru_maxrss
    # On Linux, ru_maxrss is in KB. On macOS, it's in bytes.
    # We check the platform to be safe.
    if sys.platform == "darwin":
        maxrss_mb = maxrss_kb / (1024 * 1024)
    else:
        maxrss_mb = maxrss_kb / 1024.0

    return {
        "current_mb": maxrss_mb,
        "max_mb": maxrss_mb
    }


def get_disk_usage_mb(path: str = ".") -> float:
    """Get disk usage of the project directory in MB.

    Calculates the total size of all files under the given path.
    """
    total_bytes = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                if os.path.isfile(filepath):
                    total_bytes += os.path.getsize(filepath)
            except OSError:
                continue
    return total_bytes / (1024 * 1024)


def run_experiment_script(
    script_path: str,
    args: List[str],
    project_root: Path
) -> ResourceMetrics:
    """Run a single experiment script and capture resource metrics.

    Args:
        script_path: Path to the Python script to run.
        args: Command line arguments to pass to the script.
        project_root: Root directory of the project.

    Returns:
        ResourceMetrics object with execution details.
    """
    logger = get_logger(__name__)
    logger.log("run_experiment_script", script=script_path, args=args)

    start_time = time.time()
    start_mem = get_memory_usage_mb()
    start_disk = get_disk_usage_mb(str(project_root))

    error_msg = None
    exit_code = 0

    try:
        cmd = [sys.executable, script_path] + args
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        exit_code = result.returncode
        if exit_code != 0:
            error_msg = result.stderr[:1000] if result.stderr else "Unknown error"
    except subprocess.TimeoutExpired:
        error_msg = "Script execution timed out after 1 hour"
        exit_code = -1
    except Exception as e:
        error_msg = str(e)
        exit_code = -1

    end_time = time.time()
    end_mem = get_memory_usage_mb()
    end_disk = get_disk_usage_mb(str(project_root))

    # Find output files created during this run
    output_files = []
    results_dir = project_root / "results"
    if results_dir.exists():
        for f in results_dir.iterdir():
            if f.is_file():
                output_files.append(str(f.relative_to(project_root)))

    return ResourceMetrics(
        timestamp=datetime.utcnow().isoformat(),
        script_name=os.path.basename(script_path),
        exit_code=exit_code,
        duration_seconds=end_time - start_time,
        memory_max_mb=end_mem["max_mb"],
        memory_current_mb=end_mem["current_mb"],
        disk_usage_mb=end_disk,
        output_files=output_files,
        error_message=error_msg
    )


def run_full_pipeline(project_root: Path) -> PipelineReport:
    """Run the full CI pipeline with resource tracking.

    Executes all experiment variants and aggregates metrics.

    Args:
        project_root: Root directory of the project.

    Returns:
        PipelineReport with all execution metrics.
    """
    logger = get_logger(__name__)
    logger.log("run_full_pipeline", project_root=str(project_root))

    pipeline_start = time.time()

    # Define the experiment runs to perform
    runs_config = [
        {
            "script": "code/run_experiment.py",
            "args": ["--context", "full", "--agents", "5", "--games", "100", "--seed", "42"]
        },
        {
            "script": "code/run_experiment.py",
            "args": ["--context", "limited", "--agents", "5", "--games", "100", "--seed", "42"]
        },
        {
            "script": "code/run_experiment.py",
            "args": ["--context", "full", "--agents", "3,5,7", "--games", "50", "--seed", "42"]
        }
    ]

    results: List[ResourceMetrics] = []
    for config in runs_config:
        metric = run_experiment_script(
            config["script"],
            config["args"],
            project_root
        )
        results.append(metric)

    pipeline_duration = time.time() - pipeline_start

    # Calculate summary statistics
    total_duration = sum(r.duration_seconds for r in results)
    max_memory = max(r.memory_max_mb for r in results)
    final_disk = results[-1].disk_usage_mb if results else 0.0
    success_count = sum(1 for r in results if r.exit_code == 0)

    summary = {
        "total_runs": len(results),
        "successful_runs": success_count,
        "failed_runs": len(results) - success_count,
        "total_duration_seconds": total_duration,
        "max_memory_mb": max_memory,
        "final_disk_usage_mb": final_disk
    }

    return PipelineReport(
        timestamp=datetime.utcnow().isoformat(),
        total_duration_seconds=pipeline_duration,
        runs=results,
        summary=summary
    )


def save_results(report: PipelineReport, output_path: Path) -> None:
    """Save the pipeline report to a JSON file.

    Args:
        report: The PipelineReport to save.
        output_path: Path where the report should be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CI pipeline runner."""
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI and record resource metrics"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to save the pipeline report"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root directory"
    )
    return parser


def main() -> int:
    """Main entry point for the CI pipeline runner."""
    parser = build_parser()
    args = parser.parse_args()

    logger = get_logger(__name__)
    logger.log("main", output_dir=args.output_dir, project_root=args.project_root)

    project_root = Path(args.project_root).resolve()
    output_dir = project_root / args.output_dir

    try:
        report = run_full_pipeline(project_root)
        output_file = output_dir / "pipeline_metrics.json"
        save_results(report, output_file)

        print(f"Pipeline completed successfully.")
        print(f"Total runs: {report.summary['total_runs']}")
        print(f"Successful: {report.summary['successful_runs']}")
        print(f"Failed: {report.summary['failed_runs']}")
        print(f"Total duration: {report.total_duration_seconds:.2f}s")
        print(f"Max memory: {report.summary['max_memory_mb']:.2f} MB")
        print(f"Final disk usage: {report.summary['final_disk_usage_mb']:.2f} MB")
        print(f"Report saved to: {output_file}")

        return 0
    except Exception as e:
        logger.log("pipeline_failed", error=str(e))
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
