import os
import sys
import json
import cProfile
import pstats
import io
import time
import resource
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing pipeline components
from scripts.ingest import main as ingest_main
from scripts.extract_features import main as extract_features_main
from scripts.train_model import main as train_model_main
from config.loader import get_config, get_dataset_path

def get_memory_usage_mb():
    """Get current memory usage in MB."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux/macOS
        return usage.ru_maxrss / 1024
    except Exception:
        return 0.0

def run_with_profiler(func, *args, **kwargs) -> Dict[str, Any]:
    """Run a function with cProfile and return statistics."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    start_mem = get_memory_usage_mb()
    
    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        success = False
        result = str(e)
    finally:
        profiler.disable()
        end_time = time.time()
        end_mem = get_memory_usage_mb()
    
    # Get stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    stats_text = s.getvalue()
    
    return {
        "success": success,
        "result": result,
        "runtime_seconds": end_time - start_time,
        "memory_start_mb": start_mem,
        "memory_end_mb": end_mem,
        "memory_peak_mb": max(start_mem, end_mem),
        "profile_stats": stats_text
    }

def run_full_pipeline():
    """Run the full pipeline stages with profiling."""
    config = get_config()
    
    # Ensure directories exist
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "pipeline_start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stages": {}
    }
    
    total_runtime = 0.0
    peak_memory = 0.0
    
    # Stage 1: Ingestion
    print("Running Stage 1: Ingestion...")
    stage1_start = time.time()
    stage1_mem = get_memory_usage_mb()
    
    try:
        # Run ingestion (this will fetch real data)
        ingest_main()
        stage1_success = True
    except Exception as e:
        stage1_success = False
        print(f"Ingestion failed: {e}")
    
    stage1_runtime = time.time() - stage1_start
    stage1_mem_end = get_memory_usage_mb()
    stage1_peak = max(stage1_mem, stage1_mem_end)
    
    results["stages"]["ingestion"] = {
        "success": stage1_success,
        "runtime_seconds": stage1_runtime,
        "memory_start_mb": stage1_mem,
        "memory_end_mb": stage1_mem_end,
        "memory_peak_mb": stage1_peak
    }
    
    if stage1_success:
        total_runtime += stage1_runtime
        peak_memory = max(peak_memory, stage1_peak)
    
    # Stage 2: Feature Extraction
    print("Running Stage 2: Feature Extraction...")
    stage2_start = time.time()
    stage2_mem = get_memory_usage_mb()
    
    try:
        extract_features_main()
        stage2_success = True
    except Exception as e:
        stage2_success = False
        print(f"Feature extraction failed: {e}")
    
    stage2_runtime = time.time() - stage2_start
    stage2_mem_end = get_memory_usage_mb()
    stage2_peak = max(stage2_mem, stage2_mem_end)
    
    results["stages"]["feature_extraction"] = {
        "success": stage2_success,
        "runtime_seconds": stage2_runtime,
        "memory_start_mb": stage2_mem,
        "memory_end_mb": stage2_mem_end,
        "memory_peak_mb": stage2_peak
    }
    
    if stage2_success:
        total_runtime += stage2_runtime
        peak_memory = max(peak_memory, stage2_peak)
    
    # Stage 3: Model Training
    print("Running Stage 3: Model Training...")
    stage3_start = time.time()
    stage3_mem = get_memory_usage_mb()
    
    try:
        train_model_main()
        stage3_success = True
    except Exception as e:
        stage3_success = False
        print(f"Model training failed: {e}")
    
    stage3_runtime = time.time() - stage3_start
    stage3_mem_end = get_memory_usage_mb()
    stage3_peak = max(stage3_mem, stage3_mem_end)
    
    results["stages"]["model_training"] = {
        "success": stage3_success,
        "runtime_seconds": stage3_runtime,
        "memory_start_mb": stage3_mem,
        "memory_end_mb": stage3_mem_end,
        "memory_peak_mb": stage3_peak
    }
    
    if stage3_success:
        total_runtime += stage3_runtime
        peak_memory = max(peak_memory, stage3_peak)
    
    # Final summary
    results["pipeline_end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    results["total_runtime_seconds"] = total_runtime
    results["total_runtime_hours"] = total_runtime / 3600
    results["peak_memory_mb"] = peak_memory
    
    # Check constraints
    results["constraint_satisfied"] = {
        "runtime_under_6h": total_runtime < 6 * 3600,
        "memory_under_7gb": peak_memory < 7 * 1024
    }
    
    results["overall_success"] = (
        stage1_success and stage2_success and stage3_success and
        results["constraint_satisfied"]["runtime_under_6h"] and
        results["constraint_satisfied"]["memory_under_7gb"]
    )
    
    return results

def main():
    """Main entry point for profiling the pipeline."""
    print("=" * 60)
    print("LLMXive Pipeline Performance Profiler")
    print("=" * 60)
    
    results = run_full_pipeline()
    
    # Write results to log files
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Write JSON summary
    json_path = logs_dir / "pipeline_runtime.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Write detailed profile log
    log_path = logs_dir / "runtime_profile.log"
    with open(log_path, 'w') as f:
        f.write("Pipeline Performance Profile\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Start Time: {results['pipeline_start_time']}\n")
        f.write(f"End Time: {results['pipeline_end_time']}\n")
        f.write(f"Total Runtime: {results['total_runtime_seconds']:.2f} seconds ({results['total_runtime_hours']:.2f} hours)\n")
        f.write(f"Peak Memory: {results['peak_memory_mb']:.2f} MB\n\n")
        
        f.write("Stage Details:\n")
        f.write("-" * 60 + "\n")
        for stage_name, stage_data in results['stages'].items():
            f.write(f"\n{stage_name.upper()}:\n")
            f.write(f"  Success: {stage_data['success']}\n")
            f.write(f"  Runtime: {stage_data['runtime_seconds']:.2f} seconds\n")
            f.write(f"  Memory Start: {stage_data['memory_start_mb']:.2f} MB\n")
            f.write(f"  Memory End: {stage_data['memory_end_mb']:.2f} MB\n")
            f.write(f"  Memory Peak: {stage_data['memory_peak_mb']:.2f} MB\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("Constraint Verification:\n")
        f.write(f"  Runtime < 6 hours: {results['constraint_satisfied']['runtime_under_6h']}\n")
        f.write(f"  Memory < 7 GB: {results['constraint_satisfied']['memory_under_7gb']}\n")
        f.write(f"  Overall Success: {results['overall_success']}\n")
    
    print(f"\nResults written to:")
    print(f"  - {json_path}")
    print(f"  - {log_path}")
    
    if results['overall_success']:
        print("\n✓ All performance constraints satisfied!")
        sys.exit(0)
    else:
        print("\n✗ Performance constraints NOT satisfied!")
        if not results['constraint_satisfied']['runtime_under_6h']:
            print(f"  - Runtime exceeded 6 hours: {results['total_runtime_hours']:.2f}h")
        if not results['constraint_satisfied']['memory_under_7gb']:
            print(f"  - Memory exceeded 7 GB: {results['peak_memory_mb']:.2f} MB")
        sys.exit(1)

if __name__ == "__main__":
    main()
