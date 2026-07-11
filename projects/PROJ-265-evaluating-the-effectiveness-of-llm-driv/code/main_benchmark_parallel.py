"""
Main orchestrator for parallel benchmarking (T038).
Replaces main_benchmark.py with multiprocessing optimization.
"""
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error
from benchmark.runner_parallel import run_parallel_benchmark_pipeline, ParallelBenchmarkResult

def load_valid_pairs_safe(pairs_path: Path) -> List[Dict[str, Any]]:
    """Load valid pairs with error handling."""
    if not pairs_path.exists():
        raise FileNotFoundError(f"Valid pairs file not found: {pairs_path}")
    
    with open(pairs_path, 'r') as f:
        pairs = [json.loads(line) for line in f if line.strip()]
    
    logger.info(f"Loaded {len(pairs)} valid pairs")
    return pairs

def run_full_benchmark_pipeline_parallel(
    pairs_path: Path,
    output_path: Path,
    num_iterations: int = 20,
    timeout: int = 5,
    memory_limit_mb: int = 500,
    max_workers: int = None
) -> List[ParallelBenchmarkResult]:
    """
    Run the full parallel benchmark pipeline.
    
    Args:
        pairs_path: Path to valid_pairs.jsonl
        output_path: Path for output results
        num_iterations: Number of iterations per function
        timeout: Timeout per execution
        memory_limit_mb: Memory limit per execution
        max_workers: Number of parallel workers
    
    Returns:
        List of benchmark results
    """
    logger = get_logger(__name__)
    log_stage_start(logger, "Full Parallel Benchmark Pipeline", {
        "pairs_path": str(pairs_path),
        "output_path": str(output_path),
        "num_iterations": num_iterations,
        "timeout": timeout,
        "memory_limit_mb": memory_limit_mb,
        "max_workers": max_workers
    })
    
    try:
        # Validate input exists
        if not pairs_path.exists():
            raise FileNotFoundError(f"Pairs file not found: {pairs_path}")
        
        # Run parallel benchmark
        results = run_parallel_benchmark_pipeline(
            pairs_path=pairs_path,
            output_path=output_path,
            num_iterations=num_iterations,
            timeout=timeout,
            memory_limit_mb=memory_limit_mb,
            max_workers=max_workers
        )
        
        log_stage_complete(logger, "Full Parallel Benchmark Pipeline", {
            "total_results": len(results),
            "output_path": str(output_path)
        })
        
        return results
        
    except Exception as e:
        log_stage_error(logger, "Full Parallel Benchmark Pipeline", str(e))
        raise

def main():
    """Main entry point for parallel benchmarking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run full parallel benchmark pipeline")
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
        results = run_full_benchmark_pipeline_parallel(
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