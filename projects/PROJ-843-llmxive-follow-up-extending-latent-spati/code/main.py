import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import (
    get_data_dir, get_raw_dir, get_stratified_dir, get_features_dir,
    get_results_dir, get_processed_dir, get_memory_limit_gb, ensure_directories
)
from utils.memory_monitor import get_session_metrics, clear_session_metrics
from utils.seeds import set_global_seed

# Import existing pipeline scripts to ensure they are executed
# These imports are side-effect free; they just ensure the modules are available
# The actual execution happens via subprocess calls in run_script
import data.download
import data.stratify
import data.extract_features
import geometry.solver
import geometry.warp
import geometry.aggregate_warps
import eval.download_dense_baseline
import eval.metrics
import eval.anova
import eval.sensitivity
import eval.report

def parse_memory_logs(log_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Parse raw memory_profiler logs from the specified directory (or default data/results).
    Returns a list of dictionaries containing memory metrics per run.
    """
    if log_dir is None:
        log_dir = get_results_dir()
    
    logs = []
    log_files = list(log_dir.glob("memory_*.log"))
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                # Simple parsing assuming JSON lines or specific format
                # Adjust based on actual format of memory_monitor output
                if content.strip().startswith('['):
                    # Assume JSON array
                    logs.extend(json.loads(content))
                else:
                    # Assume JSON lines
                    for line in content.splitlines():
                        if line.strip():
                            logs.append(json.loads(line))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not parse {log_file}: {e}")
    
    return logs

def aggregate_memory_metrics(memory_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate memory logs into summary statistics.
    Returns a dict with peak RAM, average RAM, and total runs.
    """
    if not memory_logs:
        return {
            "peak_ram_gb": 0.0,
            "avg_ram_gb": 0.0,
            "total_runs": 0,
            "notes": "No memory logs found"
        }
    
    ram_values = [log.get("peak_ram_gb", 0.0) for log in memory_logs if "peak_ram_gb" in log]
    
    return {
        "peak_ram_gb": max(ram_values) if ram_values else 0.0,
        "avg_ram_gb": sum(ram_values) / len(ram_values) if ram_values else 0.0,
        "total_runs": len(ram_values),
        "sample_runs": memory_logs[:5]  # Include first 5 for reference
    }

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def load_anova_results() -> Optional[Dict[str, Any]]:
    """Load ANOVA results from data/results/anova_results.json"""
    results_path = get_results_dir() / "anova_results.json"
    return load_json_safe(results_path)

def load_sensitivity_results() -> Optional[Dict[str, Any]]:
    """Load sensitivity results from data/results/sensitivity_results.json"""
    results_path = get_results_dir() / "sensitivity_results.json"
    return load_json_safe(results_path)

def load_metrics_results() -> Optional[Dict[str, Any]]:
    """Load metrics results from data/results/metrics.json"""
    results_path = get_results_dir() / "metrics.json"
    return load_json_safe(results_path)

def run_script(script_name: str, args: List[str] = None) -> bool:
    """
    Run a Python script from the code directory.
    Returns True if successful (exit code 0), False otherwise.
    """
    cmd = [sys.executable, f"code/{script_name}"]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        duration = time.time() - start_time
        print(f"Completed successfully in {duration:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Script {script_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def run_orchestrator_pipeline(phases: List[str]) -> Dict[str, Any]:
    """
    Run the specified pipeline phases in order.
    Returns a summary of execution.
    """
    phase_scripts = {
        "data_prepare": "data/stratify.py",
        "extract_features": "data/extract_features.py",
        "compute_geometry": "geometry/solver.py",
        "warp": "geometry/warp.py",
        "aggregate_warps": "geometry/aggregate_warps.py",
        "download_dense": "eval/download_dense_baseline.py",
        "compute_metrics": "eval/metrics.py",
        "run_anova": "eval/anova.py",
        "sensitivity": "eval/sensitivity.py",
        "report": "eval/report.py"
    }
    
    execution_log = []
    success_count = 0
    
    for phase in phases:
        script = phase_scripts.get(phase)
        if not script:
            print(f"Unknown phase: {phase}")
            continue
        
        print(f"\n--- Executing Phase: {phase} ---")
        success = run_script(script)
        execution_log.append({
            "phase": phase,
            "script": script,
            "success": success
        })
        if success:
            success_count += 1
        else:
            print(f"Phase {phase} failed. Stopping pipeline.")
            break
    
    return {
        "phases_requested": phases,
        "phases_completed": success_count,
        "execution_log": execution_log
    }

def write_final_metrics(
    execution_summary: Dict[str, Any],
    memory_summary: Dict[str, Any],
    anova_results: Optional[Dict[str, Any]],
    sensitivity_results: Optional[Dict[str, Any]],
    metrics_results: Optional[Dict[str, Any]]
) -> Path:
    """
    Compile all results into the final metrics.json file.
    """
    output_path = get_results_dir() / "metrics.json"
    
    final_report = {
        "execution_summary": execution_summary,
        "memory_metrics": memory_summary,
        "anova_results": anova_results,
        "sensitivity_results": sensitivity_results,
        "metrics_results": metrics_results,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"Final metrics written to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument(
        "--phase",
        nargs="+",
        default=["data_prepare", "extract_features", "compute_geometry", "warp", "aggregate_warps", "download_dense", "compute_metrics", "run_anova", "sensitivity", "report"],
        help="Phases to execute (default: all)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Set global seed
    set_global_seed(args.seed)
    
    # Ensure directories exist
    ensure_directories()
    
    print(f"Starting pipeline with phases: {args.phase}")
    
    # 1. Run the pipeline phases
    execution_summary = run_orchestrator_pipeline(args.phase)
    
    # 2. Parse and aggregate memory logs
    memory_logs = parse_memory_logs()
    memory_summary = aggregate_memory_metrics(memory_logs)
    
    # 3. Load intermediate results
    anova_results = load_anova_results()
    sensitivity_results = load_sensitivity_results()
    metrics_results = load_metrics_results()
    
    # 4. Write final aggregated metrics
    final_path = write_final_metrics(
        execution_summary,
        memory_summary,
        anova_results,
        sensitivity_results,
        metrics_results
    )
    
    print(f"\nPipeline complete. Final report: {final_path}")
    
    # Check for critical missing files
    required_files = [
        get_results_dir() / "metrics.json",
        get_results_dir() / "sparse_warped_frames.npy",
        get_raw_dir() / "dense_baseline_frames.npy"
    ]
    
    missing = [f for f in required_files if not f.exists()]
    if missing:
        print(f"Warning: Missing required deliverables: {missing}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())