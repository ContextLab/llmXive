"""
Script to verify the absence of GPU-dependent libraries in the project environment.
Checks for torch, tensorflow, and cupy.
Writes result to logs/gpu_check.log.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Define GPU libraries to check
GPU_LIBS = ["torch", "tensorflow", "cupy"]

def check_gpu_libs():
    """
    Run pip list and grep for GPU libraries.
    Returns True if no GPU libs found, False otherwise.
    """
    try:
        # Run pip list
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.lower()

        found_libs = []
        for lib in GPU_LIBS:
            if lib in output:
                found_libs.append(lib)

        return len(found_libs) == 0, found_libs

    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run pip list: {e}")
        return False, ["pip_list_error"]
    except Exception as e:
        logging.error(f"Unexpected error during GPU check: {e}")
        return False, ["unexpected_error"]

def main():
    # Ensure logs directory exists
    logs_dir = Path("code/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "gpu_check.log"

    # Configure logging to file
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Also print to stdout for immediate feedback
    print(f"Checking for GPU libraries: {GPU_LIBS}...")

    passed, found_libs = check_gpu_libs()

    if passed:
        log_entry = "GPU_LIB_CHECK: PASSED"
        print(log_entry)
    else:
        log_entry = f"GPU_LIB_CHECK: FAILED - {', '.join(found_libs)}"
        print(log_entry)

    # Append to log file
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
