"""Main experiment runner with CLI for context, agents, games, and scaling."""
from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from agent.base_agent import AgentConfig, BaseAgent
from memory.buffer import get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger


logger = get_logger(__name__)


class GameResult:
    """Result from a single game."""
    def __init__(self, game_id: int, agent_count: int, context: str,
                 specialization_index: float, retrieval_efficiency: float):
        self.game_id = game_id
        self.agent_count = agent_count
        self.context = context
        self.specialization_index = specialization_index
        self.retrieval_efficiency = retrieval_efficiency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "agent_count": self.agent_count,
            "context_condition": self.context,
            "specialization_index": self.specialization_index,
            "retrieval_efficiency": self.retrieval_efficiency
        }


def simulate_one_game(
    agent_count: int,
    game_id: int,
    context: str = "full"
) -> Tuple[float, GameResult]:
    """Simulate one game and return metrics."""
    random.seed(game_id)
    
    # Create agents
    agents = [
        BaseAgent(AgentConfig(
            agent_id=i,
            skills=[f"skill_{i % 3}"],
            specialization_level=0.5 + random.uniform(-0.2, 0.2)
        ))
        for i in range(agent_count)
    ]
    
    # Get shared buffer
    buffer = get_shared_buffer()
    
    # Store phase: agents store facts
    stored_count = 0
    for agent in agents:
        fact = f"game_{game_id}_fact_{agent.agent_id}"
        buffer.store(fact, {"agent_id": agent.agent_id, "game_id": game_id})
        stored_count += 1
    
    # Retrieval phase: agents retrieve facts
    retrieved_count = 0
    for agent in agents:
        query = f"game_{game_id}"
        results = buffer.search(query)
        if results:
            retrieved_count += len(results)
    
    # Apply context condition
    if context == "limited":
        # Limit retrieval in limited context
        retrieved_count = max(0, int(retrieved_count * 0.6))
    
    # Compute metrics
    agent_skills = [[f"skill_{i % 3}"] for i in range(agent_count)]
    spec_idx, _ = compute_specialization_index(agent_skills, num_agents=agent_count)
    ret_metrics, ret_eff = compute_retrieval_efficiency(
        retrieved=retrieved_count,
        total=stored_count if stored_count > 0 else 1,
        agents=agent_count
    )
    
    result = GameResult(
        game_id=game_id,
        agent_count=agent_count,
        context=context,
        specialization_index=spec_idx,
        retrieval_efficiency=ret_eff
    )
    
    return spec_idx, result


def run_simulation(
    context: str,
    agent_counts: List[int],
    games_per_config: int,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> List[GameResult]:
    """Run simulation for specified configurations."""
    random.seed(seed)
    
    if output_dir is None:
        output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for agent_count in agent_counts:
        logger.info(f"Running {games_per_config} games with {agent_count} agents (context={context})")
        reset_shared_buffer()
        
        for game_id in range(games_per_config):
            _, result = simulate_one_game(agent_count, game_id, context)
            results.append(result)
    
    return results


def write_results_csv(
    results: List[GameResult],
    output_path: Path
) -> None:
    """Write results to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="") as f:
        fieldnames = ["game_id", "agent_count", "context_condition", 
                     "specialization_index", "retrieval_efficiency"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())
    
    logger.info(f"Wrote {len(results)} results to {output_path}")


def aggregate_for_scaling(
    results: List[GameResult]
) -> Dict[int, Dict[str, float]]:
    """Aggregate results by agent count for scaling analysis."""
    aggregated = {}
    
    for result in results:
        if result.agent_count not in aggregated:
            aggregated[result.agent_count] = {
                "specialization_index": [],
                "retrieval_efficiency": []
            }
        
        aggregated[result.agent_count]["specialization_index"].append(result.specialization_index)
        aggregated[result.agent_count]["retrieval_efficiency"].append(result.retrieval_efficiency)
    
    # Compute means
    for agent_count in aggregated:
        spec_vals = aggregated[agent_count]["specialization_index"]
        ret_vals = aggregated[agent_count]["retrieval_efficiency"]
        
        aggregated[agent_count]["specialization_index"] = sum(spec_vals) / len(spec_vals) if spec_vals else 0.0
        aggregated[agent_count]["retrieval_efficiency"] = sum(ret_vals) / len(ret_vals) if ret_vals else 0.0
    
    return aggregated


def write_scaling_data_csv(
    aggregated: Dict[int, Dict[str, float]],
    output_path: Path
) -> None:
    """Write aggregated scaling data to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="") as f:
        fieldnames = ["agent_count", "specialization_index", "retrieval_efficiency"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for agent_count in sorted(aggregated.keys()):
            writer.writerow({
                "agent_count": agent_count,
                "specialization_index": aggregated[agent_count]["specialization_index"],
                "retrieval_efficiency": aggregated[agent_count]["retrieval_efficiency"]
            })
    
    logger.info(f"Wrote scaling data to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
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
        default="5",
        help="Agent counts (comma-separated for scaling, or single int)"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Games per configuration"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Output directory"
    )
    parser.add_argument(
        "--plot",
        choices=["scaling"],
        help="Generate plot (scaling)"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        help="Context thresholds (comma-separated)"
    )
    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agent counts
    agent_str = args.agents
    if "," in agent_str:
        agent_counts = [int(x.strip()) for x in agent_str.split(",")]
    else:
        agent_counts = [int(agent_str)]
    
    # Run simulation
    logger.info(f"Starting experiment: context={args.context}, agents={agent_counts}, games={args.games}")
    
    results = run_simulation(
        context=args.context,
        agent_counts=agent_counts,
        games_per_config=args.games,
        seed=args.seed,
        output_dir=args.output_dir
    )
    
    # Write results
    output_file = args.output_dir / f"results_{args.context}.csv"
    write_results_csv(results, output_file)
    
    # Generate scaling plot if requested
    if args.plot == "scaling":
        aggregated = aggregate_for_scaling(results)
        scaling_file = args.output_dir / "scaling_data.csv"
        write_scaling_data_csv(aggregated, scaling_file)
        logger.info(f"Generated scaling data for {len(aggregated)} agent counts")
    
    logger.info("Experiment complete")


if __name__ == "__main__":
    main()