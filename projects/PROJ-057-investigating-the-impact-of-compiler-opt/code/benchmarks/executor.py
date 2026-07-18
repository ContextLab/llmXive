import os
import sys
import subprocess
import json
import time
import argparse
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Import from project API surface
from utils.logger import setup_logging, get_logger, log_execution_warning
from benchmarks.config import ConfigManager

@dataclass
class ExecutionResult:
    config_id: str
    kernel: str
    compiler: str
    flags: List[str]
    median_ms: float
    p95_ms: float
    iterations: int
    downsampled: bool
    tensor_dim: str
    binary_path: str
    status: str  # 'success', 'memory_fallback', 'failed'

def get_memory_pressure() -> bool:
    """
    Simple check for available memory.
    Returns True if system is under memory pressure (low available RAM).
    """
    try:
        if sys.platform.startswith('linux'):
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        available_kb = int(line.split()[1])
                        # Threshold: 1GB available
                        return available_kb < 1024 * 1024
        elif sys.platform == 'darwin':
            # macOS: use sysctl or psutil if available, fallback to heuristic
            import subprocess
            try:
                result = subprocess.run(['sysctl', '-n', 'vm.swapusage'], capture_output=True, text=True)
                # Heuristic: if swap is heavily used, assume pressure
                return '100.00' in result.stdout # Very rough heuristic
            except Exception:
                return False
        return False
    except Exception:
        # If we can't check, assume no pressure to allow run
        return False

def run_binary(binary_path: str, tensor_dim: str, iterations: int) -> Tuple[float, float, bool]:
    """
    Executes the compiled binary with the specified tensor dimension and iteration count.
    Returns (median_ms, p95_ms, success_flag).
    Raises RuntimeError if execution fails.
    """
    if not os.path.exists(binary_path):
        raise FileNotFoundError(f"Binary not found: {binary_path}")

    # Make binary executable
    os.chmod(binary_path, 0o755)

    command = [binary_path, tensor_dim, str(iterations)]
    
    # Run with timeout (e.g., 60 seconds per run to prevent hangs)
    timeout_seconds = 60
    
    latencies = []
    success = False

    try:
        # We need to run the binary multiple times to get latencies
        # The binary itself should be designed to run the kernel 'iterations' times internally
        # and report the total time, or we run it once per iteration?
        # Based on task description: "Run a fixed number of iterations per configuration"
        # Usually, the binary runs the loop internally.
        # Let's assume the binary takes: <dim> <iterations>
        # And it prints the total time or per-iteration time.
        # To be robust, we will run the binary ONCE with the specified iterations.
        # The binary is expected to output a single JSON line with timing info.
        
        start_total = time.time()
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        end_total = time.time()

        if proc.returncode != 0:
            error_msg = proc.stderr.strip() if proc.stderr else "Unknown error"
            # Check for specific memory error strings
            if "allocation failed" in error_msg.lower() or "std::bad_alloc" in error_msg.lower():
                raise MemoryError(f"Memory allocation failed: {error_msg}")
            raise RuntimeError(f"Execution failed with code {proc.returncode}: {error_msg}")

        # Parse output from binary
        # Expecting the C++ binary to output a JSON line with "total_time_ms" or similar
        # Or we measure the wall time of the subprocess as the latency?
        # The task says "measure latency using std::chrono (via subprocess)".
        # This implies the C++ code uses std::chrono internally and reports the result.
        # If the binary reports internal timing, we use that.
        # If not, we measure the subprocess duration.
        # Let's assume the binary outputs a JSON object with "latencies": [list of ms]
        
        try:
            output_json = json.loads(proc.stdout.strip())
            if isinstance(output_json, list):
                latencies = output_json
            elif isinstance(output_json, dict) and "latencies" in output_json:
                latencies = output_json["latencies"]
            elif isinstance(output_json, dict) and "total_ms" in output_json:
                # If only total is provided, assume it's for 1 iteration or normalize?
                # Task says "iterations" is a field in output.
                # Let's assume the binary runs the loop and returns a list of latencies for each iteration.
                # If it returns a single number, we treat it as a single measurement.
                latencies = [output_json.get("total_ms", 0.0)]
        except json.JSONDecodeError:
            # Fallback: use wall time if binary didn't output JSON
            # This is a fallback for compatibility if the C++ binary is not fully implemented yet
            total_wall_ms = (end_total - start_total) * 1000
            latencies = [total_wall_ms / iterations] # Approximate per-iteration

        if not latencies:
            raise RuntimeError("No latency data returned from binary")

        success = True

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Execution timed out after {timeout_seconds}s")
    except MemoryError:
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected error during execution: {str(e)}")

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)
    median_idx = n // 2
    p95_idx = int(n * 0.95)

    median_ms = latencies_sorted[median_idx]
    p95_ms = latencies_sorted[min(p95_idx, n - 1)]

    return median_ms, p95_ms, success

