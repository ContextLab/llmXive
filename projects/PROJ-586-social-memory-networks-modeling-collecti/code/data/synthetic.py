import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from dataclasses import dataclass
import json

@dataclass
class SyntheticGameConfig:
    """Configuration for synthetic game generation."""
    num_agents: int
    num_items: int
    num_turns: int
    context_type: str  # 'full' or 'limited'
    difficulty: float = 0.5  # 0.0 to 1.0

def generate_synthetic_games(configs: List[SyntheticGameConfig], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for social memory experiments.
    
    This function creates deterministic but varied game scenarios based on the
    provided configuration. It simulates the core mechanics of transactive memory
    systems without requiring external datasets.
    
    Args:
        configs: List of configuration objects defining game parameters
        seed: Random seed for reproducibility
        
    Returns:
        List of game data dictionaries
    """
    np.random.seed(seed)
    games = []
    
    for idx, config in enumerate(configs):
        game_data = {
            'game_id': idx,
            'config': {
                'num_agents': config.num_agents,
                'num_items': config.num_items,
                'num_turns': config.num_turns,
                'context_type': config.context_type,
                'difficulty': config.difficulty
            },
            'turns': [],
            'final_state': {}
        }
        
        # Generate items
        items = [f"item_{i}" for i in range(config.num_items)]
        agents = [f"agent_{i}" for i in range(config.num_agents)]
        
        # Simulate turns
        for turn in range(config.num_turns):
            current_agent = agents[turn % len(agents)]
            
            # Determine action
            if np.random.random() < 0.6:
                action = "store"
                item = np.random.choice(items)
                cue = f"cue_{turn}_{current_agent}"
            else:
                action = "retrieve"
                cue = f"cue_{np.random.randint(0, max(1, turn))}"
                item = None
            
            turn_data = {
                'turn': turn,
                'agent': current_agent,
                'action': action,
                'item': item,
                'cue': cue,
                'success': np.random.random() > config.difficulty
            }
            game_data['turns'].append(turn_data)
        
        # Calculate final state metrics
        agent_knowledge = {a: [] for a in agents}
        for turn in game_data['turns']:
            if turn['action'] == 'store' and turn['success']:
                agent_knowledge[turn['agent']].append(turn['item'])
        
        game_data['final_state'] = {
            'agent_knowledge': agent_knowledge,
            'total_stores': sum(1 for t in game_data['turns'] if t['action'] == 'store' and t['success']),
            'total_retrievals': sum(1 for t in game_data['turns'] if t['action'] == 'retrieve' and t['success']),
            'unique_items_stored': len(set(t['item'] for t in game_data['turns'] if t['action'] == 'store' and t['success']))
        }
        
        games.append(game_data)
    
    return games

def generate_all_datasets(output_dir: str = 'data/generated', seed: int = 42):
    """
    Generate all synthetic datasets needed for experiments.
    
    Creates datasets for different experimental conditions (full/limited context)
    and agent counts as specified in the project requirements.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Define configurations matching the experiment requirements
    configs = [
        # US-1: Baseline (Full context)
        SyntheticGameConfig(num_agents=5, num_items=20, num_turns=10, context_type='full'),
        # US-2: Limited context
        SyntheticGameConfig(num_agents=5, num_items=20, num_turns=10, context_type='limited'),
        # US-3: Scaling (3, 5, 7 agents)
        SyntheticGameConfig(num_agents=3, num_items=20, num_turns=10, context_type='full'),
        SyntheticGameConfig(num_agents=5, num_items=20, num_turns=10, context_type='full'),
        SyntheticGameConfig(num_agents=7, num_items=20, num_turns=10, context_type='full'),
    ]
    
    games = generate_synthetic_games(configs, seed=seed)
    
    # Save to CSV
    df = pd.DataFrame([{
        'game_id': g['game_id'],
        'num_agents': g['config']['num_agents'],
        'context_type': g['config']['context_type'],
        'num_items': g['config']['num_items'],
        'num_turns': g['config']['num_turns'],
        'total_stores': g['final_state']['total_stores'],
        'total_retrievals': g['final_state']['total_retrievals'],
        'unique_items': g['final_state']['unique_items_stored']
    } for g in games])
    
    output_file = output_path / 'synthetic_games.csv'
    df.to_csv(output_file, index=False)
    print(f"Generated {len(games)} synthetic games -> {output_file}")
    
    return games

def verify_datasets(data_dir: str = 'data/generated') -> bool:
    """Verify that synthetic datasets exist and are valid."""
    data_path = Path(data_dir)
    if not data_path.exists():
        return False
    
    csv_file = data_path / 'synthetic_games.csv'
    if not csv_file.exists():
        return False
    
    try:
        df = pd.read_csv(csv_file)
        required_cols = ['game_id', 'num_agents', 'context_type']
        return all(col in df.columns for col in required_cols) and len(df) > 0
    except Exception:
        return False
