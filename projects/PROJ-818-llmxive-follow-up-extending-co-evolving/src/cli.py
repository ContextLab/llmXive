import argparse
import json
import sys
import os
import time
import signal
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.utils.checksums import verify_file_integrity, load_checksums
from src.utils.config import Config
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.generators.test_generator import TestInstanceGenerator
from src.generators.data_writer import DataWriteError, write_dataset, register_checksum
from src.analysis.validate_dataset import validate_dataset
from src.analysis.parity_checker import generate_parity_report, save_parity_report
from src.agents.sequential_agent import SequentialAgent
from src.agents.mixed_agent import MixedAgent
from src.agents.coevolving_agent import CoevolvingAgent
from src.utils.parity_checker import check_and_enforce_parity, ParityError
from src.analysis.forgetting_metrics import compute_forgetting_metrics, compute_retention_metrics
from src.analysis.statistical_tests import run_statistical_analysis
from src.analysis.report_generator import generate_final_report
from src.analysis.data_aggregator import aggregate_batch_results

class DataDependencyError(Exception):
    """Raised when required data files are missing or corrupted."""
    pass

class TimeBudgetExceededError(Exception):
    """Raised when the execution exceeds the time budget."""
    pass

class TimeBudgetEnforcer:
    def __init__(self, budget_seconds: float):
        self.budget_seconds = budget_seconds
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def check(self):
        if self.start_time is None:
            raise RuntimeError("Enforcer not started")
        elapsed = time.time() - self.start_time
        if elapsed > self.budget_seconds:
            raise TimeBudgetExceededError(f"Time budget exceeded: {elapsed:.2f}s > {self.budget_seconds}s")

def validate_data_dependencies(args):
    """
    T050: Data Flow Dependency Validator.
    Checks that required data files exist and have valid checksums before execution.
    """
    required_files = [
        "data/generated_proofs.json",
        "data/generated_grids.json",
        "data/test_instances.json"
    ]
    
    # Load checksums if available
    checksums_path = Path("data/checksums.json")
    stored_checksums = {}
    if checksums_path.exists():
        try:
            stored_checksums = load_checksums()
        except Exception as e:
            # If checksum file exists but is corrupt, we might still proceed if files exist, 
            # but strictly speaking, we should warn or fail if we can't verify integrity.
            # For T050, we focus on existence first, then integrity if checksums exist.
            print(f"Warning: Could not load checksums.json: {e}")

    for file_path in required_files:
        path = Path(file_path)
        if not path.exists():
            raise DataDependencyError(f"Required data file missing: {file_path}")
        
        # Verify checksum if available
        if file_path in stored_checksums:
            is_valid, computed_hash = verify_file_integrity(file_path, stored_checksums[file_path])
            if not is_valid:
                raise DataDependencyError(f"Data file corrupted (checksum mismatch): {file_path}")
        
    print("Data dependency validation passed.")
    return True

def create_parser():
    parser = argparse.ArgumentParser(prog="llmxive", description="Co-Evolving Policy Distillation Pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic datasets")
    gen_parser.add_argument("--logic", type=int, default=100, help="Number of logic proofs")
    gen_parser.add_argument("--grid", type=int, default=50, help="Number of grid worlds")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    gen_parser.add_argument("--output", type=str, default="data/synthetic_dataset.json", help="Output file")

    # Train command (replaces 'run')
    train_parser = subparsers.add_parser("train", help="Run training conditions")
    train_parser.add_argument("--conditions", type=str, default="sequential,mixed,coevolving", 
                              help="Comma-separated list of conditions")
    train_parser.add_argument("--generations", type=int, default=50, help="Number of generations")
    train_parser.add_argument("--runs-per-condition", type=int, default=30, help="Runs per condition")
    train_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    train_parser.add_argument("--validate-first", action="store_true", default=True, 
                              help="Run data dependency validation before training")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze results")
    analyze_parser.add_argument("--input", type=str, default="data/results/batch_metrics.json", 
                                help="Input metrics file")
    analyze_parser.add_argument("--output", type=str, default="data/results/statistical_report.json", 
                                help="Output report file")

    return parser

def run_generate(args):
    config = Config()
    config.seed = args.seed
    
    logic_gen = LogicProofGenerator(config)
    grid_gen = GridWorldGenerator(config)
    
    proofs = logic_gen.generate(args.logic)
    grids = grid_gen.generate(args.grid)
    
    # Write data
    write_dataset(proofs, "data/generated_proofs.json")
    write_dataset(grids, "data/generated_grids.json")
    
    # Generate test instances
    test_gen = TestInstanceGenerator(config)
    test_instances = test_gen.generate()
    write_dataset(test_instances, "data/test_instances.json")
    
    # Validate
    validate_dataset()
    
    # Register checksums
    register_checksum("data/generated_proofs.json")
    register_checksum("data/generated_grids.json")
    register_checksum("data/test_instances.json")
    
    print(f"Generated {len(proofs)} proofs, {len(grids)} grids, and test instances.")

def run_train(args):
    if args.validate_first:
        try:
            validate_data_dependencies(args)
        except DataDependencyError as e:
            print(f"Data validation failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    conditions = [c.strip() for c in args.conditions.split(",")]
    config = Config()
    config.seed = args.seed
    
    # Run training for each condition
    for condition in conditions:
        if condition == "sequential":
            agent = SequentialAgent(config)
        elif condition == "mixed":
            agent = MixedAgent(config)
        elif condition == "coevolving":
            agent = CoevolvingAgent(config)
        else:
            print(f"Unknown condition: {condition}", file=sys.stderr)
            continue
        
        # Execute training loop with parity enforcement
        for i in range(args.runs_per_condition):
            try:
                # Enforce parity budget
                check_and_enforce_parity(config.budget, agent.evaluation_count)
                agent.run(args.generations)
            except ParityError as e:
                print(f"Parity error in run {i}: {e}", file=sys.stderr)
                # Log but continue to next run or break depending on strictness
                break
            
    print("Training complete.")

def run_analyze(args):
    # Aggregate results
    aggregate_batch_results()
    
    # Compute metrics
    compute_forgetting_metrics()
    compute_retention_metrics()
    
    # Run statistical tests
    run_statistical_analysis()
    
    # Generate report
    generate_final_report(args.output)
    
    # Generate parity report
    generate_parity_report()
    save_parity_report("data/results/parity_report.json")
    
    print(f"Analysis complete. Report saved to {args.output}")

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if args.command == "generate":
        run_generate(args)
    elif args.command == "train":
        run_train(args)
    elif args.command == "analyze":
        run_analyze(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()