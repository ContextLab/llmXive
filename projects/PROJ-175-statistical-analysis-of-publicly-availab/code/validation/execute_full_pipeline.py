import os
import sys
import json
import time
import subprocess
import psutil
from pathlib import Path

# Ensure the project root is in the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.memory_monitor import get_memory_usage_gb

def run_pipeline_step(step_name, script_path, args=None):
    """
    Executes a specific pipeline step and returns the result status.
    """
    print(f"--- Executing: {step_name} ---")
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    start_time = time.time()
    try:
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True
        )
        duration = time.time() - start_time
        print(f"SUCCESS: {step_name} completed in {duration:.2f}s")
        return {
            "status": "success",
            "duration_seconds": duration,
            "stdout": result.stdout[-500:] if result.stdout else "", # Truncate for log
            "stderr": result.stderr[-500:] if result.stderr else ""
        }
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"FAILED: {step_name} failed with code {e.returncode}")
        return {
            "status": "failed",
            "duration_seconds": duration,
            "error_code": e.returncode,
            "stdout": e.stdout[-500:] if e.stdout else "",
            "stderr": e.stderr[-500:] if e.stderr else ""
        }
    except Exception as e:
        duration = time.time() - start_time
        print(f"ERROR: {step_name} raised exception: {str(e)}")
        return {
            "status": "error",
            "duration_seconds": duration,
            "error_message": str(e)
        }

def generate_final_log(log_data, output_path):
    """
    Writes the final execution log to the specified JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    print(f"Final execution log saved to: {output_path}")

def main():
    """
    Orchestrates the full pipeline execution for T043.
    """
    start_total_time = time.time()
    peak_memory_gb = 0.0
    overall_status = "success"
    
    steps = [
        ("01_Verification", "code/data/verify.py", []),
        ("02_Download", "code/data/download.py", []),
        ("03_Preprocess", "code/data/preprocess.py", []),
        ("04_Split", "code/data/split.py", []),
        ("05_Diagnostics_VIF", "code/models/diagnostics.py", ["--step", "vif"]),
        ("06_Model_Logistic", "code/models/fit_logistic.py", []),
        ("07_Model_Bayesian", "code/models/fit_bayesian.py", []),
        ("08_Diagnostics_LRT", "code/models/diagnostics.py", ["--step", "lrt"]),
        ("09_Evaluation_Metrics", "code/evaluation/metrics.py", []),
        ("10_Evaluation_Report", "code/evaluation/report.py", []),
    ]

    execution_details = []

    for step_name, script_rel_path, args in steps:
        script_path = PROJECT_ROOT / script_rel_path
        if not script_path.exists():
            log_entry = {
                "step": step_name,
                "status": "skipped",
                "reason": "Script not found",
                "duration_seconds": 0
            }
            execution_details.append(log_entry)
            overall_status = "failed"
            print(f"WARNING: Script {script_path} not found. Skipping {step_name}.")
            continue

        # Check memory before step
        mem_before = get_memory_usage_gb()
        
        result = run_pipeline_step(step_name, script_path, args)
        
        # Check memory after step
        mem_after = get_memory_usage_gb()
        current_peak = max(mem_before, mem_after)
        if current_peak > peak_memory_gb:
            peak_memory_gb = current_peak

        if result["status"] != "success":
            overall_status = "failed"
            # We could choose to stop here, but the task asks for a full execution log.
            # We continue to see what else fails, but mark overall as failed.
        
        execution_details.append({
            "step": step_name,
            "status": result["status"],
            "duration_seconds": result.get("duration_seconds", 0),
            "error_details": result.get("stderr", "") if result["status"] != "success" else None
        })

    end_total_time = time.time()
    total_duration = end_total_time - start_total_time

    final_log = {
        "execution_id": "T043-full-pipeline",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_status": overall_status,
        "total_runtime_seconds": total_duration,
        "peak_memory_gb": round(peak_memory_gb, 2),
        "steps": execution_details
    }

    output_file = PROJECT_ROOT / "data" / "final_execution_log.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    generate_final_log(final_log, output_file)

    return 0 if overall_status == "success" else 1

if __name__ == "__main__":
    sys.exit(main())