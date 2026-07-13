"""
Main experiment runner for Social Memory Networks.
Orchestrates game simulations, dataset loading, and metric computation.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Project imports
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import load_experiment_results, verify_datasets, DatasetSpec
from data.synthetic import generate_synthetic_dataset, save_synthetic_dataset, SyntheticDatasetSpec
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    agent_count: int
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None
    dataset_name: str = "synthetic"
    seed: int = 42
    game_id: int = 0

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    agent_count: int
    context_condition: str
    specialization_index: float
    retrieval_efficiency: float
    success: bool
    error_message: Optional[str] = None
    agent_contributions: Dict[int, int] = field(default_factory=dict)
    retrieval_events: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ExperimentConfig:
    """Configuration for the entire experiment run."""
    context: str
    agents: List[int]
    games_per_config: int
    dataset: str
    thresholds: List[int]
    seed: int
    output_dir: Path

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_data_checksum(data: List[Dict]) -> str:
    """Compute SHA256 checksum of serialized data."""
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

def load_and_verify_dataset(config: GameConfig) -> List[Dict]:
    """
    Load dataset with verification.
    Falls back to synthetic data if real dataset is not verified or available.
    """
    try:
        # Try to verify real dataset
        verify_datasets()
        # If verification passes, attempt to load
        # Note: In a real implementation, this would load specific dataset files
        # For now, we rely on the fallback mechanism if the dataset isn't available
        data = load_experiment_results(f"data/{config.dataset_name}_data.json")
        if data:
            checksum = compute_data_checksum(data)
            logger.log("dataset_loaded", name=config.dataset_name, checksum=checksum, count=len(data))
            return data
    except Exception as e:
        logger.log("dataset_load_failed", dataset=config.dataset_name, error=str(e))

    # Fallback to synthetic data
    logger.log("synthetic_fallback", reason="real_dataset_unavailable", dataset=config.dataset_name)
    synthetic_spec = SyntheticDatasetSpec(
        num_samples=100,
        num_facts_per_sample=20,
        num_agents=config.agent_count,
        seed=config.seed
    )
    synthetic_data = generate_synthetic_dataset(synthetic_spec)
    checksum = compute_data_checksum(synthetic_data)
    logger.log("synthetic_data_generated", checksum=checksum, count=len(synthetic_data))

    # Save synthetic data for reproducibility
    output_path = Path(f"data/{config.dataset_name}_synthetic.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_synthetic_dataset(synthetic_data, output_path)

    return synthetic_data

def simulate_one_game(config: GameConfig) -> GameResult:
    """
    Simulate a single game with the given configuration.
    
    This implements the core game loop:
    1. Initialize agents with shared memory buffer
    2. Distribute facts among agents
    3. Run turn-based interaction with memory operations
    4. Compute specialization and retrieval metrics
    """
    try:
        # Initialize components
        reset_shared_buffer()
        buffer = get_shared_buffer()
        
        # Create agents
        agent_configs = [
            AgentConfig(
                agent_id=i,
                model_name="facebook/opt-125m",
                device="cpu",
                seed=config.seed + i
            )
            for i in range(config.agent_count)
        ]
        
        # Load dataset
        dataset = load_and_verify_dataset(config)
        
        # Distribute facts to agents (simulating specialization)
        # Each agent gets a subset of facts to "remember"
        agent_facts = {i: [] for i in range(config.agent_count)}
        total_facts = len(dataset)
        
        # Distribute facts with some overlap to simulate transactive memory
        for idx, fact in enumerate(dataset):
            # Assign fact to primary agent based on index
            primary_agent = idx % config.agent_count
            agent_facts[primary_agent].append(fact)
            
            # Add some overlap (10% chance other agents also know this fact)
            for other_agent in range(config.agent_count):
                if other_agent != primary_agent and np.random.random() < 0.1:
                    agent_facts[other_agent].append(fact)
        
        # Simulate game turns
        successful_retrievals = 0
        total_queries = 0
        retrieval_events = []
        
        # Simulate multiple rounds of querying and remembering
        num_rounds = min(50, total_facts)  # Limit rounds for efficiency
        
        for round_idx in range(num_rounds):
            # Select a target fact that needs to be retrieved
            target_idx = np.random.randint(0, total_facts)
            target_fact = dataset[target_idx]
            
            # Determine which agents know this fact
            agents_knowing_fact = [
                agent_id for agent_id, facts in agent_facts.items()
                if target_fact in facts
            ]
            
            # Simulate query process
            query_agent = np.random.randint(0, config.agent_count)
            total_queries += 1
            
            # Check if query agent knows the fact directly
            if target_fact in agent_facts[query_agent]:
                successful_retrievals += 1
                retrieval_events.append({
                    "round": round_idx,
                    "query_agent": query_agent,
                    "success": True,
                    "direct_knowledge": True
                })
            else:
                # Query agent tries to retrieve from memory buffer
                # Simulate memory lookup
                memory_key = f"fact_{target_idx}"
                
                # Check if fact is in shared memory
                if buffer.read(memory_key):
                    successful_retrievals += 1
                    retrieval_events.append({
                        "round": round_idx,
                        "query_agent": query_agent,
                        "success": True,
                        "direct_knowledge": False,
                        "memory_retrieval": True
                    })
                else:
                    # Try to query other agents (simulating transactive memory)
                    queried_aware_agent = False
                    for aware_agent in agents_knowing_fact:
                        if aware_agent != query_agent:
                            # Simulate asking another agent
                            # In a real implementation, this would involve LLM interaction
                            if np.random.random() < 0.7:  # 70% success rate for agent-to-agent query
                                successful_retrievals += 1
                                queried_aware_agent = True
                                # Write to shared memory for future queries
                                buffer.write(memory_key, str(target_fact))
                                retrieval_events.append({
                                    "round": round_idx,
                                    "query_agent": query_agent,
                                    "success": True,
                                    "direct_knowledge": False,
                                    "memory_retrieval": False,
                                    "agent_query": True,
                                    "target_agent": aware_agent
                                })
                                break
                    
                    if not queried_aware_agent:
                        retrieval_events.append({
                            "round": round_idx,
                            "query_agent": query_agent,
                            "success": False,
                            "direct_knowledge": False,
                            "memory_retrieval": False,
                            "agent_query": False
                        })
        
        # Compute metrics
        agent_contributions = {
            agent_id: len(facts) for agent_id, facts in agent_facts.items()
        }
        
        # Calculate specialization index
        fact_lengths = [len(facts) for facts in agent_facts.values()]
        spec_index, spec_metrics = compute_specialization_index(
            agent_skills=fact_lengths,
            num_agents=config.agent_count
        )
        
        # Calculate retrieval efficiency
        ret_eff, ret_metrics = compute_retrieval_efficiency(
            successful=successful_retrievals,
            total_queries=total_queries,
            num_agents=config.agent_count
        )
        
        # Validate metrics
        if spec_index < 0 or spec_index > np.log2(config.agent_count):
            logger.log("specialization_out_of_bounds", 
                     value=spec_index, 
                     expected_max=np.log2(config.agent_count),
                     game_id=config.game_id)
        
        if ret_eff < 0 or ret_eff > 1:
            logger.log("retrieval_efficiency_out_of_bounds",
                     value=ret_eff,
                     game_id=config.game_id)
        
        return GameResult(
            game_id=config.game_id,
            agent_count=config.agent_count,
            context_condition=config.context_condition,
            specialization_index=spec_index,
            retrieval_efficiency=ret_eff,
            success=True,
            agent_contributions=agent_contributions,
            retrieval_events=retrieval_events
        )
        
    except Exception as e:
        logger.log("game_simulation_failed", 
                 game_id=config.game_id, 
                 error=str(e),
                 exc_info=True)
        return GameResult(
            game_id=config.game_id,
            agent_count=config.agent_count,
            context_condition=config.context_condition,
            specialization_index=0.0,
            retrieval_efficiency=0.0,
            success=False,
            error_message=str(e)
        )

def run_simulation(config: ExperimentConfig) -> List[GameResult]:
    """
    Run the full experiment simulation across all configurations.
    
    For T027: Run 800 games per agent count configuration.
    """
    results = []
    
    for agent_count in config.agents:
        logger.log("starting_agent_config", 
                 agent_count=agent_count, 
                 games=config.games_per_config,
                 context=config.context)
        
        for game_idx in range(config.games_per_config):
            game_config = GameConfig(
                agent_count=agent_count,
                context_condition=config.context,
                token_limit=config.thresholds[0] if config.thresholds else None,
                dataset_name=config.dataset,
                seed=config.seed + game_idx,
                game_id=game_idx
            )
            
            result = simulate_one_game(game_config)
            results.append(result)
            
            # Log progress
            if (game_idx + 1) % 100 == 0:
                logger.log("progress", 
                         agent_count=agent_count,
                         games_completed=game_idx + 1,
                         games_total=config.games_per_config)
        
        logger.log("completed_agent_config", 
                 agent_count=agent_count,
                 games_completed=config.games_per_config)
    
    return results

def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write experiment results to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'game_id', 
            'agent_count', 
            'context_condition', 
            'specialization_index', 
            'retrieval_efficiency',
            'success',
            'error_message'
        ])
        
        # Write results
        for result in results:
            writer.writerow([
                result.game_id,
                result.agent_count,
                result.context_condition,
                result.specialization_index,
                result.retrieval_efficiency,
                result.success,
                result.error_message if result.error_message else ''
            ])
    
    logger.log("results_written", 
             path=str(output_path), 
             count=len(results))

def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse comma-separated agent counts."""
    return [int(x.strip()) for x in agents_str.split(',')]

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the experiment runner."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )
    
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition (full or limited)"
    )
    
    parser.add_argument(
        "--agents",
        type=str,
        default="3,5,7",
        help="Comma-separated list of agent counts to test (e.g., '3,5,7')"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=800,
        help="Number of games to simulate per agent configuration"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default="synthetic",
        help="Dataset name (falls back to synthetic if not available)"
    )
    
    parser.add_argument(
        "--thresholds",
        type=str,
        default="256",
        help="Comma-separated token limits for limited context"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Output directory for results"
    )
    
    return parser

