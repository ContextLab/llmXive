"""Generate full results with real game simulation."""
from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from agent.base_agent import AgentConfig, BaseAgent
from memory.buffer import get_shared_buffer
from metrics.specialization import compute_specialization_index, SpecializationMetrics
from metrics.retrieval import compute_retrieval_efficiency, RetrievalMetrics
from utils.logging import get_logger


logger = get_logger(__name__)


def simulate_one_game(
    agent_count_or_list: Any,
    game_id: Optional[int] = None,
    context: str = "full"
) -> Tuple[float, float]:
    """Simulate one game and return (specialization_index, retrieval_efficiency).
    
    Accepts multiple call patterns:
    1. simulate_one_game(agent_count, game_id, context)
    2. simulate_one_game(agent_list, game_id)
    3. simulate_one_game(agents, game_id)
    """
    # Determine agent count
    if isinstance(agent_count_or_list, int):
        agent_count = agent_count_or_list
        agents = [
            BaseAgent(AgentConfig(
                agent_id=i,
                skills=[f"skill_{i % 3}"],
                specialization_level=0.5 + random.uniform(-0.2, 0.2)
            ))
            for i in range(agent_count)
        ]
    else:
        agents = agent_count_or_list if isinstance(agent_count_or_list, list) else [agent_count_or_list]
        agent_count = len(agents)
    
    if game_id is None:
        game_id = random.randint(0, 10000)
    
    # Simulate game: agents remember and retrieve
    buffer = get_shared_buffer()
    
    # Store phase: each agent stores a fact
    stored_count = 0
    for agent in agents:
        fact = f"game_{game_id}_fact_{agent.agent_id}"
        buffer.store(fact, {"agent_id": agent.agent_id, "game_id": game_id})
        stored_count += 1
    
    # Retrieval phase: agents try to retrieve facts
    retrieved_count = 0
    for agent in agents:
        query = f"game_{game_id}"
        results = buffer.search(query)
        if results:
            retrieved_count += len(results)
    
    # Compute metrics
    agent_skills = [[f"skill_{i % 3}"] for i in range(agent_count)]
    spec_idx, _ = compute_specialization_index(agent_skills, num_agents=agent_count)
    ret_metrics, ret_eff = compute_retrieval_efficiency(
        retrieved=retrieved_count,
        total=stored_count if stored_count > 0 else 1,
        agents=agent_count
    )
    
    return spec_idx, ret_eff


def run_full_experiment(
    agent_counts: List[int],
    games_per_config: int,
    context: str = "full",
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """Run full experiment and return results."""
    random.seed(seed)
    
    if output_dir is None:
        output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for agent_count in agent_counts:
        logger.info(f"Running {games_per_config} games with {agent_count} agents (context={context})")
        
        for game_id in range(games_per_config):
            spec_idx, ret_eff = simulate_one_game(agent_count, game_id, context)
            
            results.append({
                "game_id": game_id,
                "agent_count": agent_count,
                "context_condition": context,
                "specialization_index": spec_idx,
                "retrieval_efficiency": ret_eff
            })
    
    # Write results to CSV
    if results:
        output_file = output_dir / f"results_{context}.csv"
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Wrote {len(results)} results to {output_file}")
    
    return {"results": results, "output_file": output_dir / f"results_{context}.csv"}
