"""
CI Pipeline Runner with Resource Profiling.

Runs the full experiment pipeline on a CI runner and records:
- Runtime (wall-clock seconds)
- Peak memory usage (MB)
- Disk usage changes (MB)

Outputs a JSON report to results/pipeline_profile.json.
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

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

def get_memory_usage_mb() -> float:
    """Get current peak memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux
    return usage.ru_maxrss / 1024.0

def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of a directory in MB."""
    if not path.exists():
        return 0.0
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total += os.path.getsize(filepath)
            except OSError:
                continue
    return total / (1024 * 1024)

def run_and_profile(
    script_path: Path,
    args: List[str],
    timeout_seconds: int = 3600
) -> Dict[str, Any]:
    """
    Run a script with resource profiling.
    
    Returns a dict with:
    - command: str
    - exit_code: int
    - runtime_seconds: float
    - peak_memory_mb: float
    - disk_usage_mb: float
    - stdout: str (truncated)
    - stderr: str (truncated)
    """
    start_time = time.time()
    initial_disk = get_disk_usage_mb(RESULTS_DIR)
    
    cmd = [sys.executable, str(script_path)] + args
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1
        result_stdout = ""
        result_stderr = "Process timed out"
    except Exception as e:
        exit_code = -1
        result_stdout = ""
        result_stderr = str(e)
    
    end_time = time.time()
    final_disk = get_disk_usage_mb(RESULTS_DIR)
    peak_memory = get_memory_usage_mb()
    
    return {
        "command": " ".join(cmd),
        "exit_code": exit_code,
        "runtime_seconds": round(end_time - start_time, 3),
        "peak_memory_mb": round(peak_memory, 2),
        "disk_usage_mb": round(final_disk - initial_disk, 2),
        "stdout": result.stdout[:2000] if result.stdout else "",
        "stderr": result.stderr[:2000] if result.stderr else ""
    }

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI with resource profiling"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to simulate per condition"
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent counts (e.g., '5' or '3,5,7')"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds"
    )
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define pipeline stages
    stages = [
        {
            "name": "full_context_experiment",
            "script": PROJECT_ROOT / "code" / "run_experiment.py",
            "args": [
                "--context", "full",
                "--agents", args.agents,
                "--games", str(args.games),
                "--seed", "42"
            ]
        },
        {
            "name": "limited_context_experiment",
            "script": PROJECT_ROOT / "code" / "run_experiment.py",
            "args": [
                "--context", "limited",
                "--agents", args.agents,
                "--games", str(args.games),
                "--seed", "42"
            ]
        }
    ]
    
    # Add scaling experiment if multiple agent counts
    if "," in args.agents:
        stages.append({
            "name": "scaling_experiment",
            "script": PROJECT_ROOT / "code" / "run_scaling_experiment.py",
            "args": [
                "--agents", args.agents,
                "--games", str(args.games),
                "--seed", "42"
            ]
        })
    
    results = {
        "run_timestamp": datetime.utcnow().isoformat(),
        "config": {
            "games": args.games,
            "agents": args.agents,
            "timeout_seconds": args.timeout
        },
        "stages": []
    }
    
    total_runtime = 0
    total_memory = 0
    total_disk = 0
    
    for stage in stages:
        print(f"Running stage: {stage['name']}")
        report = run_and_profile(
            stage["script"],
            stage["args"],
            timeout_seconds=args.timeout
        )
        results["stages"].append({
            "name": stage["name"],
            **report
        })
        
        total_runtime += report["runtime_seconds"]
        total_memory = max(total_memory, report["peak_memory_mb"])
        total_disk += report["disk_usage_mb"]
        
        if report["exit_code"] != 0:
            print(f"  WARNING: Stage {stage['name']} failed with code {report['exit_code']}")
    
    results["summary"] = {
        "total_runtime_seconds": round(total_runtime, 3),
        "peak_memory_mb": round(total_memory, 2),
        "total_disk_growth_mb": round(total_disk, 2),
        "stages_completed": len([s for s in results["stages"] if s["exit_code"] == 0]),
        "stages_total": len(results["stages"])
    }
    
    # Write report
    report_path = RESULTS_DIR / "pipeline_profile.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nProfile report written to: {report_path}")
    print(f"Total runtime: {results['summary']['total_runtime_seconds']}s")
    print(f"Peak memory: {results['summary']['peak_memory_mb']}MB")
    print(f"Disk growth: {results['summary']['total_disk_growth_mb']}MB")
    
    return 0 if results["summary"]["stages_completed"] == results["summary"]["stages_total"] else 1

if __name__ == "__main__":
    sys.exit(main())
