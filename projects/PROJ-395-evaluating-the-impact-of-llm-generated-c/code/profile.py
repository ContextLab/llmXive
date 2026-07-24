"""
Memory profiling harness for LLM-generated and human-written code solutions.

This module provides functions to:
- Profile single code executions for memory usage
- Check stability of measurements across multiple runs
- Profile complete code solutions with stability checks
- Handle various execution errors gracefully

The profiler uses tracemalloc for steady-state memory and memory_profiler
for peak memory measurements.
"""

import os
import sys
import time
import tracemalloc
import subprocess
import tempfile
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import statistics

# Import shared utilities and exceptions
from utils import (
    ExecutionTimeoutError,
    OutOfMemoryError,
    SyntaxErrorWrapper,
    timeout_context,
    run_with_timeout_and_memory_limit,
    execute_code_safely,
    retry_on_transient_error,
    calculate_total_resource_cost,
    write_memory_measurements_csv,
    read_memory_measurements_csv
)
import config

# Constants
PROFILE_RUNS = 3
STABILITY_IQR_THRESHOLD = 0.15  # 15% of median
MAX_STABILITY_RETRIES = 2
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MEMORY_LIMIT_GB = 7.0


def profile_single_execution(
    code: str,
    problem_id: str,
    source_type: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_gb: float = DEFAULT_MEMORY_LIMIT_GB
) -> Dict[str, Any]:
    """
    Profile a single execution of code for memory usage.

    Args:
        code: The Python code to profile
        problem_id: Identifier for the problem being solved
        source_type: Type of code source ('llm' or 'human')
        timeout_seconds: Maximum execution time in seconds
        memory_limit_gb: Maximum memory limit in gigabytes

    Returns:
        Dictionary containing:
            - problem_id: Problem identifier
            - source_type: Source type ('llm' or 'human')
            - peak_memory: Peak memory usage in bytes
            - steady_state: Steady-state memory usage in bytes
            - execution_time: Execution time in seconds
            - status: 'success', 'timeout', 'oom', 'syntax_error', or 'runtime_error'
            - total_resource_cost: Calculated resource cost (Memory * Time + penalty)
    """
    result = {
        'problem_id': problem_id,
        'source_type': source_type,
        'peak_memory': 0,
        'steady_state': 0,
        'execution_time': 0,
        'status': 'success',
        'total_resource_cost': 0
    }

    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Start tracemalloc before execution
        tracemalloc.start()

        start_time = time.time()

        # Execute the code with timeout and memory limits
        try:
            with timeout_context(timeout_seconds):
                # Execute the code
                exec_globals = {}
                exec(code, exec_globals)

                # Get memory snapshots
                current, peak = tracemalloc.get_traced_memory()

                end_time = time.time()
                execution_time = end_time - start_time

                result['steady_state'] = current
                result['peak_memory'] = peak
                result['execution_time'] = execution_time
                result['status'] = 'success'

        except ExecutionTimeoutError:
            result['status'] = 'timeout'
            result['execution_time'] = timeout_seconds
            # Calculate resource cost for timeout (censored data)
            result['total_resource_cost'] = calculate_total_resource_cost(
                0,  # Memory not available
                timeout_seconds,
                is_failure=True
            )
            return result

        except OutOfMemoryError:
            result['status'] = 'oom'
            result['execution_time'] = time.time() - start_time
            # Calculate resource cost for OOM (censored data)
            result['total_resource_cost'] = calculate_total_resource_cost(
                0,  # Memory not available
                result['execution_time'],
                is_failure=True
            )
            return result

        except SyntaxError as e:
            result['status'] = 'syntax_error'
            result['execution_time'] = time.time() - start_time
            # Calculate resource cost for syntax error
            result['total_resource_cost'] = calculate_total_resource_cost(
                0,  # Memory not available
                result['execution_time'],
                is_failure=True
            )
            return result

        except Exception as e:
            result['status'] = 'runtime_error'
            result['execution_time'] = time.time() - start_time
            # Calculate resource cost for runtime error
            result['total_resource_cost'] = calculate_total_resource_cost(
                0,  # Memory not available
                result['execution_time'],
                is_failure=True
            )
            return result

        finally:
            tracemalloc.stop()

        # Calculate resource cost for successful execution
        result['total_resource_cost'] = calculate_total_resource_cost(
            result['peak_memory'],
            result['execution_time'],
            is_failure=False
        )

    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    return result


