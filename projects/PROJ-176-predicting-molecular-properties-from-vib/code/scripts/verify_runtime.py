import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Ensure the code directory is in the path for imports if running as script
# but here we are orchestrating the main.py execution
CODE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = CODE_ROOT.parent
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD_SECONDS = 6 * 3600  # 6 hours

def run_pipeline_stage():
    """
    Executes code/main.py end-to-end (download, preprocess, train, evaluate, validate)
    measures wall-clock time, and writes the result to results/runtime_verification.json.
    """
    output_file = RESULTS_DIR / "runtime_verification.json"
    
    # Construct the command to run the full pipeline
    # We assume the main.py CLI has subcommands for each stage as per T009/T016/T023/T031/T040
    # The task implies an "end-to-end" run. We will invoke the main entry point.
    # Depending on implementation, it might be `python main.py all` or a sequence.
    # Given T009 says "CLI skeleton with argparse subcommands for each phase", 
    # and T045 says "Run code/main.py end-to-end", we assume a sequence or a specific 'all' command.
    # To be safe and robust, we will attempt to run the sequence of commands defined in the plan:
    # download -> preprocess -> train -> evaluate -> validate
    
    stages = [
        "download",
        "preprocess",
        "train",
        "evaluate",
        "validate"
    ]

    start_time = time.time()
    success = True
    error_msg = None
    completed_stages = []

    try:
        # Check if data exists to skip download if needed? 
        # The task says "Run code/main.py end-to-end", implying the full flow.
        # We will run the stages sequentially.
        
        for stage in stages:
            print(f"Running stage: {stage}...")
            cmd = [sys.executable, str(CODE_ROOT / "main.py"), stage]
            
            # Run with timeout per stage? No, we measure total time.
            # But we need to ensure we don't hang indefinitely if a stage fails.
            # We'll let it run. If a stage fails, we stop.
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=False, # Stream output to user
                text=True
            )
            
            if result.returncode != 0:
                success = False
                error_msg = f"Stage '{stage}' failed with return code {result.returncode}"
                break
            
            completed_stages.append(stage)
            print(f"Stage '{stage}' completed successfully.")

    except Exception as e:
        success = False
        error_msg = str(e)
    
    end_time = time.time()
    total_duration = end_time - start_time
    passed = success and (total_duration <= THRESHOLD_SECONDS)

    report = {
        "task_id": "T045",
        "timestamp": datetime.now().isoformat(),
        "threshold_seconds": THRESHOLD_SECONDS,
        "actual_duration_seconds": round(total_duration, 2),
        "passed": passed,
        "status": "pass" if passed else "fail",
        "completed_stages": completed_stages,
        "error": error_msg
    }

    # Write the report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nRuntime verification complete.")
    print(f"Total duration: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)")
    print(f"Threshold: {THRESHOLD_SECONDS} seconds (6 hours)")
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    print(f"Report saved to: {output_file}")

    return 0 if passed else 1

def main():
    sys.exit(run_pipeline_stage())

if __name__ == "__main__":
    main()