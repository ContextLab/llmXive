"""
Performance profiling and optimization for the llmXive pipeline.

This script runs the full pipeline under cProfile to identify bottlenecks
and measures runtime/memory usage against GitHub Actions constraints.

Deliverables:
- data/logs/runtime_profile.log: Raw cProfile output
- data/logs/pipeline_runtime.json: Summary metrics verifying SC-004
"""
import os
import sys
import json
import cProfile
import pstats
import io
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import pipeline stages
from scripts.ingest import main as ingest_main
from scripts.extract_features import main as extract_features_main
from scripts.train_model import main as train_model_main
from scripts.generate_ground_truth import main as generate_ground_truth_main
from scripts.finalize_features import main as finalize_features_main
from scripts.generate_model_report import main as generate_model_report_main

# Ensure log directory exists
log_dir = project_root / "data" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# GitHub Actions Free Tier Constraints
MAX_RUNTIME_HOURS = 6.0
MAX_RAM_GB = 7.0
TARGET_RUNTIME_HOURS = 5.0  # Optimization goal

def run_with_profiler(func, func_name: str) -> Tuple[float, float, Dict[str, Any]]:
    """
    Runs a function under cProfile and tracemalloc.
    Returns (runtime_seconds, peak_memory_gb, stats_dict).
    """
    # Start memory tracking
    tracemalloc.start()
    
    # Start timer
    start_time = time.perf_counter()
    
    # Run profiler
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        func()
    except Exception as e:
        # Re-raise but ensure profiling stops
        profiler.disable()
        tracemalloc.stop()
        raise e
    
    # Stop profiler
    profiler.disable()
    end_time = time.perf_counter()
    
    # Stop memory tracking
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    runtime_seconds = end_time - start_time
    peak_memory_gb = peak / (1024 ** 3)
    
    # Convert stats to dict for JSON serialization
    stats_stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stats_stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    # Extract top 10 cumulative times
    stats_dict = {
        "function": [],
        "cumulative_time": [],
        "call_count": []
    }
    
    # Parse the stats output to get top functions
    # Note: pstats.Stats doesn't have a direct 'top' method returning dict,
    # so we parse the string or use internal stats
    for func_key, (cc, nc, tt, ct, callers) in sorted(profiler.stats.items(), key=lambda x: x[1][3], reverse=True)[:10]:
        filename, line_num, func_name_inner = func_key
        stats_dict["function"].append(f"{os.path.basename(filename)}:{func_name_inner}")
        stats_dict["cumulative_time"].append(round(ct, 4))
        stats_dict["call_count"].append(nc)
    
    return runtime_seconds, peak_memory_gb, stats_dict

def run_full_pipeline():
    """
    Executes the full pipeline in sequence.
    Order: Ingest -> Ground Truth -> Features -> Model Training -> Report
    """
    print("Starting full pipeline execution...")
    
    # 1. Ingest (Download and parse)
    print("Stage 1: Ingest")
    # Note: ingest_main() might require arguments or config setup. 
    # We call it as defined in the API surface. 
    # If it requires args, we assume default behavior or config file exists.
    try:
        ingest_main()
    except SystemExit:
        pass # Expected if main() calls sys.exit()
    
    # 2. Generate Ground Truth (Run baseline)
    print("Stage 2: Generate Ground Truth")
    try:
        generate_ground_truth_main()
    except SystemExit:
        pass

    # 3. Extract Features
    print("Stage 3: Extract Features")
    try:
        extract_features_main()
    except SystemExit:
        pass

    # 4. Finalize Features
    print("Stage 4: Finalize Features")
    try:
        finalize_features_main()
    except SystemExit:
        pass

    # 5. Train Model
    print("Stage 5: Train Model")
    try:
        train_model_main()
    except SystemExit:
        pass

    # 6. Generate Report
    print("Stage 6: Generate Model Report")
    try:
        generate_model_report_main()
    except SystemExit:
        pass

    print("Pipeline execution completed.")

def main():
    """Main entry point for profiling."""
    print(f"Running pipeline profiling on: {project_root}")
    print(f"Constraints: Max Runtime {MAX_RUNTIME_HOURS}h, Max RAM {MAX_RAM_GB}GB")
    
    try:
        runtime_seconds, peak_memory_gb, top_stats = run_with_profiler(run_full_pipeline, "full_pipeline")
        
        runtime_hours = runtime_seconds / 3600
        
        # Check constraints
        runtime_ok = runtime_hours <= MAX_RUNTIME_HOURS
        memory_ok = peak_memory_gb <= MAX_RAM_GB
        optimization_goal_met = runtime_hours <= TARGET_RUNTIME_HOURS
        
        profile_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "constraints": {
                "max_runtime_hours": MAX_RUNTIME_HOURS,
                "max_ram_gb": MAX_RAM_GB,
                "target_runtime_hours": TARGET_RUNTIME_HOURS
            },
            "results": {
                "runtime_seconds": round(runtime_seconds, 2),
                "runtime_hours": round(runtime_hours, 4),
                "peak_memory_gb": round(peak_memory_gb, 4),
                "runtime_constraint_satisfied": runtime_ok,
                "memory_constraint_satisfied": memory_ok,
                "optimization_goal_met": optimization_goal_met,
                "status": "PASS" if (runtime_ok and memory_ok) else "FAIL"
            },
            "top_bottlenecks": top_stats
        }
        
        # Write JSON report
        report_path = log_dir / "pipeline_runtime.json"
        with open(report_path, "w") as f:
            json.dump(profile_data, f, indent=2)
        print(f"Pipeline runtime report written to: {report_path}")
        
        # Write raw profile log (simplified text representation)
        log_path = log_dir / "runtime_profile.log"
        with open(log_path, "w") as f:
            f.write(f"Pipeline Profile Summary\n")
            f.write(f"========================\n")
            f.write(f"Total Runtime: {runtime_hours:.4f} hours\n")
            f.write(f"Peak Memory: {peak_memory_gb:.4f} GB\n")
            f.write(f"Status: {profile_data['results']['status']}\n\n")
            f.write(f"Top 10 Bottlenecks (Cumulative Time):\n")
            for func, ct, nc in zip(top_stats["function"], top_stats["cumulative_time"], top_stats["call_count"]):
                f.write(f"  {func}: {ct:.4f}s ({nc} calls)\n")
        
        print(f"Raw profile log written to: {log_path}")
        
        # Print summary to stdout
        print("\n--- Performance Summary ---")
        print(f"Runtime: {runtime_hours:.4f} hours (Limit: {MAX_RUNTIME_HOURS}h)")
        print(f"Memory: {peak_memory_gb:.4f} GB (Limit: {MAX_RAM_GB}GB)")
        print(f"Status: {profile_data['results']['status']}")
        
        if not optimization_goal_met:
            print(f"WARNING: Runtime exceeds optimization target ({TARGET_RUNTIME_HOURS}h).")
            print("Consider optimizing identified bottlenecks.")
        
        if not runtime_ok or not memory_ok:
            print("CRITICAL: Constraints violated. Pipeline optimization required.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Profiling failed with error: {e}")
        # Write failure report
        report_path = log_dir / "pipeline_runtime.json"
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "status": "FAIL",
                "error": str(e)
            }, f, indent=2)
        raise

if __name__ == "__main__":
    main()
