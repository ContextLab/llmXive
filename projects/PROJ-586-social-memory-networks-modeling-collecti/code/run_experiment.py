"""
Main experiment runner for Social Memory Networks.
Implements CLI parsing, game simulation loop, and result aggregation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# Local imports based on project API surface
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import get_dataset, load_experiment_results, save_experiment_results, enable_synthetic_fallback, disable_synthetic_fallback, DatasetLoader
from data.synthetic import generate_synthetic_dataset, save_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None
    dataset_name: str = "hanabi"
    seed: int = 42
    max_turns: int = 20
    use_synthetic: bool = False

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    success: bool
    error_message: Optional[str] = None


def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse agents argument which can be a single int or comma-separated list."""
    try:
        if ',' in agents_str:
            return [int(x.strip()) for x in agents_str.split(',')]
        return [int(agents_str.strip())]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid agents format: {agents_str}")


def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_data_checksum(data: List[Dict[str, Any]]) -> str:
    """Compute checksum of dataset content for reproducibility."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict[str, Any]], str]:
    """
    Load dataset from real source or trigger synthetic fallback.
    Returns (data_list, checksum).
    """
    dataset_path = Path(f"data/{config.dataset_name}.json")
    
    # Try to load real dataset first
    if dataset_path.exists():
        try:
            data = load_experiment_results(dataset_path)
            if data:
                checksum = compute_data_checksum(data)
                logger.log("dataset_loaded", path=str(dataset_path), checksum=checksum)
                return data, checksum
        except Exception as e:
            logger.log("dataset_load_failed", path=str(dataset_path), error=str(e))
    
    # Trigger synthetic fallback as per FR-011
    logger.log("synthetic_fallback_triggered", reason="real_dataset_unavailable")
    enable_synthetic_fallback()
    
    # Generate synthetic data as fallback
    synthetic_data = generate_synthetic_dataset(
        name=config.dataset_name,
        num_records=100,  # Generate enough for simulation
        seed=config.seed
    )
    
    # Save synthetic data for reproducibility
    save_synthetic_dataset(synthetic_data, dataset_path)
    
    checksum = compute_data_checksum(synthetic_data)
    logger.log("synthetic_dataset_generated", path=str(dataset_path), checksum=checksum)
    return synthetic_data, checksum


def truncate_context(context: str, token_limit: int) -> str:
    """Truncate context to specified token limit."""
    if token_limit is None:
        return context
    
    # Simple tokenization by splitting on whitespace
    tokens = context.split()
    if len(tokens) <= token_limit:
        return context
    
    truncated = ' '.join(tokens[:token_limit])
    logger.log("context_truncated", original_tokens=len(tokens), truncated_tokens=token_limit)
    return truncated


def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    current_context: str,
    turn_number: int
) -> Tuple[str, Dict[str, Any]]:
    """
    Simulate a single turn for an agent.
    Returns (response, memory_action).
    """
    # Prepare context for agent
    prompt = f"Turn {turn_number}: {current_context}"
    
    # Agent generates response
    response = agent.generate(prompt)
    
    # Check for memory actions in response
    memory_action = None
    if "<MEMORY_ACTION>" in response:
        # Extract and parse memory action
        try:
            start_idx = response.find("<MEMORY_ACTION>")
            end_idx = response.find("</MEMORY_ACTION>")
            if end_idx > start_idx:
                action_json = response[start_idx + len("<MEMORY_ACTION>"):end_idx].strip()
                memory_action = json.loads(action_json)
                
                # Execute memory action
                if memory_action.get("type") == "write":
                    memory_buffer.write(
                        key=memory_action["key"],
                        value=memory_action["value"]
                    )
                elif memory_action.get("type") == "read":
                    memory_buffer.read(key=memory_action["key"])
        except (json.JSONDecodeError, KeyError) as e:
            logger.log("memory_action_parse_failed", error=str(e))
    
    return response, memory_action


def simulate_one_game(config: GameConfig) -> GameResult:
    """
    Simulate a single game with the given configuration.
    Returns GameResult with metrics.
    """
    # Set seed for reproducibility
    random.seed(config.seed)
    
    # Load dataset
    data, checksum = load_and_verify_dataset(config)
    
    # Initialize agents
    agents = []
    for i in range(config.num_agents):
        agent_config = AgentConfig(
            model_name="facebook/opt-125m",
            device="cpu",
            seed=config.seed + i
        )
        agent = BaseAgent(agent_config)
        agents.append(agent)
    
    # Initialize shared memory buffer
    memory_buffer = get_shared_buffer()
    memory_buffer.reset()
    
    # Game state tracking
    agent_facts = {i: set() for i in range(config.num_agents)}
    successful_retrievals = 0
    total_queries = 0
    
    # Game loop
    current_context = data[0]["context"] if data else "Initial context"
    
    for turn in range(config.max_turns):
        # Select active agent (round-robin for simplicity)
        agent_idx = turn % config.num_agents
        active_agent = agents[agent_idx]
        
        # Apply context truncation if limited context
        if config.context_condition == "limited":
            effective_context = truncate_context(current_context, config.token_limit or 256)
        else:
            effective_context = current_context
        
        # Simulate turn
        response, memory_action = simulate_game_turn(
            active_agent, memory_buffer, effective_context, turn
        )
        
        # Extract facts from response (simplified extraction)
        if "fact:" in response.lower():
            fact = response.split("fact:")[1].split(".")[0].strip()
            agent_facts[agent_idx].add(fact)
        
        # Track retrieval attempts
        if "<MEMORY_ACTION>" in response and "read" in response:
            total_queries += 1
            # Check if retrieval was successful (simplified check)
            if "success" in response.lower() or memory_action:
                successful_retrievals += 1
        
        # Update context for next turn
        current_context = f"{current_context} {response}"
    
    # Compute metrics
    facts_list = [list(facts) for facts in agent_facts.values()]
    spec_index, _ = compute_specialization_index(facts_list, num_agents=config.num_agents)
    ret_eff, _ = compute_retrieval_efficiency(successful_retrievals, total_queries, config.num_agents)
    
    return GameResult(
        game_id=turn,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        context_condition=config.context_condition,
        agent_count=config.num_agents,
        success=True
    )


def run_simulation(
    num_games: int,
    agent_counts: List[int],
    context_condition: str,
    dataset_name: str,
    token_limit: Optional[int] = None,
    seed: int = 42
) -> List[GameResult]:
    """
    Run multiple game simulations across different agent counts.
    Returns list of GameResult objects.
    """
    results = []
    
    for agent_count in agent_counts:
        logger.log("simulation_batch_start", agent_count=agent_count, games=num_games)
        
        for game_idx in range(num_games):
            config = GameConfig(
                num_agents=agent_count,
                context_condition=context_condition,
                token_limit=token_limit,
                dataset_name=dataset_name,
                seed=seed + game_idx,
                max_turns=20
            )
            
            try:
                result = simulate_one_game(config)
                results.append(result)
                
                if (game_idx + 1) % 100 == 0:
                    logger.log("simulation_progress", 
                               agent_count=agent_count, 
                               games_completed=game_idx + 1, 
                               total=num_games)
            except Exception as e:
                logger.log("simulation_error", game_id=game_idx, error=str(e))
                # Record failed game
                results.append(GameResult(
                    game_id=game_idx,
                    specialization_index=0.0,
                    retrieval_efficiency=0.0,
                    context_condition=context_condition,
                    agent_count=agent_count,
                    success=False,
                    error_message=str(e)
                ))
        
        logger.log("simulation_batch_complete", agent_count=agent_count, games_completed=num_games)
    
    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write simulation results to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'game_id', 'specialization_index', 'retrieval_efficiency',
            'context_condition', 'agent_count', 'success', 'error_message'
        ])
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'game_id': result.game_id,
                'specialization_index': result.specialization_index,
                'retrieval_efficiency': result.retrieval_efficiency,
                'context_condition': result.context_condition,
                'agent_count': result.agent_count,
                'success': result.success,
                'error_message': result.error_message or ''
            })
    
    logger.log("results_written", path=str(output_path), count=len(results))


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition: full or limited"
    )
    
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent count(s): single number or comma-separated list (e.g., 3,5,7)"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate per configuration"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default="hanabi",
        help="Dataset name (hanabi or coqa)"
    )
    
    parser.add_argument(
        "--token-limit",
        type=int,
        default=None,
        help="Token limit for limited context (default: no limit)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: auto-generated)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    return parser


def main():
    """Main entry point for experiment runner."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agent counts
    agent_counts = parse_agents_arg(args.agents)
    
    logger.log("experiment_start", 
               context=args.context, 
               agents=agent_counts, 
               games=args.games, 
               dataset=args.dataset)
    
    # Run simulation
    results = run_simulation(
        num_games=args.games,
        agent_counts=agent_counts,
        context_condition=args.context,
        dataset_name=args.dataset,
        seed=args.seed,
        game_id="batch"
    )
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"results_{args.context}_agents_{'_'.join(map(str, agent_counts))}.csv"
        output_path = output_dir / output_filename
    
    # Write results
    write_results_csv(results, output_path)
    
    # Log summary
    successful = sum(1 for r in results if r.success)
    logger.log("experiment_complete", 
               total_games=len(results), 
               successful_games=successful, 
               output=str(output_path))
    
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())