def check_stability(
    measurements: List[Dict[str, Any]],
    metric: str = 'peak_memory'
) -> Tuple[bool, float, float]:
    """
    Check if a set of measurements is stable based on IQR threshold.

    Args:
        measurements: List of measurement dictionaries
        metric: The metric to check for stability ('peak_memory' or 'steady_state')

    Returns:
        Tuple of (is_stable, iqr_value, median_value)
    """
    if len(measurements) < 2:
        return True, 0.0, 0.0

    values = [m[metric] for m in measurements if m['status'] == 'success']

    if len(values) < 2:
        return True, 0.0, 0.0

    # Calculate IQR
    sorted_values = sorted(values)
    n = len(sorted_values)

    # Calculate Q1 and Q3
    q1_idx = n // 4
    q3_idx = (3 * n) // 4

    q1 = sorted_values[q1_idx]
    q3 = sorted_values[q3_idx]
    iqr = q3 - q1

    # Calculate median
    median = statistics.median(values)

    # Check if IQR is within threshold of median
    if median == 0:
        return True, iqr, median

    iqr_ratio = iqr / median
    is_stable = iqr_ratio <= STABILITY_IQR_THRESHOLD

    return is_stable, iqr, median


def profile_code_solution(
    code: str,
    problem_id: str,
    source_type: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_gb: float = DEFAULT_MEMORY_LIMIT_GB,
    max_runs: int = PROFILE_RUNS,
    max_retries: int = MAX_STABILITY_RETRIES
) -> List[Dict[str, Any]]:
    """
    Profile a code solution with stability checks.

    Runs the code multiple times and checks for stability. If the measurements
    are not stable, re-runs up to max_retries times.

    Args:
        code: The Python code to profile
        problem_id: Identifier for the problem
        source_type: Type of code source ('llm' or 'human')
        timeout_seconds: Maximum execution time
        memory_limit_gb: Maximum memory limit
        max_runs: Number of runs for stability check
        max_retries: Maximum number of retries if unstable

    Returns:
        List of measurement dictionaries (all runs, including retries)
    """
    all_measurements = []
    current_runs = []

    # Initial runs
    for i in range(max_runs):
        result = profile_single_execution(
            code, problem_id, source_type, timeout_seconds, memory_limit_gb
        )
        all_measurements.append(result)
        current_runs.append(result)

    # Check stability
    is_stable, iqr, median = check_stability(current_runs)

    retry_count = 0
    while not is_stable and retry_count < max_retries:
        retry_count += 1
        # Additional runs for retry
        for i in range(max_runs):
            result = profile_single_execution(
                code, problem_id, source_type, timeout_seconds, memory_limit_gb
            )
            all_measurements.append(result)
            current_runs.append(result)

        # Check stability again with all runs so far
        is_stable, iqr, median = check_stability(current_runs)

    return all_measurements


def process_problems(
    problems: List[Dict[str, str]],
    output_path: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_gb: float = DEFAULT_MEMORY_LIMIT_GB
) -> None:
    """
    Process a list of problems and write results to CSV.

    Args:
        problems: List of dictionaries with 'problem_id', 'code', 'source_type'
        output_path: Path to output CSV file
        timeout_seconds: Maximum execution time per problem
        memory_limit_gb: Maximum memory limit
    """
    results = []

    for problem in problems:
        problem_id = problem['problem_id']
        code = problem['code']
        source_type = problem['source_type']

        print(f"Processing problem {problem_id} ({source_type})...")

        try:
            # Profile the code solution
            measurements = profile_code_solution(
                code, problem_id, source_type,
                timeout_seconds, memory_limit_gb
            )

            # Add all measurements to results
            for measurement in measurements:
                results.append(measurement)

        except Exception as e:
            # Handle any unexpected errors gracefully
            error_result = {
                'problem_id': problem_id,
                'source_type': source_type,
                'peak_memory': 0,
                'steady_state': 0,
                'execution_time': 0,
                'status': 'error',
                'total_resource_cost': 0,
                'error_message': str(e)
            }
            results.append(error_result)
            print(f"Error processing problem {problem_id}: {e}")

    # Write results to CSV
    write_memory_measurements_csv(results, output_path)
    print(f"Results written to {output_path}")


def main():
    """
    Main entry point for the profiling harness.

    Reads problems from a JSON file, profiles them, and writes results to CSV.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Profile code solutions for memory usage')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file with problems')
    parser.add_argument('--output', '-o', required=True, help='Output CSV file path')
    parser.add_argument('--timeout', '-t', type=int, default=DEFAULT_TIMEOUT_SECONDS,
                      help='Timeout in seconds per execution')
    parser.add_argument('--memory-limit', '-m', type=float, default=DEFAULT_MEMORY_LIMIT_GB,
                      help='Memory limit in GB')

    args = parser.parse_args()

    # Load problems from JSON
    with open(args.input, 'r') as f:
        problems = json.load(f)

    # Process problems
    process_problems(
        problems,
        args.output,
        args.timeout,
        args.memory_limit
    )


if __name__ == '__main__':
    main()