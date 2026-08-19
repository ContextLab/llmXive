"""
Run Full Scaling Experiments (T029c).
Executes the BES loop in symbolic mode across the full complexity range (N=10..500).
Produces data/processed/scaling_raw_logs.json with timestamps, CPU usage, and durations.
"""
import os
import sys
import json
import time
import logging
import argparse
import gc
from datetime import datetime
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main import BESOrchestrator, BESRunResult
from utils.seed import set_seed
from utils.logger import setup_logging, log
from utils.monitor import get_cpu_percent_inline
from config import load_config

# Configure logging
logger = logging.getLogger(__name__)

def run_full_scaling_experiments(
    n_min: int = 10,
    n_max: int = 500,
    step: int = 10,
    count_per_n: int = 1,
    output_path: str = "data/processed/scaling_raw_logs.json",
    mode: str = "symbolic"
):
    """
    Executes the BES loop for a range of N values and logs performance metrics.

    Args:
        n_min: Minimum puzzle size N.
        n_max: Maximum puzzle size N.
        step: Increment step for N.
        count_per_n: Number of puzzles to run per N value.
        output_path: Path to the output JSON log file.
        mode: Execution mode ('symbolic' or 'neural').

    Returns:
        List of log entries.
    """
    setup_logging(level=logging.INFO)
    logger.info(f"Starting full scaling experiments: N={n_min}..{n_max}, step={step}")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results = []
    start_time_total = time.time()

    # Load configuration for defaults
    try:
        config = load_config()
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using defaults.")
        config = {}

    seed = config.get('seed', 42)
    set_seed(seed)

    # Iterate over complexity range
    current_n = n_min
    while current_n <= n_max:
        logger.info(f"Running experiments for N={current_n} (count={count_per_n})")

        for i in range(count_per_n):
            gc.collect() # Ensure memory is clean

            # Start timing and CPU monitoring
            t_start = time.time()
            cpu_start = get_cpu_percent_inline()

            try:
                # Instantiate Orchestrator
                # Note: We assume the orchestrator handles puzzle generation internally
                # or we pass the N parameter if the API supports it.
                # Based on T024, main.py orchestrates the loop. We call it here.
                
                # Since main.py's main() is CLI, we instantiate BESOrchestrator directly.
                # We need to construct a minimal config dict for the run.
                run_config = {
                    'mode': mode,
                    'n': current_n,
                    'count': 1, # Run one at a time in this loop
                    'seed': seed + i
                }
                
                orchestrator = BESOrchestrator(run_config)
                
                # Execute the run
                result: BESRunResult = orchestrator.run()
                
                # Capture metrics
                t_end = time.time()
                cpu_end = get_cpu_percent_inline()
                duration = t_end - t_start
                
                # Calculate average CPU if multiple samples were taken (simplified here to start/end delta)
                # For a more accurate average, we would sample during the run.
                # Using start/end as a proxy for the task requirement "CPU-percent".
                # Ideally, we log the peak or average, but the constraint asks for "CPU-percent".
                # We will log the start reading and the duration.
                
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "n": current_n,
                    "attempt_index": i,
                    "mode": mode,
                    "duration_seconds": duration,
                    "cpu_percent_start": cpu_start,
                    "cpu_percent_end": cpu_end,
                    "success": result.success,
                    "error": str(result.error) if result.error else None,
                    "puzzle_id": result.puzzle_id if hasattr(result, 'puzzle_id') else None
                }
                
                results.append(log_entry)
                logger.info(f"  Completed N={current_n}, idx={i}, success={result.success}, duration={duration:.3f}s")
                
            except Exception as e:
                t_end = time.time()
                duration = t_end - t_start
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "n": current_n,
                    "attempt_index": i,
                    "mode": mode,
                    "duration_seconds": duration,
                    "cpu_percent_start": cpu_start,
                    "cpu_percent_end": get_cpu_percent_inline(),
                    "success": False,
                    "error": str(e),
                    "puzzle_id": None
                }
                results.append(log_entry)
                logger.error(f"  Failed N={current_n}, idx={i}: {e}", exc_info=True)
            
            # Small delay to let system settle
            time.sleep(0.1)

        current_n += step

    total_duration = time.time() - start_time_total
    logger.info(f"Full scaling experiments completed in {total_duration:.2f}s. Total entries: {len(results)}")

    # Write results to disk
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results written to {output_file}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run Full Scaling Experiments (T029c)")
    parser.add_argument('--n-min', type=int, default=10, help="Minimum N")
    parser.add_argument('--n-max', type=int, default=500, help="Maximum N")
    parser.add_argument('--step', type=int, default=10, help="Step size for N")
    parser.add_argument('--count', type=int, default=1, help="Count per N")
    parser.add_argument('--output', type=str, default="data/processed/scaling_raw_logs.json", help="Output file path")
    parser.add_argument('--mode', type=str, default="symbolic", choices=["symbolic", "neural"], help="Execution mode")
    
    args = parser.parse_args()

    run_full_scaling_experiments(
        n_min=args.n_min,
        n_max=args.n_max,
        step=args.step,
        count_per_n=args.count,
        output_path=args.output,
        mode=args.mode
    )

if __name__ == "__main__":
    main()