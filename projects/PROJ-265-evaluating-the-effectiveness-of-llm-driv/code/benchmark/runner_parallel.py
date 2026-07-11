"""
Parallel benchmark runner for T038.
Optimizes the benchmark loop using multiprocessing to meet target runtime.
"""
import os
import sys
import json
import time
import tracemalloc
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import traceback

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.sandbox import run_in_sandbox, SandboxTimeoutError, SandboxMemoryError
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error

@dataclass
class ParallelBenchmarkResult:
    pair_id: str
    stratum: str
    original_times: List[float]
    original_memory: List[float]
    simplified_times: List[float]
    simplified_memory: List[float]
    original_mean_time: float
    original_std_time: float
    simplified_mean_time: float
    simplified_std_time: float
    status: str  # 'success', 'timeout', 'memory_error', 'exception'
    error_message: str = ""

def _load_valid_pairs_safe(pairs_path: Path) -> List[Dict[str, Any]]:
    """Load valid pairs with error handling."""
    if not pairs_path.exists():
        raise FileNotFoundError(f"Valid pairs file not found: {pairs_path}")
    
    with open(pairs_path, 'r') as f:
        return [json.loads(line) for line in f if line.strip()]

def _benchmark_single_pair(args: Tuple[str, Dict[str, Any], int, int, int]) -> ParallelBenchmarkResult:
    """
    Benchmark a single function pair.
    Args: (pair_id, pair_data, num_iterations, timeout, memory_limit_mb)
    """
    pair_id, pair_data, num_iterations, timeout, memory_limit_mb = args
    original_code = pair_data['original_code']
    simplified_code = pair_data['simplified_code']
    stratum = pair_data.get('stratum', 'unknown')
    
    result = ParallelBenchmarkResult(
        pair_id=pair_id,
        stratum=stratum,
        original_times=[],
        original_memory=[],
        simplified_times=[],
        simplified_memory=[],
        original_mean_time=0.0,
        original_std_time=0.0,
        simplified_mean_time=0.0,
        simplified_std_time=0.0,
        status='success'
    )
    
    try:
        # Benchmark original function
        for i in range(num_iterations):
            start_time = time.perf_counter()
            tracemalloc.start()
            
            try:
                run_in_sandbox(original_code, timeout=timeout, memory_limit_mb=memory_limit_mb)
                current, peak = tracemalloc.get_traced_memory()
                elapsed = time.perf_counter() - start_time
                
                result.original_times.append(elapsed)
                result.original_memory.append(peak / 1024 / 1024)  # Convert to MB
                
            except SandboxTimeoutError:
                result.status = 'timeout'
                result.error_message = f"Original function timed out on iteration {i}"
                break
            except SandboxMemoryError:
                result.status = 'memory_error'
                result.error_message = f"Original function exceeded memory limit on iteration {i}"
                break
            except Exception as e:
                result.status = 'exception'
                result.error_message = f"Original function exception on iteration {i}: {str(e)}"
                break
            finally:
                tracemalloc.stop()
        
        # If original succeeded, benchmark simplified function
        if result.status == 'success':
            for i in range(num_iterations):
                start_time = time.perf_counter()
                tracemalloc.start()
                
                try:
                    run_in_sandbox(simplified_code, timeout=timeout, memory_limit_mb=memory_limit_mb)
                    current, peak = tracemalloc.get_traced_memory()
                    elapsed = time.perf_counter() - start_time
                    
                    result.simplified_times.append(elapsed)
                    result.simplified_memory.append(peak / 1024 / 1024)  # Convert to MB
                    
                except SandboxTimeoutError:
                    result.status = 'timeout'
                    result.error_message = f"Simplified function timed out on iteration {i}"
                    break
                except SandboxMemoryError:
                    result.status = 'memory_error'
                    result.error_message = f"Simplified function exceeded memory limit on iteration {i}"
                    break
                except Exception as e:
                    result.status = 'exception'
                    result.error_message = f"Simplified function exception on iteration {i}: {str(e)}"
                    break
                finally:
                    tracemalloc.stop()
        
        # Calculate statistics if we have data
        if result.original_times:
            import statistics
            result.original_mean_time = statistics.mean(result.original_times)
            result.original_std_time = statistics.stdev(result.original_times) if len(result.original_times) > 1 else 0.0
        
        if result.simplified_times:
            import statistics
            result.simplified_mean_time = statistics.mean(result.simplified_times)
            result.simplified_std_time = statistics.stdev(result.simplified_times) if len(result.simplified_times) > 1 else 0.0
            
    except Exception as e:
        result.status = 'exception'
        result.error_message = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
    
    return result

