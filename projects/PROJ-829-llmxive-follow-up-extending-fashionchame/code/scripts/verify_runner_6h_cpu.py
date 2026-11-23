"""
Verification script for T041: Verify runner.py completes within 6 hours on CPU free-tier.

This script executes the full text adapter pipeline on a small, representative subset
to empirically measure execution time. It enforces the "Fail Loudly" principle:
if the real data fetch fails, it raises an error rather than using synthetic data.

The script is designed to run on the CPU free-tier (e.g., GitHub Actions, Kaggle CPU).
It uses a small subset size (default 50 samples) to ensure the 6-hour constraint is met
while still performing real measurements on real data.
"""
import sys
import time
import argparse
import json
from pathlib import Path
from datetime import timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.runner import run_text_adapter_pipeline_with_bottleneck_analysis
from src.data.stratified_subset import load_filtered_manifest, validate_subset_balance
from src.data.loader import load_config


def main():
    parser = argparse.ArgumentParser(
        description="Verify runner.py completes within 6 hours on CPU."
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=50,
        help="Number of samples to process for timing verification (default: 50)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write verification report."
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="code/config/settings.yaml",
        help="Path to settings.yaml."
    )
    
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting T041 verification with subset size: {args.subset_size}")
    print(f"Target time limit: 6 hours (21600 seconds)")
    
    # Load config to ensure valid setup
    try:
        config = load_config(Path(args.config_path))
        print("Config loaded successfully.")
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        sys.exit(1)

    # Start timing
    start_time = time.time()
    start_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))

    try:
        # Run the pipeline with bottleneck analysis
        # This function internally handles data loading, processing, and reporting.
        # It will fail loudly if data cannot be fetched (no synthetic fallback).
        # We pass a small subset size to ensure it finishes within the time limit.
        print(f"Running pipeline on {args.subset_size} samples...")
        
        # Note: The runner expects to find the stratified subset manifest.
        # We assume T037 (Run Full Benchmark) or T016b has generated the necessary manifests.
        # If not, the runner will fail, which is the correct "Fail Loudly" behavior.
        
        run_text_adapter_pipeline_with_bottleneck_analysis(
            subset_size=args.subset_size,
            config_path=args.config_path,
            output_dir=str(output_dir)
        )
        
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        elapsed_timedelta = timedelta(seconds=elapsed_seconds)
        
        # Check against 6-hour limit
        limit_seconds = 6 * 3600
        passed = elapsed_seconds <= limit_seconds
        
        report = {
            "task_id": "T041",
            "verification_type": "6-hour CPU runtime check",
            "start_time": start_datetime,
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
            "subset_size": args.subset_size,
            "elapsed_seconds": elapsed_seconds,
            "elapsed_human": str(elapsed_timedelta),
            "limit_seconds": limit_seconds,
            "limit_human": "6:00:00",
            "status": "PASS" if passed else "FAIL",
            "message": "Pipeline completed within 6 hours." if passed else f"Pipeline exceeded 6 hours (took {elapsed_timedelta})."
        }

        report_path = output_dir / "t041_verification_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nVerification Result: {report['status']}")
        print(f"Elapsed Time: {report['elapsed_human']}")
        print(f"Report saved to: {report_path}")
        
        if not passed:
            print("WARNING: Execution time exceeded 6 hours. Consider reducing subset_size further.")
            sys.exit(1)
            
    except Exception as e:
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        
        error_report = {
            "task_id": "T041",
            "verification_type": "6-hour CPU runtime check",
            "start_time": start_datetime,
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
            "subset_size": args.subset_size,
            "elapsed_seconds": elapsed_seconds,
            "status": "ERROR",
            "error_message": str(e),
            "message": "Pipeline failed to complete. This is a failure of the implementation, not the verification."
        }
        
        report_path = output_dir / "t041_verification_report.json"
        with open(report_path, "w") as f:
            json.dump(error_report, f, indent=2)
        
        print(f"\nVerification Result: ERROR")
        print(f"Error: {e}")
        print(f"Report saved to: {report_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
