"""
CI Pipeline Runner with Resource Profiling.

Executes the full experiment pipeline on a CI runner, recording:
- Wall-clock runtime per stage
- Peak memory usage (RSS)
- Peak disk usage

Outputs a JSON report to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/ci_profile_report.json`.

This script avoids synthetic data fabrication by using a minimal, deterministic
subset of the experiment (small N) to measure system performance without
generating fake research results.
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
from typing import Dict, Any, List

# Ensure we are in the project root context for imports if needed,
# but this script primarily orchestrates subprocess calls.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB (RSS)."""
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
            fp = Path(dirpath) / filename
            if fp.is_file():
                total += fp.stat().st_size
    return total / (1024 * 1024)

def run_and_profile(
    command: List[str],
    description: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Run a command, measuring time, memory, and disk growth.
    
    Returns a dict with:
      - description
      - command
      - status (success/fail)
      - duration_seconds
      - peak_memory_mb
      - disk_output_mb (if output dir specified)
      - error (if failed)
    """
    result = {
        "description": description,
        "command": " ".join(command),
        "status": "unknown",
        "duration_seconds": 0.0,
        "peak_memory_mb": 0.0,
        "disk_output_mb": 0.0,
        "error": None
    }

    if dry_run:
        result["status"] = "skipped (dry-run)"
        return result

    start_time = time.time()
    initial_memory = get_memory_usage_mb()
    
    # Capture disk usage of results dir before if it exists
    initial_disk = get_disk_usage_mb(RESULTS_DIR) if RESULTS_DIR.exists() else 0.0

    try:
        # Run the command
        proc = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        duration = time.time() - start_time
        final_memory = get_memory_usage_mb()
        final_disk = get_disk_usage_mb(RESULTS_DIR) if RESULTS_DIR.exists() else 0.0

        result["duration_seconds"] = round(duration, 3)
        result["peak_memory_mb"] = round(final_memory - initial_memory, 2)
        result["disk_output_mb"] = round(final_disk - initial_disk, 2)

        if proc.returncode == 0:
            result["status"] = "success"
        else:
            result["status"] = "failed"
            result["error"] = f"Exit code {proc.returncode}\n{proc.stderr}"
            
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Command timed out after 1 hour"
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)

    return result

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI with resource profiling"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not execute, just report structure"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RESULTS_DIR / "ci_profile_report.json",
        help="Path to output JSON report"
    )
    parser.add_argument(
        "--subset",
        type=int,
        default=10,
        help="Number of games to run for profiling (small N to avoid long runtime)"
    )
    return parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Starting CI Pipeline Profile at {datetime.now().isoformat()}")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Results Dir: {RESULTS_DIR}")
    print(f"Dry Run: {args.dry_run}")
    print("-" * 60)

    stages = []

    # Stage 1: Full Context Experiment (Small N)
    # Using --games {args.subset} to keep runtime short for CI profiling
    # This measures the pipeline overhead and memory footprint without
    # generating massive datasets.
    cmd_full = [
        sys.executable,
        "code/run_experiment.py",
        "--context", "full",
        "--agents", "3",
        "--games", str(args.subset),
        "--seed", "42"
    ]
    stages.append(run_and_profile(
        cmd_full,
        f"Full Context Experiment (N={args.subset})",
        dry_run=args.dry_run
    ))

    # Stage 2: Limited Context Experiment (Small N)
    cmd_limited = [
        sys.executable,
        "code/run_experiment.py",
        "--context", "limited",
        "--agents", "3",
        "--games", str(args.subset),
        "--seed", "42"
    ]
    stages.append(run_and_profile(
        cmd_limited,
        f"Limited Context Experiment (N={args.subset})",
        dry_run=args.dry_run
    ))

    # Stage 3: Scaling Analysis (Small N)
    cmd_scaling = [
        sys.executable,
        "code/run_scaling_experiment.py",
        "--agents", "3,5,7",
        "--games", str(args.subset),
        "--plot", "scaling"
    ]
    stages.append(run_and_profile(
        cmd_scaling,
        f"Scaling Analysis (N={args.subset} per group)",
        dry_run=args.dry_run
    ))

    # Stage 4: ANOVA Analysis
    cmd_anova = [
        sys.executable,
        "code/analysis/anova.py",
        "--input", str(RESULTS_DIR / "results_full.csv")
    ]
    # Only run if input exists (may not exist in dry run or if prev step failed)
    if not args.dry_run and (RESULTS_DIR / "results_full.csv").exists():
        stages.append(run_and_profile(
            cmd_anova,
            "ANOVA Statistical Analysis",
            dry_run=False
        ))
    else:
        stages.append({
            "description": "ANOVA Statistical Analysis",
            "command": " ".join(cmd_anova),
            "status": "skipped (input missing or dry-run)",
            "duration_seconds": 0.0,
            "peak_memory_mb": 0.0,
            "disk_output_mb": 0.0,
            "error": None
        })

    # Compile final report
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "PROJ-586-social-memory-networks-modeling-collecti",
        "task_id": "T035",
        "environment": {
            "python": sys.version,
            "platform": sys.platform,
            "cwd": str(Path.cwd())
        },
        "parameters": {
            "games_per_stage": args.subset,
            "dry_run": args.dry_run
        },
        "stages": stages,
        "summary": {
            "total_stages": len(stages),
            "successful": sum(1 for s in stages if s["status"] == "success"),
            "failed": sum(1 for s in stages if s["status"] == "failed"),
            "skipped": sum(1 for s in stages if "skipped" in s["status"]),
            "total_duration_seconds": sum(s["duration_seconds"] for s in stages),
            "total_memory_mb": max(s["peak_memory_mb"] for s in stages) if stages else 0.0,
            "total_disk_mb": sum(s["disk_output_mb"] for s in stages)
        }
    }

    # Write report
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("-" * 60)
    print(f"Report written to: {output_path}")
    print(f"Summary: {report['summary']['successful']} success, "
          f"{report['summary']['failed']} failed, "
          f"{report['summary']['skipped']} skipped")
    
    return 0 if report["summary"]["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
