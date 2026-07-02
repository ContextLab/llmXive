import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class SyntheticGameConfig:
    num_games: int
    agent_count: int
    context_condition: str
    seed: int
    max_items: int = 100
    max_actions_per_game: int = 50

def generate_synthetic_games(config: SyntheticGameConfig) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for social memory experiments.
    
    This function creates deterministic, reproducible game data based on the seed.
    It simulates agent interactions with a shared memory buffer.
    """
    np.random.seed(config.seed)
    random.seed(config.seed)
    
    games = []
    for i in range(config.num_games):
        game_seed = config.seed + i
        np.random.seed(game_seed)
        random.seed(game_seed)
        
        # Generate game structure
        num_items = min(config.max_items, config.agent_count * 10)
        num_actions = min(config.max_actions_per_game, config.agent_count * 20)
        
        # Create items
        items = []
        for j in range(num_items):
            items.append({
                'id': j,
                'type': np.random.choice(['fact', 'event', 'concept']),
                'value': np.random.rand(),
                'agent_owner': np.random.randint(0, config.agent_count)
            })
        
        # Create actions
        actions = []
        base_prob = 0.7 if config.context_condition == 'full' else 0.4
        
        for j in range(num_actions):
            action_type = np.random.choice(['store', 'retrieve', 'update'], p=[0.4, 0.4, 0.2])
            agent_id = np.random.randint(0, config.agent_count)
            
            if action_type == 'retrieve':
                success_prob = base_prob * (1 - 0.1 * config.agent_count / 10)
                success = np.random.rand() < max(0.1, success_prob)
            else:
                success = True
            
            actions.append({
                'id': j,
                'type': action_type,
                'agent_id': agent_id,
                'success': success,
                'timestamp': j * 0.1
            })
        
        games.append({
            'game_id': i,
            'agent_count': config.agent_count,
            'context_condition': config.context_condition,
            'seed': game_seed,
            'items': items,
            'actions': actions
        })
    
    return games

def generate_all_datasets(output_dir: str = 'data/synthetic') -> Dict[str, str]:
    """
    Generate all synthetic datasets needed for experiments.
    
    Returns a dictionary mapping dataset names to file paths.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    configs = [
        SyntheticGameConfig(100, 3, 'full', 42),
        SyntheticGameConfig(100, 5, 'full', 42),
        SyntheticGameConfig(100, 7, 'full', 42),
        SyntheticGameConfig(100, 3, 'limited', 42),
        SyntheticGameConfig(100, 5, 'limited', 42),
        SyntheticGameConfig(100, 7, 'limited', 42),
    ]
    
    file_paths = {}
    for config in configs:
        games = generate_synthetic_games(config)
        filename = f"synthetic_{config.context_condition}_agents{config.agent_count}.csv"
        filepath = output_path / filename
        
        df = pd.DataFrame([{
            'game_id': g['game_id'],
            'agent_count': g['agent_count'],
            'context_condition': g['context_condition'],
            'seed': g['seed'],
            'num_items': len(g['items']),
            'num_actions': len(g['actions'])
        } for g in games])
        
        df.to_csv(filepath, index=False)
        file_paths[f"{config.context_condition}_{config.agent_count}"] = str(filepath)
    
    return file_paths

import random
