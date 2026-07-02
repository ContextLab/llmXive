import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from dataclasses import dataclass

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SyntheticGameConfig:
    """Configuration for synthetic game generation."""
    num_games: int
    num_agents: int
    context_type: str  # 'full' or 'limited'
    seed: int = 42
    max_turns: int = 10
    memory_capacity: int = 50


def generate_synthetic_games(
    num_games: int,
    num_agents: int,
    context_type: str = "full",
    seed: int = 42,
    max_turns: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for social memory experiments.

    This creates realistic game traces where agents interact and store memories,
    suitable for measuring specialization and retrieval efficiency.

    Args:
        num_games: Number of games to generate
        num_agents: Number of agents per game
        context_type: 'full' or 'limited' context
        seed: Random seed
        max_turns: Maximum turns per game

    Returns:
        List of game dictionaries with traces and metadata
    """
    np.random.seed(seed)
    games = []

    for game_id in range(num_games):
        game_seed = seed + game_id
        np.random.seed(game_seed)

        # Game metadata
        game = {
            "game_id": game_id,
            "agent_count": num_agents,
            "context_type": context_type,
            "turns": []
        }

        # Simulate turns
        for turn in range(max_turns):
            active_agent = turn % num_agents

            # Generate action
            action_types = ["query", "store", "retrieve", "ignore"]
            action = np.random.choice(action_types)

            # Generate memory content
            memory_content = f"content_{game_id}_{turn}_{np.random.randint(0, 1000)}"

            # Determine if memory is stored
            store_memory = action in ["store", "retrieve"] and np.random.random() > 0.3

            turn_data = {
                "turn": turn,
                "agent": active_agent,
                "action": action,
                "memory_content": memory_content if store_memory else None,
                "stored": store_memory,
                "context_size": np.random.randint(100, 512) if context_type == "limited" else np.random.randint(100, 2048)
            }

            game["turns"].append(turn_data)

        games.append(game)

    return games


def generate_all_datasets(data_dir: Optional[Union[str, Path]] = None) -> None:
    """
    Generate all required synthetic datasets.

    Args:
        data_dir: Output directory (defaults to 'data/')
    """
    data_dir = Path(data_dir) if data_dir else Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating synthetic datasets...")

    # Generate datasets for different configurations
    configs = [
        (100, 3, "full"),
        (100, 5, "full"),
        (100, 7, "full"),
        (100, 3, "limited"),
        (100, 5, "limited"),
        (100, 7, "limited"),
    ]

    for count, agents, ctx in configs:
        games = generate_synthetic_games(count, agents, ctx)
        output_path = data_dir / f"games_{agents}agents_{ctx}.csv"

        # Flatten for CSV
        flat_data = []
        for game in games:
            for turn in game["turns"]:
                flat_data.append({
                    "game_id": game["game_id"],
                    "agent_count": game["agent_count"],
                    "context_type": game["context_type"],
                    "turn": turn["turn"],
                    "agent": turn["agent"],
                    "action": turn["action"],
                    "memory_content": turn["memory_content"],
                    "stored": turn["stored"],
                    "context_size": turn["context_size"]
                })

        df = pd.DataFrame(flat_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} rows to {output_path}")


def verify_datasets(data_dir: Optional[Union[str, Path]] = None) -> bool:
    """
    Verify that required synthetic datasets exist.

    Args:
        data_dir: Data directory to check

    Returns:
        True if all datasets exist, False otherwise
    """
    data_dir = Path(data_dir) if data_dir else Path("data")
    required_files = [
        "games_3agents_full.csv",
        "games_5agents_full.csv",
        "games_7agents_full.csv",
        "games_3agents_limited.csv",
        "games_5agents_limited.csv",
        "games_7agents_limited.csv",
    ]

    missing = [f for f in required_files if not (data_dir / f).exists()]
    if missing:
        logger.warning(f"Missing datasets: {missing}")
        return False

    return True