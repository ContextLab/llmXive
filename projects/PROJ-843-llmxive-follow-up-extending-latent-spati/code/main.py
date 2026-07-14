import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path to allow relative imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_results_dir, get_raw_dir, get_memory_limit_gb, ensure_directories
from utils.memory_monitor import MemoryMonitor, get_session_metrics, clear_session_metrics
from utils.seeds import set_global_seed

# Import pipeline stage main functions
from data.download import main as download_main
from data.stratify import main as stratify_main
from data.extract_features import main as extract_features_main
from geometry.run_pipeline import main as geometry_pipeline_main
from eval.download_dense_baseline import main as download_dense_main
from eval.metrics import main as metrics_main
from eval.anova import main as anova_main
from eval.sensitivity import main as sensitivity_main
from eval.report import main as report_main

# --- Helper Functions ---

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    try:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {path}: {e}")
    return None

def parse_memory_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse raw memory_profiler logs (assumed to be JSON lines or similar format)
    and return a list of aggregated metrics.
    
    Since the specific log format isn't strictly defined in the prompt, 
    we assume a standard JSON-lines format where each line is a metric snapshot.
    If no logs exist, return an empty list.
    """
    logs = []
    if not log_dir.exists():
        return logs
        
    for file_path in log_dir.glob("*.jsonl"):
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            logs.append(entry)
                        except json.JSONDecodeError:
                            continue
        except IOError:
            continue
    return logs

def aggregate_memory_metrics(logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate memory logs into summary statistics (peak, mean, etc.)."""
    if not logs:
        return {"peak_ram_gb": 0.0, "mean_ram_gb": 0.0, "total_samples": 0}
    
    ram_values = [log.get('memory_mb', 0) for log in logs if 'memory_mb' in log]
    if not ram_values:
        return {"peak_ram_gb": 0.0, "mean_ram_gb": 0.0, "total_samples": 0}
        
    return {
        "peak_ram_gb": max(ram_values) / 1024.0,
        "mean_ram_gb": sum(ram_values) / len(ram_values) / 1024.0,
        "total_samples": len(ram_values)
    }

def load_anova_results(results_dir: Path) -> Optional[Dict[str, Any]]:
    """Load ANOVA results from the expected file path."""
    path = results_dir / "anova_results.json"
    return load_json_safe(path)

def load_sensitivity_results(results_dir: Path) -> Optional[Dict[str, Any]]:
    """Load sensitivity sweep results from the expected file path."""
    path = results_dir / "sensitivity_results.json"
    return load_json_safe(path)

def load_metrics_results(results_dir: Path) -> Optional[Dict[str, Any]]:
    """Load metrics results from the expected file path."""
    path = results_dir / "metrics.json"
    return load_json_safe(path)

def run_script(script_name: str, args: List[str] = None) -> bool:
    """
    Run a Python script within the project.
    Returns True if exit code is 0, False otherwise.
    """
    script_path = PROJECT_ROOT / "code" / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)
        if result.returncode != 0:
            print(f"Error: Script {script_name} failed with code {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"Error executing {script_name}: {e}")
        return False

def run_orchestrator_pipeline(phases: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Orchestrates the full pipeline or specific phases.
    Collects memory metrics and aggregates them into the final report.
    """
    results_dir = get_results_dir()
    ensure_directories()
    
    # Initialize Memory Monitor
    monitor = MemoryMonitor(log_path=results_dir / "memory_log.jsonl")
    monitor.start()
    
    start_time = time.time()
    pipeline_results = {
        "phases_run": [],
        "errors": [],
        "timing": {},
        "memory": {}
    }
    
    # Define phases and their corresponding scripts
    phase_map = {
        "data_prepare": [
            ("download", ["--phase", "download"]),
            ("stratify", []),
            ("setup_data", []) # Ensures directories/schemas
        ],
        "extract_features": [
            ("extract_features", [])
        ],
        "compute_geometry": [
            ("run_pipeline", []) # Runs solver + warp + aggregate
        ],
        "evaluate": [
            ("download_dense_baseline", []), # Ensure baseline exists
            ("metrics", []),
            ("anova", []),
            ("sensitivity", [])
        ],
        "report": [
            ("report", [])
        ]
    }
    
    # If specific phases requested, filter; otherwise run all
    phases_to_run = phases if phases else list(phase_map.keys())
    
    for phase in phases_to_run:
        if phase not in phase_map:
            print(f"Warning: Unknown phase '{phase}', skipping.")
            continue
        
        print(f"\n--- Executing Phase: {phase} ---")
        phase_start = time.time()
        phase_success = True
        
        for script_name, args in phase_map[phase]:
            # Check if we need to run the script
            # Note: Some scripts might be idempotent or check existence internally.
            # We run them as per the orchestrator logic.
            if not run_script(f"{script_name}.py", args):
                phase_success = False
                pipeline_results["errors"].append(f"Phase {phase}: {script_name} failed")
                # Depending on strictness, we might break here. 
                # For now, we log and continue to next script if possible, 
                # but usually a phase failure stops the phase.
                break 
        
        phase_duration = time.time() - phase_start
        pipeline_results["timing"][phase] = phase_duration
        
        if phase_success:
            pipeline_results["phases_run"].append(phase)
        else:
            print(f"Phase {phase} did not complete successfully.")
            # We continue to allow partial reporting if possible, 
            # but final metrics might be incomplete.
    
    # Stop monitoring
    monitor.stop()
    
    # Collect Memory Metrics
    session_metrics = get_session_metrics()
    raw_logs = parse_memory_logs(results_dir)
    aggregated_mem = aggregate_memory_metrics(raw_logs)
    
    # Also include the session's specific snapshot if available
    if session_metrics:
        aggregated_mem["session_peak_gb"] = session_metrics.get('peak_memory_gb', 0)
        aggregated_mem["session_duration_sec"] = session_metrics.get('duration_sec', 0)

    # Load computed results from previous steps
    anova_data = load_anova_results(results_dir)
    sensitivity_data = load_sensitivity_results(results_dir)
    metrics_data = load_metrics_results(results_dir)
    
    # Construct Final Report
    final_report = {
        "pipeline_execution": {
            "total_wall_clock_sec": time.time() - start_time,
            "phases_completed": pipeline_results["phases_run"],
            "errors": pipeline_results["errors"],
            "phase_durations": pipeline_results["timing"]
        },
        "memory_metrics": aggregated_mem,
        "analysis_results": {
            "anova": anova_data,
            "sensitivity": sensitivity_data,
            "metrics": metrics_data
        }
    }
    
    # Write Final Report
    output_path = results_dir / "metrics.json"
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\n--- Orchestrator Complete ---")
    print(f"Final report written to: {output_path}")
    print(f"Total time: {final_report['pipeline_execution']['total_wall_clock_sec']:.2f}s")
    print(f"Peak RAM: {aggregated_mem.get('peak_ram_gb', 0):.2f} GB")
    
    return final_report

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument(
        "--phase", 
        type=str, 
        nargs='+', 
        choices=["data_prepare", "extract_features", "compute_geometry", "evaluate", "report", "all"],
        default=["all"],
        help="Specific phases to run. Default: all"
    )
    args = parser.parse_args()
    
    phases = None
    if args.phase != ["all"]:
        phases = args.phase
        
    try:
        run_orchestrator_pipeline(phases)
    except Exception as e:
        print(f"Orchestrator failed with critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()