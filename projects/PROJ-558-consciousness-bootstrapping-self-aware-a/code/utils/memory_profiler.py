import os
import sys
import resource
import argparse
import time
import subprocess
import logging
from pathlib import Path

from utils.logging import get_logger

logger = get_logger(__name__)

def get_current_memory_mb():
    """
    Returns the current memory usage of the process in MB.
    Uses resource.getrusage for Unix-like systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, but MB on macOS.
    # We normalize to MB.
    maxrss_kb = usage.ru_maxrss
    if sys.platform == 'darwin':
        # macOS reports in MB
        return maxrss_kb
    else:
        # Linux reports in KB
        return maxrss_kb / 1024.0

def get_peak_memory_mb():
    """
    Returns the peak memory usage of the process in MB.
    This is the same as get_current_memory_mb for resource.getrusage,
    as it tracks the high-water mark.
    """
    return get_current_memory_mb()

def profile_training_script(script_path: str, args: list = None):
    """
    Runs the training script and captures peak memory usage.
    
    Args:
        script_path: Path to the Python script to run (e.g., code/training/train.py)
        args: Optional list of command-line arguments to pass to the script.
    
    Returns:
        dict: Contains 'peak_memory_mb', 'exit_code', and 'duration_seconds'.
    """
    logger.info(f"Starting memory profiling for script: {script_path}")
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    start_time = time.time()
    peak_mem_before = get_peak_memory_mb()
    
    try:
        # Run the subprocess. We need to capture the exit code.
        # The child process will have its own memory usage.
        # To measure the child's peak memory, we can use a wrapper or
        # parse the output if the child logs it.
        # However, a robust way on Unix is to use /usr/bin/time -v or
        # a custom wrapper that reports maxrss.
        # For simplicity and portability within the project, we will
        # rely on the child process logging its own peak memory if it does,
        # or we can use a Python wrapper that forks and measures.
        
        # Let's use a Python wrapper approach:
        # We'll run the script inside a function that measures memory,
        # but since the script might be long-running, we can't easily
        # inject into it without modifying it.
        # Alternative: Use 'resource' in a wrapper script.
        
        # Better approach for this task:
        # The task asks to "Run memory profiling on the training script".
        # We will execute the script as a subprocess and measure the
        # peak memory of the *subprocess* using a helper.
        
        # We'll create a temporary wrapper script that runs the target
        # and reports memory.
        
        wrapper_code = f"""
import sys
import resource
import subprocess

def get_peak_mb():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    # ru_maxrss for children is in KB on Linux
    return usage.ru_maxrss / 1024.0

result = subprocess.run(sys.argv[1:], capture_output=True, text=True)
peak = get_peak_mb()
print(f"PEAK_MEMORY_MB:{{peak}}")
sys.exit(result.returncode)
"""
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapper_code)
            wrapper_path = f.name
        
        try:
            full_cmd = [sys.executable, wrapper_path] + cmd
            process = subprocess.run(full_cmd, capture_output=True, text=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse output for PEAK_MEMORY_MB
            peak_memory = 0.0
            for line in process.stdout.splitlines():
                if line.startswith("PEAK_MEMORY_MB:"):
                    try:
                        peak_memory = float(line.split(":")[1])
                    except ValueError:
                        pass
            
            return {
                'peak_memory_mb': peak_memory,
                'exit_code': process.returncode,
                'duration_seconds': duration,
                'stdout': process.stdout,
                'stderr': process.stderr
            }
        finally:
            os.unlink(wrapper_path)
            
    except Exception as e:
        logger.error(f"Error during profiling: {e}")
        return {
            'peak_memory_mb': 0.0,
            'exit_code': -1,
            'duration_seconds': time.time() - start_time,
            'error': str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Memory profiling for training script")
    parser.add_argument("--script", type=str, default="code/training/train.py",
                        help="Path to the script to profile")
    parser.add_argument("--args", type=str, nargs='*', default=[],
                        help="Arguments to pass to the script")
    parser.add_argument("--output", type=str, default="artifacts/results/memory_profile.log",
                        help="Path to the output log file")
    parser.add_argument("--max-batch-size", type=int, default=32,
                        help="Max batch size to test (optional, passed as arg)")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare args for the script
    script_args = args.args
    if args.max_batch_size:
        # Check if --batch-size is already in args, if not add it
        if "--batch-size" not in script_args and "-b" not in script_args:
            script_args.extend(["--batch-size", str(args.max_batch_size)])
    
    logger.info(f"Running memory profile on {args.script} with args: {script_args}")
    
    result = profile_training_script(args.script, script_args)
    
    log_lines = [
        f"Memory Profiling Report",
        f"=======================",
        f"Script: {args.script}",
        f"Arguments: {' '.join(script_args)}",
        f"Duration: {result['duration_seconds']:.2f} seconds",
        f"Exit Code: {result['exit_code']}",
        f"Peak Memory (RSS): {result['peak_memory_mb']:.2f} MB",
        f"Limit (7GB): 7168.00 MB",
        f"Status: {'PASS' if result['peak_memory_mb'] < 7168.0 else 'FAIL'}",
        f"",
        f"Stdout (last 50 lines):",
    ]
    
    if result.get('stdout'):
        stdout_lines = result['stdout'].splitlines()
        for line in stdout_lines[-50:]:
            log_lines.append(line)
    else:
        log_lines.append("No stdout captured.")
        
    if result.get('stderr'):
        log_lines.append("")
        log_lines.append("Stderr:")
        for line in result['stderr'].splitlines():
            log_lines.append(line)
            
    if result.get('error'):
        log_lines.append("")
        log_lines.append(f"Error: {result['error']}")
        
    log_content = "\n".join(log_lines)
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(log_content)
        
    logger.info(f"Memory profile log written to {output_path}")
    print(log_content)
    
    # Fail loudly if over limit
    if result['peak_memory_mb'] >= 7168.0:
        sys.exit(1)

if __name__ == "__main__":
    main()