"""CI Pipeline Runner with Resource Profiling.

Executes the full research pipeline on a CI runner and records
runtime, memory usage, and disk usage for each stage.
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
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ResourceMetrics:
    """Resource usage metrics for a single run."""
    script_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    max_memory_mb: float
    exit_code: int
    output_files: List[str]
    status: str  # "success", "failed", "timeout"

@dataclass
class PipelineReport:
    """Full pipeline execution report."""
    pipeline_name: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    runner_environment: Dict[str, Any]
    stage_results: List[ResourceMetrics]
    summary: Dict[str, Any]

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB using resource module."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of a directory in MB."""
    if not path.exists():
        return 0.0
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = Path(dirpath) / f
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total / (1024 * 1024)

def run_experiment_script(
    script_path: Path,
    args: List[str],
    timeout_seconds: Optional[int] = None
) -> ResourceMetrics:
    """Run a single experiment script and capture metrics."""
    start_time = datetime.utcnow().isoformat()
    start_cpu = resource.getrusage(resource.RUSAGE_SELF)
    max_mem = 0.0

    cmd = [sys.executable, str(script_path)] + args
    logger.log("run_experiment", script=str(script_path), args=args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=script_path.parent
        )
        exit_code = result.returncode
        status = "success" if exit_code == 0 else "failed"

        # Check output files if success
        output_files = []
        if status == "success":
            # Common output locations
            for pattern in ["results/*.csv", "results/*.pdf", "results/*.md"]:
                    import glob
                    for f in glob.glob(str(script_path.parent.parent / pattern)):
                        output_files.append(f)

        end_time = datetime.utcnow().isoformat()
        end_cpu = resource.getrusage(resource.RUSAGE_SELF)

        duration = (
            (end_cpu.ru_utime + end_cpu.ru_stime) -
            (start_cpu.ru_utime + start_cpu.ru_stime)
        )
        max_mem = (end_cpu.ru_maxrss - start_cpu.ru_maxrss) / 1024.0
        if max_mem < 0:
            max_mem = end_cpu.ru_maxrss / 1024.0

        return ResourceMetrics(
            script_name=script_path.name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            max_memory_mb=max_mem,
            exit_code=exit_code,
            output_files=output_files,
            status=status
        )

    except subprocess.TimeoutExpired:
        end_time = datetime.utcnow().isoformat()
        return ResourceMetrics(
            script_name=script_path.name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=timeout_seconds,
            max_memory_mb=get_memory_usage_mb(),
            exit_code=-1,
            output_files=[],
            status="timeout"
        )
    except Exception as e:
        end_time = datetime.utcnow().isoformat()
        logger.log("run_experiment_error", error=str(e))
        return ResourceMetrics(
            script_name=script_path.name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=0.0,
            max_memory_mb=get_memory_usage_mb(),
            exit_code=-1,
            output_files=[],
            status="failed"
        )

def run_full_pipeline(
    project_root: Path,
    timeout_per_stage: int = 3600
) -> PipelineReport:
    """Run the full research pipeline and collect metrics."""
    start_time = datetime.utcnow()
    start_ts = start_time.isoformat()

    # Define pipeline stages
    stages = [
        ("full_context", ["run_experiment.py", "--context", "full", "--agents", "5", "--games", "100", "--seed", "42"]),
        ("limited_context", ["run_experiment.py", "--context", "limited", "--agents", "5", "--games", "100", "--seed", "42"]),
        ("scaling", ["run_experiment.py", "--context", "full", "--agents", "3,5,7", "--games", "800", "--plot", "scaling"]),
    ]

    results: List[ResourceMetrics] = []
    code_script = project_root / "code"

    for stage_name, args in stages:
        logger.log("stage_start", stage=stage_name)
        metric = run_experiment_script(code_script / args[0], args[1:], timeout_per_stage)
        results.append(metric)
        logger.log("stage_end", stage=stage_name, status=metric.status)

    end_time = datetime.utcnow()
    total_duration = (end_time - start_time).total_seconds()

    # Build summary
    successful = sum(1 for r in results if r.status == "success")
    total_memory = sum(r.max_memory_mb for r in results)
    total_time = sum(r.duration_seconds for r in results)

    report = PipelineReport(
        pipeline_name="PROJ-586-social-memory-networks-modeling-collecti",
        start_time=start_ts,
        end_time=end_time.isoformat(),
        total_duration_seconds=total_duration,
        runner_environment={
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": str(Path.cwd()),
        },
        stage_results=results,
        summary={
            "total_stages": len(stages),
            "successful_stages": successful,
            "failed_stages": len(stages) - successful,
            "total_memory_mb": total_memory,
            "total_cpu_seconds": total_time,
        }
    )

    return report

def save_results(report: PipelineReport, output_dir: Path) -> None:
    """Save pipeline report to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pipeline_ci_report.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, default=str)

    logger.log("save_report", path=str(report_path))

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI runner with resource profiling"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Path to project root directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory to write report"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout per stage in seconds"
    )
    return parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve()

    logger.log("pipeline_start", project=str(project_root))

    report = run_full_pipeline(project_root, args.timeout)
    save_results(report, output_dir)

    logger.log("pipeline_complete", status="success" if report.summary["failed_stages"] == 0 else "partial")

    # Print summary to stdout
    print(json.dumps(asdict(report.summary), indent=2))

    return 0 if report.summary["failed_stages"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
