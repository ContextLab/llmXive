"""
Dataset loaders for social memory network experiments.

This module provides dataset loading functionality with synthetic fallback
when real datasets (Hanabi, CoQA) are not programmatically accessible.
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from .synthetic import generate_all_datasets

class DatasetLoader:
    """
    Dataset loader for social memory experiments.
    
    Provides methods to load, generate, and save datasets for experiments.
    """
    
    def __init__(self, dataset_name: str = "synthetic"):
        """
        Initialize dataset loader.
        
        Args:
            dataset_name: Name of dataset to load
        """
        self.dataset_name = dataset_name
        self.dataset = None
    
    def load(self, **kwargs) -> Dict[str, Any]:
        """
        Load dataset.
        
        Args:
            **kwargs: Additional loading parameters
        
        Returns:
            Dataset dictionary
        """
        if self.dataset_name == "synthetic":
            self.dataset = generate_all_datasets(**kwargs)
        else:
            raise ValueError(f"Unsupported dataset: {self.dataset_name}")
        
        return self.dataset

def get_dataset(
    dataset_name: str = "synthetic",
    num_games: int = 1000,
    num_agents: int = 3,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Get dataset by name.
    
    Args:
        dataset_name: Dataset name
        num_games: Number of games
        num_agents: Number of agents
        seed: Random seed
    
    Returns:
        Dataset dictionary
    """
    if dataset_name == "synthetic":
        return generate_all_datasets(
            dataset_name="synthetic",
            num_games=num_games,
            num_agents=num_agents,
            seed=seed
        )
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

def load_experiment_results(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load experiment results from CSV file.
    
    Args:
        filepath: Path to results CSV file
    
    Returns:
        DataFrame with experiment results
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Results file not found: {filepath}")
    
    return pd.read_csv(filepath)

def save_experiment_results(
    df: pd.DataFrame,
    filepath: Union[str, Path]
) -> None:
    """
    Save experiment results to CSV file.
    
    Args:
        df: DataFrame with results
        filepath: Output path
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)

def get_dataset_spec(dataset_name: str = "synthetic") -> Dict[str, Any]:
    """
    Get dataset specification.
    
    Args:
        dataset_name: Dataset name
    
    Returns:
        Dataset specification dictionary
    """
    if dataset_name == "synthetic":
        return {
            "name": "synthetic",
            "description": "Synthetic game data for social memory experiments",
            "fields": ["game_id", "items", "agent_items", "turns"],
            "num_games": 1000,
            "num_agents": 3,
            "num_items": 20,
            "num_turns": 10
        }
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

def generate_all_datasets(
    dataset_name: str = "synthetic",
    num_games: int = 1000,
    num_agents: int = 3,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generate all datasets needed for experiments.
    
    Args:
        dataset_name: Dataset name
        num_games: Number of games
        num_agents: Number of agents
        seed: Random seed
    
    Returns:
        Dictionary with all generated datasets
    """
    return generate_all_datasets(
        dataset_name=dataset_name,
        num_games=num_games,
        num_agents=num_agents,
        seed=seed
    )

if __name__ == "__main__":
    # Test loader
    loader = DatasetLoader("synthetic")
    dataset = loader.load(num_games=10)
    print(f"Loaded {len(dataset['games'])} games")