def run_parallel_benchmark_pipeline(
    pairs_path: Path,
    output_path: Path,
    num_iterations: int = 20,
    timeout: int = 5,
    memory_limit_mb: int = 500,
    max_workers: int = None
) -> List[ParallelBenchmarkResult]:
    """
    Run benchmark pipeline in parallel using multiprocessing.
    
    Args:
        pairs_path: Path to valid_pairs.jsonl
        output_path: Path for output results JSON
        num_iterations: Number of iterations per function
        timeout: Timeout in seconds per execution
        memory_limit_mb: Memory limit in MB per execution
        max_workers: Number of parallel workers (defaults to CPU count)
    
    Returns:
        List of ParallelBenchmarkResult objects
    """
    logger = get_logger(__name__)
    log_stage_start(logger, "Parallel Benchmark Pipeline", {
        "pairs_path": str(pairs_path),
        "num_iterations": num_iterations,
        "timeout": timeout,
        "memory_limit_mb": memory_limit_mb,
        "max_workers": max_workers
    })
    
    try:
        # Load pairs
        pairs = _load_valid_pairs_safe(pairs_path)
        logger.info(f"Loaded {len(pairs)} pairs for benchmarking")
        
        if max_workers is None:
            max_workers = os.cpu_count() or 1
        
        # Prepare arguments for each pair
        args_list = [
            (pair['id'], pair, num_iterations, timeout, memory_limit_mb)
            for pair in pairs
        ]
        
        results = []
        start_time = time.perf_counter()
        
        # Process in parallel
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_benchmark_single_pair, args): args[0] for args in args_list}
            
            for future in as_completed(futures):
                pair_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed benchmark for pair {pair_id}: {result.status}")
                except Exception as e:
                    logger.error(f"Error processing pair {pair_id}: {str(e)}")
                    results.append(ParallelBenchmarkResult(
                        pair_id=pair_id,
                        stratum='unknown',
                        original_times=[],
                        original_memory=[],
                        simplified_times=[],
                        simplified_memory=[],
                        original_mean_time=0.0,
                        original_std_time=0.0,
                        simplified_mean_time=0.0,
                        simplified_std_time=0.0,
                        status='exception',
                        error_message=str(e)
                    ))
        
        total_time = time.perf_counter() - start_time
        logger.info(f"Completed {len(results)} benchmarks in {total_time:.2f} seconds")
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        
        log_stage_complete(logger, "Parallel Benchmark Pipeline", {
            "total_pairs": len(results),
            "successful": sum(1 for r in results if r.status == 'success'),
            "total_time": total_time,
            "output_path": str(output_path)
        })
        
        return results
        
    except Exception as e:
        log_stage_error(logger, "Parallel Benchmark Pipeline", str(e))
        raise

def main():
    """Main entry point for parallel benchmarking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run parallel benchmark pipeline")
    parser.add_argument("--pairs", type=str, default="data/processed/valid_pairs.jsonl",
                      help="Path to valid pairs JSONL file")
    parser.add_argument("--output", type=str, default="results/benchmark_results_parallel.json",
                      help="Path for output results JSON")
    parser.add_argument("--iterations", type=int, default=20,
                      help="Number of iterations per function")
    parser.add_argument("--timeout", type=int, default=5,
                      help="Timeout in seconds per execution")
    parser.add_argument("--memory-limit", type=int, default=500,
                      help="Memory limit in MB per execution")
    parser.add_argument("--workers", type=int, default=None,
                      help="Number of parallel workers (default: CPU count)")
    
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    log_stage_start(logger, "Parallel Benchmark Main", vars(args))
    
    try:
        results = run_parallel_benchmark_pipeline(
            pairs_path=Path(args.pairs),
            output_path=Path(args.output),
            num_iterations=args.iterations,
            timeout=args.timeout,
            memory_limit_mb=args.memory_limit,
            max_workers=args.workers
        )
        
        success_count = sum(1 for r in results if r.status == 'success')
        logger.info(f"Pipeline completed: {success_count}/{len(results)} successful")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
