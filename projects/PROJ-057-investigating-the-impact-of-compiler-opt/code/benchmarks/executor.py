"""
Executor for running compiled C++ kernels and measuring latency.
Implements fixed iteration counts, memory fallback, and adaptive stopping.
"""
import os
import sys
import subprocess
import json
import time
import argparse
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

# Configuration
DATA_INTERMEDIATES = Path("data/intermediates/raw_logs")
DATA_INTERMEDIATES.mkdir(parents=True, exist_ok=True)

# Constitution Principle VII: Fixed iteration count
FIXED_ITERATIONS = 1000
# Adaptive stop condition: CV <= 1% after 30 iterations
MIN_ITERATIONS_FOR_ADAPTIVE = 30
ADAPTIVE_THRESHOLD = 0.01

@dataclass
class ExecutionResult:
    median: float
    p95: float
    iterations: int
    config_id: str
    downsampled_flag: bool
    std_dev: float
    cv: float
    success: bool
    error_message: Optional[str] = None

def get_memory_pressure():
    """
    Simple heuristic to detect memory pressure.
    Returns True if available memory is critically low.
    """
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            mem_total = 0
            mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            
            if mem_total == 0:
                return False
            return (mem_available / mem_total) < 0.2
    except Exception:
        # Fallback: assume no pressure if we can't check
        return False

def run_binary(
    binary_path: str,
    args: List[str],
    iterations: int = FIXED_ITERATIONS
) -> Tuple[List[float], Optional[str]]:
    """
    Run a binary multiple times and collect latencies.
    
    Args:
        binary_path: Path to the compiled binary.
        args: Arguments to pass to the binary (excluding the binary path).
        iterations: Number of times to run the binary.
    
    Returns:
        Tuple of (list of latencies in seconds, error message if failed).
    """
    latencies = []
    
    for i in range(iterations):
        try:
            start = time.perf_counter()
            result = subprocess.run(
                [binary_path] + args,
                capture_output=True,
                text=True,
                timeout=60  # 60s timeout per run
            )
            end = time.perf_counter()
            
            if result.returncode != 0:
                return latencies, f"Binary exited with code {result.returncode}: {result.stderr}"
            
            latencies.append(end - start)
        except subprocess.TimeoutExpired:
            return latencies, "Binary execution timed out"
        except Exception as e:
            return latencies, str(e)
    
    return latencies, None

def compute_statistics(latencies: List[float]) -> Dict[str, float]:
    """Compute median, p95, std dev, and CV."""
    if not latencies:
        return {"median": 0.0, "p95": 0.0, "std_dev": 0.0, "cv": 0.0}
    
    arr = np.array(latencies)
    median = float(np.median(arr))
    p95 = float(np.percentile(arr, 95))
    std_dev = float(np.std(arr))
    cv = std_dev / median if median > 0 else 0.0
    
    return {
        "median": median,
        "p95": p95,
        "std_dev": std_dev,
        "cv": cv
    }

def execute_with_fallback(
    binary_path: str,
    kernel_type: str,
    config_id: str,
    base_dim: int = 768,
    fallback_dim: int = 512
) -> ExecutionResult:
    """
    Execute a binary with memory pressure fallback.
    
    Args:
        binary_path: Path to the binary.
        kernel_type: Type of kernel (matmul, softmax, layernorm).
        config_id: Unique configuration ID.
        base_dim: Base dimension (e.g., 768).
        fallback_dim: Fallback dimension if memory pressure detected (e.g., 512).
    
    Returns:
        ExecutionResult object.
    """
    current_dim = base_dim
    downsampled = False
    max_attempts = 2
    attempt = 0
    
    all_latencies = []
    error_msg = None
    
    while attempt < max_attempts:
        attempt += 1
        dim_args = [str(current_dim), str(current_dim), f"/tmp/output_{kernel_type}_{attempt}.bin"]
        
        # Check memory pressure before attempting
        if attempt == 1 and get_memory_pressure():
            print(f"Memory Pressure detected, downscaling from {base_dim}x{base_dim} to {fallback_dim}x{fallback_dim}")
            current_dim = fallback_dim
            downsampled = True
            continue
        
        latencies, err = run_binary(binary_path, dim_args, iterations=FIXED_ITERATIONS)
        
        if err:
            error_msg = err
            if attempt == 1 and current_dim == base_dim:
                # Try fallback once
                print(f"First run failed with {base_dim}x{base_dim}, trying fallback {fallback_dim}x{fallback_dim}")
                current_dim = fallback_dim
                downsampled = True
                continue
            else:
                # Both failed
                break
        else:
            all_latencies.extend(latencies)
            break
    
    if not all_latencies:
        return ExecutionResult(
            median=0.0,
            p95=0.0,
            iterations=0,
            config_id=config_id,
            downsampled_flag=downsampled,
            std_dev=0.0,
            cv=0.0,
            success=False,
            error_message=error_msg or "Execution failed"
        )
    
    stats = compute_statistics(all_latencies)
    
    # Adaptive stopping check
    # If we have enough iterations and CV is low, we could stop early in a streaming context
    # Here we ran fixed iterations, but we log the CV for analysis
    if len(all_latencies) >= MIN_ITERATIONS_FOR_ADAPTIVE and stats["cv"] <= ADAPTIVE_THRESHOLD:
        print(f"Adaptive stop condition met (CV={stats['cv']:.4f} <= {ADAPTIVE_THRESHOLD})")
    
    return ExecutionResult(
        median=stats["median"],
        p95=stats["p95"],
        iterations=len(all_latencies),
        config_id=config_id,
        downsampled_flag=downsampled,
        std_dev=stats["std_dev"],
        cv=stats["cv"],
        success=True
    )

def save_result(result: ExecutionResult, output_path: Optional[str] = None):
    """Save execution result to a JSONL file."""
    if output_path is None:
        output_path = str(DATA_INTERMEDIATES / f"{result.config_id}.jsonl")
    
    with open(output_path, 'a') as f:
        f.write(json.dumps(asdict(result)) + '\n')

def main():
    """CLI entry point for testing executor."""
    parser = argparse.ArgumentParser(description="Execute compiled kernels.")
    parser.add_argument("--binary", type=str, required=True, help="Path to the binary.")
    parser.add_argument("--kernel", type=str, required=True, help="Kernel type (matmul, softmax, layernorm).")
    parser.add_argument("--config-id", type=str, required=True, help="Configuration ID.")
    parser.add_argument("--dim", type=int, default=768, help="Base dimension.")
    parser.add_argument("--fallback-dim", type=int, default=512, help="Fallback dimension.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.binary):
        print(f"Error: Binary not found: {args.binary}", file=sys.stderr)
        sys.exit(1)
    
    result = execute_with_fallback(
        args.binary,
        args.kernel,
        args.config_id,
        args.dim,
        args.fallback_dim
    )
    
    save_result(result)
    
    if result.success:
        print(f"Execution successful. Median: {result.median:.6f}s, P95: {result.p95:.6f}s, CV: {result.cv:.4f}")
    else:
        print(f"Execution failed: {result.error_message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
