"""
Synthetic dataset generation for social memory network experiments.

This module generates synthetic game data for testing and development
when real datasets (Hanabi, CoQA) are not programmatically accessible.
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class SyntheticGameConfig:
    """Configuration for synthetic game generation."""
    num_games: int = 1000
    num_agents: int = 3
    num_turns: int = 10
    num_items: int = 20
    seed: int = 42
    context_length: int = 512

def generate_synthetic_games(config: SyntheticGameConfig) -> Dict[str, Any]:
    """
    Generate synthetic game data for social memory experiments.
    
    Args:
        config: Configuration for game generation
    
    Returns:
        Dictionary with games and metadata
    """
    np.random.seed(config.seed)
    
    games = []
    for game_id in range(config.num_games):
        # Generate game items (facts to remember)
        items = [
            f"Item {i}: {np.random.choice(['red', 'blue', 'green', 'yellow'])} {np.random.choice(['circle', 'square', 'triangle', 'star'])}"
            for i in range(config.num_items)
        ]
        
        # Assign items to agents (specialization)
        agent_items = {}
        for agent_id in range(config.num_agents):
            agent_items[agent_id] = items[agent_id * (config.num_items // config.num_agents):
                                          (agent_id + 1) * (config.num_items // config.num_agents)]
        
        # Generate turns
        turns = []
        for turn in range(config.num_turns):
            turn_data = {
                "turn": turn,
                "question": f"Question {turn}: What is the {np.random.choice(['color', 'shape', 'type'])} of item {np.random.randint(config.num_items)}?",
                "context": " ".join(items[:min(10, len(items))]),
                "expected_answer": items[np.random.randint(config.num_items)]
            }
            turns.append(turn_data)
        
        # Create game record
        game = {
            "game_id": game_id,
            "items": items,
            "agent_items": agent_items,
            "turns": turns,
            "num_agents": config.num_agents,
            "context": " ".join(items[:config.context_length])
        }
        games.append(game)
    
    return {
        "games": games,
        "config": {
            "num_games": config.num_games,
            "num_agents": config.num_agents,
            "num_items": config.num_items,
            "seed": config.seed
        }
    }

def generate_all_datasets(
    dataset_name: str = "synthetic",
    num_games: int = 1000,
    num_agents: int = 3,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generate all datasets needed for experiments.
    
    Args:
        dataset_name: Name of dataset type
        num_games: Number of games to generate
        num_agents: Number of agents
        seed: Random seed
    
    Returns:
        Dictionary with generated datasets
    """
    config = SyntheticGameConfig(
        num_games=num_games,
        num_agents=num_agents,
        seed=seed
    )
    
    if dataset_name == "synthetic":
        return generate_synthetic_games(config)
    else:
        # Default to synthetic
        return generate_synthetic_games(config)

if __name__ == "__main__":
    # Test generation
    dataset = generate_all_datasets(num_games=10, num_agents=3)
    print(f"Generated {len(dataset['games'])} games")
    print(f"Config: {dataset['config']}")
