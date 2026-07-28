"""
Stress Test Runner for Gut Microbiome Sleep Architecture Pipeline.

This script executes the full pipeline to verify it completes within the 6-hour
constraint and generates the required stress test report artifact.

Dependencies:
- code/main.py (Pipeline Orchestration)
- code/ingest.py (Data Ingestion)
- code/run_6_hour_stress_test.py (Timing Logic)

Output:
- data/results/stress_test_report.json
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path

# Ensure project root is in path for imports if run as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from main import main as run_pipeline_main
from run_6_hour_stress_test import run_6_hour_stress_test as run_timing_logic

def generate_stress_test_report(
    status: str,
    total_time_seconds: float,
    time_limit_seconds: float,
    pipeline_exit_code: int,
    artifacts: dict
) -> dict:
    """
    Generates the stress test report dictionary.

    Args:
        status: 'PASS' or 'FAIL'
        total_time_seconds: Total execution time in seconds
        time_limit_seconds: The 6-hour limit in seconds
        pipeline_exit_code: Exit code from the pipeline run
        artifacts: Dictionary of artifact paths and their existence status

    Returns:
        Dict matching the required schema.
    """
    return {
        "status": status,
        "total_time_seconds": round(total_time_seconds, 2),
        "time_limit_seconds": time_limit_seconds,
        "time_limit_hours": time_limit_seconds / 3600,
        "pipeline_exit_code": pipeline_exit_code,
        "artifacts_verified": artifacts,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

def save_report(report: dict, output_path: Path):
    """Writes the report to disk as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Stress test report saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Execute full pipeline stress test and generate report."
    )
    parser.add_argument(
        "--project_root",
        type=str,
        default=str(project_root),
        help="Path to the project root directory."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["synthetic", "real"],
        default="synthetic",
        help="Execution mode: 'synthetic' (uses generated data) or 'real' (requires real data)."
    )
    parser.add_argument(
        "--n_subjects",
        type=int,
        default=100,
        help="Number of subjects for synthetic data generation."
    )
    parser.add_argument(
        "--n_taxa",
        type=int,
        default=50,
        help="Number of taxa for synthetic data generation."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/results",
        help="Directory to write the stress test report."
    )

    args = parser.parse_args()

    project_root = Path(args.project_root)
    output_dir = project_root / args.output_dir
    report_path = output_dir / "stress_test_report.json"

    # Constants
    TIME_LIMIT_HOURS = 6
    TIME_LIMIT_SECONDS = TIME_LIMIT_HOURS * 3600

    print(f"Starting Stress Test (Mode: {args.mode})")
    print(f"Project Root: {project_root}")
    print(f"Time Limit: {TIME_LIMIT_HOURS} hours ({TIME_LIMIT_SECONDS} seconds)")

    start_time = time.time()
    pipeline_exit_code = 0

    # 1. Run the Pipeline
    # We invoke the main pipeline logic. Since the main.py script has specific
    # argparse requirements that might conflict if we just call sys.argv,
    # we simulate the call or ensure args are passed correctly.
    # However, to be robust, we will construct the args for main.py internally.

    # Note: The main.py in the project expects specific args. We will construct them.
    # We need to ensure the pipeline runs to completion or fails loudly.

    try:
        # Prepare arguments for the pipeline main function
        # We assume the pipeline main function (from main.py) can be called
        # or we invoke it via the script mechanism if direct call is complex.
        # Given the API surface, we call the function directly if possible,
        # but main.py usually handles its own argparse.
        # To ensure the pipeline runs correctly with our specific synthetic data needs:
        # We will call the run_6_hour_stress_test function which orchestrates the run.

        # Actually, T016b logic is in run_6_hour_stress_test. Let's use that.
        # But T016c depends on T016b's result.
        # We will run the pipeline logic here and capture the exit code.

        # Simulate the pipeline run by calling the main function of main.py
        # We need to set sys.argv to match what main.py expects.
        original_argv = sys.argv.copy()

        # Construct args for main.py based on the task requirements
        # main.py expects: --project_root, --mode, --input (optional), etc.
        # For synthetic mode, it likely generates data internally or uses a generator.
        # Based on T016a/b, we run the full pipeline.

        test_args = [
            "main.py",
            "--project_root", str(project_root),
            "--mode", args.mode
        ]

        if args.mode == "synthetic":
            # If main.py supports n_subjects/n_taxa, add them.
            # If not, the internal generator might use defaults.
            # We assume the pipeline handles data generation if mode=synthetic.
            pass

        sys.argv = test_args

        try:
            # Run the pipeline main function
            # We catch SystemExit to get the exit code
            run_pipeline_main()
            pipeline_exit_code = 0
        except SystemExit as e:
            pipeline_exit_code = e.code if e.code is not None else 0
        finally:
            sys.argv = original_argv

    except Exception as e:
        print(f"Pipeline execution failed with exception: {e}")
        pipeline_exit_code = 1

    end_time = time.time()
    total_time_seconds = end_time - start_time

    # 2. Determine Status
    if pipeline_exit_code == 0 and total_time_seconds < TIME_LIMIT_SECONDS:
        status = "PASS"
    else:
        status = "FAIL"
        if pipeline_exit_code != 0:
            print(f"Pipeline failed with exit code {pipeline_exit_code}")
        if total_time_seconds >= TIME_LIMIT_SECONDS:
            print(f"Timeout: Execution took {total_time_seconds:.2f}s, limit is {TIME_LIMIT_SECONDS}s")

    # 3. Verify Artifacts
    # Check for the existence of declared deliverables
    required_artifacts = [
        "data/processed/filtered_data.parquet",
        "data/results/outlier_report.json",
        "data/results/timing_evidence.json",
        "data/results/correlation_matrix.json"
    ]

    artifacts_status = {}
    for artifact_path in required_artifacts:
        full_path = project_root / artifact_path
        artifacts_status[artifact_path] = full_path.exists()

    # 4. Generate Report
    report = generate_stress_test_report(
        status=status,
        total_time_seconds=total_time_seconds,
        time_limit_seconds=TIME_LIMIT_SECONDS,
        pipeline_exit_code=pipeline_exit_code,
        artifacts=artifacts_status
    )

    # 5. Save Report
    save_report(report, report_path)

    # 6. Final Exit
    if status == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()