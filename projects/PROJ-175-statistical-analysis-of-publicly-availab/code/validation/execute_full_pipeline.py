import os
import sys
import json
import time
import subprocess
import psutil
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.memory_monitor import get_memory_usage_gb

def run_pipeline_step(step_name, script_path, args=None):
    """
    Executes a pipeline step script and returns the result status.
    """
    print(f"--- Executing: {step_name} ---")
    start_time = time.time()
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per step
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            print(f"ERROR in {step_name}:")
            print(result.stderr)
            return {
                "status": "FAILED",
                "step": step_name,
                "runtime_seconds": elapsed,
                "error": result.stderr
            }
        
        print(f"Completed: {step_name} in {elapsed:.2f}s")
        return {
            "status": "SUCCESS",
            "step": step_name,
            "runtime_seconds": elapsed
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "step": step_name,
            "runtime_seconds": 3600,
            "error": "Step timed out after 1 hour"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "step": step_name,
            "runtime_seconds": time.time() - start_time,
            "error": str(e)
        }

def main():
    """
    Executes the full pipeline end-to-end and logs results to data/pipeline_execution_log.json.
    """
    start_time = time.time()
    peak_ram_mb = 0.0
    step_results = []
    artifacts_created = []
    overall_status = "SUCCESS"

    # Define the sequence of pipeline steps based on the task dependencies
    # We execute the core scripts that generate the required artifacts
    steps = [
        ("Data Verification", "code/data/verify.py"),
        ("Data Download", "code/data/download.py"),
        ("Data Preprocessing", "code/data/preprocess.py"),
        ("Data Split", "code/data/split.py"),
        ("VIF Diagnostics", "code/models/diagnostics.py"),
        ("Logistic Regression", "code/models/fit_logistic.py"),
        ("Bayesian Model", "code/models/fit_bayesian.py"),
        ("Evaluation Metrics", "code/evaluation/metrics.py"),
        ("AUC Delta & Report", "code/evaluation/report.py"),
        ("Capture Final Metrics", "code/evaluation/capture_metrics.py")
    ]

    # Track peak memory
    def update_peak_memory():
        nonlocal peak_ram_mb
        current = get_memory_usage_gb() * 1024
        if current > peak_ram_mb:
            peak_ram_mb = current

    for step_name, script_rel_path in steps:
        script_path = project_root / script_rel_path
        if not script_path.exists():
            print(f"WARNING: Script not found: {script_path}")
            # If a script is missing, we might skip it or fail. 
            # For a full pipeline execution test, missing scripts usually mean failure.
            # However, we continue to log what we can.
            result = {"status": "SKIPPED", "step": step_name, "error": "Script not found"}
            step_results.append(result)
            overall_status = "PARTIAL"
            continue

        result = run_pipeline_step(step_name, script_path)
        step_results.append(result)
        update_peak_memory()

        if result["status"] not in ["SUCCESS", "SKIPPED"]:
            overall_status = "FAILED"
            # We could break here, but let's try to run remaining non-dependent steps
            # or just log the failure.
            print(f"Pipeline failed at step: {step_name}")

    # Define expected artifacts based on the pipeline logic
    expected_artifacts = [
        "data/verification_report.json",
        "data/processed/co_occurrence_matrix.parquet",
        "data/processed/flavor_similarity.parquet",
        "data/processed/final_features.parquet",
        "data/vif_scores_initial.json",
        "data/final/logistic_results.json",
        "data/final/bayesian_results.json",
        "data/evaluation_metrics.json",
        "data/auc_delta_metrics.json",
        "data/pipeline_execution_log.json" # This one is being written now
    ]

    # Check which artifacts actually exist
    for artifact in expected_artifacts:
        full_path = project_root / artifact
        if full_path.exists():
            artifacts_created.append(artifact)

    end_time = time.time()
    total_runtime = end_time - start_time

    # Ensure peak memory is updated one last time
    update_peak_memory()

    # Construct the final log
    execution_log = {
        "status": overall_status,
        "runtime_seconds": total_runtime,
        "peak_ram_mb": peak_ram_mb,
        "start_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
        "end_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time)),
        "steps": step_results,
        "artifacts_created": artifacts_created
    }

    # Write the log to disk
    output_path = project_root / "data" / "pipeline_execution_log.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(execution_log, f, indent=2)

    print(f"\n--- Pipeline Execution Complete ---")
    print(f"Status: {overall_status}")
    print(f"Total Runtime: {total_runtime:.2f} seconds")
    print(f"Peak RAM: {peak_ram_mb:.2f} MB")
    print(f"Artifacts Created: {len(artifacts_created)}")
    print(f"Log saved to: {output_path}")

    return execution_log

if __name__ == "__main__":
    main()
