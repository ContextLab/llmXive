"""
Orchestrator for the llmXive pipeline.
Executes phases sequentially, aggregates memory logs, and writes final metrics.
"""
import argparse
import json
import os
import sys
import subprocess
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_results_dir, get_data_dir, ensure_directories
from utils.memory_monitor import get_session_metrics, clear_session_metrics

def locate_memory_logs(logs_dir: Optional[Path] = None) -> List[Path]:
    """Locate all memory profiler log files."""
    if logs_dir is None:
        logs_dir = Path(get_data_dir()) / "logs"
    if not logs_dir.exists():
        return []
    return list(logs_dir.glob("*.log"))

def parse_memory_log(log_path: Path) -> Dict[str, Any]:
    """
    Parse a memory profiler log file to extract peak RAM and wall-clock time.
    Expected format: 'Line #    Mem usage    Increment   Line Contents'
    We look for the maximum 'Mem usage' value.
    """
    peak_mem_mb = 0.0
    wall_clock_seconds = 0.0
    lines = log_path.read_text().splitlines()
    
    # Simple heuristic: find max memory line
    # Format usually: '    123.456 MiB'
    mem_pattern = re.compile(r'(\d+\.?\d*)\s*MiB')
    
    for line in lines:
        match = mem_pattern.search(line)
        if match:
            val = float(match.group(1))
            if val > peak_mem_mb:
                peak_mem_mb = val
        
        # Look for wall clock if logged explicitly
        if "elapsed" in line.lower() or "time" in line.lower():
            time_match = re.search(r'(\d+\.?\d*)\s*s', line)
            if time_match:
                wall_clock_seconds = max(wall_clock_seconds, float(time_match.group(1)))

    return {
        "peak_memory_mb": peak_mem_mb,
        "wall_clock_seconds": wall_clock_seconds,
        "log_file": str(log_path)
    }

def aggregate_memory_metrics(logs: List[Path]) -> Dict[str, Any]:
    """Aggregate metrics from all memory logs."""
    total_peak = 0.0
    total_time = 0.0
    details = []
    
    for log in logs:
        try:
            metrics = parse_memory_log(log)
            details.append(metrics)
            total_peak = max(total_peak, metrics["peak_memory_mb"])
            total_time += metrics["wall_clock_seconds"]
        except Exception as e:
            print(f"Warning: Could not parse {log}: {e}")
    
    return {
        "overall_peak_memory_mb": total_peak,
        "total_wall_clock_seconds": total_time,
        "log_details": details
    }

def aggregate_and_write_memory_logs(output_path: Path):
    """Locate, parse, and aggregate memory logs, writing to output."""
    logs = locate_memory_logs()
    if not logs:
        print("No memory logs found. Creating empty summary.")
        summary = {
            "overall_peak_memory_mb": 0.0,
            "total_wall_clock_seconds": 0.0,
            "log_details": [],
            "note": "No memory logs found in data/logs"
        }
    else:
        summary = aggregate_memory_metrics(logs)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Memory metrics aggregated to {output_path}")
    return summary

def write_metrics_json(results: Dict[str, Any], output_path: Path):
    """Write the final metrics.json file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Final metrics written to {output_path}")

def run_phase_command(phase_name: str, script_name: str, args: List[str] = None) -> bool:
    """Run a specific phase script."""
    cmd = [sys.executable, f"code/{script_name}"]
    if args:
        cmd.extend(args)
    
    print(f"Running phase '{phase_name}': {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, cwd=project_root)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Phase '{phase_name}' failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Script 'code/{script_name}' not found.")
        return False

def phase_data_prepare() -> bool:
    """Run data preparation (download + stratify)."""
    success = True
    if not run_phase_command("data_prepare", "data/download.py"):
        success = False
    if not run_phase_command("data_stratify", "data/stratify.py"):
        success = False
    return success

def phase_extract_features() -> bool:
    """Run feature extraction."""
    return run_phase_command("extract_features", "data/extract_features.py")

def phase_compute_geometry() -> bool:
    """Run geometry solver and warping."""
    return run_phase_command("compute_geometry", "geometry/run_pipeline.py")

def phase_evaluate() -> bool:
    """Run evaluation metrics and aggregation."""
    success = True
    # Download dense baseline if not present
    if not (Path(get_data_dir()) / "raw" / "dense_baseline_frames.npy").exists():
        if not run_phase_command("download_dense", "eval/download_dense_baseline.py"):
            # If download fails, we might proceed with sparse only or fail
            print("Warning: Dense baseline download failed, proceeding with sparse metrics if available.")
    
    # Run metrics calculation
    if not run_phase_command("evaluate_metrics", "eval/metrics.py"):
        success = False
    
    # Run ANOVA
    if not run_phase_command("anova", "eval/anova.py"):
        success = False
    
    # Run sensitivity
    if not run_phase_command("sensitivity", "eval/sensitivity.py"):
        success = False
    
    return success

def run_full_pipeline():
    """Execute the full pipeline and aggregate results."""
    ensure_directories()
    results = {
        "pipeline_start": time.time(),
        "phases": {},
        "memory": {}
    }

    # Phase 1: Data Prep
    t0 = time.time()
    success_1 = phase_data_prepare()
    results["phases"]["data_prepare"] = {
        "success": success_1,
        "duration": time.time() - t0
    }
    if not success_1:
        print("Data preparation failed. Stopping pipeline.")
        # Still try to write what we have
    
    # Phase 2: Features
    t0 = time.time()
    success_2 = phase_extract_features()
    results["phases"]["extract_features"] = {
        "success": success_2,
        "duration": time.time() - t0
    }

    # Phase 3: Geometry
    t0 = time.time()
    success_3 = phase_compute_geometry()
    results["phases"]["compute_geometry"] = {
        "success": success_3,
        "duration": time.time() - t0
    }

    # Phase 4: Evaluation
    t0 = time.time()
    success_4 = phase_evaluate()
    results["phases"]["evaluate"] = {
        "success": success_4,
        "duration": time.time() - t0
    }

    results["pipeline_end"] = time.time()
    results["overall_success"] = all([success_1, success_2, success_3, success_4])

    # Aggregate Memory Logs
    memory_summary = aggregate_and_write_memory_logs(Path(get_results_dir()) / "memory_summary.json")
    results["memory"] = memory_summary

    # Write Final Metrics
    write_metrics_json(results, Path(get_results_dir()) / "metrics.json")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument("--phase", type=str, choices=[
        "all", "data_prepare", "extract_features", "compute_geometry", "evaluate"
    ], default="all", help="Which phase to run")
    parser.add_argument("--output", type=str, default=None, help="Output path for metrics (default: data/results/metrics.json)")
    
    args = parser.parse_args()
    
    if args.phase == "all":
        run_full_pipeline()
    elif args.phase == "data_prepare":
        phase_data_prepare()
    elif args.phase == "extract_features":
        phase_extract_features()
    elif args.phase == "compute_geometry":
        phase_compute_geometry()
    elif args.phase == "evaluate":
        phase_evaluate()
        
        # If just evaluating, ensure memory logs are aggregated
        aggregate_and_write_memory_logs(Path(get_results_dir()) / "memory_summary.json")
        
        # Load existing metrics if any and update
        metrics_path = Path(get_results_dir()) / "metrics.json"
        if metrics_path.exists():
            with open(metrics_path) as f:
                current = json.load(f)
            current["memory"] = aggregate_memory_metrics(locate_memory_logs())
            write_metrics_json(current, metrics_path)
        else:
            write_metrics_json({"note": "No prior metrics found, only evaluation phase run"}, metrics_path)

if __name__ == "__main__":
    main()