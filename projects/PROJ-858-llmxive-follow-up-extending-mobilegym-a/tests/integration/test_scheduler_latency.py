"""
Integration test for scheduler latency benchmarking (T024).

Verifies that scheduler latency is < 10% of batch execution time.
Uses real data from tests/fixtures/mock_coverage_history.json.
"""
import json
import os
import sys
import time
import statistics
from typing import Dict, List, Any

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from code.scheduler.curriculum_scheduler import run_scheduler, initialize_scheduler_config
from code.utils.logging import get_task_logger, log_task_start, log_task_complete

# Constants for benchmarking
LATENCY_THRESHOLD_PERCENT = 10.0
BATCH_SIZE = 5
NUM_ITERATIONS = 10
MOCK_HISTORY_PATH = "tests/fixtures/mock_coverage_history.json"


def load_mock_coverage_history() -> List[Dict[str, Any]]:
    """Load real mock coverage history from fixture file."""
    fixture_path = os.path.join(PROJECT_ROOT, MOCK_HISTORY_PATH)
    if not os.path.exists(fixture_path):
        raise FileNotFoundError(f"Mock coverage history fixture not found at {fixture_path}")
    
    with open(fixture_path, 'r') as f:
        return json.load(f)


def measure_scheduler_latency(
    coverage_history: List[Dict[str, Any]],
    batch_size: int,
    num_iterations: int
) -> Dict[str, float]:
    """
    Measure scheduler latency over multiple iterations.
    
    Returns:
        Dictionary with mean, median, min, max latency in seconds.
    """
    config = initialize_scheduler_config()
    latencies = []
    
    for i in range(num_iterations):
        start_time = time.perf_counter()
        
        # Run scheduler with mock history
        result = run_scheduler(
            coverage_history=coverage_history,
            batch_size=batch_size,
            config=config
        )
        
        end_time = time.perf_counter()
        latency = end_time - start_time
        latencies.append(latency)
        
        # Verify result structure
        assert isinstance(result, dict), "Scheduler should return a dictionary"
        assert 'tasks' in result, "Result should contain 'tasks' key"
        assert len(result['tasks']) == batch_size, f"Expected {batch_size} tasks, got {len(result['tasks'])}"
    
    return {
        'mean': statistics.mean(latencies),
        'median': statistics.median(latencies),
        'min': min(latencies),
        'max': max(latencies),
        'std_dev': statistics.stdev(latencies) if len(latencies) > 1 else 0.0
    }


def estimate_batch_execution_time(batch_size: int) -> float:
    """
    Estimate batch execution time based on typical MobileGym rollout duration.
    
    This is a conservative estimate based on CPU-only inference times for 
    Qwen3-VL-4B-Instruct model (as specified in project constraints).
    
    Returns:
        Estimated batch execution time in seconds.
    """
    # Typical rollout time for vision-language model on CPU: ~2-5 seconds
    # Conservative estimate: 3 seconds per rollout
    avg_rollout_time = 3.0
    return avg_rollout_time * batch_size


def run_latency_benchmark() -> bool:
    """
    Run the full latency benchmark and verify results.
    
    Returns:
        True if benchmark passes (latency < 10% of batch time), False otherwise.
    """
    logger = get_task_logger("T024_latency_benchmark")
    log_task_start(logger, "T024", "Running scheduler latency benchmark")
    
    try:
        # Load real mock data
        logger.info("Loading mock coverage history from fixture")
        coverage_history = load_mock_coverage_history()
        logger.info(f"Loaded {len(coverage_history)} coverage vectors")
        
        if not coverage_history:
            raise ValueError("Mock coverage history is empty")
        
        # Measure scheduler latency
        logger.info(f"Running scheduler benchmark: {NUM_ITERATIONS} iterations, batch_size={BATCH_SIZE}")
        latency_stats = measure_scheduler_latency(
            coverage_history=coverage_history,
            batch_size=BATCH_SIZE,
            num_iterations=NUM_ITERATIONS
        )
        
        logger.info(f"Scheduler latency stats: mean={latency_stats['mean']:.4f}s, "
                   f"median={latency_stats['median']:.4f}s, max={latency_stats['max']:.4f}s")
        
        # Estimate batch execution time
        batch_execution_time = estimate_batch_execution_time(BATCH_SIZE)
        logger.info(f"Estimated batch execution time: {batch_execution_time:.2f}s")
        
        # Calculate threshold
        threshold = batch_execution_time * (LATENCY_THRESHOLD_PERCENT / 100.0)
        logger.info(f"Latency threshold (10% of batch time): {threshold:.4f}s")
        
        # Verify latency is within threshold
        max_latency = latency_stats['max']
        passed = max_latency < threshold
        
        if passed:
            logger.info(f"✓ PASS: Max scheduler latency ({max_latency:.4f}s) < threshold ({threshold:.4f}s)")
        else:
            logger.error(f"✗ FAIL: Max scheduler latency ({max_latency:.4f}s) >= threshold ({threshold:.4f}s)")
        
        # Write benchmark results to data/processed/
        results = {
            'task_id': 'T024',
            'benchmark_type': 'scheduler_latency',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'parameters': {
                'batch_size': BATCH_SIZE,
                'num_iterations': NUM_ITERATIONS,
                'latency_threshold_percent': LATENCY_THRESHOLD_PERCENT
            },
            'results': {
                'scheduler_latency': latency_stats,
                'estimated_batch_execution_time': batch_execution_time,
                'threshold': threshold,
                'max_latency': max_latency,
                'passed': passed
            }
        }
        
        results_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'scheduler_latency_benchmark.json')
        os.makedirs(os.path.dirname(results_path), exist_ok=True)
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Benchmark results written to {results_path}")
        
        log_task_complete(logger, "T024", f"Latency benchmark {'passed' if passed else 'failed'}")
        return passed
        
    except Exception as e:
        logger.error(f"Benchmark failed with error: {str(e)}")
        log_task_complete(logger, "T024", f"Failed: {str(e)}")
        return False


def main():
    """Entry point for the latency benchmark test."""
    print("=" * 60)
    print("T024: Scheduler Latency Benchmark")
    print("=" * 60)
    
    success = run_latency_benchmark()
    
    if success:
        print("\n✓ Benchmark PASSED: Scheduler latency is within acceptable limits.")
        sys.exit(0)
    else:
        print("\n✗ Benchmark FAILED: Scheduler latency exceeds threshold.")
        sys.exit(1)


if __name__ == "__main__":
    main()