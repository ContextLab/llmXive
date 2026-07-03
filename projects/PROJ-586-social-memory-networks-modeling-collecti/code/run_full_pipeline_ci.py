"""
CI Runner for Social Memory Networks Pipeline.

Executes the full pipeline and records runtime, memory, and disk usage.
Designed to run on CI runners (CPU-only) and produce a JSON metrics report.
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
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure we are in the code directory context
CODE_ROOT = Path(__file__).parent
PROJECT_ROOT = CODE_ROOT.parent
RESULTS_DIR = PROJECT_ROOT / "results"


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB (RSS)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux


def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of a directory in MB."""
    if not path.exists():
        return 0.0
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                continue
    return total_size / (1024 * 1024)


def run_and_profile(script_name: str, args: List[str], output_dir: Path) -> Dict[str, Any]:
    """
    Run a script and profile its resource usage.
    
    Returns a dictionary with timing, memory, and disk metrics.
    """
    script_path = CODE_ROOT / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    start_time = time.time()
    start_mem = get_memory_usage_mb()
    start_disk = get_disk_usage_mb(output_dir)

    cmd = [sys.executable, str(script_path)] + args
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(CODE_ROOT),
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
        exit_code = -2
        stdout = ""
        stderr = str(e)

    end_time = time.time()
    end_mem = get_memory_usage_mb()
    end_disk = get_disk_usage_mb(output_dir)

    return {
        "script": script_name,
        "args": args,
        "exit_code": exit_code,
        "duration_seconds": round(end_time - start_time, 2),
        "start_memory_mb": round(start_mem, 2),
        "end_memory_mb": round(end_mem, 2),
        "peak_memory_mb": round(max(start_mem, end_mem), 2),
        "start_disk_mb": round(start_disk, 2),
        "end_disk_mb": round(end_disk, 2),
        "disk_delta_mb": round(end_disk - start_disk, 2),
        "stdout_lines": len(stdout.splitlines()),
        "stderr_lines": len(stderr.splitlines()),
        "success": exit_code == 0
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CI runner."""
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI and record metrics"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(RESULTS_DIR),
        help="Directory to store results and metrics"
    )
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="limited",
        help="Context condition for experiments"
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents for simulation"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to simulate (reduced for CI)"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma-separated context thresholds"
    )
    return parser


def main() -> int:
    """Main entry point for CI pipeline execution."""
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_report = {
        "pipeline_run": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cwd": str(Path.cwd())
            },
            "parameters": {
                "context": args.context,
                "agents": args.agents,
                "games": args.games,
                "thresholds": [int(t) for t in args.thresholds.split(",")]
            },
            "stages": []
        }
    }

    # Stage 1: Run the main experiment
    print(f"[CI] Running experiment: context={args.context}, agents={args.agents}, games={args.games}")
    
    experiment_args = [
        "--context", args.context,
        "--agents", str(args.agents),
        "--games", str(args.games),
        "--output-dir", str(output_dir)
    ]
    
    # Add thresholds if supported
    try:
        experiment_args.extend(["--thresholds", args.thresholds])
    except:
        pass  # Some scripts might not support this flag

    stage1 = run_and_profile("run_experiment.py", experiment_args, output_dir)
    metrics_report["pipeline_run"]["stages"].append(stage1)
    print(f"[CI] Stage 1 (experiment) completed: exit_code={stage1['exit_code']}")

    # Stage 2: Run ANOVA analysis
    if stage1["success"]:
        print("[CI] Running ANOVA analysis")
        stage2 = run_and_profile("analysis/anova.py", [], output_dir)
        metrics_report["pipeline_run"]["stages"].append(stage2)
        print(f"[CI] Stage 2 (anova) completed: exit_code={stage2['exit_code']}")

    # Stage 3: Run power analysis
    if stage1["success"]:
        print("[CI] Running power analysis")
        stage3 = run_and_profile("analysis/power.py", [], output_dir)
        metrics_report["pipeline_run"]["stages"].append(stage3)
        print(f"[CI] Stage 3 (power) completed: exit_code={stage3['exit_code']}")

    # Stage 4: Run sensitivity analysis
    if stage1["success"]:
        print("[CI] Running sensitivity analysis")
        sensitivity_args = ["--thresholds", args.thresholds]
        stage4 = run_and_profile("analysis/sensitivity.py", sensitivity_args, output_dir)
        metrics_report["pipeline_run"]["stages"].append(stage4)
        print(f"[CI] Stage 4 (sensitivity) completed: exit_code={stage4['exit_code']}")

    # Final summary
    total_duration = sum(s["duration_seconds"] for s in metrics_report["pipeline_run"]["stages"])
    peak_memory = max((s["peak_memory_mb"] for s in metrics_report["pipeline_run"]["stages"]), default=0)
    total_disk_delta = sum(s["disk_delta_mb"] for s in metrics_report["pipeline_run"]["stages"])
    success_count = sum(1 for s in metrics_report["pipeline_run"]["stages"] if s["success"])

    metrics_report["pipeline_run"]["summary"] = {
        "total_duration_seconds": round(total_duration, 2),
        "peak_memory_mb": round(peak_memory, 2),
        "total_disk_delta_mb": round(total_disk_delta, 2),
        "stages_run": len(metrics_report["pipeline_run"]["stages"]),
        "stages_successful": success_count,
        "overall_success": success_count == len(metrics_report["pipeline_run"]["stages"])
    }

    # Write the metrics report
    report_path = output_dir / "ci_pipeline_metrics.json"
    with open(report_path, "w") as f:
        json.dump(metrics_report, f, indent=2)

    print(f"[CI] Metrics report written to: {report_path}")
    print(f"[CI] Summary: {metrics_report['pipeline_run']['summary']}")

    return 0 if metrics_report["pipeline_run"]["summary"]["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())