"""
T016b: Execute streaming log extraction with explicit memory monitoring.

This script invokes the streaming parser (T016) while simultaneously
monitoring RSS memory usage via ResourceMonitor (T007). It validates
that peak memory usage remains under the 7GB threshold required by FR-007.

Output:
    data/results/extraction_memory_log.json
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path to ensure imports work regardless of cwd
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.resource_monitor import ResourceMonitor
from src.features.extract import process_logs_streaming


def run_extraction_with_monitoring() -> Dict[str, Any]:
    """
    Runs the streaming extraction process while monitoring memory.
    
    Returns a dictionary containing the results of the execution and
    memory statistics.
    """
    # Configuration
    raw_data_dir = project_root / "data" / "raw"
    output_dir = project_root / "data" / "results"
    output_file = output_dir / "extraction_memory_log.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the resource monitor
    # We monitor RSS (Resident Set Size) which is the actual physical memory used
    monitor = ResourceMonitor()
    monitor.start()
    
    start_time = time.time()
    success = False
    error_message = None
    peak_rss_mb = 0.0
    rows_processed = 0
    
    try:
        # Verify input data exists before starting
        if not raw_data_dir.exists():
            raise FileNotFoundError(
                f"Raw data directory not found: {raw_data_dir}. "
                "Run T011 to download the EnterpriseClawBench dataset first."
            )
        
        # Find log files in the raw data directory
        log_files = list(raw_data_dir.glob("*.jsonl")) + list(raw_data_dir.glob("*.json"))
        
        if not log_files:
            raise FileNotFoundError(
                f"No .json or .jsonl files found in {raw_data_dir}. "
                "Ensure the dataset has been downloaded correctly."
            )
        
        print(f"Starting extraction on {len(log_files)} file(s)...")
        
        # Execute the streaming extraction process
        # This generator yields processed feature chunks
        total_rows = 0
        for chunk in process_logs_streaming(log_files):
            total_rows += len(chunk)
            rows_processed = total_rows
            
            # Periodically check memory usage (every 1000 rows)
            if total_rows % 1000 == 0:
                current_stats = monitor.get_current_stats()
                current_rss_mb = current_stats.get('rss_mb', 0)
                if current_rss_mb > peak_rss_mb:
                    peak_rss_mb = current_rss_mb
                
                # Log progress
                print(f"Processed {total_rows} rows. Current RSS: {current_rss_mb:.2f} MB")
        
        # Final memory check
        final_stats = monitor.get_current_stats()
        peak_rss_mb = max(peak_rss_mb, final_stats.get('rss_mb', 0))
        
        # Calculate duration
        end_time = time.time()
        duration_seconds = end_time - start_time
        
        success = True
        
    except Exception as e:
        error_message = str(e)
        success = False
        # Stop monitoring even on error
        monitor.stop()
        raise
    finally:
        # Stop the monitor to ensure final stats are captured
        monitor.stop()
        
        # If we haven't checked peak yet (e.g., very small dataset), get it now
        if not success and peak_rss_mb == 0:
            stats = monitor.get_current_stats()
            peak_rss_mb = stats.get('rss_mb', 0)
    
    # Determine compliance with FR-007 (peak RSS < 7GB)
    # 7GB = 7 * 1024 MB = 7168 MB
    threshold_mb = 7 * 1024
    is_compliant = peak_rss_mb < threshold_mb
    
    # Prepare the result report
    result = {
        "status": "success" if success else "failed",
        "execution_details": {
            "files_processed": len(log_files) if success else 0,
            "rows_processed": rows_processed,
            "duration_seconds": round(duration_seconds, 2) if success else 0,
            "error_message": error_message
        },
        "memory_statistics": {
            "peak_rss_mb": round(peak_rss_mb, 2),
            "peak_rss_gb": round(peak_rss_mb / 1024, 2),
            "threshold_mb": threshold_mb,
            "threshold_gb": threshold_mb / 1024,
            "is_compliant": is_compliant
        },
        "fr_007_compliance": {
            "requirement": "Peak RSS must be < 7GB",
            "passed": is_compliant,
            "peak_observed_gb": round(peak_rss_mb / 1024, 2)
        }
    }
    
    # Write the report to disk
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nExtraction complete.")
    print(f"Peak Memory Usage: {peak_rss_mb/1024:.2f} GB")
    print(f"Compliance (FR-007): {'PASS' if is_compliant else 'FAIL'}")
    print(f"Report saved to: {output_file}")
    
    return result


def main():
    """Entry point for the script."""
    try:
        run_extraction_with_monitoring()
    except Exception as e:
        # Ensure we still write a failure report if the script crashes
        output_file = project_root / "data" / "results" / "extraction_memory_log.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        failure_report = {
            "status": "failed",
            "execution_details": {
                "error_message": str(e),
                "rows_processed": 0
            },
            "memory_statistics": {
                "peak_rss_mb": 0,
                "threshold_mb": 7 * 1024,
                "is_compliant": False
            },
            "fr_007_compliance": {
                "requirement": "Peak RSS must be < 7GB",
                "passed": False,
                "peak_observed_gb": 0
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(failure_report, f, indent=2)
        
        print(f"FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()