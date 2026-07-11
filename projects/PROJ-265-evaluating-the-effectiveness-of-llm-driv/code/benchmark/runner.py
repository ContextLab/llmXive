"""
Benchmark runner for executing original and simplified code functions.
Enforces 5s timeout and 500MB memory limits on every iteration.
"""
import os
import sys
import time
import tracemalloc
import json
import tempfile
import subprocess
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import sandbox utilities for strict execution limits
from utils.sandbox import (
    run_in_sandbox,
    SandboxTimeoutError,
    SandboxMemoryError,
    SandboxExecutionError,
    ExecutionResult
)
from utils.logger import (
    get_logger,
    log_stage_start,
    log_stage_complete,
    log_stage_error,
    log_message
)

logger = get_logger(__name__)

# Configuration constants
DEFAULT_ITERATIONS = 20
TIMEOUT_SECONDS = 5
MEMORY_LIMIT_MB = 500
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_MB * 1024 * 1024


class BenchmarkResult:
    """Stores benchmark results for a single function execution."""
    def __init__(self, code_type: str, stratum: str, func_name: str):
        self.code_type = code_type
        self.stratum = stratum
        self.func_name = func_name
        self.timings: List[float] = []
        self.memory_peaks: List[int] = []
        self.success_count = 0
        self.timeout_count = 0
        self.memory_limit_count = 0
        self.error_count = 0
        self.error_messages: List[str] = []

    def add_result(self, success: bool, duration: float, memory: int, error: Optional[str] = None):
        if success:
            self.timings.append(duration)
            self.memory_peaks.append(memory)
            self.success_count += 1
        else:
            if error and "timeout" in error.lower():
                self.timeout_count += 1
            elif error and "memory" in error.lower():
                self.memory_limit_count += 1
            else:
                self.error_count += 1
            if error:
                self.error_messages.append(error)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code_type": self.code_type,
            "stratum": self.stratum,
            "func_name": self.func_name,
            "success_count": self.success_count,
            "timeout_count": self.timeout_count,
            "memory_limit_count": self.memory_limit_count,
            "error_count": self.error_count,
            "mean_time_ms": (sum(self.timings) / len(self.timings) * 1000) if self.timings else 0.0,
            "std_time_ms": (
                (sum((t - sum(self.timings)/len(self.timings))**2 for t in self.timings) / len(self.timings))**0.5 * 1000
            ) if len(self.timings) > 1 else 0.0,
            "mean_memory_bytes": sum(self.memory_peaks) / len(self.memory_peaks) if self.memory_peaks else 0,
            "max_memory_bytes": max(self.memory_peaks) if self.memory_peaks else 0,
            "total_iterations": self.success_count + self.timeout_count + self.memory_limit_count + self.error_count
        }


def run_single_benchmark(
    code: str,
    func_name: str,
    iterations: int,
    timeout: int = TIMEOUT_SECONDS,
    memory_limit: int = MEMORY_LIMIT_BYTES
) -> Tuple[List[float], List[int], List[Optional[str]]]:
    """
    Execute code repeatedly in a sandbox with strict limits.
    Returns lists of durations, memory peaks, and error messages.
    """
    durations = []
    memory_peaks = []
    errors = []

    for i in range(iterations):
        start_time = time.perf_counter()
        tracemalloc.start()

        try:
            # Create a temporary script to run the function
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                # Run in sandbox with limits
                result = run_in_sandbox(
                    python_path=sys.executable,
                    script_path=temp_path,
                    timeout_seconds=timeout,
                    memory_limit_bytes=memory_limit
                )

                current, peak = tracemalloc.get_traced_memory()
                duration = time.perf_counter() - start_time
                tracemalloc.stop()

                if result.success:
                    durations.append(duration)
                    memory_peaks.append(peak)
                    errors.append(None)
                else:
                    error_msg = result.error or "Unknown execution error"
                    durations.append(duration)
                    memory_peaks.append(peak)
                    errors.append(error_msg)

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            duration = time.perf_counter() - start_time
            tracemalloc.stop()
            durations.append(duration)
            memory_peaks.append(0)
            errors.append(str(e))

    return durations, memory_peaks, errors


def benchmark_function_pair(
    original_code: str,
    simplified_code: str,
    func_name: str,
    stratum: str,
    iterations: int = DEFAULT_ITERATIONS
) -> Tuple[BenchmarkResult, BenchmarkResult]:
    """
    Benchmark both original and simplified versions of a function.
    """
    log_message(logger, "Starting benchmark", func_name=func_name, stratum=stratum, iterations=iterations)

    # Benchmark original
    orig_durations, orig_memory, orig_errors = run_single_benchmark(
        original_code, func_name, iterations
    )

    orig_result = BenchmarkResult("original", stratum, func_name)
    for i, (dur, mem, err) in enumerate(zip(orig_durations, orig_memory, orig_errors)):
        orig_result.add_result(err is None, dur, mem, err)

    # Benchmark simplified
    simp_durations, simp_memory, simp_errors = run_single_benchmark(
        simplified_code, func_name, iterations
    )

    simp_result = BenchmarkResult("simplified", stratum, func_name)
    for i, (dur, mem, err) in enumerate(zip(simp_durations, simp_memory, simp_errors)):
        simp_result.add_result(err is None, dur, mem, err)

    log_message(
        logger,
        "Benchmark complete",
        func_name=func_name,
        orig_success=orig_result.success_count,
        simp_success=simp_result.success_count
    )

    return orig_result, simp_result


def load_valid_pairs(input_path: Path) -> List[Dict[str, Any]]:
    """Load valid pairs from JSONL file."""
    pairs = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))
    return pairs


def run_benchmark_pipeline(
    input_path: Path,
    output_path: Path,
    iterations: int = DEFAULT_ITERATIONS
) -> Path:
    """
    Run benchmark on all valid pairs and save results.
    """
    log_stage_start(logger, "benchmark_pipeline", input=str(input_path), iterations=iterations)

    pairs = load_valid_pairs(input_path)
    log_message(logger, f"Loaded {len(pairs)} pairs for benchmarking")

    all_results = []

    for idx, pair in enumerate(pairs):
        log_message(logger, f"Processing pair {idx+1}/{len(pairs)}", func_name=pair.get('func_name', 'unknown'))

        original_code = pair.get('original_code', '')
        simplified_code = pair.get('simplified_code', '')
        func_name = pair.get('func_name', 'unknown')
        stratum = pair.get('stratum', 'unknown')

        if not original_code or not simplified_code:
            log_stage_error(logger, "Skipping pair with missing code", func_name=func_name)
            continue

        try:
            orig_result, simp_result = benchmark_function_pair(
                original_code, simplified_code, func_name, stratum, iterations
            )
            all_results.append(orig_result.to_dict())
            all_results.append(simp_result.to_dict())
        except Exception as e:
            log_stage_error(logger, f"Benchmark failed for {func_name}: {str(e)}")
            continue

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in all_results:
            f.write(json.dumps(result) + '\n')

    log_stage_complete(logger, "benchmark_pipeline", output=str(output_path), results=len(all_results))
    return output_path


def main():
    """Entry point for benchmark runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run benchmark on valid code pairs")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/valid_pairs.jsonl",
        help="Path to input valid_pairs.jsonl"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/benchmark_results.jsonl",
        help="Path to output benchmark results"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of iterations per function (default: {DEFAULT_ITERATIONS})"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        log_stage_error(logger, f"Input file not found: {input_path}")
        sys.exit(1)

    run_benchmark_pipeline(input_path, output_path, args.iterations)
    print(f"Benchmark complete. Results saved to {output_path}")


if __name__ == "__main__":
    main()