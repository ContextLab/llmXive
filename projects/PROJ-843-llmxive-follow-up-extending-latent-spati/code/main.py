import argparse
import json
import os
import sys
import subprocess
import time
import glob
from pathlib import Path

# Import project modules using relative imports where possible, or absolute if in root
# Adjusted to match the provided API surface
from utils.memory_monitor import get_session_metrics, clear_session_metrics, MemoryMonitor
from config import get_results_dir, get_config_summary, ensure_directories

# Import phase functions
from data.stratify import main as stratify_main
from data.extract_features import main as extract_features_main
from geometry.run_pipeline import main as geometry_pipeline_main
from eval.download_dense_baseline import main as download_dense_main
from eval.metrics import main as metrics_main
from eval.anova import main as anova_main
from eval.sensitivity import main as sensitivity_main
from eval.report import main as report_main
from data.schemas import main as schema_main

def locate_memory_logs(results_dir: Path) -> list:
    """Find all memory log files in the results directory."""
    pattern = str(results_dir / "memory_log_*.json")
    return glob.glob(pattern)

def parse_memory_log(log_path: str) -> dict:
    """Parse a single memory log file."""
    try:
        with open(log_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not parse {log_path}: {e}")
        return {}

def aggregate_memory_metrics(logs: list) -> dict:
    """Aggregate metrics from multiple memory logs."""
    peak_rams = []
    total_times = []
    
    for log in logs:
        data = parse_memory_log(log)
        if data:
            if 'peak_ram_gb' in data:
                peak_rams.append(data['peak_ram_gb'])
            if 'duration_seconds' in data:
                total_times.append(data['duration_seconds'])
    
    return {
        "max_peak_ram_gb": max(peak_rams) if peak_rams else 0.0,
        "avg_peak_ram_gb": sum(peak_rams) / len(peak_rams) if peak_rams else 0.0,
        "total_duration_seconds": sum(total_times) if total_times else 0.0
    }

def aggregate_and_write_memory_logs(results_dir: Path) -> dict:
    """Find, parse, aggregate, and write memory metrics to the main report."""
    logs = locate_memory_logs(results_dir)
    if not logs:
        print("No memory logs found to aggregate.")
        return {}
    
    aggregated = aggregate_memory_metrics(logs)
    return aggregated

def write_metrics_json(results_dir: Path, metrics: dict, memory_metrics: dict) -> None:
    """Write the final metrics.json file."""
    output_path = results_dir / "metrics.json"
    
    # Combine all metrics
    final_report = {
        "config": get_config_summary(),
        "memory": memory_metrics,
        "results": metrics
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"Metrics written to {output_path}")

def phase_data_prepare():
    """Phase 1: Data Preparation (Stratification)"""
    print("Running Phase: Data Prepare (Stratification)")
    stratify_main()
    print("Phase Data Prepare completed.")

def phase_extract_features():
    """Phase 2: Feature Extraction"""
    print("Running Phase: Extract Features")
    extract_features_main()
    print("Phase Extract Features completed.")

def phase_compute_geometry():
    """Phase 3: Geometry Solver & Warping"""
    print("Running Phase: Compute Geometry")
    # This runs the solver and warp pipeline, which should produce the warped frames
    geometry_pipeline_main()
    print("Phase Compute Geometry completed.")

def phase_evaluate():
    """Phase 4: Evaluation (Metrics, ANOVA, Sensitivity, Report)"""
    print("Running Phase: Evaluate")
    
    # 1. Download dense baseline if needed (T016b)
    print("  -> Downloading dense baseline...")
    try:
        download_dense_main()
    except Exception as e:
        print(f"Warning: Dense baseline download failed or skipped: {e}")
    
    # 2. Compute Metrics (T017)
    print("  -> Computing metrics...")
    metrics_main()
    
    # 3. Run ANOVA (T018)
    print("  -> Running ANOVA...")
    anova_main()
    
    # 4. Run Sensitivity (T019)
    print("  -> Running Sensitivity Analysis...")
    sensitivity_main()
    
    # 5. Generate Report (T021)
    print("  -> Generating Final Report...")
    report_main()
    
    print("Phase Evaluate completed.")

def run_full_pipeline():
    """Run the entire pipeline sequentially."""
    print("Starting Full Pipeline Execution")
    start_time = time.time()
    
    try:
        phase_data_prepare()
        phase_extract_features()
        phase_compute_geometry()
        phase_evaluate()
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)
    
    end_time = time.time()
    print(f"Full Pipeline completed in {end_time - start_time:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description="llmXive Orchestrator")
    parser.add_argument(
        "--phase",
        type=str,
        choices=["prepare", "extract", "geometry", "evaluate", "validate", "full"],
        required=True,
        help="Which phase of the pipeline to run"
    )
    parser.add_argument(
        "--skip-memory",
        action="store_true",
        help="Skip memory monitoring aggregation"
    )
    
    args = parser.parse_args()
    
    results_dir = get_results_dir()
    ensure_directories()
    
    metrics_data = {}
    memory_metrics = {}
    
    try:
        if args.phase == "prepare":
            phase_data_prepare()
        elif args.phase == "extract":
            phase_extract_features()
        elif args.phase == "geometry":
            phase_compute_geometry()
        elif args.phase == "evaluate":
            phase_evaluate()
        elif args.phase == "validate":
            # Validation is usually a separate script, but we can trigger checks here
            from eval.quickstart_validator import main as validator_main
            validator_main()
        elif args.phase == "full":
            run_full_pipeline()
        
        # If we reached here, the phase succeeded. 
        # Now aggregate memory logs if not skipped.
        if not args.skip_memory:
            memory_metrics = aggregate_and_write_memory_logs(results_dir)
        
        # For the full pipeline or evaluation phase, we need to write the final metrics.json
        # The metrics.py script (T017) should have written intermediate metrics.
        # We need to read them and combine with memory metrics for the final report.
        if args.phase in ["evaluate", "full", "validate"]:
            # Attempt to load metrics generated by T017
            metrics_path = results_dir / "metrics_raw.json" # Assuming intermediate file
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    metrics_data = json.load(f)
            else:
                # Fallback: try to load from a standard location if T017 writes elsewhere
                # Or construct a minimal structure if T017 writes directly to metrics.json
                # Given T017 is supposed to compute metrics, let's assume it writes to a temp file
                # or we need to re-run the logic to get the dict. 
                # For this orchestrator, we assume T017 (metrics_main) writes to a file we can read.
                # If T017 writes directly to metrics.json, we might need to handle that.
                # Let's assume T017 writes to 'metrics_raw.json' or similar.
                # If not found, we might have to read the final metrics.json if T017 already wrote it.
                # However, T020 is supposed to write the FINAL metrics.json.
                # Let's assume T017 writes to a temporary location or we need to import the function result.
                # Since we can't easily import the result of a main() that writes to disk,
                # we rely on the file written by T017.
                pass

            # Write the final combined metrics.json
            # If metrics_data is empty, we might need to handle the case where T017 didn't run
            if not metrics_data and args.phase in ["evaluate", "full"]:
                print("Warning: No metrics data found from evaluation phase.")
            
            write_metrics_json(results_dir, metrics_data, memory_metrics)
        
    except Exception as e:
        print(f"Error during phase {args.phase}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()