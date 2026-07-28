"""
CLI entry point for the Co-Evolving Policy Distillation pipeline.

This module establishes the command structure for the automated science pipeline.
It provides the main entry point and argument parsing for various pipeline stages:
- Data generation and validation
- Agent training (Sequential, Mixed, Co-evolving)
- Batch execution and statistical analysis
- Report generation
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import configuration utilities
from src.utils.config import load_config, get_default_config, save_config
from src.utils.checksums import load_checksums, verify_file_integrity

# Import analysis modules
from src.analysis.validate_dataset import main as validate_main
from src.analysis.data_aggregator import main as aggregate_main
from src.analysis.forgetting_metrics import main as metrics_main
from src.analysis.statistical_tests import main as stats_main
from src.analysis.report_generator import main as report_main

# Import generator modules
from src.generators.logic_generator import main as logic_main
from src.generators.grid_generator import main as grid_main
from src.generators.test_generator import main as test_main
from src.generators.data_writer import main as writer_main

# Import agent modules (for training)
from src.agents.sequential_agent import SequentialAgent
from src.agents.mixed_agent import MixedAgent
from src.agents.coevolving_agent import CoevolvingAgent

# Import parity checker
from src.utils.parity_checker import ParityChecker, verify_run_parity

# Import performance optimizer
from src.utils.performance_optimizer import optimize_data_generation, ensure_ci_completeness

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="llmxive-pipeline",
        description="Co-Evolving Policy Distillation Research Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate and validate training data
  python -m src.cli generate --config config/default.json
  
  # Run validation gate
  python -m src.cli validate --data-dir data/generated
  
  # Train agents (single run)
  python -m src.cli train --condition coevolving --seed 42
  
  # Run batch experiments
  python -m src.cli batch --runs 30 --conditions sequential mixed coevolving
  
  # Analyze results
  python -m src.cli analyze --results-dir data/results
  
  # Generate final report
  python -m src.cli report --results-dir data/results
        """
    )

    # Top-level subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate subcommand
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate synthetic training and test data"
    )
    gen_parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/default.json",
        help="Path to configuration file"
    )
    gen_parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="data/generated",
        help="Output directory for generated data"
    )
    gen_parser.add_argument(
        "--logic-count", "-l",
        type=int,
        default=100,
        help="Number of logic proofs to generate"
    )
    gen_parser.add_argument(
        "--grid-count", "-g",
        type=int,
        default=100,
        help="Number of grid worlds to generate"
    )
    gen_parser.add_argument(
        "--test-count", "-t",
        type=int,
        default=20,
        help="Number of held-out test instances to generate"
    )

    # Validate subcommand
    val_parser = subparsers.add_parser(
        "validate",
        help="Validate generated datasets"
    )
    val_parser.add_argument(
        "--data-dir", "-d",
        type=str,
        required=True,
        help="Directory containing generated data to validate"
    )
    val_parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/default.json",
        help="Path to configuration file"
    )

    # Train subcommand
    train_parser = subparsers.add_parser(
        "train",
        help="Train agents under specific conditions"
    )
    train_parser.add_argument(
        "--condition", "-m",
        type=str,
        required=True,
        choices=["sequential", "mixed", "coevolving"],
        help="Training condition/strategy"
    )
    train_parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/default.json",
        help="Path to configuration file"
    )
    train_parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    train_parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="data/results",
        help="Output directory for training results"
    )
    train_parser.add_argument(
        "--data-dir", "-d",
        type=str,
        default="data/generated",
        help="Directory containing training data"
    )

    # Batch subcommand
    batch_parser = subparsers.add_parser(
        "batch",
        help="Run multiple training experiments in batch"
    )
    batch_parser.add_argument(
        "--runs", "-n",
        type=int,
        default=30,
        help="Number of independent runs per condition"
    )
    config_parser.add_argument(
        "--conditions",
        type=str,
        nargs="+",
        choices=["sequential", "mixed", "coevolving"],
        default=["sequential", "mixed", "coevolving"],
        help="Conditions to run"
    )
    batch_parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/default.json",
        help="Path to configuration file"
    )
    batch_parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="data/results",
        help="Output directory for batch results"
    )
    batch_parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=1,
        help="Number of parallel processes (default: 1)"
    )

    # Analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze batch results and compute metrics"
    )
    analyze_parser.add_argument(
        "--results-dir", "-r",
        type=str,
        required=True,
        help="Directory containing batch results"
    )
    analyze_parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="data/results",
        help="Output directory for analysis results"
    )
    analyze_parser.add_argument(
        "--compute-retention",
        action="store_true",
        help="Compute retention metrics"
    )

    # Report subcommand
    report_parser = subparsers.add_parser(
        "report",
        help="Generate final analysis report"
    )
    report_parser.add_argument(
        "--results-dir", "-r",
        type=str,
        required=True,
        help="Directory containing analysis results"
    )
    report_parser.add_argument(
        "--output-file", "-o",
        type=str,
        default="data/results/forgetting_analysis.json",
        help="Output file for the final report"
    )

    # Config subcommand
    config_cmd_parser = subparsers.add_parser(
        "config",
        help="Manage pipeline configuration"
    )
    config_cmd_parser.add_argument(
        "--action", "-a",
        type=str,
        required=True,
        choices=["show", "save", "load"],
        help="Configuration action"
    )
    config_cmd_parser.add_argument(
        "--config-file", "-f",
        type=str,
        default="config/default.json",
        help="Path to configuration file"
    )

    # Checksum subcommand
    checksum_parser = subparsers.add_parser(
        "checksum",
        help="Manage and verify data checksums"
    )
    checksum_parser.add_argument(
        "--action", "-a",
        type=str,
        required=True,
        choices=["compute", "verify", "list"],
        help="Checksum action"
    )
    checksum_parser.add_argument(
        "--data-dir", "-d",
        type=str,
        default="data/generated",
        help="Directory containing data files"
    )
    checksum_parser.add_argument(
        "--checksum-file", "-c",
        type=str,
        default="data/checksums.json",
        help="Path to checksums file"
    )

    # Parity check subcommand
    parity_parser = subparsers.add_parser(
        "parity",
        help="Verify parity of rule evaluations across conditions"
    )
    parity_parser.add_argument(
        "--results-dir", "-r",
        type=str,
        required=True,
        help="Directory containing results from multiple conditions"
    )
    parity_parser.add_argument(
        "--conditions",
        type=str,
        nargs="+",
        required=True,
        help="Conditions to compare for parity"
    )

    return parser

