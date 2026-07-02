"""
Dataset loaders for social memory network experiments.
"""
import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from .synthetic import generate_all_datasets

class DatasetLoader:
    """Base class for dataset loaders."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self, dataset_name: str) -> pd.DataFrame:
        """Load a dataset by name."""
        raise NotImplementedError("Subclasses must implement load()")
    
    def save(self, data: pd.DataFrame, dataset_name: str):
        """Save a dataset by name."""
        raise NotImplementedError("Subclasses must implement save()")

def get_dataset(
    dataset_name: str,
    num_games: int = 1000,
    num_agents: int = 5,
    context_condition: str = "full",
    seed: int = 42,
    threshold: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get a dataset by name.
    
    Currently only synthetic datasets are supported as per spec (Hanabi/CoQA URLs unavailable).
    
    Args:
        dataset_name: Name of the dataset ("synthetic")
        num_games: Number of games to generate
        num_agents: Number of agents
        context_condition: "full" or "limited"
        seed: Random seed
        threshold: Token threshold for limited context
    
    Returns:
        List of game dictionaries
    """
    if dataset_name == "synthetic":
        return generate_all_datasets(
            num_games=num_games,
            num_agents=num_agents,
            context_condition=context_condition,
            seed=seed,
            threshold=threshold
        )
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}. Only 'synthetic' is supported.")

def load_experiment_results(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load experiment results from a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        DataFrame with experiment results
    """
    return pd.read_csv(file_path)

def save_experiment_results(
    results: List[Dict[str, Any]],
    file_path: Union[str, Path]
):
    """
    Save experiment results to a CSV file.
    
    Args:
        results: List of result dictionaries
        file_path: Path to save the CSV file
    """
    df = pd.DataFrame(results)
    df.to_csv(file_path, index=False)

def get_dataset_spec(dataset_name: str) -> Dict[str, Any]:
    """
    Get the specification for a dataset.
    
    Args:
        dataset_name: Name of the dataset
    
    Returns:
        Dictionary with dataset specification
    """
    if dataset_name == "synthetic":
        return {
            "name": "synthetic",
            "description": "Synthetic game data for social memory experiments",
            "fields": ["game_id", "facts", "memory_traces", "context_condition"],
            "num_games": 1000,
            "num_agents": 5,
            "context_conditions": ["full", "limited"]
        }
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

def generate_all_datasets(
    num_games: int,
    num_agents: int,
    context_condition: str,
    seed: int,
    threshold: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate all synthetic datasets needed for the experiment.
    
    Args:
        num_games: Number of games to generate
        num_agents: Number of agents
        context_condition: "full" or "limited"
        seed: Random seed
        threshold: Token threshold for limited context
    
    Returns:
        List of generated game dictionaries
    """
    from data.synthetic import generate_synthetic_games
    return generate_synthetic_games(
        num_games=num_games,
        num_agents=num_agents,
        context_condition=context_condition,
        seed=seed,
        threshold=threshold
    )
