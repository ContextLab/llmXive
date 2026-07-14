import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    get_raw_dir, get_results_dir, get_features_dir, get_stratified_dir,
    ensure_directories, get_config_summary, get_max_ram_mb
)
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor

# Import phase modules
from data.download import main as download_main
from data.stratify import main as stratify_main
from data.extract_features import main as extract_features_main
from eval.download_dense_baseline import main as download_dense_baseline_main
from geometry.run_pipeline import main as geometry_main
from geometry.aggregate_warps import main as aggregate_warps_main
from eval.metrics import main as metrics_main
from eval.anova import main as anova_main
from eval.sensitivity import main as sensitivity_main
from eval.report import main as report_main

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument("--phase", type=str, required=True, 
                        choices=["data_prepare", "extract_features", "compute_geometry", "evaluate"],
                        help="Which phase of the pipeline to run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args()

def parse_memory_logs(log_path: Path) -> Dict[str, Any]:
    """
    Parse raw memory_profiler logs from T005 and aggregate them.
    Returns a dict with peak RAM and other stats.
    """
    if not log_path.exists():
        return {"peak_ram_mb": 0.0, "log_path": str(log_path), "status": "missing"}
    
    try:
        content = log_path.read_text()
        # Simple heuristic: look for "Maximum memory usage" or similar patterns
        # Depending on memory_profiler output format, adjust parsing
        lines = content.splitlines()
        max_mem = 0.0
        for line in lines:
            if "MB" in line:
                try:
                    # Extract number before MB
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "MB" and i > 0:
                            val = float(parts[i-1])
                            if val > max_mem:
                                max_mem = val
                except ValueError:
                    continue
        
        return {
            "peak_ram_mb": max_mem,
            "log_path": str(log_path),
            "status": "parsed",
            "raw_lines_analyzed": len(lines)
        }
    except Exception as e:
        return {"peak_ram_mb": 0.0, "log_path": str(log_path), "status": "error", "error": str(e)}

def phase_data_prepare():
    """Phase 1 & 2: Download data and prepare dense baseline."""
    print("Starting Phase: Data Preparation")
    ensure_directories()
    set_global_seed(42) # Default seed if not passed via args

    # 1. Download RealEstate10K (T007)
    print("Running: Download Dataset")
    try:
        download_main()
    except Exception as e:
        print(f"Warning: Dataset download may have issues: {e}")
        # Continue, as T016b (dense baseline) might still run or we might have cached data

    # 2. Download/Generate Dense Baseline (T016b) - CRITICAL FOR US3
    print("Running: Download/Generate Dense Baseline")
    ret = download_dense_baseline_main()
    if ret != 0:
        print("ERROR: Dense baseline generation failed. Pipeline cannot proceed for US3.")
        return 1

    # 3. Stratify Dataset (T008) - Optional if we just need baseline, but part of flow
    print("Running: Stratify Dataset")
    try:
        stratify_main()
    except SystemExit as e:
        if e.code == 1:
            print("INFO: Stratification aborted (n<50). Skipping to geometry if possible.")
        else:
            raise

    print("Phase: Data Preparation Complete")
    return 0

def phase_extract_features():
    """Phase 3: Extract sparse features."""
    print("Starting Phase: Extract Features")
    ensure_directories()
    
    print("Running: Extract Sparse Features")
    ret = extract_features_main()
    if ret != 0:
        print("ERROR: Feature extraction failed.")
        return 1
    
    print("Phase: Extract Features Complete")
    return 0

def phase_compute_geometry():
    """Phase 4: Compute geometry and warp."""
    print("Starting Phase: Compute Geometry")
    ensure_directories()

    # 1. Run Solver (T010)
    print("Running: Geometry Solver")
    try:
        geometry_main()
    except Exception as e:
        print(f"Error in geometry solver: {e}")
        return 1

    # 2. Aggregate Warps (T012)
    print("Running: Aggregate Warped Frames")
    try:
        aggregate_warps_main()
    except Exception as e:
        print(f"Error in aggregation: {e}")
        return 1

    print("Phase: Compute Geometry Complete")
    return 0

def phase_evaluate():
    """Phase 5 & 6: Metrics, ANOVA, Sensitivity, Report."""
    print("Starting Phase: Evaluation")
    ensure_directories()

    # 1. Compute Metrics (T017) - Requires dense baseline and sparse warps
    print("Running: Compute Metrics")
    try:
        metrics_main()
    except Exception as e:
        print(f"Error in metrics computation: {e}")
        return 1

    # 2. ANOVA (T018)
    print("Running: ANOVA Analysis")
    try:
        anova_main()
    except Exception as e:
        print(f"Error in ANOVA: {e}")
        return 1

    # 3. Sensitivity (T019)
    print("Running: Sensitivity Analysis")
    try:
        sensitivity_main()
    except Exception as e:
        print(f"Error in sensitivity analysis: {e}")
        return 1

    # 4. Report (T021)
    print("Running: Generate Report")
    try:
        report_main()
    except Exception as e:
        print(f"Error in report generation: {e}")
        return 1

    print("Phase: Evaluation Complete")
    return 0

def main():
    args = parse_args()
    
    # Initialize Memory Monitor
    monitor = MemoryMonitor()
    monitor.start()

    start_time = time.time()
    ret_code = 0

    try:
        if args.phase == "data_prepare":
            ret_code = phase_data_prepare()
        elif args.phase == "extract_features":
            ret_code = phase_extract_features()
        elif args.phase == "compute_geometry":
            ret_code = phase_compute_geometry()
        elif args.phase == "evaluate":
            ret_code = phase_evaluate()
    except Exception as e:
        print(f"FATAL ERROR in {args.phase}: {e}")
        import traceback
        traceback.print_exc()
        ret_code = 1
    finally:
        elapsed = time.time() - start_time
        monitor.stop()
        
        # Log final stats
        print(f"Phase {args.phase} finished in {elapsed:.2f}s")
        
        # Aggregate Memory Profiler logs (T020 specific requirement)
        # The memory monitor usually writes to a log file or we can read from the standard location
        # Assuming the memory monitor writes to a file in the results or a standard location.
        # We will construct the path based on the project structure.
        results_dir = get_results_dir()
        log_path = results_dir / "memory_profile.log"
        
        memory_stats = parse_memory_logs(log_path)
        monitor_stats = {
            "peak_ram_mb": monitor.get_peak_memory_mb() if hasattr(monitor, 'get_peak_memory_mb') else memory_stats.get("peak_ram_mb", 0.0),
            "wall_clock_seconds": elapsed
        }
        
        # Merge stats
        final_stats = {
            "phase": args.phase,
            "wall_clock_seconds": elapsed,
            "memory": {
                "peak_ram_mb": monitor_stats["peak_ram_mb"],
                "log_parsed": memory_stats
            }
        }
        
        # Write to metrics.json (or update existing if we are in evaluate phase)
        # The task says "aggregate them into the final data/results/metrics.json"
        # We will append/update this file.
        metrics_path = results_dir / "metrics.json"
        
        existing_metrics = {}
        if metrics_path.exists():
            try:
                with open(metrics_path, 'r') as f:
                    existing_metrics = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_metrics = {}
        
        # Update or add the current phase stats
        phase_key = f"phase_{args.phase}"
        existing_metrics[phase_key] = final_stats
        
        with open(metrics_path, 'w') as f:
            json.dump(existing_metrics, f, indent=2)
        
        print(f"Memory stats aggregated to {metrics_path}")

        if ret_code == 0:
            print("SUCCESS")
        else:
            print("FAILED")
    
    sys.exit(ret_code)

if __name__ == "__main__":
    main()