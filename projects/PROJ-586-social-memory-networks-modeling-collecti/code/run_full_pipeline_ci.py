"""CI Pipeline Runner with Resource Profiling.

This module executes the full research pipeline on a CI runner and records
runtime, memory, and disk usage metrics. It is designed to be robust against
missing dependencies by skipping heavy model loads if necessary and focusing
on the pipeline orchestration and resource measurement.
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
from typing import Any, Dict, List, Optional, Tuple

# Attempt to import optional heavy dependencies, but do not fail if missing
# to allow the CI runner to profile the pipeline structure even if models fail to load.
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure output directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def get_memory_usage_mb() -> float:
    """Get current memory usage of the process in MB."""
    try:
        # Try psutil first for more accurate RSS
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        else:
            # Fallback to resource module (Unix only)
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux/macOS
            return usage.ru_maxrss / 1024.0
    except Exception:
        return 0.0


def get_disk_usage_mb(path: Optional[Path] = None) -> float:
    """Get disk usage of the project directory in MB."""
    target = path or PROJECT_ROOT
    if not target.exists():
        return 0.0
    try:
        total = 0
        for dirpath, dirnames, filenames in os.walk(target):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total += os.path.getsize(filepath)
        return total / (1024 * 1024)
    except Exception:
        return 0.0


def run_experiment_script(script_name: str, args: List[str], timeout: int = 3600) -> Tuple[int, str, str]:
    """Run a specific experiment script and capture output.

    Args:
        script_name: Name of the script in code/ directory
        args: List of command line arguments
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    script_path = PROJECT_ROOT / "code" / script_name
    if not script_path.exists():
        return 1, "", f"Script not found: {script_path}"

    cmd = [sys.executable, str(script_path)] + args
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        duration = time.time() - start_time
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return -1, "", f"Process timed out after {timeout} seconds"
    except Exception as e:
        return 1, "", str(e)


def run_full_pipeline() -> List[Dict[str, Any]]:
    """Run the full pipeline steps and collect metrics.

    This function orchestrates the execution of key pipeline components:
    1. Full context experiment
    2. Limited context experiment
    3. Scaling experiment

    It records metrics for each step and aggregates them.
    """
    results = []
    base_args = {
        "full_context": ["--context", "full", "--agents", "5", "--games", "100", "--seed", "42"],
        "limited_context": ["--context", "limited", "--agents", "5", "--games", "100", "--seed", "42"],
        "scaling": ["--context", "full", "--agents", "3,5,7", "--games", "50", "--plot", "scaling", "--seed", "42"]
    }

    # Define pipeline steps
    steps = [
        {"name": "full_context", "script": "run_experiment.py", "args": base_args["full_context"]},
        {"name": "limited_context", "script": "run_experiment.py", "args": base_args["limited_context"]},
        {"name": "scaling", "script": "run_experiment.py", "args": base_args["scaling"]},
    ]

    for step in steps:
        step_start = time.time()
        initial_mem = get_memory_usage_mb()
        initial_disk = get_disk_usage_mb()

        return_code, stdout, stderr = run_experiment_script(
            step["script"],
            step["args"],
            timeout=1800  # 30 min per step
        )

        step_end = time.time()
        final_mem = get_memory_usage_mb()
        final_disk = get_disk_usage_mb()

        step_result = {
            "step": step["name"],
            "script": step["script"],
            "args": step["args"],
            "return_code": return_code,
            "duration_seconds": step_end - step_start,
            "memory_peak_mb": final_mem,
            "memory_delta_mb": final_mem - initial_mem,
            "disk_usage_mb": final_disk,
            "disk_delta_mb": final_disk - initial_disk,
            "success": return_code == 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Log output to file for debugging
        log_file = LOGS_DIR / f"{step['name']}_log.txt"
        with open(log_file, "w") as f:
            f.write(f"Return Code: {return_code}\n")
            f.write(f"Duration: {step_result['duration_seconds']:.2f}s\n")
            f.write(f"Stdout:\n{stdout}\n")
            f.write(f"Stderr:\n{stderr}\n")

        results.append(step_result)

    return results


def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """Save pipeline results to a JSON file."""
    if output_path is None:
        output_path = RESULTS_DIR / "pipeline_metrics.json"

    output_data = {
        "pipeline_run": {
            "timestamp": datetime.utcnow().isoformat(),
            "project_root": str(PROJECT_ROOT),
            "python_version": sys.version,
            "total_steps": len(results),
            "successful_steps": sum(1 for r in results if r["success"]),
            "total_duration_seconds": sum(r["duration_seconds"] for r in results),
            "max_memory_mb": max(r["memory_peak_mb"] for r in results) if results else 0,
            "final_disk_usage_mb": results[-1]["disk_usage_mb"] if results else 0
        },
        "steps": results
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2, default=str)

    return output_path


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI runner and record metrics."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RESULTS_DIR / "pipeline_metrics.json",
        help="Output path for metrics JSON"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds for each step"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not execute, just report configuration"
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    print(f"Starting pipeline run at {datetime.utcnow().isoformat()}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output: {args.output}")

    if args.dry_run:
        print("Dry run mode - skipping execution")
        return 0

    try:
        results = run_full_pipeline()
        output_path = save_results(results, args.output)
        print(f"Pipeline run complete. Results saved to {output_path}")

        # Print summary
        success_count = sum(1 for r in results if r["success"])
        print(f"Steps: {len(results)} total, {success_count} successful")
        print(f"Total duration: {sum(r['duration_seconds'] for r in results):.2f}s")
        print(f"Peak memory: {max(r['memory_peak_mb'] for r in results):.2f} MB")

        return 0 if success_count == len(results) else 1

    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        # Even on failure, save what we have
        try:
            save_results([], args.output)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
