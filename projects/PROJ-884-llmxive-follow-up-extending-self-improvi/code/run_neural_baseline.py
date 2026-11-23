"""
Run the neural subset baseline experiments.

This script executes the BES loop with a small LLM (distilbert-tiny) on a subset
of puzzles to measure performance metrics for the neural baseline.

Usage:
    python code/run_neural_baseline.py --n 10 50 --count 10 --types sudoku,pathfinding
"""
import os
import sys
import json
import time
import logging
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.main import BESOrchestrator, BESRunResult
from code.config import load_config, initialize_experiment
from code.utils.seed import set_seed
from code.utils.logger import setup_logging, log

def parse_args():
    parser = argparse.ArgumentParser(description="Run neural subset baseline experiments")
    parser.add_argument("--n", type=int, nargs="+", default=[10, 50],
                      help="Range of puzzle sizes (e.g., --n 10 50)")
    parser.add_argument("--count", type=int, default=10,
                      help="Number of puzzles to generate per size")
    parser.add_argument("--types", type=str, nargs="+", default=["sudoku", "pathfinding"],
                      help="Puzzle types to include")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                      help="Output directory for results")
    parser.add_argument("--seed", type=int, default=42,
                      help="Random seed for reproducibility")
    return parser.parse_args()

def setup_experiment():
    """Initialize experiment configuration and logging."""
    config = initialize_experiment()
    config["mode"] = "neural_subset"
    config["baseline"] = "neural"
    
    # Set up logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    logger.info(f"Initialized experiment: {config['experiment_id']}")
    
    return config

def run_neural_baseline(args, config):
    """Execute the neural subset baseline run."""
    logger = logging.getLogger(__name__)
    
    # Set random seed
    set_seed(config.get("seed", args.seed))
    
    # Prepare output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize results collection
    results = {
        "experiment_id": config["experiment_id"],
        "mode": "neural_subset",
        "baseline": "neural",
        "timestamp": datetime.utcnow().isoformat(),
        "parameters": {
            "n_range": args.n,
            "count": args.count,
            "types": args.types,
            "seed": args.seed
        },
        "runs": []
    }
    
    # Run experiments for each puzzle size
    for n in range(args.n[0], args.n[1] + 1, 10):  # Step by 10 from 10 to 50
        logger.info(f"Running neural baseline for puzzle size N={n}")
        
        for i in range(args.count):
            puzzle_id = f"neural_n{n}_i{i}"
            logger.info(f"  Running puzzle {puzzle_id}")
            
            try:
                # Initialize orchestrator for this puzzle
                orchestrator = BESOrchestrator(
                    mode="neural_subset",
                    puzzle_size=n,
                    puzzle_type=random.choice(args.types),
                    config=config
                )
                
                # Execute the BES loop
                start_time = time.time()
                result: BESRunResult = orchestrator.run()
                end_time = time.time()
                
                # Record metrics
                run_data = {
                    "puzzle_id": puzzle_id,
                    "puzzle_size": n,
                    "puzzle_type": result.puzzle_type,
                    "success": result.success,
                    "duration_seconds": end_time - start_time,
                    "iterations": result.iterations,
                    "final_score": result.final_score,
                    "timestamp": datetime.utcnow().isoformat(),
                    "gpu_time_seconds": result.gpu_time if hasattr(result, 'gpu_time') else 0.0,
                    "cpu_percent": result.cpu_percent if hasattr(result, 'cpu_percent') else 0.0
                }
                
                results["runs"].append(run_data)
                logger.info(f"    Completed: success={result.success}, duration={run_data['duration_seconds']:.2f}s")
                
            except Exception as e:
                logger.error(f"    Failed for puzzle {puzzle_id}: {str(e)}")
                results["runs"].append({
                    "puzzle_id": puzzle_id,
                    "puzzle_size": n,
                    "error": str(e),
                    "success": False,
                    "duration_seconds": 0.0
                })
    
    return results

def save_results(results: Dict[str, Any], output_dir: Path):
    """Save results to JSON file."""
    output_file = output_dir / "neural_baseline_results.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.getLogger(__name__).info(f"Results saved to {output_file}")
    return output_file

def main():
    """Main entry point for neural baseline execution."""
    args = parse_args()
    
    # Setup experiment
    config = setup_experiment()
    
    # Run baseline
    results = run_neural_baseline(args, config)
    
    # Save results
    output_dir = Path(args.output_dir)
    output_file = save_results(results, output_dir)
    
    # Print summary
    logger = logging.getLogger(__name__)
    logger.info(f"Neural baseline completed. Total runs: {len(results['runs'])}")
    
    success_count = sum(1 for r in results["runs"] if r.get("success", False))
    logger.info(f"Success rate: {success_count}/{len(results['runs'])} = {success_count/len(results['runs']):.2%}")
    
    if results["runs"]:
        avg_duration = sum(r.get("duration_seconds", 0) for r in results["runs"]) / len(results["runs"])
        logger.info(f"Average duration: {avg_duration:.2f}s")
        
        if any(r.get("gpu_time_seconds", 0) > 0 for r in results["runs"]):
            avg_gpu_time = sum(r.get("gpu_time_seconds", 0) for r in results["runs"]) / len(results["runs"])
            logger.info(f"Average GPU time: {avg_gpu_time:.2f}s")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())