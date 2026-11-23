import os
import sys
import json
import time
import argparse
from pathlib import Path

# Import existing pipeline components
from main import (
    setup_paths,
    estimate_ram_usage,
    determine_compute_strategy,
    save_compute_strategy,
    run_compute_feasibility_check,
    run_ingestion_and_validation,
    run_analysis,
    run_diagnostics
)
from config import get_config
from data_generator import generate_synthetic_dataset, set_seeds
from ingest import load_streamed_dataset, compute_online_statistics

def run_6_hour_stress_test(args):
    """
    Executes the full pipeline (US1-US3) on a large dataset (T070 proxy or real)
    to verify execution time < 6 hours.
    Output: data/results/6_hour_stress_test_report.json
    """
    # Setup paths and config
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    setup_paths(project_root)
    config = get_config()

    start_time = time.time()
    report = {
        "task_id": "T071",
        "start_time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
        "status": "running",
        "dataset_source": args.dataset_source or "T070_PROXY",
        "dataset_path": None,
        "ram_estimate_gb": None,
        "compute_strategy": None,
        "phases": {},
        "end_time_iso": None,
        "total_duration_seconds": None,
        "threshold_seconds": 6 * 3600,
        "passed": None
    }

    try:
        # 1. Locate or Generate Dataset (T070 Proxy if no real data specified)
        dataset_path = None
        if args.dataset_source and Path(args.dataset_source).exists():
            dataset_path = Path(args.dataset_source)
        else:
            # Fallback to T070 proxy if available, otherwise generate a large synthetic proxy
            proxy_path = project_root / "data" / "raw" / "large_proxy.csv"
            if proxy_path.exists():
                dataset_path = proxy_path
            else:
                # Generate T070 Large Proxy on the fly if missing
                print("T070 Proxy missing. Generating large synthetic proxy for stress test...")
                set_seeds(42)
                generate_synthetic_dataset(
                    n_subjects=2000, # Large N for stress test
                    output_path=str(proxy_path),
                    is_synthetic=True
                )
                dataset_path = proxy_path

        report["dataset_path"] = str(dataset_path)

        # 2. RAM Pre-Check (T058)
        print("Running RAM Pre-Check (T058)...")
        ram_estimate = estimate_ram_usage(dataset_path)
        report["ram_estimate_gb"] = ram_estimate
        
        strategy = determine_compute_strategy(ram_estimate)
        report["compute_strategy"] = strategy
        save_compute_strategy(strategy)

        if strategy == "FAIL":
            raise RuntimeError(f"CRITICAL: Dataset too large for standard runner (RAM estimate: {ram_estimate}GB). Halting.")

        # 3. Ingestion & Validation (US1)
        print("Running Ingestion & Validation (US1)...")
        t_start = time.time()
        # If streaming is required, use the streaming loader; otherwise standard
        if strategy == "STREAM":
            # Simulate streaming for the proxy (chunked processing)
            # In a real scenario, this would iterate chunks. For the proxy, we ensure the logic runs.
            print("Using streaming mode for ingestion...")
            # Note: For the proxy CSV, we load it but simulate the chunked logic overhead
            # to ensure the path is exercised without OOM on the runner.
            # The actual 'load_streamed_dataset' function handles the chunking logic.
            # We pass the path to the main ingestion flow which respects the strategy.
            pass 
        
        run_ingestion_and_validation(dataset_path, strategy)
        t_end = time.time()
        report["phases"]["us1_ingestion"] = {
            "duration_seconds": t_end - t_start,
            "status": "success"
        }

        # 4. Analysis (US2)
        print("Running Analysis (US2)...")
        t_start = time.time()
        run_analysis(strategy)
        t_end = time.time()
        report["phases"]["us2_analysis"] = {
            "duration_seconds": t_end - t_start,
            "status": "success"
        }

        # 5. Diagnostics (US3)
        print("Running Diagnostics (US3)...")
        t_start = time.time()
        run_diagnostics(strategy)
        t_end = time.time()
        report["phases"]["us3_diagnostics"] = {
            "duration_seconds": t_end - t_start,
            "status": "success"
        }

        # 6. Finalize Report
        end_time = time.time()
        total_duration = end_time - start_time
        
        report["end_time_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time))
        report["total_duration_seconds"] = total_duration
        report["passed"] = total_duration < report["threshold_seconds"]
        report["status"] = "completed"

        # Write report to disk
        results_dir = project_root / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        report_path = results_dir / "6_hour_stress_test_report.json"
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Stress test completed in {total_duration:.2f}s. Threshold: {report['threshold_seconds']}s. Passed: {report['passed']}")
        print(f"Report written to: {report_path}")

        return report

    except Exception as e:
        report["status"] = "failed"
        report["error"] = str(e)
        report["end_time_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
        report["total_duration_seconds"] = time.time() - start_time
        
        # Write failure report
        results_dir = project_root / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        report_path = results_dir / "6_hour_stress_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Stress test FAILED: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="6-Hour Stress Test Runner (T071)")
    parser.add_argument("--project-root", type=str, help="Project root directory")
    parser.add_argument("--dataset-source", type=str, help="Path to specific dataset to test")
    args = parser.parse_args()
    run_6_hour_stress_test(args)

if __name__ == "__main__":
    main()
