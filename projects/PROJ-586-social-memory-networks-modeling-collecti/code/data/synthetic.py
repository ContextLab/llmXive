"""
Synthetic data generation for social memory experiments.
Generates realistic game scenarios for testing multi-agent memory systems.
"""
import os
import random
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass

@dataclass
class SyntheticGameConfig:
    """Configuration for synthetic game generation."""
    n_games: int = 1000
    n_agents: int = 5
    n_rounds: int = 10
    seed: int = 42

def generate_synthetic_games(config: SyntheticGameConfig) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for social memory experiments.
    
    Args:
        config: Configuration for game generation
    
    Returns:
        List of game dictionaries with game_id, state, rounds, success
    """
    random.seed(config.seed)
    np.random.seed(config.seed)
    
    games = []
    
    for game_id in range(config.n_games):
        # Generate random game state
        state = {
            'game_id': game_id,
            'initial_state': random.choice(['simple', 'moderate', 'complex']),
            'target_memory': f"memory_{game_id}_{random.randint(1000, 9999)}"
        }
        
        # Generate rounds
        rounds = []
        for round_num in range(config.n_rounds):
            round_data = {
                'round': round_num,
                'agent_actions': [
                    {
                        'agent_id': i,
                        'action': random.choice(['store', 'retrieve', 'update', 'none']),
                        'content': f"content_{game_id}_{round_num}_{i}"
                    }
                    for i in range(config.n_agents)
                ]
            }
            rounds.append(round_data)
        
        # Determine success based on memory operations
        success = random.random() > 0.3  # 70% success rate
        
        game = {
            'game_id': game_id,
            'state': state,
            'rounds': rounds,
            'success': success,
            'n_agents': config.n_agents,
            'n_rounds': config.n_rounds
        }
        
        games.append(game)
    
    return games

def generate_all_datasets() -> None:
    """Generate all required synthetic datasets."""
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Generate games
    config = SyntheticGameConfig(
        n_games=2000,  # Generate extra for flexibility
        n_agents=5,
        n_rounds=10,
        seed=42
    )
    
    games = generate_synthetic_games(config)
    
    # Save to CSV
    csv_path = output_dir / "synthetic_games.csv"
    with open(csv_path, 'w') as f:
        f.write("game_id,initial_state,target_memory,n_agents,n_rounds,success\n")
        for game in games:
            f.write(f"{game['game_id']},{game['state']['initial_state']},"
                   f"{game['state']['target_memory']},{game['n_agents']},"
                   f"{game['n_rounds']},{game['success']}\n")

def verify_datasets() -> bool:
    """
    Verify that required synthetic datasets exist.
    
    Returns:
        True if datasets exist, False otherwise
    """
    dataset_path = Path("data/synthetic_games.csv")
    if not dataset_path.exists():
        return False
    
    # Check file size
    if dataset_path.stat().st_size == 0:
        return False
    
    return True
