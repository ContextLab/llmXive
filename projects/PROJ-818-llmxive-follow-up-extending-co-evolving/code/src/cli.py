import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import agents
from src.agents.sequential_agent import SequentialAgent
from src.agents.mixed_agent import MixedAgent
from src.agents.coevolving_agent import CoevolvingAgent
from src.utils.config import load_config, Config
from src.utils.parity_checker import ParityChecker, ParityError, EvaluationStats
from src.generators.data_writer import write_dataset, register_checksum
from src.utils.checksums import update_checksum_for_file
from src.analysis.validate_dataset import validate_dataset, load_generated_data
from src.generators.test_generator import TestInstanceGenerator

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llmXive Co-Evolving Policy Distillation CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Train command
    train_parser = subparsers.add_parser("train", help="Run training loop")
    train_parser.add_argument("--condition", type=str, choices=["sequential", "mixed", "coevolving"], required=True,
                              help="Training condition to execute")
    train_parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    train_parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory for results")
    train_parser.add_argument("--seed", type=int, default=42, help="Random seed")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate generated dataset")
    validate_parser.add_argument("--data-dir", type=str, default="data", help="Directory containing generated data")

    return parser

def load_training_data(data_dir: str) -> Dict[str, Any]:
    """Load generated training data from disk."""
    data_path = Path(data_dir)
    proofs_path = data_path / "generated_proofs.json"
    grids_path = data_path / "generated_grids.json"

    if not proofs_path.exists() or not grids_path.exists():
        raise FileNotFoundError(f"Training data not found in {data_dir}")

    with open(proofs_path, 'r') as f:
        proofs = json.load(f)
    with open(grids_path, 'r') as f:
        grids = json.load(f)

    return {"proofs": proofs, "grids": grids}

def run_sequential_training(config: Config, data: Dict[str, Any], output_dir: str, seed: int) -> Dict[str, Any]:
    """Execute sequential training loop with parity enforcement."""
    agent = SequentialAgent(config, seed=seed)
    parity_checker = ParityChecker(budget=config.rule_evaluation_budget)
    
    results = []
    total_evals = 0

    # Process proofs
    for instance in data["proofs"]:
        # Check parity before evaluation
        if not parity_checker.can_evaluate(1):
            raise ParityError(f"Budget exceeded at proof evaluation. Current: {parity_checker.current_count}, Budget: {config.rule_evaluation_budget}")
        
        result = agent.train_on_instance(instance, domain="logic")
        parity_checker.record_evaluation(1)
        total_evals += 1
        results.append(result)

    # Process grids
    for instance in data["grids"]:
        if not parity_checker.can_evaluate(1):
            raise ParityError(f"Budget exceeded at grid evaluation. Current: {parity_checker.current_count}, Budget: {config.rule_evaluation_budget}")
        
        result = agent.train_on_instance(instance, domain="grid")
        parity_checker.record_evaluation(1)
        total_evals += 1
        results.append(result)

    return {
        "condition": "sequential",
        "total_evaluations": total_evals,
        "final_state": agent.get_state(),
        "results": results
    }

def run_mixed_training(config: Config, data: Dict[str, Any], output_dir: str, seed: int) -> Dict[str, Any]:
    """Execute mixed training loop with parity enforcement."""
    agent = MixedAgent(config, seed=seed)
    parity_checker = ParityChecker(budget=config.rule_evaluation_budget)
    
    results = []
    total_evals = 0
    all_instances = data["proofs"] + data["grids"]
    
    # Shuffle instances for mixed training
    import random
    random.seed(seed)
    random.shuffle(all_instances)

    for instance in all_instances:
        if not parity_checker.can_evaluate(1):
            raise ParityError(f"Budget exceeded at mixed evaluation. Current: {parity_checker.current_count}, Budget: {config.rule_evaluation_budget}")
        
        domain = "logic" if "axioms" in instance else "grid"
        result = agent.train_on_instance(instance, domain=domain)
        parity_checker.record_evaluation(1)
        total_evals += 1
        results.append(result)

    return {
        "condition": "mixed",
        "total_evaluations": total_evals,
        "final_state": agent.get_state(),
        "results": results
    }

def run_coevolving_training(config: Config, data: Dict[str, Any], output_dir: str, seed: int) -> Dict[str, Any]:
    """Execute co-evolving training loop with parity enforcement."""
    agent = CoevolvingAgent(config, seed=seed)
    parity_checker = ParityChecker(budget=config.rule_evaluation_budget)
    
    results = []
    total_evals = 0
    
    # Split data for sub-populations
    half = len(data["proofs"]) // 2
    pop1_proof_data = data["proofs"][:half]
    pop2_proof_data = data["proofs"][half:]
    grid_data = data["grids"]

    # Training loop
    for generation in range(config.generations):
        # Process population 1
        for instance in pop1_proof_data:
            if not parity_checker.can_evaluate(1):
                raise ParityError(f"Budget exceeded at coevolving pop1 eval. Current: {parity_checker.current_count}, Budget: {config.rule_evaluation_budget}")
            
            result = agent.train_on_instance(instance, domain="logic", population=0)
            parity_checker.record_evaluation(1)
            total_evals += 1
            results.append(result)

        # Process population 2
        for instance in pop2_proof_data:
            if not parity_checker.can_evaluate(1):
                raise ParityError(f"Budget exceeded at coevolving pop2 eval. Current: {parity_checker.current_count}, Budget: {config.rule_evaluation_budget}")
            
            result = agent.train_on_instance(instance, domain="logic", population=1)
            parity_checker.record_evaluation(1)
            total_evals += 1
            results.append(result)

        # Process grids for both populations
        for instance in grid_data:
            if not parity_checker.can_evaluate(1):
                raise ParityError(f"Budget exceeded at coevolving grid eval. Current: {parity_checker.current_count}, Budget: {config.rule_evaluation_budget}")
            
            result = agent.train_on_instance(instance, domain="grid", population=0)
            parity_checker.record_evaluation(1)
            total_evals += 1
            results.append(result)

            if not parity_checker.can_evaluate(1):
                raise ParityError(f"Budget exceeded at coevolving grid eval 2. Current: {parity_checker.current_count}, Budget: {config.rule_evaluation_budget}")
            
            result = agent.train_on_instance(instance, domain="grid", population=1)
            parity_checker.record_evaluation(1)
            total_evals += 1
            results.append(result)

        # Bidirectional exchange at every generation
        agent.exchange_rule_sets()

    return {
        "condition": "coevolving",
        "total_evaluations": total_evals,
        "final_state": agent.get_state(),
        "results": results
    }

def execute_training_loop(condition: str, config_path: str, output_dir: str, seed: int) -> None:
    """Main training orchestration with parity enforcement."""
    config = load_config(config_path)
    data = load_training_data("data")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if condition == "sequential":
        result = run_sequential_training(config, data, output_dir, seed)
    elif condition == "mixed":
        result = run_mixed_training(config, data, output_dir, seed)
    elif condition == "coevolving":
        result = run_coevolving_training(config, data, output_dir, seed)
    else:
        raise ValueError(f"Unknown condition: {condition}")

    # Write results
    result_file = output_path / f"{condition}_result.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Update checksum
    update_checksum_for_file(str(result_file))
    
    print(f"Training completed. Results written to {result_file}")
    print(f"Total rule evaluations: {result['total_evaluations']}")

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "train":
        execute_training_loop(
            condition=args.condition,
            config_path=args.config,
            output_dir=args.output_dir,
            seed=args.seed
        )
    elif args.command == "validate":
        success = validate_dataset(args.data_dir)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()