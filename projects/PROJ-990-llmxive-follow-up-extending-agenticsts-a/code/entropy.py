import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import json
import os

from config import load_config_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llmXive.entropy')

def calculate_shannon_entropy(probabilities: List[float]) -> float:
    """Calculate Shannon entropy H = -sum(p * log(p))."""
    if not probabilities:
        return 0.0
    # Filter out zeros to avoid log(0)
    p = np.array([p for p in probabilities if p > 0])
    if len(p) == 0:
        return 0.0
    p = p / p.sum() # Normalize
    entropy = -np.sum(p * np.log2(p))
    return entropy

def extract_move_distribution(turn_data: Dict) -> List[float]:
    """Extract probability distribution of legal moves."""
    moves = turn_data.get('legal_moves', [])
    if not moves:
        return []
    # Assume uniform distribution if not provided
    prob = 1.0 / len(moves)
    return [prob] * len(moves)

def calculate_entropy_for_trajectory(turns: List[Dict]) -> float:
    """Calculate average entropy for a trajectory."""
    entropies = []
    for turn in turns:
        dist = extract_move_distribution(turn)
        if dist:
            entropies.append(calculate_shannon_entropy(dist))
    return np.mean(entropies) if entropies else 0.0

def process_trajectories():
    """
    Process metrics_with_moves.csv to calculate entropy.
    Output: data/processed/metrics_with_moves.csv (updated with entropy column)
    """
    config = load_config_from_file('config.json')
    in_path = Path(config['data']['processed']) / 'metrics_with_moves.csv'
    out_path = Path(config['data']['processed']) / 'metrics_with_moves.csv'
    log_path = Path(config['data']['processed']) / 'edge_case_warnings.log'
    
    if not in_path.exists():
        logger.warning("metrics_with_moves.csv not found. Skipping entropy calculation.")
        return

    df = pd.read_csv(in_path)
    
    # Group by trajectory_id
    df['legal_moves'] = df['legal_moves'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    
    entropies = []
    warnings = []
    
    for traj_id, group in df.groupby('trajectory_id'):
        turns = group.to_dict('records')
        try:
            ent = calculate_entropy_for_trajectory(turns)
            if np.isnan(ent) or np.isinf(ent):
                warnings.append(f"Warning: NaN/Inf entropy detected at trajectory {traj_id}, turn 0")
                ent = float('inf')
            entropies.append(ent)
        except Exception as e:
            warnings.append(f"Warning: Error calculating entropy for {traj_id}: {e}")
            entropies.append(0.0)
    
    # Map back to rows
    traj_to_entropy = dict(zip(df['trajectory_id'].unique(), entropies))
    df['entropy'] = df['trajectory_id'].map(traj_to_entropy)
    
    df.to_csv(out_path, index=False)
    
    if warnings:
        with open(log_path, 'a') as f:
            for w in warnings:
                f.write(w + '\n')
        logger.info(f"Written {len(warnings)} entropy warnings to {log_path}")

def main():
    process_trajectories()

if __name__ == '__main__':
    main()
