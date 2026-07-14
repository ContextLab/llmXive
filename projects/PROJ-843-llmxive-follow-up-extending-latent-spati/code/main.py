import argparse
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, Any

from config import (
    get_project_root, get_raw_dir, get_results_dir, 
    get_features_dir, get_stratified_dir, ensure_directories
)
from data.download import main as download_main
from data.stratify import main as stratify_main
from data.extract_features import main as extract_features_main
from geometry.solver import main as solver_main
from geometry.warp import main as warp_main
from geometry.aggregate_warps import main as aggregate_warps_main
from eval.download_dense_baseline import main as download_dense_main
from eval.metrics import main as metrics_main
from eval.anova import main as anova_main
from eval.sensitivity import main as sensitivity_main
from eval.report import main as report_main
from utils.memory_monitor import MemoryMonitor, parse_memory_logs

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument("--phase", type=str, required=True, 
                        choices=["data_prepare", "extract_features", "compute_geometry", 
                                 "download_dense_baseline", "evaluate", "all"])
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()

def parse_memory_logs() -> Dict[str, Any]:
    """Aggregate memory logs from all phases."""
    results_dir = get_results_dir()
    logs = []
    for f in results_dir.glob("mem_*.json"):
        try:
            with open(f, 'r') as file:
                logs.append(json.load(file))
        except Exception:
            pass
    
    total_peak = max([l.get('peak_ram_mb', 0) for l in logs] + [0])
    total_time = sum([l.get('elapsed_seconds', 0) for l in logs])
    return {
        "peak_ram_mb": total_peak,
        "total_elapsed_seconds": total_time,
        "logs": logs
    }

def phase_data_prepare():
    print("=== Phase: Data Preparation ===")
    ensure_directories(get_raw_dir(), get_stratified_dir())
    # Download
    print("Downloading dataset...")
    download_main()
    # Stratify
    print("Stratifying dataset...")
    stratify_main()
    print("Data preparation complete.")

def phase_extract_features():
    print("=== Phase: Extract Features ===")
    ensure_directories(get_features_dir())
    extract_features_main()
    print("Feature extraction complete.")

def phase_compute_geometry():
    print("=== Phase: Compute Geometry ===")
    ensure_directories(get_results_dir())
    # Solver
    print("Running Solver...")
    solver_main()
    # Warp
    print("Running Warp...")
    warp_main()
    # Aggregate
    print("Aggregating Warps...")
    aggregate_warps_main()
    print("Geometry computation complete.")

def phase_download_dense_baseline():
    print("=== Phase: Download Dense Baseline ===")
    ensure_directories(get_raw_dir())
    download_dense_main()
    print("Dense baseline download complete.")

def phase_evaluate():
    print("=== Phase: Evaluation ===")
    ensure_directories(get_results_dir())
    
    # Run Metrics
    print("Calculating Metrics...")
    metrics_main()
    
    # Run ANOVA
    print("Running ANOVA...")
    anova_main()
    
    # Run Sensitivity
    print("Running Sensitivity Analysis...")
    sensitivity_main()
    
    # Generate Report
    print("Generating Report...")
    report_main()
    
    print("Evaluation complete.")

def aggregate_final_metrics():
    print("=== Aggregating Final Metrics ===")
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    
    memory_stats = parse_memory_logs()
    
    # Load metrics (primary metrics from metrics.py)
    metrics_path = results_dir / "metrics.json"
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    
    # Load ANOVA results
    anova_path = results_dir / "anova_results.json"
    anova = {}
    if anova_path.exists():
        with open(anova_path, 'r') as f:
            anova = json.load(f)
    
    # Load Sensitivity Analysis results
    sens_path = results_dir / "sensitivity_analysis.json"
    sensitivity = {}
    if sens_path.exists():
        with open(sens_path, 'r') as f:
            sensitivity = json.load(f)
    
    # Compile the final report according to MetricReport schema
    final_report = {
        "memory_stats": memory_stats,
        "metrics": metrics,
        "anova": anova,
        "sensitivity": sensitivity,
        "timestamp": time.time()
    }
    
    # Write the final aggregated report to data/results/metrics.json
    # as per task T020 requirement to parse logs and aggregate into metrics.json
    out_path = results_dir / "metrics.json"
    with open(out_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"Final aggregated metrics saved to {out_path}")
    return final_report

def main():
    args = parse_args()
    monitor = MemoryMonitor(log_path=get_results_dir() / "main_monitor.json")
    monitor.start()
    
    try:
        if args.phase == "data_prepare":
            phase_data_prepare()
        elif args.phase == "extract_features":
            phase_extract_features()
        elif args.phase == "compute_geometry":
            phase_compute_geometry()
        elif args.phase == "download_dense_baseline":
            phase_download_dense_baseline()
        elif args.phase == "evaluate":
            phase_evaluate()
        elif args.phase == "all":
            phase_data_prepare()
            phase_extract_features()
            phase_compute_geometry()
            phase_download_dense_baseline()
            phase_evaluate()
            aggregate_final_metrics()
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()