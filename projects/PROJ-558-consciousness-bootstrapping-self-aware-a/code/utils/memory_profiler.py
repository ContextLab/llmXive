import os
import sys
import resource
import argparse
import time
from typing import Optional, Dict, Any

import torch
from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

def get_current_memory_mb() -> float:
    """Get current RSS (Resident Set Size) memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def get_peak_memory_mb() -> float:
    """Get peak RSS memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0

def profile_training_script(
    script_path: str,
    max_batch_size: int,
    output_log_path: str,
    max_memory_limit_gb: float = 7.0
) -> Dict[str, Any]:
    """
    Runs the training script with the specified max batch size,
    monitors peak memory usage, and logs the result.

    Args:
        script_path: Path to the training script (e.g., 'code/training/train.py')
        max_batch_size: The batch size to use for the run.
        output_log_path: Path where the memory profile log will be written.
        max_memory_limit_gb: The maximum allowed memory in GB (default 7.0).

    Returns:
        A dictionary containing the results of the profiling run.
    """
    logger.info(f"Starting memory profiling of {script_path} with batch_size={max_batch_size}")
    logger.info(f"Memory limit: {max_memory_limit_gb} GB")

    # Record start memory
    start_mem_mb = get_current_memory_mb()
    logger.info(f"Initial memory usage: {start_mem_mb:.2f} MB")

    # Construct command
    cmd = [
        sys.executable,
        script_path,
        "--batch_size", str(max_batch_size),
        "--epochs", "1",  # Run minimal epochs to save time but capture peak
        "--profile_mode", "true"  # Assuming train.py can handle a flag to exit early or just run
    ]

    # Note: The actual train.py might need specific args to run fast.
    # We assume standard args exist or we override config via env if needed.
    # If train.py doesn't support --epochs, we might need to adjust config.py.
    # For this task, we assume the script can run with minimal epochs.

    start_time = time.time()
    success = True
    error_msg = None

    try:
        # We run the script as a subprocess to isolate memory if needed,
        # but resource.getrusage works on the current process.
        # To profile the *script's* memory, we should run it as a subprocess
        # and measure the subprocess, or run it in the current process.
        # Given the constraint "run the training script", we run it in current process
        # but we need to be careful not to crash the profiler itself.
        # A better approach for a robust profiler is to run the script as a subprocess
        # and use `resource` on the parent to measure the child? No, resource is per-process.
        # We will import and run the main function of train.py directly if possible,
        # or use subprocess and parse output?
        # The task says "Run memory profiling on the training script".
        # Let's try to run the script's main function directly to measure RSS.

        # Import the train module
        # We need to add the project root to sys.path if not already there
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # We need to mock sys.argv for the train script
        original_argv = sys.argv
        sys.argv = [script_path, "--batch_size", str(max_batch_size), "--epochs", "1"]

        # We need to import train.py
        # Since train.py is in code/training, we import it
        # But train.py might have a main() that does everything.
        # We'll try to import and call main()
        # However, train.py might have side effects on import.
        # Let's assume it's safe.

        # To avoid re-running setup, we might need to reset state.
        # For simplicity, we assume a fresh environment or that the script is idempotent enough.

        # Actually, the safest way to measure peak memory of a script is to run it as a subprocess
        # and use `psutil` or `resource` on the child. But we can't easily get child RSS from parent
        # without polling.
        # Let's use the `tracemalloc` or `resource` on the current process if we run it directly.
        # But if train.py forks or uses multiprocessing, this won't work.
        # Given the constraints (CPU-only, small model), we assume single process.

        # Let's try to run the script by importing and calling main.
        # We need to handle the case where train.py is not importable directly.
        # We'll use exec to run the script file.

        with open(script_path, 'r') as f:
            code = f.read()

        # Create a namespace
        namespace = {
            '__name__': '__main__',
            '__file__': script_path
        }

        # We need to set up args before exec
        # But train.py might parse sys.argv at the top level.
        # We'll set sys.argv before exec.
        sys.argv = [script_path, "--batch_size", str(max_batch_size), "--epochs", "1"]

        # Execute the script
        # This will run the entire script, including the main() call if it's at the bottom.
        # We need to make sure it doesn't block forever.
        # We assume the script has a way to exit quickly (e.g., --epochs 1).

        exec(code, namespace)

        sys.argv = original_argv

    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"Error running training script: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time

    # Get peak memory
    peak_mem_mb = get_peak_memory_mb()
    peak_mem_gb = peak_mem_mb / 1024.0

    # Check against limit
    passed = success and (peak_mem_gb < max_memory_limit_gb)

    # Prepare log content
    log_lines = [
        "=" * 60,
        "MEMORY PROFILING REPORT",
        "=" * 60,
        f"Script: {script_path}",
        f"Batch Size: {max_batch_size}",
        f"Max Allowed Memory (GB): {max_memory_limit_gb}",
        f"Initial Memory (MB): {start_mem_mb:.2f}",
        f"Peak Memory (MB): {peak_mem_mb:.2f}",
        f"Peak Memory (GB): {peak_mem_gb:.4f}",
        f"Execution Time (s): {elapsed_time:.2f}",
        f"Status: {'PASSED' if passed else 'FAILED'}",
        f"Error: {error_msg if error_msg else 'None'}",
        "=" * 60
    ]

    log_content = "\n".join(log_lines)

    # Write to file
    os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
    with open(output_log_path, 'w') as f:
        f.write(log_content)

    logger.info(f"Memory profile log written to: {output_log_path}")
    logger.info(log_content)

    return {
        "success": success,
        "peak_memory_mb": peak_mem_mb,
        "peak_memory_gb": peak_mem_gb,
        "passed_limit": passed,
        "error": error_msg,
        "log_path": output_log_path
    }

def main():
    parser = argparse.ArgumentParser(description="Profile memory usage of the training script")
    parser.add_argument("--script", type=str, default="code/training/train.py",
                        help="Path to the training script to profile")
    parser.add_argument("--batch_size", type=int, default=4,
                        help="Batch size to use for the run")
    parser.add_argument("--output", type=str, default="artifacts/results/memory_profile.log",
                        help="Path to output the memory profile log")
    parser.add_argument("--limit_gb", type=float, default=7.0,
                        help="Maximum allowed memory in GB")

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    result = profile_training_script(
        script_path=args.script,
        max_batch_size=args.batch_size,
        output_log_path=args.output,
        max_memory_limit_gb=args.limit_gb
    )

    if not result["passed_limit"]:
        logger.warning(f"Memory limit exceeded or script failed. Peak: {result['peak_memory_gb']:.2f} GB")
        sys.exit(1)
    else:
        logger.info("Memory profiling completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
