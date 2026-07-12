import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Import configuration
from config import (
    get_data_dir,
    get_raw_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
    get_memory_limit_gb,
    ensure_directories
)

# Import memory monitoring utilities
from utils.memory_monitor import (
    get_session_metrics,
    clear_session_metrics,
    MemoryMonitor
)

# Import evaluation modules to aggregate results
from eval.metrics import main as run_metrics_evaluation
from eval.anova import main as run_anova_evaluation
from eval.sensitivity import main as run_sensitivity_evaluation

def parse_memory_logs() -> List[Dict[str, Any]]:
    """
    Parse raw memory_profiler logs from previous stages.
    Assumes logs are stored in data/results or a standard location.
    Returns a list of metric dictionaries.
    """
    results_dir = get_results_dir()
    logs = []
    
    # Look for memory log files (e.g., memory_log_*.json or similar)
    # Since T005 logs to disk, we scan for them here.
    # If no logs exist, return empty list (graceful degradation)
    if not results_dir.exists():
        return logs

    log_files = list(results_dir.glob("memory_log_*.json"))
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                content = json.load(f)
                if isinstance(content, list):
                    logs.extend(content)
                else:
                    logs.append(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not parse {log_file}: {e}")
            continue
    
    return logs

def aggregate_memory_metrics(raw_logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate raw memory logs into summary statistics for the report.
    """
    if not raw_logs:
        return {
            "peak_ram_gb": 0.0,
            "total_wall_time_seconds": 0.0,
            "num_samples": 0
        }

    peak_rams = [log.get('peak_ram_gb', 0.0) for log in raw_logs if 'peak_ram_gb' in log]
    times = [log.get('wall_time_seconds', 0.0) for log in raw_logs if 'wall_time_seconds' in log]

    return {
        "peak_ram_gb": max(peak_rams) if peak_rams else 0.0,
        "total_wall_time_seconds": sum(times) if times else 0.0,
        "num_samples": len(raw_logs)
    }

def load_anova_results() -> Dict[str, Any]:
    """
    Load ANOVA results from data/results/anova_results.json if it exists.
    """
    results_dir = get_results_dir()
    path = results_dir / "anova_results.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {"interaction_p_value": None, "status": "not_found"}

def load_sensitivity_results() -> Dict[str, Any]:
    """
    Load sensitivity sweep results from data/results/sensitivity_results.json.
    """
    results_dir = get_results_dir()
    path = results_dir / "sensitivity_results.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {"status": "not_found"}

def load_metrics_results() -> Dict[str, Any]:
    """
    Load metrics results from data/results/metrics.json.
    """
    results_dir = get_results_dir()
    path = results_dir / "metrics.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {"status": "not_found"}

def main():
    """
    Orchestrator for the llmXive pipeline.
    1. Ensures directories exist.
    2. Aggregates memory logs from T005.
    3. Collects results from T017 (metrics), T018 (anova), T019 (sensitivity).
    4. Writes final aggregated report to data/results/metrics.json.
    """
    print("Starting T020: Orchestrator and Final Report Aggregation")
    
    # Ensure output directories exist
    ensure_directories()
    results_dir = get_results_dir()
    
    start_time = time.time()
    
    # 1. Parse and aggregate memory logs
    print("Parsing memory logs from previous stages...")
    raw_memory_logs = parse_memory_logs()
    memory_summary = aggregate_memory_metrics(raw_memory_logs)
    
    # 2. Collect evaluation results
    print("Collecting metrics evaluation results...")
    metrics_data = load_metrics_results()
    
    print("Collecting ANOVA results...")
    anova_data = load_anova_results()
    
    print("Collecting sensitivity analysis results...")
    sensitivity_data = load_sensitivity_results()
    
    end_time = time.time()
    orchestrator_wall_time = end_time - start_time
    
    # 3. Construct final report
    # We merge the specific metrics into a single report structure
    # as per FR-007 MetricReport schema concept.
    final_report = {
        "pipeline_version": "T020-orchestrator",
        "execution_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "memory_metrics": {
            "peak_ram_gb": memory_summary["peak_ram_gb"],
            "total_wall_time_seconds": memory_summary["total_wall_time_seconds"] + orchestrator_wall_time,
            "log_samples_analyzed": memory_summary["num_samples"]
        },
        "sparse_metrics": metrics_data.get("sparse", {}),
        "dense_metrics": metrics_data.get("dense", {}),
        "comparison": metrics_data.get("comparison", {}),
        "statistical_validation": {
            "anova": anova_data,
            "sensitivity": sensitivity_data
        },
        "status": "completed"
    }
    
    # 4. Write final report
    output_path = results_dir / "metrics.json"
    print(f"Writing final aggregated report to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print("T020 completed successfully.")
    print(f"Final report saved to: {output_path}")
    
    return final_report

if __name__ == "__main__":
    main()