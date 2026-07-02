"""
Synthetic dataset generation for social memory network experiments.

This module generates realistic synthetic game data for testing and validation.
Per spec FR-004, synthetic data is used as real datasets (Hanabi/CoQA) are unavailable.
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
    num_agents: int = 5
    context_condition: str = "full"
    seed: int = 42
    threshold: Optional[int] = None
    min_facts: int = 10
    max_facts: int = 50
    domains: List[str] = None

def generate_synthetic_games(
    num_games: int,
    num_agents: int,
    context_condition: str,
    seed: int,
    threshold: Optional[int] = None,
    min_facts: int = 10,
    max_facts: int = 50,
    domains: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for social memory experiments.
    
    Args:
        num_games: Number of games to generate
        num_agents: Number of agents in each game
        context_condition: "full" or "limited"
        seed: Random seed for reproducibility
        threshold: Token threshold for limited context (optional)
        min_facts: Minimum number of facts per game
        max_facts: Maximum number of facts per game
        domains: List of domain categories (default: standard set)
    
    Returns:
        List of game dictionaries with facts and memory traces
    """
    if domains is None:
        domains = ["science", "history", "art", "technology", "geography"]
    
    np.random.seed(seed)
    
    games = []
    
    for game_id in range(num_games):
        # Generate facts for this game
        num_facts = np.random.randint(min_facts, max_facts + 1)
        facts = []
        
        for i in range(num_facts):
            fact_id = f"fact_{game_id}_{i}"
            domain = np.random.choice(domains)
            fact_content = f"{domain} fact {i} from game {game_id}"
            
            facts.append({
                "id": fact_id,
                "domain": domain,
                "content": fact_content,
                "assigned_agent": np.random.randint(0, num_agents)
            })
        
        # Create memory traces for each agent
        memory_traces = {i: [] for i in range(num_agents)}
        
        # Determine retention rate based on context condition
        if context_condition == "full":
            retention_rate = 0.9
        else:
            # Limited context: lower retention, depends on threshold
            if threshold:
                retention_rate = max(0.3, 0.6 - (threshold / 2000.0))
            else:
                retention_rate = 0.4
            retention_rate = min(retention_rate, 0.5)
        
        # Assign facts to agents' memory
        for fact in facts:
            assigned = fact["assigned_agent"]
            memory_traces[assigned].append(fact)
            
            # Other agents may also remember with some probability
            for other_agent in range(num_agents):
                if other_agent != assigned:
                    if np.random.random() < retention_rate * 0.3:
                        memory_traces[other_agent].append(fact)
        
        games.append({
            "game_id": game_id,
            "facts": facts,
            "memory_traces": memory_traces,
            "context_condition": context_condition,
            "num_agents": num_agents,
            "threshold": threshold
        })
    
    return games

def generate_all_datasets(
    num_games: int,
    num_agents: int,
    context_condition: str,
    seed: int,
    threshold: Optional[int] = None,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate all synthetic datasets and save to disk.
    
    Args:
        num_games: Number of games to generate
        num_agents: Number of agents
        context_condition: "full" or "limited"
        seed: Random seed
        threshold: Token threshold for limited context
        output_dir: Directory to save datasets (optional)
    
    Returns:
        List of generated game dictionaries
    """
    games = generate_synthetic_games(
        num_games=num_games,
        num_agents=num_agents,
        context_condition=context_condition,
        seed=seed,
        threshold=threshold
    )
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save as CSV (simplified representation)
        df_data = []
        for game in games:
            for fact in game["facts"]:
                df_data.append({
                    "game_id": game["game_id"],
                    "fact_id": fact["id"],
                    "domain": fact["domain"],
                    "assigned_agent": fact["assigned_agent"]
                })
        
        df = pd.DataFrame(df_data)
        filename = f"synthetic_{context_condition}_agents{num_agents}.csv"
        df.to_csv(output_path / filename, index=False)
    
    return games