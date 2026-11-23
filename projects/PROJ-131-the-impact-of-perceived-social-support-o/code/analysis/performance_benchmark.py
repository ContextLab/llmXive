import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

def run_benchmark(logger: logging.Logger) -> Dict[str, Any]:
    """Run performance benchmark and return timing data."""
    import pandas as pd
    
    start = time.time()
    
    # Load cohort
    cohort_path = project_root / "data" / "results" / "analysis_cohort.csv"
    if cohort_path.exists():
        df = pd.read_csv(cohort_path)
        logger.info(f"Loaded cohort: {len(df)} rows")
    else:
        logger.warning("Cohort not found. Skipping load benchmark.")
        df = None
    
    load_time = time.time() - start
    
    # Simulate processing time (placeholder for actual benchmark)
    process_start = time.time()
    if df is not None:
        _ = df.describe()
    process_time = time.time() - process_start
    
    total_time = time.time() - start
    
    return {
        "load_time_sec": load_time,
        "process_time_sec": process_time,
        "total_time_sec": total_time,
        "n_rows": len(df) if df is not None else 0
    }

def main():
    """Entry point for performance benchmark (T062)."""
    logger = get_logger(__name__)
    logger.info("Running Performance Benchmark")
    
    try:
        results = run_benchmark(logger)
        
        # Save report
        output_path = project_root / "data" / "results" / "performance_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Performance report saved to {output_path}")
        logger.info(f"Total pipeline time: {results['total_time_sec']:.2f}s")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()