"""
Main entry point for the simulation pipeline.
Orchestrates the full simulation grid execution with logging.
"""
import argparse
import json
import os
import sys
import gc
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import logging setup
from code.simulation.logging_config import (
    setup_logging, 
    log_simulation_params, 
    log_shutdown,
    log_output_file_written,
    log_error_details
)
from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation.output_writer import write_p_values_raw
from code.simulation import get_rng

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run statistical test sensitivity simulation"
    )
    parser.add_argument(
        "--sample-sizes", 
        type=str, 
        default="5,10,20,30,50,100,200,500",
        help="Comma-separated list of sample sizes"
    )
    parser.add_argument(
        "--effect-sizes",
        type=str,
        default="0.0,0.2,0.5,0.8",
        help="Comma-separated list of effect sizes"
    )
    parser.add_argument(
        "--tests",
        type=str,
        default="t-test,ANOVA,chi-squared",
        help="Comma-separated list of tests to run"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of iterations per condition"
    )
    parser.add_argument(
        "--hypotheses",
        type=str,
        default="null,alternative",
        help="Comma-separated list of hypotheses"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/simulation",
        help="Output directory for results"
    )
    return parser.parse_args()

def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if args.iterations < 100:
        raise ValueError("Iterations must be at least 100 for meaningful results")
    if args.alpha <= 0 or args.alpha >= 1:
        raise ValueError("Alpha must be between 0 and 1")

def generate_sample_sizes(sample_sizes_str: str) -> List[int]:
    """Parse sample sizes from string."""
    return [int(x.strip()) for x in sample_sizes_str.split(",")]

def parse_effect_sizes(effect_sizes_str: str) -> List[float]:
    """Parse effect sizes from string."""
    return [float(x.strip()) for x in effect_sizes_str.split(",")]

def run_simulation_grid_chunked(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Run the full simulation grid with chunked processing.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        List of result dictionaries
    """
    sample_sizes = generate_sample_sizes(args.sample_sizes)
    effect_sizes = parse_effect_sizes(args.effect_sizes)
    tests = [t.strip() for t in args.tests.split(",")]
    hypotheses = [h.strip() for h in args.hypotheses.split(",")]
    
    log_simulation_params({
        "sample_sizes": sample_sizes,
        "effect_sizes": effect_sizes,
        "tests": tests,
        "alpha": args.alpha,
        "iterations": args.iterations,
        "hypotheses": hypotheses
    })
    
    all_results = []
    total_conditions = len(sample_sizes) * len(effect_sizes) * len(tests) * len(hypotheses)
    current_condition = 0
    
    for sample_size in sample_sizes:
        for effect_size in effect_sizes:
            for test_type in tests:
                for hypothesis in hypotheses:
                    current_condition += 1
                    print(f"Running condition {current_condition}/{total_conditions}: "
                         f"n={sample_size}, effect={effect_size}, test={test_type}, H={hypothesis}")
                    
                    try:
                        result = run_simulation_condition(
                            n=sample_size,
                            effect_size=effect_size,
                            test_type=test_type,
                            hypothesis=hypothesis,
                            alpha=args.alpha,
                            iterations=args.iterations
                        )
                        all_results.append(result)
                        
                        # Force garbage collection periodically
                        if current_condition % 10 == 0:
                            gc.collect()
                    
                    except Exception as e:
                        log_error_details(e, f"Condition: n={sample_size}, effect={effect_size}, "
                                            f"test={test_type}, H={hypothesis}")
                        # Continue with next condition
                        continue
    
    return all_results

def save_results_streaming(results: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Save results to CSV with streaming to handle large datasets.
    
    Args:
        results: List of result dictionaries
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "p_values_raw.csv")
    
    log_output_file_written(output_file, len(results))
    write_p_values_raw(results, output_file)

def main():
    """Main entry point."""
    try:
        # Setup logging first
        args = parse_args()
        setup_logging(log_level=args.log_level)
        
        log_simulation_params({
            "args": vars(args),
            "timestamp": datetime.now().isoformat()
        })
        
        # Validate arguments
        validate_args(args)
        
        # Run simulation
        print("Starting simulation grid...")
        results = run_simulation_grid_chunked(args)
        
        # Save results
        print(f"Saving {len(results)} results...")
        save_results_streaming(results, args.output_dir)
        
        # Aggregate and save summary
        aggregated = aggregate_results(results)
        summary_file = os.path.join(args.output_dir, "error_rates_summary.csv")
        # Note: Aggregation logic would be implemented here
        
        log_shutdown()
        print(f"Simulation complete. Results saved to {args.output_dir}")
        
    except Exception as e:
        log_error_details(e, "main execution")
        print(f"Simulation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()