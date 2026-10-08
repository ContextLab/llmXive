"""
Memory profiling harness for code solutions.

This module provides functions to profile memory usage of code solutions,
including:
    - Single execution profiling with tracemalloc
    - Stability checking (IQR-based)
    - Timeout and error handling
    - Batch processing of problems

Key Functions:
    - profile_single_execution: Profile one execution of code
    - check_stability: Verify measurement stability across runs
    - profile_code_solution: Profile a solution with stability check
    - process_problems: Batch process multiple problems

Profiling Strategy:
    - Uses tracemalloc for steady-state memory
    - Uses memory_profiler for peak memory (if available)
    - Implements IQR-based stability check (max 2 retries)
    - Handles timeouts (60s) and syntax errors gracefully

Usage:
    from profile import process_problems
    measurements = process_problems(solutions, output_path='data/processed/memory_measurements.csv')
"""

import os
import sys
import time
import tracemalloc
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from config import (
    TIMEOUT_SECONDS,
    CI_MEMORY_LIMIT_GB,
    STABILITY_IQR_THRESHOLD,
    STABILITY_MAX_RUNS,
    DATA_PROCESSED_DIR
)
from utils import (
    ExecutionTimeoutError,
    OutOfMemoryError,
    SyntaxErrorWrapper,
    run_with_timeout_and_memory_limit,
    calculate_total_resource_cost
)


def profile_single_execution(code: str, timeout: int = TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Profile memory usage of a single code execution.

    Args:
        code: Code string to execute.
        timeout: Execution timeout in seconds.

    Returns:
        Dict[str, Any]: Profiling results including peak_memory, steady_state, status.
    """
    result = {
        'peak_memory': 0,
        'steady_state': 0,
        'status': 'success',
        'execution_time': 0
    }

    # Write code to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        # Start memory tracking
        tracemalloc.start()

        start_time = time.time()

        # Execute with timeout and memory limit
        try:
            exec_result = run_with_timeout_and_memory_limit(
                temp_path,
                timeout=timeout,
                memory_limit_gb=CI_MEMORY_LIMIT_GB
            )

            if exec_result['status'] == 'timeout':
                result['status'] = 'timeout'
                result['peak_memory'] = 0
                result['steady_state'] = 0
            elif exec_result['status'] == 'oom':
                result['status'] = 'oom'
                result['peak_memory'] = 0
                result['steady_state'] = 0
            else:
                # Get memory stats
                current, peak = tracemalloc.get_traced_memory()
                result['peak_memory'] = peak
                result['steady_state'] = current
                result['execution_time'] = time.time() - start_time

        except ExecutionTimeoutError:
            result['status'] = 'timeout'
            result['peak_memory'] = 0
            result['steady_state'] = 0
        except OutOfMemoryError:
            result['status'] = 'oom'
            result['peak_memory'] = 0
            result['steady_state'] = 0
        except SyntaxErrorWrapper as e:
            result['status'] = 'N/A'
            result['peak_memory'] = 0
            result['steady_state'] = 0
        except Exception as e:
            result['status'] = 'error'
            result['peak_memory'] = 0
            result['steady_state'] = 0

    finally:
        tracemalloc.stop()
        os.unlink(temp_path)

    return result


def check_stability(measurements: List[float], threshold: float = STABILITY_IQR_THRESHOLD) -> bool:
    """
    Check if a set of measurements is stable.

    Stability is determined by the Interquartile Range (IQR) relative to
    the median. If IQR > threshold * median, the measurements are unstable.

    Args:
        measurements: List of measurement values.
        threshold: IQR threshold as fraction of median.

    Returns:
        bool: True if stable, False otherwise.
    """
    if len(measurements) < 3:
        return True  # Not enough data to assess stability

    arr = np.array(measurements)
    median = np.median(arr)
    if median == 0:
        return True  # Avoid division by zero

    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1

    return (iqr / median) <= threshold


def profile_code_solution(
    code: str,
    max_runs: int = STABILITY_MAX_RUNS,
    timeout: int = TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Profile a code solution with stability checking.

    Runs the code multiple times and checks for stability. If unstable,
    re-runs up to max_runs times.

    Args:
        code: Code string to profile.
        max_runs: Maximum number of runs for stability check.
        timeout: Timeout per execution.

    Returns:
        Dict[str, Any]: Final profiling results with median values.
    """
    all_peaks = []
    all_steady = []
    all_times = []
    statuses = []

    for run in range(max_runs):
        result = profile_single_execution(code, timeout)
        statuses.append(result['status'])

        if result['status'] == 'success':
            all_peaks.append(result['peak_memory'])
            all_steady.append(result['steady_state'])
            all_times.append(result['execution_time'])

        # Check stability if we have enough successful runs
        if len(all_peaks) >= 3:
            if check_stability(all_peaks):
                break

    # Calculate median values
    if all_peaks:
      median_peak = float(np.median(all_peaks))
      median_steady = float(np.median(all_steady))
      median_time = float(np.median(all_times))
    else:
      median_peak = 0
      median_steady = 0
      median_time = 0

    # Determine overall status
    if 'timeout' in statuses:
        final_status = 'timeout'
    elif 'oom' in statuses:
        final_status = 'oom'
    elif 'N/A' in statuses:
        final_status = 'N/A'
    else:
        final_status = 'success'

    # Calculate resource cost
    resource_cost = calculate_total_resource_cost(
        median_peak,
        median_time,
        final_status
    )

    return {
        'peak_memory': median_peak,
        'steady_state': median_steady,
        'execution_time': median_time,
        'status': final_status,
        'total_resource_cost': resource_cost,
        'n_runs': len(all_peaks)
    }


def process_problems(
    solutions: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process multiple code solutions and profile their memory usage.

    Args:
        solutions: List of solution dictionaries with 'solution' code.
        output_path: Optional path to save CSV results.

    Returns:
        List[Dict]: List of profiling results.
    """
    results = []

    for i, sol in enumerate(solutions):
        print(f"Profiling solution {i+1}/{len(solutions)}")

        code = sol.get('solution')
        if not code:
            results.append({
                'problem_id': sol.get('problem_id', i),
                'source_type': sol.get('source_type', 'unknown'),
                'peak_memory': 0,
                'steady_state': 0,
                'status': 'N/A',
                'total_resource_cost': 0
            })
            continue

        profile_result = profile_code_solution(code)

        result = {
            'problem_id': sol.get('problem_id', i),
            'source_type': sol.get('source_type', 'LLM'),
            'peak_memory': profile_result['peak_memory'],
            'steady_state': profile_result['steady_state'],
            'status': profile_result['status'],
            'total_resource_cost': profile_result['total_resource_cost']
        }
        results.append(result)

    # Save to CSV if path provided
    if output_path:
        from utils import write_memory_measurements_csv
        write_memory_measurements_csv(results, output_path)

    return results


def main():
    """
    Main entry point for profiling.

    Loads generated solutions and profiles them.
    """
    import json
    from config import DATA_PROCESSED_DIR

    input_path = os.path.join(DATA_PROCESSED_DIR, 'generated_solutions.json')
    output_path = os.path.join(DATA_PROCESSED_DIR, 'memory_measurements.csv')

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r') as f:
        solutions = json.load(f)

    print(f"Profiling {len(solutions)} solutions...")
    results = process_problems(solutions, output_path)

    print(f"Profiling complete. Results saved to {output_path}")


if __name__ == '__main__':
    main()