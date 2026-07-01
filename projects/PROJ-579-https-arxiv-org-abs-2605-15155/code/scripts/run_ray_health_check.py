import os
import sys
import json
import subprocess
from pathlib import Path

def main():
    """
    Executes the Ray health check and generates outputs/health/ray_health.json.
    
    This script:
    1. Ensures the output directory exists.
    2. Runs the vendored Ray health check entry point.
    3. Captures exit code and output.
    4. Writes a JSON report to outputs/health/ray_health.json.
    5. Exits with 0 on success (script ran and produced report), 
       1 if the underlying check failed or crashed.
    """
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "outputs" / "health"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "ray_health.json"
    
    # Path to the vendored entry point defined in T010
    # Adjusted to be relative to the project root structure implied by tasks.md
    # tasks.md mentions: external/SDAR/tests/ray_cpu/check_worker_alive/main.py
    check_script_path = project_root / "external" / "SDAR" / "tests" / "ray_cpu" / "check_worker_alive" / "main.py"
    
    result = {
        "status": "unknown",
        "exit_code": -1,
        "cpu_count_detected": 0,
        "message": "",
        "timestamp": None
    }
    
    if not check_script_path.exists():
        result["status"] = "error"
        result["message"] = f"Vendored health check script not found: {check_script_path}"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Error: {result['message']}")
        sys.exit(1)
    
    try:
        # Run the script in the current environment
        # We rely on the venv being active as per prerequisites
        proc = subprocess.run(
            [sys.executable, str(check_script_path)],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "CUDA_VISIBLE_DEVICES": ""}
        )
        
        result["exit_code"] = proc.returncode
        result["timestamp"] = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()
        
        # Parse output for CPU count if present
        output_lines = proc.stdout.splitlines()
        cpu_count = 0
        found_success_msg = False
        
        for line in output_lines:
            if "CPUs detected" in line:
                try:
                    # Expect format like "2 CPUs detected" or "Detected 4 CPUs"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            cpu_count = int(part)
                            break
                except ValueError:
                    pass
            if "Ray cluster healthy" in line or "healthy" in line.lower():
                found_success_msg = True
        
        result["cpu_count_detected"] = cpu_count
        
        if proc.returncode == 0 and cpu_count >= 2 and found_success_msg:
            result["status"] = "success"
            result["message"] = "Ray cluster healthy and CPU count verified."
            print("Health check passed.")
        elif proc.returncode != 0:
            result["status"] = "failed"
            result["message"] = f"Script exited with code {proc.returncode}. Stderr: {proc.stderr}"
            print(f"Health check failed: {result['message']}")
        else:
            result["status"] = "warning"
            result["message"] = "Script ran but did not meet success criteria (CPU < 2 or missing health msg)."
            print(f"Health check warning: {result['message']}")
            
        # Write the result to the output file
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"Report written to: {output_file}")
        
        # T012 Requirement: Ensure script exits with code 0 and generates file on success.
        # If the underlying check failed, we still generated the report, but T012 specifically
        # asks for exit 0 *and* generation on success. If the check itself failed, 
        # we should arguably exit 1 to signal the pipeline failure, but the task says 
        # "on success". We interpret this as: if the health check logic succeeded, exit 0.
        if result["status"] == "success":
            sys.exit(0)
        else:
            # Even if we generated the file, if the health check failed, the task 
            # "Ensure script exits with code 0... on success" implies we shouldn't 
            # exit 0 if it wasn't successful. However, the task is to implement the 
            # script that *does* this. If the check fails, the script should report 
            # the failure in the JSON and exit non-zero to stop the pipeline.
            sys.exit(1)

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["message"] = "Health check script timed out after 60 seconds."
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Timeout: {result['message']}")
        sys.exit(1)
    except Exception as e:
        result["status"] = "exception"
        result["message"] = str(e)
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Exception: {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    main()