"""
Pilot Scaling Experiments Runner (T029b)

Executes the BES loop with --mode symbolic on a small subset of puzzles (N=10..50)
to profile runtime and memory usage, generating scaling_raw_logs.json.
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.main import BESOrchestrator, BESRunResult
from code.utils.seed import set_seed
from code.utils.logger import setup_logging
from code.config import initialize_experiment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pilot_scaling")

def run_pilot_scaling(
    n_values: list,
    count: int,
    output_path: Path,
    seed: int = 42
):
    """
    Run pilot scaling experiments across specified N values.

    Args:
        n_values: List of puzzle sizes to test (e.g., [10, 20, 30, 40, 50])
        count: Number of puzzles to generate/test per N value
        output_path: Path to write scaling_raw_logs.json
        seed: Random seed for reproducibility
    """
    set_seed(seed)
    results = []
    
    logger.info(f"Starting pilot scaling experiments: N={n_values}, count={count}")
    
    for n in n_values:
        logger.info(f"Running experiments for N={n}")
        start_time = time.time()
        
        try:
            # Initialize experiment context
            exp_id = initialize_experiment(
                experiment_id=f"pilot_scaling_n{n}",
                mode="symbolic",
                n=n,
                count=count
            )
            
            # Create orchestrator
            orchestrator = BESOrchestrator(
                experiment_id=exp_id,
                mode="symbolic",
                n=n,
                count=count,
                seed=seed
            )
            
            # Run the experiment
            result: BESRunResult = orchestrator.run()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Record metrics
            result_record = {
                "puzzle_id": f"pilot_n{n}_batch",
                "n": n,
                "count": count,
                "success_count": result.success_count,
                "total_attempts": result.total_attempts,
                "success_rate": result.success_count / result.total_attempts if result.total_attempts > 0 else 0.0,
                "wall_clock_seconds": duration,
                "avg_time_per_puzzle": duration / count if count > 0 else 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "mode": "symbolic",
                "status": "completed" if result.success_count > 0 else "partial"
            }
            
            # Add detailed stats if available
            if hasattr(result, 'memory_usage_mb'):
                result_record['memory_usage_mb'] = result.memory_usage_mb
            if hasattr(result, 'cpu_percent_avg'):
                result_record['cpu_percent_avg'] = result.cpu_percent_avg
                
            results.append(result_record)
            logger.info(f"N={n}: Success rate={result_record['success_rate']:.2%}, "
                      f"Duration={duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error running experiments for N={n}: {str(e)}", exc_info=True)
            results.append({
                "puzzle_id": f"pilot_n{n}_batch",
                "n": n,
                "count": count,
                "success_count": 0,
                "total_attempts": 0,
                "success_rate": 0.0,
                "wall_clock_seconds": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "mode": "symbolic",
                "status": "failed",
                "error": str(e)
            })
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump({
            "experiment_type": "pilot_scaling",
            "n_values": n_values,
            "count_per_n": count,
            "seed": seed,
            "results": results,
            "generated_at": datetime.utcnow().isoformat()
        }, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run pilot scaling experiments")
    parser.add_argument(
        "--n-range",
        type=str,
        default="10,20,30,40,50",
        help="Comma-separated list of N values to test (default: 10,20,30,40,50)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of puzzles per N value (default: 5)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/scaling_raw_logs.json",
        help="Output path for results (default: data/processed/scaling_raw_logs.json)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    
    args = parser.parse_args()
    
    # Parse N values
    n_values = [int(x.strip()) for x in args.n_range.split(",")]
    output_path = Path(args.output)
    
    # Validate N range for pilot (should be small subset)
    if max(n_values) > 50:
        logger.warning(f"Max N value {max(n_values)} exceeds pilot range (50). "
                     f"Consider reducing for pilot experiments.")
    
    run_pilot_scaling(
        n_values=n_values,
        count=args.count,
        output_path=output_path,
        seed=args.seed
    )

if __name__ == "__main__":
    main()