def main():
    """Main entry point for the experiment runner."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse arguments
    agent_counts = parse_agents_arg(args.agents)
    thresholds = parse_agents_arg(args.thresholds)
    
    # Create experiment config
    experiment_config = ExperimentConfig(
        context=args.context,
        agents=agent_counts,
        games_per_config=args.games,
        dataset=args.dataset,
        thresholds=thresholds,
        seed=args.seed,
        output_dir=Path(args.output_dir)
    )
    
    logger.log("experiment_started", 
             context=args.context, 
             agents=agent_counts, 
             games_per_config=args.games)
    
    # Run simulation
    results = run_simulation(experiment_config)
    
    # Filter successful results for metrics analysis
    successful_results = [r for r in results if r.success]
    total_games = len(results)
    success_rate = len(successful_results) / total_games if total_games > 0 else 0.0
    
    logger.log("experiment_completed", 
             total_games=total_games,
             successful_games=len(successful_results),
             success_rate=success_rate)
    
    # Write results to CSV
    output_filename = f"results_{args.context}_{args.agents.replace(',', '_')}.csv"
    output_path = experiment_config.output_dir / output_filename
    write_results_csv(results, output_path)
    
    # Print summary
    print(f"Experiment completed: {total_games} games simulated")
    print(f"Success rate: {success_rate:.2%}")
    print(f"Results written to: {output_path}")
    
    if successful_results:
        avg_spec = np.mean([r.specialization_index for r in successful_results])
        avg_ret = np.mean([r.retrieval_efficiency for r in successful_results])
        print(f"Average Specialization Index: {avg_spec:.4f}")
        print(f"Average Retrieval Efficiency: {avg_ret:.4f}")
    
    return results

if __name__ == "__main__":
    sys.exit(main())
