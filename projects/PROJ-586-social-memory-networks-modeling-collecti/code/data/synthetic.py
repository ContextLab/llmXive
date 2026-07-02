"""
Synthetic data generation for social memory experiments.

This module generates controlled synthetic datasets for testing the pipeline
when real datasets are unavailable. The generated data follows the experimental
design specifications for social memory network simulations.

IMPORTANT: This module generates CONTROLLED synthetic data for testing purposes only.
It does not fabricate experimental results - it creates the input data structures
that the actual simulation will process to generate real measurements.
"""

import os
import random
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
from dataclasses import dataclass, asdict


@dataclass
class SyntheticGameConfig:
    """Configuration for generating synthetic game data."""
    num_games: int = 1000
    num_agents: int = 3
    context_tokens: int = 512
    seed: int = 42
    max_turns: int = 50
    memory_capacity: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyntheticGameConfig':
        """Create config from dictionary."""
        return cls(**data)


def generate_synthetic_games(config: SyntheticGameConfig) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for testing the social memory pipeline.
    
    This function creates structured synthetic data that mimics the format
    of real game interactions, but uses controlled random values for testing
    purposes. The actual metrics are computed by running the simulation
    on this data, not fabricated here.
    
    Args:
        config: Configuration for generating the games
        
    Returns:
        List of synthetic game records
    """
    random.seed(config.seed)
    np.random.seed(config.seed)
    
    games = []
    
    for game_id in range(config.num_games):
        # Generate game structure
        game = {
            'game_id': game_id,
            'agent_count': config.num_agents,
            'context_tokens': config.context_tokens,
            'max_turns': config.max_turns,
            'memory_capacity': config.memory_capacity,
            'seed': config.seed,
            'turns': [],
            'memory_actions': [],
            'final_state': {}
        }
        
        # Generate turns
        for turn in range(config.max_turns):
            turn_data = {
                'turn_id': turn,
                'agent_id': f"agent_{random.randint(0, config.num_agents - 1)}",
                'action': random.choice(['store', 'retrieve', 'update', 'none']),
                'content_length': random.randint(10, 200),
                'query_length': random.randint(5, 100) if random.random() > 0.5 else 0
            }
            game['turns'].append(turn_data)
            
            # Generate memory actions
            if turn_data['action'] in ['store', 'update']:
                game['memory_actions'].append({
                    'turn_id': turn,
                    'type': turn_data['action'],
                    'content': f"Memory content for turn {turn} by {turn_data['agent_id']}",
                    'timestamp': turn
                })
        
        # Generate final state
        game['final_state'] = {
            'total_turns': config.max_turns,
            'memory_entries': len(game['memory_actions']),
            'unique_agents': config.num_agents
        }
        
        games.append(game)
    
    return games


def generate_all_datasets(output_dir: Union[str, Path], num_games: int = 1000) -> None:
    """
    Generate all synthetic datasets needed for the experiments.
    
    This function creates the synthetic input data files that will be used
    by the simulation scripts. It does not compute any metrics - those are
    calculated by running the actual simulation on this data.
    
    Args:
        output_dir: Directory to save the generated datasets
        num_games: Number of games to generate per dataset
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate full context dataset
    full_config = SyntheticGameConfig(
        num_games=num_games,
        num_agents=5,
        context_tokens=2048,
        seed=42
    )
    full_games = generate_synthetic_games(full_config)
    
    full_file = output_path / "synthetic_full_context.json"
    with open(full_file, 'w') as f:
        import json
        json.dump(full_games, f, indent=2)
    
    # Generate limited context dataset
    limited_config = SyntheticGameConfig(
        num_games=num_games,
        num_agents=5,
        context_tokens=256,
        seed=42
    )
    limited_games = generate_synthetic_games(limited_config)
    
    limited_file = output_path / "synthetic_limited_context.json"
    with open(limited_file, 'w') as f:
        import json
        json.dump(limited_games, f, indent=2)
    
    # Generate scaling dataset for different agent counts
    scaling_games = []
    for agent_count in [3, 5, 7]:
        scaling_config = SyntheticGameConfig(
            num_games=800,  # 800 games per config as per US-3 spec
            num_agents=agent_count,
            context_tokens=512,
            seed=42 + agent_count
        )
        games = generate_synthetic_games(scaling_config)
        for game in games:
            game['agent_count'] = agent_count
        scaling_games.extend(games)
    
    scaling_file = output_path / "synthetic_scaling.json"
    with open(scaling_file, 'w') as f:
        import json
        json.dump(scaling_games, f, indent=2)

    print(f"Generated synthetic datasets in {output_path}")
    print(f"  - Full context: {num_games} games")
    print(f"  - Limited context: {num_games} games")
    print(f"  - Scaling: {len(scaling_games)} games (3, 5, 7 agents)")


def verify_datasets() -> bool:
    """
    Verify that the synthetic datasets are properly generated.
    
    Returns:
        True if all datasets exist and are valid, False otherwise
    """
    base_dir = Path(__file__).parent.parent / "data"
    datasets = [
        "synthetic_full_context.json",
        "synthetic_limited_context.json",
        "synthetic_scaling.json"
    ]
    
    all_valid = True
    for dataset in datasets:
        dataset_path = base_dir / dataset
        if not dataset_path.exists():
            print(f"Missing dataset: {dataset_path}")
            all_valid = False
            continue
        
        try:
            with open(dataset_path, 'r') as f:
                import json
                data = json.load(f)
                if not isinstance(data, list) or len(data) == 0:
                    print(f"Invalid dataset: {dataset_path}")
                    all_valid = False
        except Exception as e:
            print(f"Error reading {dataset_path}: {e}")
            all_valid = False
    
    return all_valid
