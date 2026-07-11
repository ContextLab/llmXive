"""
Main entry point for the llmXive simulation pipeline.

Provides a CLI argument parser to configure simulation parameters,
select policies, and define execution paths.
"""
import argparse
import sys
from typing import Optional

from utils.config import LOG_LEVELS, DEFAULT_SEED, DEFAULT_MEMORY_LIMIT
from utils.exceptions import SimulationError


def create_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for the simulation pipeline."""
    parser = argparse.ArgumentParser(
        prog="llmxive-sim",
        description="Discrete-event simulation for MinT infrastructure workload analysis."
    )

    # Simulation Configuration
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})"
    )
    
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=DEFAULT_MEMORY_LIMIT,
        help=f"Memory limit in bytes (default: {DEFAULT_MEMORY_LIMIT})"
    )

    # Data Paths
    parser.add_argument(
        "--trace-path",
        type=str,
        default="data/processed/trace.csv",
        help="Path to the input request trace CSV file."
    )
    
    parser.add_argument(
        "--topology-path",
        type=str,
        default="data/processed/topology_graph.json",
        help="Path to the LoRA topology graph JSON file."
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/logs",
        help="Directory to store simulation logs and artifacts."
    )

    # Policy Selection
    parser.add_argument(
        "--policy",
        type=str,
        choices=["fcfs", "greedy", "topological"],
        default="fcfs",
        help="Scheduling policy to use (default: fcfs)."
    )

    # Replications (for statistical analysis)
    parser.add_argument(
        "--replications",
        type=int,
        default=1,
        help="Number of independent simulation replications to run."
    )

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        choices=LOG_LEVELS,
        default="INFO",
        help=f"Logging verbosity level (default: INFO)."
    )

    return parser


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_parser()
    return parser.parse_args(args)


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the simulation pipeline.
    
    Args:
        argv: Optional list of command line arguments. If None, uses sys.argv.
        
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        args = parse_args(argv)
        
        # TODO: Import and run the simulation engine once T022 is complete
        # For now, this validates the CLI and configuration setup.
        
        print(f"llmXive Simulation Pipeline")
        print(f"  Policy: {args.policy}")
        print(f"  Seed: {args.seed}")
        print(f"  Memory Limit: {args.memory_limit} bytes")
        print(f"  Trace: {args.trace_path}")
        print(f"  Topology: {args.topology_path}")
        print(f"  Replications: {args.replications}")
        print(f"  Output: {args.output_dir}")
        
        # Placeholder for actual simulation execution logic
        # This will be replaced by T028 (run_simulation) and T032 (run_experiment)
        if args.replications == 1:
            print("Running single simulation replication...")
            # from simulation.run_simulation import run_single_trace
            # run_single_trace(args)
        else:
            print(f"Running {args.replications} replications for statistical analysis...")
            # from simulation.run_experiment import run_experiment
            # run_experiment(args)
        
        return 0

    except SimulationError as e:
        print(f"Simulation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())