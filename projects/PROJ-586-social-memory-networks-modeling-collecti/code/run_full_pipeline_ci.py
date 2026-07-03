"""
CI Pipeline Runner for Social Memory Networks.

This script runs the full experiment pipeline on a CI runner, recording
runtime, memory, and disk usage metrics. It handles the execution of
the main experiment scripts and profiles system resource consumption.

Output: projects/PROJ-586-social-memory-networks-modeling-collecti/results/pipeline_metrics.json
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
from typing import Any, Dict, List, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB (RSS) using resource module."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, bytes on macOS
    # Detect platform and convert appropriately
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)  # bytes to MB
    else:
        return usage.ru_maxrss / 1024  # KB to MB


def get_disk_usage_mb(path: Path) -> float:
    """Get disk usage of a directory in MB."""
    if not path.exists():
        return 0.0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.exists():
                total_size += filepath.stat().st_size
    
    return total_size / (1024 * 1024)


def run_experiment_script(
    script_name: str,
    args: List[str],
    timeout_minutes: int = 60
) -> Tuple[bool, float, str, Dict[str, Any]]:
    """
    Run an experiment script and collect metrics.
    
    Args:
        script_name: Name of the Python script in code/
        args: Command line arguments
        timeout_minutes: Timeout in minutes
        
    Returns:
        Tuple of (success, elapsed_time, output, resource_metrics)
    """
    script_path = PROJECT_ROOT / "code" / script_name
    
    if not script_path.exists():
        logger.log("script_not_found", path=str(script_path))
        return False, 0.0, f"Script not found: {script_path}", {}
    
    start_time = time.time()
    start_mem = get_memory_usage_mb()
    start_disk = get_disk_usage_mb(PROJECT_ROOT / "data")
    
    cmd = [sys.executable, str(script_path)] + args
    timeout_seconds = timeout_minutes * 60
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        elapsed_time = time.time() - start_time
        end_mem = get_memory_usage_mb()
        end_disk = get_disk_usage_mb(PROJECT_ROOT / "data")
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        metrics = {
            "success": success,
            "returncode": result.returncode,
            "elapsed_time_seconds": round(elapsed_time, 2),
            "peak_memory_mb": round(end_mem, 2),
            "memory_delta_mb": round(end_mem - start_mem, 2),
            "disk_start_mb": round(start_disk, 2),
            "disk_end_mb": round(end_disk, 2),
            "disk_delta_mb": round(end_disk - start_disk, 2),
            "command": " ".join(cmd)
        }
        
        return success, elapsed_time, output, metrics
        
    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        end_mem = get_memory_usage_mb()
        
        return False, elapsed_time, f"Timeout after {timeout_minutes} minutes", {
            "success": False,
            "error": "timeout",
            "elapsed_time_seconds": round(elapsed_time, 2),
            "peak_memory_mb": round(end_mem, 2),
            "command": " ".join(cmd)
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        end_mem = get_memory_usage_mb()
        
        return False, elapsed_time, str(e), {
            "success": False,
            "error": str(e),
            "elapsed_time_seconds": round(elapsed_time, 2),
            "peak_memory_mb": round(end_mem, 2),
            "command": " ".join(cmd)
        }


def run_full_pipeline() -> Dict[str, Any]:
    """
    Run the full experiment pipeline with profiling.
    
    Executes:
    1. Full context experiment (100 games for speed)
    2. Limited context experiment (100 games for speed)
    3. Scaling experiment (3 agent counts)
    4. Analysis scripts
    
    Returns:
        Dictionary with all metrics and results
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "runner": "ci",
        "pipeline_version": "1.0.0",
        "experiments": {},
        "summary": {}
    }
    
    # Experiment configurations
    experiments = [
        {
            "name": "full_context_baseline",
            "script": "run_experiment.py",
            "args": ["--context", "full", "--agents", "5", "--games", "100", "--seed", "42"],
            "description": "Full context baseline with 5 agents, 100 games"
        },
        {
            "name": "limited_context",
            "script": "run_experiment.py",
            "args": ["--context", "limited", "--agents", "5", "--games", "100", "--seed", "42"],
            "description": "Limited context with 5 agents, 100 games"
        },
        {
            "name": "scaling_analysis",
            "script": "run_scaling_experiment.py",
            "args": ["--counts", "3,5,7", "--games", "50", "--seed", "42"],
            "description": "Scaling analysis with 3, 5, 7 agents (50 games each)"
        }
    ]
    
    total_start = time.time()
    total_mem_start = get_memory_usage_mb()
    total_disk_start = get_disk_usage_mb(PROJECT_ROOT / "results")
    
    all_success = True
    
    for exp in experiments:
        logger.log("experiment_start", name=exp["name"])
        
        success, elapsed, output, metrics = run_experiment_script(
            exp["script"],
            exp["args"],
            timeout_minutes=30
        )
        
        exp_result = {
            "description": exp["description"],
            "script": exp["script"],
            "args": exp["args"],
            "success": success,
            "elapsed_time_seconds": metrics.get("elapsed_time_seconds", 0),
            "peak_memory_mb": metrics.get("peak_memory_mb", 0),
            "memory_delta_mb": metrics.get("memory_delta_mb", 0),
            "disk_delta_mb": metrics.get("disk_delta_mb", 0),
            "output_preview": output[:500] if output else "",
            "full_output": output
        }
        
        results["experiments"][exp["name"]] = exp_result
        
        if not success:
            all_success = False
            logger.log("experiment_failed", name=exp["name"], error=output[:200])
        else:
            logger.log("experiment_success", name=exp["name"], elapsed=elapsed)
    
    total_elapsed = time.time() - total_start
    total_mem_end = get_memory_usage_mb()
    total_disk_end = get_disk_usage_mb(PROJECT_ROOT / "results")
    
    results["summary"] = {
        "total_experiments": len(experiments),
        "successful_experiments": sum(1 for e in results["experiments"].values() if e["success"]),
        "failed_experiments": sum(1 for e in results["experiments"].values() if not e["success"]),
        "total_elapsed_seconds": round(total_elapsed, 2),
        "peak_memory_mb": round(total_mem_end, 2),
        "total_memory_delta_mb": round(total_mem_end - total_mem_start, 2),
        "total_disk_delta_mb": round(total_disk_end - total_disk_start, 2),
        "overall_success": all_success
    }
    
    return results


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.log("results_saved", path=str(output_path), size_mb=results["summary"]["total_disk_delta_mb"])


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run full pipeline on CI with resource profiling"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/pipeline_metrics.json",
        help="Output path for metrics JSON"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout per experiment in minutes"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games per experiment (reduced for CI)"
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    output_path = PROJECT_ROOT / args.output
    
    logger.log("pipeline_start", output=str(output_path), timeout=args.timeout)
    
    try:
        results = run_full_pipeline()
        save_results(results, output_path)
        
        if results["summary"]["overall_success"]:
            logger.log("pipeline_complete", status="success")
            return 0
        else:
            logger.log("pipeline_complete", status="partial_failure")
            return 1
            
    except Exception as e:
        logger.log("pipeline_failed", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
