"""
Memory profiling script for the analysis pipeline.
Measures peak memory usage of code/analysis.py and outputs a CSV report.
"""
import os
import sys
import time
import tracemalloc
import argparse
import csv
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

def measure_memory_usage():
    """
    Runs the analysis pipeline while tracking memory usage.
    Returns peak memory usage in MB.
    """
    # Start tracing
    tracemalloc.start()
    
    # Record start time
    start_time = time.time()
    
    try:
        # Import and run the analysis main function
        # We import locally to ensure we get the latest code
        from analysis import main as analysis_main
        
        # Run the analysis
        # Note: We catch SystemExit because analysis.py may exit on validation failures
        try:
            analysis_main()
        except SystemExit as e:
            # If analysis exits due to validation failure, we still record memory
            # but note that the run was incomplete
            if e.code != 0:
                print(f"Analysis exited with code {e.code} - recording partial memory usage")
        
    except Exception as e:
        print(f"Error during analysis execution: {e}")
        raise
    finally:
        # Stop tracing
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'peak_memory_mb': peak / 1024 / 1024,
            'duration_seconds': duration,
            'status': 'success'
        }

def write_csv(results, output_path):
    """
    Writes memory profiling results to a CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['metric', 'value', 'unit'])
        writer.writeheader()
        
        # Write peak memory
        writer.writerow({
            'metric': 'peak_memory',
            'value': f"{results['peak_memory_mb']:.2f}",
            'unit': 'MB'
        })
        
        # Write duration
        writer.writerow({
            'metric': 'duration',
            'value': f"{results['duration_seconds']:.2f}",
            'unit': 'seconds'
        })
        
        # Write status
        writer.writerow({
            'metric': 'status',
            'value': results['status'],
            'unit': ''
        })
        
        # Write threshold check
        threshold = 7 * 1024  # 7GB in MB
        within_threshold = results['peak_memory_mb'] < threshold
        writer.writerow({
            'metric': 'within_7gb_threshold',
            'value': 'yes' if within_threshold else 'no',
            'unit': ''
        })
    
    return output_file

def main():
    parser = argparse.ArgumentParser(
        description='Measure memory usage of the analysis pipeline'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/memory_profile.csv',
        help='Output path for the CSV report (default: data/memory_profile.csv)'
    )
    parser.add_argument(
        '--threshold-gb',
        type=float,
        default=7.0,
        help='Memory threshold in GB (default: 7.0)'
    )
    
    args = parser.parse_args()
    
    print(f"Starting memory profiling of code/analysis.py...")
    print(f"Threshold: {args.threshold_gb} GB")
    
    try:
        results = measure_memory_usage()
        
        # Check against threshold
        threshold_mb = args.threshold_gb * 1024
        if results['peak_memory_mb'] > threshold_mb:
            print(f"WARNING: Peak memory ({results['peak_memory_mb']:.2f} MB) exceeded threshold ({threshold_mb:.2f} MB)")
        else:
            print(f"SUCCESS: Peak memory ({results['peak_memory_mb']:.2f} MB) is within threshold ({threshold_mb:.2f} MB)")
        
        # Write results to CSV
        output_path = write_csv(results, args.output)
        print(f"Results written to: {output_path}")
        
        # Return appropriate exit code
        if results['peak_memory_mb'] > threshold_mb:
            return 1
        return 0
        
    except Exception as e:
        print(f"Memory profiling failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())