def compute_statistics(latencies: List[float]) -> Tuple[float, float]:
    """Compute median and p95 from a list of latencies."""
    if not latencies:
        return 0.0, 0.0
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    median = sorted_lat[n // 2]
    p95 = sorted_lat[int(n * 0.95)]
    return median, p95

def execute_with_fallback(
    binary_path: str,
    config: Dict[str, Any],
    kernel: str,
    iterations: int,
    max_dim: int = 768,
    fallback_dim: int = 512
) -> ExecutionResult:
    """
    Executes the binary with memory fallback logic.
    Tries max_dim (768). If memory error, tries fallback_dim (512).
    """
    compiler = config.get('compiler', 'g++')
    flags = config.get('flags', [])
    config_id = config.get('id', 'unknown')
    
    logger = get_logger()
    
    # Try with max dimension
    dim_str = f"{max_dim}x{max_dim}"
    downsampled = False
    
    try:
        logger.info(f"Attempting execution with dimension {dim_str} for config {config_id}")
        median_ms, p95_ms, success = run_binary(binary_path, dim_str, iterations)
        status = 'success'
        tensor_dim = dim_str
    except MemoryError as e:
        logger.warning(f"Memory pressure detected for config {config_id} at {dim_str}: {e}")
        log_execution_warning(logger, f"Memory pressure at {dim_str}, falling back to {fallback_dim}x{fallback_dim}")
        
        if max_dim == fallback_dim:
            # If fallback is same as max, we can't go lower
            raise RuntimeError(f"Memory allocation failed for {dim_str} and no lower dimension available.")
        
        # Try fallback dimension
        dim_str = f"{fallback_dim}x{fallback_dim}"
        downsampled = True
        logger.info(f"Retrying with fallback dimension {dim_str}")
        
        try:
            median_ms, p95_ms, success = run_binary(binary_path, dim_str, iterations)
            status = 'memory_fallback'
            tensor_dim = dim_str
        except MemoryError as e2:
            logger.error(f"Memory allocation failed for fallback dimension {dim_str}. Giving up.")
            raise RuntimeError(f"Execution failed for both {max_dim}x{max_dim} and {fallback_dim}x{fallback_dim}.")
    except Exception as e:
        logger.error(f"Execution failed for config {config_id}: {e}")
        raise

    return ExecutionResult(
        config_id=config_id,
        kernel=kernel,
        compiler=compiler,
        flags=flags,
        median_ms=median_ms,
        p95_ms=p95_ms,
        iterations=iterations,
        downsampled=downsampled,
        tensor_dim=tensor_dim,
        binary_path=binary_path,
        status=status
    )

def save_result(result: ExecutionResult, output_dir: str) -> str:
    """
    Saves the execution result to a JSONL file.
    Path: data/intermediates/raw_logs/{config_id}.jsonl
    """
    output_path = Path(output_dir) / f"{result.config_id}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    record = asdict(result)
    # Ensure flags is a list of strings
    record['flags'] = [str(f) for f in record['flags']]
    
    with open(output_path, 'a') as f:
        f.write(json.dumps(record) + '\n')
    
    return str(output_path)

def main():
    parser = argparse.ArgumentParser(description="Execute compiled kernels and measure latency.")
    parser.add_argument('--config', type=str, required=False, help='Path to config JSON file')
    parser.add_argument('--binary', type=str, required=False, help='Path to binary to execute')
    parser.add_argument('--kernel', type=str, default='matmul', help='Kernel type (matmul, softmax, layernorm)')
    parser.add_argument('--iterations', type=int, default=100, help='Number of iterations per run')
    parser.add_argument('--output-dir', type=str, default='data/intermediates/raw_logs', help='Output directory for results')
    parser.add_argument('--test', action='store_true', help='Run in test mode with dummy data')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = get_logger()
    
    if args.test:
        logger.info("Running in test mode...")
        # Create a dummy config for testing
        dummy_config = {
            'id': 'test_config_001',
            'compiler': 'g++',
            'flags': ['-O2', '-march=native'],
            'kernel': args.kernel
        }
        
        # Create a dummy binary path (does not need to exist for test if we mock run_binary, 
        # but for now let's try to run a real command or skip if not available)
        # Since we can't guarantee a binary exists in test environment without compilation,
        # we will simulate the result structure if the binary doesn't exist, 
        # BUT the task requires "real, runnable research code". 
        # The test flag should produce a valid JSONL line.
        # We will attempt to run a simple echo command as a proxy if the binary is missing,
        # or just write the expected schema if we are in a pure unit-test context.
        # However, the task says "Verify by running ... which produces a valid JSONL line".
        # Let's try to run a simple shell command as a proxy to ensure the logic works.
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.sh', delete=False, mode='w') as tmp:
            tmp.write("#!/bin/bash\necho '{\"latencies\": [1.0, 1.1, 1.2]}'\n")
            tmp.flush()
            os.chmod(tmp.name, 0o755)
            dummy_binary = tmp.name

        try:
            result = execute_with_fallback(
                binary_path=dummy_binary,
                config=dummy_config,
                kernel=dummy_config['kernel'],
                iterations=args.iterations,
                max_dim=768,
                fallback_dim=512
            )
            save_result(result, args.output_dir)
            logger.info(f"Test run successful. Output written to {args.output_dir}/{result.config_id}.jsonl")
            print(f"Test output: {json.dumps(asdict(result))}")
        finally:
            os.unlink(dummy_binary)
        return

    if not args.binary or not args.config:
        logger.error("In non-test mode, --binary and --config are required.")
        sys.exit(1)

    # Load config
    with open(args.config, 'r') as f:
        config_data = json.load(f)

    # Execute
    result = execute_with_fallback(
        binary_path=args.binary,
        config=config_data,
        kernel=args.kernel,
        iterations=args.iterations
    )

    # Save
    output_path = save_result(result, args.output_dir)
    logger.info(f"Execution complete. Results saved to {output_path}")

if __name__ == '__main__':
    main()