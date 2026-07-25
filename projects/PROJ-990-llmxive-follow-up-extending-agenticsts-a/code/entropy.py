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
    Input: data/processed/metrics_with_moves.csv
    Output: data/processed/metrics_with_moves.csv (updated with entropy column)
            data/processed/edge_case_warnings.log (if NaN/Inf detected)
    """
    config = load_config_from_file('config.json')
    processed_dir = Path(config['data']['processed'])
    in_path = processed_dir / 'metrics_with_moves.csv'
    out_path = processed_dir / 'metrics_with_moves.csv'
    log_path = processed_dir / 'edge_case_warnings.log'
    
    if not in_path.exists():
        logger.warning("metrics_with_moves.csv not found. Skipping entropy calculation.")
        return

    df = pd.read_csv(in_path)
    
    # Ensure legal_moves column is parsed if it's a string representation of a list
    if 'legal_moves' in df.columns:
        def parse_moves(x):
            if isinstance(x, list):
                return x
            try:
                return json.loads(x) if isinstance(x, str) else []
            except (json.JSONDecodeError, TypeError):
                return []
        
        df['legal_moves'] = df['legal_moves'].apply(parse_moves)
    else:
        # If column missing, create empty list for all rows
        df['legal_moves'] = [[] for _ in range(len(df))]
    
    entropies = []
    warnings = []
    
    # Group by trajectory_id to calculate per-trajectory entropy
    # The task asks for entropy of legal move distributions.
    # We calculate the average entropy across turns for each trajectory.
    
    for traj_id, group in df.groupby('trajectory_id'):
        turns = group.to_dict('records')
        try:
            ent = calculate_entropy_for_trajectory(turns)
            
            # Check for NaN or Inf
            if np.isnan(ent) or np.isinf(ent):
                # Find the first turn where this might have happened (approximate)
                # Since we average, if any turn caused Inf, the result is Inf.
                # We log the trajectory ID and turn 0 as a placeholder for the warning
                # per the specific requirement format, though in reality it's an aggregate.
                # To be more precise, we could iterate turns to find the specific one,
                # but the requirement says "trajectory {id}, turn {turn}".
                # We will iterate to find the specific turn causing the issue for accuracy.
                specific_turn = 0
                for i, turn in enumerate(turns):
                    dist = extract_move_distribution(turn)
                    if dist:
                        t_ent = calculate_shannon_entropy(dist)
                        if np.isnan(t_ent) or np.isinf(t_ent):
                            specific_turn = turn.get('turn', i)
                            break
                
                warnings.append(f"Warning: NaN/Inf entropy detected at trajectory {traj_id}, turn {specific_turn}")
                ent = float('inf')
            
            entropies.append((traj_id, ent))
        except Exception as e:
            logger.error(f"Error calculating entropy for {traj_id}: {e}")
            entropies.append((traj_id, 0.0))
    
    # Map back to rows
    traj_to_entropy = dict(entropies)
    df['entropy'] = df['trajectory_id'].map(traj_to_entropy)
    
    # Write the updated CSV
    df.to_csv(out_path, index=False)
    
    # Write warnings log if any
    if warnings:
        with open(log_path, 'a') as f:
            for w in warnings:
                f.write(w + '\n')
        logger.info(f"Written {len(warnings)} entropy warnings to {log_path}")
    else:
        logger.info("No NaN/Inf entropy warnings detected.")

def main():
    process_trajectories()

if __name__ == '__main__':
    main()