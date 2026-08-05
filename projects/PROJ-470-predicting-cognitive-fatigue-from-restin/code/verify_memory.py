"""
Memory verification script for the cognitive fatigue pipeline.
Runs the full pipeline (Download -> Preprocess -> Features -> Analysis)
and measures peak RSS (Resident Set Size) using Python's resource module.
Writes results to data/analysis/memory_report.json.
"""
import os
import sys
import json
import resource
import time
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from download import main as run_download
from preprocess import main as run_preprocess
from features import main as run_features
from analysis import main as run_analysis

# Configuration
MEMORY_LIMIT_MB = 7 * 1024  # 7 GB in MB
REPORT_PATH = project_root / "data" / "analysis" / "memory_report.json"

def get_peak_memory_mb():
    """Get peak Resident Set Size (RSS) in MB for the current process."""
    # rusage.ru_maxrss is in KB on Linux, MB on macOS
    # We normalize to MB for consistency
    usage = resource.getrusage(resource.RUSAGE_SELF)
    maxrss_kb = usage.ru_maxrss
    
    # On Linux, ru_maxrss is in KB. On macOS, it's in bytes (sometimes) or KB.
    # Standard Linux behavior: KB
    if sys.platform.startswith('linux'):
        return maxrss_kb / 1024.0
    elif sys.platform == 'darwin':
        # macOS reports in bytes typically, but let's check standard
        # Actually, on macOS, ru_maxrss is in bytes.
        return maxrss_kb / (1024 * 1024)
    else:
        # Fallback: assume KB
        return maxrss_kb / 1024.0

def check_sample_size():
    """
    Check if we have sufficient sample size (N >= 30) from the feature files.
    Returns True if N >= 30, False otherwise.
    """
    lzc_path = project_root / "data" / "processed" / "lzc_metrics.csv"
    if not lzc_path.exists():
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(lzc_path)
        unique_participants = df['participant_id'].nunique()
        return unique_participants >= 30
    except Exception:
        return False

def run_pipeline():
    """Run the full pipeline stages sequentially."""
    stages = [
        ("Download", run_download),
        ("Preprocess", run_preprocess),
        ("Features", run_features),
        ("Analysis", run_analysis)
    ]
    
    for name, stage_func in stages:
        print(f"Running stage: {name}...")
        try:
            stage_func()
            print(f"Stage {name} completed successfully.")
        except SystemExit as e:
            if e.code != 0:
                print(f"Stage {name} failed with exit code {e.code}")
                raise
        except Exception as e:
            print(f"Stage {name} raised an exception: {e}")
            raise

def main():
    """Main entry point for memory verification."""
    print("Starting memory verification pipeline...")
    
    # Ensure output directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Check sample size first
    has_sufficient_data = check_sample_size()
    
    if not has_sufficient_data:
        print("WARNING: Insufficient real data (N < 30) for full memory profiling.")
        print("Skipping full pipeline memory profile.")
        
        result = {
            "peak_memory_mb": 0.0,
            "limit_mb": MEMORY_LIMIT_MB,
            "status": "SKIPPED",
            "reason": "Insufficient sample size (N < 30) in real data."
        }
        
        with open(REPORT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Report written to {REPORT_PATH}")
        return
    
    print(f"Running full pipeline on real data (N >= 30). Memory limit: {MEMORY_LIMIT_MB} MB")
    
    try:
        # Run the pipeline
        run_pipeline()
        
        # Get peak memory usage
        peak_memory = get_peak_memory_mb()
        
        # Determine status
        status = "PASS" if peak_memory <= MEMORY_LIMIT_MB else "FAIL"
        
        result = {
            "peak_memory_mb": peak_memory,
            "limit_mb": MEMORY_LIMIT_MB,
            "status": status
        }
        
        with open(REPORT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Pipeline completed. Peak memory: {peak_memory:.2f} MB (Limit: {MEMORY_LIMIT_MB} MB)")
        print(f"Status: {status}")
        print(f"Report written to {REPORT_PATH}")
        
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        
        # Even on failure, record the memory usage up to that point
        peak_memory = get_peak_memory_mb()
        result = {
            "peak_memory_mb": peak_memory,
            "limit_mb": MEMORY_LIMIT_MB,
            "status": "FAIL",
            "error": str(e)
        }
        
        with open(REPORT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        sys.exit(1)

if __name__ == "__main__":
    main()