def load_training_data(data_dir: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load training data from the specified directory.
    
    Args:
        data_dir: Path to directory containing generated data
        config: Configuration dictionary
    
    Returns:
        Dictionary containing loaded training data
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")
    
    # Load logic proofs
    logic_file = data_path / "logic_proofs.json"
    if logic_file.exists():
        with open(logic_file, 'r') as f:
            logic_data = json.load(f)
    else:
        logic_data = []
    
    # Load grid worlds
    grid_file = data_path / "grid_worlds.json"
    if grid_file.exists():
        with open(grid_file, 'r') as f:
            grid_data = json.load(f)
    else:
        grid_data = []
    
    return {
        "logic_proofs": logic_data,
        "grid_worlds": grid_data,
        "config": config
    }

def run_sequential_training(data: Dict[str, Any], config: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """
    Run sequential training condition.
    
    Args:
        data: Training data dictionary
        config: Configuration dictionary
        output_dir: Output directory for results
    
    Returns:
        Training results dictionary
    """
    agent = SequentialAgent(config)
    results = agent.train(data)
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    result_file = output_path / "sequential_results.json"
    
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results

def run_mixed_training(data: Dict[str, Any], config: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """
    Run mixed-task training condition.
    
    Args:
        data: Training data dictionary
        config: Configuration dictionary
        output_dir: Output directory for results
    
    Returns:
        Training results dictionary
    """
    agent = MixedAgent(config)
    results = agent.train(data)
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    result_file = output_path / "mixed_results.json"
    
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results

def run_coevolving_training(data: Dict[str, Any], config: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """
    Run co-evolving training condition.
    
    Args:
        data: Training data dictionary
        config: Configuration dictionary
        output_dir: Output directory for results
    
    Returns:
        Training results dictionary
    """
    agent = CoevolvingAgent(config)
    results = agent.train(data)
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    result_file = output_path / "coevolving_results.json"
    
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results

def execute_training_loop(
    condition: str,
    data: Dict[str, Any],
    config: Dict[str, Any],
    output_dir: str
) -> Dict[str, Any]:
    """
    Execute training loop for a specific condition.
    
    Args:
        condition: Training condition name
        data: Training data dictionary
        config: Configuration dictionary
        output_dir: Output directory for results
    
    Returns:
        Training results dictionary
    """
    if condition == "sequential":
        return run_sequential_training(data, config, output_dir)
    elif condition == "mixed":
        return run_mixed_training(data, config, output_dir)
    elif condition == "coevolving":
        return run_coevolving_training(data, config, output_dir)
    else:
        raise ValueError(f"Unknown training condition: {condition}")

def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Handle subcommands
    if args.command == "generate":
        # Placeholder for generation logic
        print(f"Generating data: {args.logic_count} logic proofs, {args.grid_count} grids")
        print(f"Output directory: {args.output_dir}")
        sys.exit(0)

    elif args.command == "validate":
        # Delegate to validation module
        sys.argv = ["validate", "--data-dir", args.data_dir]
        if hasattr(args, 'config'):
            sys.argv.extend(["--config", args.config])
        validate_main()

    elif args.command == "train":
        # Load configuration
        config = load_config(args.config)
        config["seed"] = args.seed
        
        # Load data
        data = load_training_data(args.data_dir, config)
        
        # Execute training
        results = execute_training_loop(
            args.condition,
            data,
            config,
            args.output_dir
        )
        
        print(f"Training completed for condition: {args.condition}")
        print(f"Results saved to: {args.output_dir}")

    elif args.command == "batch":
        print(f"Batch execution: {args.runs} runs for conditions: {args.conditions}")
        print(f"Output directory: {args.output_dir}")
        print(f"Parallel processes: {args.parallel}")
        # Placeholder for batch execution logic
        sys.exit(0)

    elif args.command == "analyze":
        # Delegate to aggregation/analysis modules
        sys.argv = ["analyze", "--results-dir", args.results_dir]
        if hasattr(args, 'output_dir'):
            sys.argv.extend(["--output-dir", args.output_dir])
        if args.compute_retention:
            sys.argv.append("--compute-retention")
        aggregate_main()

    elif args.command == "report":
        # Delegate to report generation
        sys.argv = ["report", "--results-dir", args.results_dir]
        if hasattr(args, 'output_file'):
            sys.argv.extend(["--output-file", args.output_file])
        report_main()

    elif args.command == "config":
        if args.action == "show":
            config = get_default_config()
            print(json.dumps(config, indent=2))
        elif args.action == "save":
            config = get_default_config()
            save_config(config, args.config_file)
            print(f"Configuration saved to: {args.config_file}")
        elif args.action == "load":
            config = load_config(args.config_file)
            print(f"Configuration loaded from: {args.config_file}")
            print(json.dumps(config, indent=2))

    elif args.command == "checksum":
        if args.action == "compute":
            print(f"Computing checksums for: {args.data_dir}")
            # Placeholder for checksum computation
        elif args.action == "verify":
            print(f"Verifying checksums from: {args.checksum_file}")
            # Placeholder for verification
        elif args.action == "list":
            print(f"Listing checksums from: {args.checksum_file}")
            # Placeholder for listing

    elif args.command == "parity":
        print(f"Checking parity for conditions: {args.conditions}")
        print(f"Results directory: {args.results_dir}")
        # Placeholder for parity checking
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()