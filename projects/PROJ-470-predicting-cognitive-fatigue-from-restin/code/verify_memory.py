"""
Memory verification script for the cognitive fatigue pipeline.
Measures peak RSS (Resident Set Size) of the main process while running
the full pipeline (Download -> Preprocess -> Features -> Analysis)
without memory_profiler overhead.
"""
import os
import sys
import json
import resource
import time
from pathlib import Path

# Ensure we are in the project root
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

# Constants
MEMORY_LIMIT_MB = 7168  # 7 GB
OUTPUT_PATH = PROJECT_ROOT / "data" / "analysis" / "memory_report.json"

def get_peak_memory_mb():
    """Get the peak resident set size of the current process in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, but in bytes on macOS.
    # We normalize to KB first, then to MB.
    if sys.platform == 'darwin':
        # macOS reports in bytes
        maxrss_kb = usage.ru_maxrss // 1024
    else:
        # Linux reports in KB
        maxrss_kb = usage.ru_maxrss
    
    return maxrss_kb / 1024.0

def run_download():
    """Run the download stage."""
    print("Running Download stage...")
    from download import main as download_main
    download_main()

def run_preprocess():
    """Run the preprocess stage."""
    print("Running Preprocess stage...")
    from preprocess import main as preprocess_main
    preprocess_main()

def run_features():
    """Run the features stage."""
    print("Running Features stage...")
    from features import main as features_main
    features_main()

def run_analysis():
    """Run the analysis stage."""
    print("Running Analysis stage...")
    from analysis import main as analysis_main
    analysis_main()

def run_report():
    """Run the report stage."""
    print("Running Report stage...")
    from report import main as report_main
    report_main()

def run_pipeline():
    """Run the full pipeline sequentially."""
    # Run stages sequentially. 
    # Note: If a stage fails, the script will exit with an error code,
    # and memory reporting will be incomplete (which is acceptable as the pipeline failed).
    run_download()
    run_preprocess()
    run_features()
    run_analysis()
    run_report()

def main():
    print("Starting memory verification pipeline...")
    print(f"Memory limit: {MEMORY_LIMIT_MB} MB")
    
    # Record initial memory
    start_mem = get_peak_memory_mb()
    print(f"Initial memory usage: {start_mem:.2f} MB")
    
    try:
        # Run the full pipeline
        run_pipeline()
        
        # Record final peak memory
        peak_mem = get_peak_memory_mb()
        print(f"Peak memory usage: {peak_mem:.2f} MB")
        
        # Determine status
        status = "PASS" if peak_mem <= MEMORY_LIMIT_MB else "FAIL"
        
        # Prepare report
        report = {
            "peak_memory_mb": round(peak_mem, 2),
            "limit_mb": MEMORY_LIMIT_MB,
            "status": status
        }
        
        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Memory report written to: {OUTPUT_PATH}")
        print(f"Status: {status}")
        
        if status == "FAIL":
            print(f"ERROR: Peak memory ({peak_mem:.2f} MB) exceeded limit ({MEMORY_LIMIT_MB} MB)")
            sys.exit(1)
            
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        # Even if pipeline fails, we should try to report the memory usage so far
        peak_mem = get_peak_memory_mb()
        report = {
            "peak_memory_mb": round(peak_mem, 2),
            "limit_mb": MEMORY_LIMIT_MB,
            "status": "ERROR",
            "error": str(e)
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        raise

if __name__ == "__main__":
    main()