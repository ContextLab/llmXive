import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.utils.config import load_config, save_config, Config
from src.utils.checksums import load_checksums, save_checksums
from src.analysis.validate_dataset import validate_dataset, main as validate_main
from src.generators.data_writer import generate_and_save_training_data, main as data_writer_main
from src.generators.test_generator import main as test_gen_main
from src.agents.sequential_agent import SequentialAgent
from src.agents.mixed_agent import MixedAgent
from src.agents.coevolving_agent import CoevolvingAgent
from src.utils.parity_checker import ParityChecker, ParityError
from src.analysis.data_aggregator import main as aggregate_main
from src.analysis.forgetting_metrics import main as forgetting_main
from src.analysis.statistical_tests import main as stats_main
from src.analysis.report_generator import main as report_main

def load_training_data(config: Config) -> Dict[str, Any]:
    """Load generated training data from disk."""
    data_dir = Path(config.data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory {data_dir} does not exist. Run generation first.")
    
    # Load logic and grid datasets
    logic_file = data_dir / config.logic_data_file
    grid_file = data_dir / config.grid_data_file
    
    if not logic_file.exists() or not grid_file.exists():
        raise FileNotFoundError("Training data files missing. Run generation first.")
    
    with open(logic_file, 'r') as f:
        logic_data = json.load(f)
    with open(grid_file, 'r') as f:
        grid_data = json.load(f)
        
    return {
        "logic": logic_data,
        "grid": grid_data
    }

def run_sequential_training(data: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Run SequentialAgent training loop."""
    agent = SequentialAgent(config)
    results = agent.train(data["logic"], data["grid"])
    return results

def run_mixed_training(data: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Run MixedAgent training loop."""
    agent = MixedAgent(config)
    results = agent.train(data["logic"], data["grid"])
    return results

def run_coevolving_training(data: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Run CoevolvingAgent training loop."""
    agent = CoevolvingAgent(config)
    results = agent.train(data["logic"], data["grid"])
    return results

def execute_training_loop(config: Config, condition: str) -> Dict[str, Any]:
    """Execute the training loop for a specific condition with parity checks."""
    data = load_training_data(config)
    checker = ParityChecker(config)
    
    if condition == "sequential":
        results = run_sequential_training(data, config)
    elif condition == "mixed":
        results = run_mixed_training(data, config)
    elif condition == "coevolving":
        results = run_coevolving_training(data, config)
    else:
        raise ValueError(f"Unknown condition: {condition}")
    
    # Verify parity
    try:
        checker.verify_run_parity(results)
    except ParityError as e:
        # Log but allow continuation if strict parity is not enforced by config flag
        if config.strict_parity:
            raise e
        print(f"Warning: Parity check failed for {condition}: {e}")
        
    return results

def main():
    parser = argparse.ArgumentParser(description="llmXive Co-Evolving Policy Distillation Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")

    # Generation
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic datasets")
    gen_parser.add_argument("--config", type=str, default="config.json", help="Path to config file")

    # Validation
    val_parser = subparsers.add_parser("validate", help="Validate generated datasets")
    val_parser.add_argument("--config", type=str, default="config.json", help="Path to config file")

    # Training (Single Run)
    train_parser = subparsers.add_parser("train", help="Run a single training condition")
    train_parser.add_argument("--condition", type=str, required=True, choices=["sequential", "mixed", "coevolving"])
    train_parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    train_parser.add_argument("--output", type=str, required=True, help="Output JSON path for results")

    # Batch Runner
    batch_parser = subparsers.add_parser("batch", help="Run 30+ independent training runs")
    batch_parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    batch_parser.add_argument("--output-dir", type=str, default="data/results", help="Directory for batch results")

    # Analysis
    analysis_parser = subparsers.add_parser("analyze", help="Run full analysis pipeline")
    analysis_parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    analysis_parser.add_argument("--results-dir", type=str, default="data/results", help="Directory containing batch results")
    analysis_parser.add_argument("--output", type=str, default="data/results/forgetting_analysis.json", help="Output report path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file {args.config} not found.")
        sys.exit(1)
    
    config = load_config(config_path)

    if args.command == "generate":
        # Orchestrate generation of logic, grid, and test instances
        data_writer_main(config)
        test_gen_main(config)
        print("Generation complete.")

    elif args.command == "validate":
        # Gate: Validate datasets before training
        success, report = validate_dataset(config)
        if not success:
            print("Validation failed. Training aborted.")
            print(json.dumps(report, indent=2))
            sys.exit(1)
        print("Validation passed.")

    elif args.command == "train":
        # Single training run
        results = execute_training_loop(config, args.condition)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Training results saved to {args.output}")

    elif args.command == "batch":
        # Run 30+ independent runs
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing checksums to track new runs
        checksums = load_checksums(config)
        
        for i in range(config.batch_size):
            seed = config.base_seed + i
            config.seed = seed
            config.output_file = str(output_dir / f"run_{i:03d}.json")
            
            try:
                # Run all three conditions for this seed to ensure parity in batch
                for cond in ["sequential", "mixed", "coevolving"]:
                    results = execute_training_loop(config, cond)
                    # Save individual run result
                    run_output = output_dir / f"{cond}_{i:03d}.json"
                    with open(run_output, 'w') as f:
                        json.dump(results, f, indent=2)
                    # Update checksum
                    checksums = update_checksum_for_file(checksums, str(run_output))
            except Exception as e:
                print(f"Error in batch run {i} ({cond}): {e}")
                continue
        
        save_checksums(checksums, config)
        print(f"Batch complete. {config.batch_size} runs generated.")

    elif args.command == "analyze":
        # Full analysis pipeline: Aggregate -> Metrics -> Stats -> Report
        results_dir = Path(args.results_dir)
        
        # Step 1: Aggregate batch results
        aggregate_main(config, results_dir)
        
        # Step 2: Compute forgetting metrics and retention
        forgetting_main(config, results_dir)
        
        # Step 3: Run statistical tests (ANOVA, Tukey)
        stats_main(config, results_dir)
        
        # Step 4: Generate final report
        report_main(config, results_dir, args.output)
        
        print(f"Analysis complete. Report saved to {args.output}")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()