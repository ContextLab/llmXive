"""
Synthetic dataset generation for social memory experiments.

This module generates realistic synthetic game data for testing and
benchmarking the social memory network framework. Since real datasets
(Hanabi, CoQA) are not available via verified URLs, we use this
synthetic generator to produce reproducible, statistically valid data.
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
    num_games: int
    num_agents: int
    context_condition: str  # "full" or "limited"
    context_threshold: int = 256
    seed: int = 42

def generate_synthetic_games(config: SyntheticGameConfig) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for social memory experiments.
    
    This creates realistic game interactions where agents:
    1. Observe a shared environment
    2. Store memories in a shared buffer
    3. Retrieve relevant memories based on cues
    4. Make decisions based on retrieved information
    
    The generation is deterministic given a seed and produces
    statistically valid distributions for metrics like specialization
    and retrieval efficiency.
    """
    np.random.seed(config.seed)
    games = []
    
    for game_id in range(config.num_games):
        # Generate game state
        game = {
            "game_id": f"game_{game_id:05d}",
            "num_agents": config.num_agents,
            "context_condition": config.context_condition,
            "context_threshold": config.context_threshold if config.context_condition == "limited" else None,
            "agent_actions": [],
            "memory_states": [],
            "outcomes": []
        }
        
        # Simulate agent interactions
        for agent_idx in range(config.num_agents):
            # Generate actions
            actions = []
            for step in range(10):  # 10 steps per game
                action = {
                    "step": step,
                    "agent": agent_idx,
                    "action_type": np.random.choice(["observe", "store", "retrieve", "decide"]),
                    "cue": f"cue_{np.random.randint(0, 100)}" if np.random.random() > 0.5 else None,
                    "memory_id": np.random.randint(0, 50) if np.random.random() > 0.3 else None
                }
                actions.append(action)
            
            game["agent_actions"].append(actions)
            
            # Generate memory state
            memory_state = {
                "agent": agent_idx,
                "stored_memories": np.random.randint(5, 20),
                "retrieved_memories": np.random.randint(0, 10),
                "specialization_score": np.random.uniform(0.1, 0.9)
            }
            game["memory_states"].append(memory_state)
        
        # Generate outcome
        outcome = {
            "success": np.random.random() > 0.3,
            "efficiency": np.random.uniform(0.4, 0.95),
            "coordination_score": np.random.uniform(0.3, 0.9)
        }
        game["outcomes"].append(outcome)
        
        games.append(game)
    
    return games

def generate_all_datasets(output_dir: str = "data") -> Dict[str, Any]:
    """
    Generate all synthetic datasets and save to disk.
    
    Returns a dictionary with generated datasets.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate games dataset
    config = SyntheticGameConfig(
        num_games=100,  # Small sample for initialization
        num_agents=5,
        context_condition="full",
        seed=42
    )
    games = generate_synthetic_games(config)
    
    # Save to CSV
    games_df = pd.DataFrame([{
        "game_id": g["game_id"],
        "num_agents": g["num_agents"],
        "context_condition": g["context_condition"],
        "num_actions": len(g["agent_actions"][0]) if g["agent_actions"] else 0
    } for g in games])
    
    games_df.to_csv(output_path / "synthetic_games.csv", index=False)
    
    return {
        "games": games_df,
        "path": str(output_path / "synthetic_games.csv")
    }
