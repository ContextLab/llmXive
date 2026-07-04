"""CI Pipeline Runner for Social Memory Networks.

Executes the full experiment pipeline on a CI runner, recording runtime,
memory usage, and disk consumption. Produces a JSON report and CSV metrics.
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

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ResourceMetrics:
    """Resource usage metrics for a single run."""
    runtime_seconds: float
    peak_memory_mb: float
    disk_usage_mb: float
    timestamp: str
    command: str
    exit_code: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class PipelineReport:
    """Aggregated report for the full pipeline run."""
    total_runtime_seconds: float
    total_peak_memory_mb: float
    total_disk_usage_mb: float
    timestamp: str
    runs: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None


def get_memory_usage_mb() -> float:
    """Get current peak memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0


def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of a directory in MB."""
    if not path.exists():
        return 0.0
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.exists():
                total += filepath.stat().st_size
    return total / (1024 * 1024)


def run_experiment_script(
    script_name: str,
    args: List[str],
    project_root: Path
) -> ResourceMetrics:
    """Run a single experiment script and capture metrics."""
    script_path = project_root / script_name
    if not script_path.exists():
        return ResourceMetrics(
            runtime_seconds=0.0,
            peak_memory_mb=0.0,
            disk_usage_mb=0.0,
            timestamp=datetime.utcnow().isoformat(),
            command=f"python {script_name} {' '.join(args)}",
            exit_code=-1,
            success=False,
            error_message=f"Script not found: {script_path}"
        )

    start_time = time.time()
    start_memory = get_memory_usage_mb()
    start_disk = get_disk_usage_mb(project_root / "data")

    cmd = [sys.executable, str(script_path)] + args
    logger.log("run_command", command=" ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        exit_code = -1
        stdout = ""
        stderr = "Timeout expired"
    except Exception as e:
        exit_code = -1
        stdout = ""
        stderr = str(e)

    end_time = time.time()
    end_memory = get_memory_usage_mb()
    end_disk = get_disk_usage_mb(project_root / "data")

    runtime = end_time - start_time
    peak_memory = max(start_memory, end_memory)
    disk_usage = end_disk - start_disk

    success = exit_code == 0
    error_msg = stderr if not success else None

    logger.log(
        "experiment_complete",
        script=script_name,
        args=" ".join(args),
        exit_code=exit_code,
        runtime_seconds=runtime,
        success=success
    )

    return ResourceMetrics(
        runtime_seconds=runtime,
        peak_memory_mb=peak_memory,
        disk_usage_mb=disk_usage,
        timestamp=datetime.utcnow().isoformat(),
        command=" ".join(cmd),
        exit_code=exit_code,
        success=success,
        error_message=error_msg
    )


def run_full_pipeline(project_root: Path) -> PipelineReport:
    """Run the full pipeline of experiments."""
    start_time = time.time()
    start_memory = get_memory_usage_mb()
    start_disk = get_disk_usage_mb(project_root / "data")

    runs: List[Dict[str, Any]] = []
    all_success = True
    error_messages: List[str] = []

    # Define the experiments to run based on tasks.md requirements
    experiments = [
        # US-1: Full context experiment
        {
            "name": "full_context",
            "script": "code/run_experiment.py",
            "args": ["--context", "full", "--agents", "5", "--games", "100"]
        },
        # US-2: Limited context experiment
        {
            "name": "limited_context",
            "script": "code/run_experiment.py",
            "args": ["--context", "limited", "--agents", "5", "--games", "100"]
        },
        # US-3: Scaling analysis
        {
            "name": "scaling_analysis",
            "script": "code/run_experiment.py",
            "args": ["--context", "full", "--agents", "3,5,7", "--games", "50", "--plot", "scaling"]
        }
    ]

    for exp in experiments:
        logger.log("starting_experiment", name=exp["name"])
        metrics = run_experiment_script(
            exp["script"],
            exp["args"],
            project_root
        )
        runs.append(asdict(metrics))
        if not metrics.success:
            all_success = False
            error_messages.append(f"{exp['name']}: {metrics.error_message}")

    end_time = time.time()
    end_memory = get_memory_usage_mb()
    end_disk = get_disk_usage_mb(project_root / "data")

    total_runtime = end_time - start_time
    total_peak_memory = max(start_memory, end_memory)
    total_disk_usage = end_disk - start_disk

    return PipelineReport(
        total_runtime_seconds=total_runtime,
        total_peak_memory_mb=total_peak_memory,
        total_disk_usage_mb=total_disk_usage,
        timestamp=datetime.utcnow().isoformat(),
        runs=runs,
        success=all_success,
        error_message="; ".join(error_messages) if error_messages else None
    )


def save_results(report: PipelineReport, output_dir: Path) -> None:
    """Save the pipeline report to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON report
    json_path = output_dir / "ci_pipeline_report.json"
    with open(json_path, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)

    # Save CSV metrics summary
    csv_path = output_dir / "ci_pipeline_metrics.csv"
    with open(csv_path, "w") as f:
        f.write("experiment,runtime_seconds,peak_memory_mb,disk_usage_mb,success,exit_code\n")
        for run in report.runs:
            f.write(
                f"{run['command'].split()[-2] if len(run['command'].split()) > 2 else 'unknown'},"
                f"{run['runtime_seconds']:.2f},"
                f"{run['peak_memory_mb']:.2f},"
                f"{run['disk_usage_mb']:.2f},"
                f"{run['success']},"
                f"{run['exit_code']}\n"
            )

    logger.log("results_saved", json_path=str(json_path), csv_path=str(csv_path))


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the CI pipeline runner."""
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI and record metrics"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory to save results"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root directory"
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve()

    logger.log("pipeline_start", project_root=str(project_root), output_dir=str(output_dir))

    try:
        report = run_full_pipeline(project_root)
        save_results(report, output_dir)

        logger.log(
            "pipeline_complete",
            success=report.success,
            total_runtime=report.total_runtime_seconds,
            total_memory=report.total_peak_memory_mb
        )

        return 0 if report.success else 1

    except Exception as e:
        logger.log("pipeline_failed", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
