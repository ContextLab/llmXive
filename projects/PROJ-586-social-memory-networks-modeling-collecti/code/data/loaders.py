"""
Dataset loaders for Social Memory Networks.
Provides interfaces for loading real datasets and managing synthetic data.
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
        raise NotImplementedError

def get_dataset(dataset_name: str) -> pd.DataFrame:
    """
    Get a dataset by name.
    
    Currently only synthetic datasets are supported as per spec requirements.
    Real datasets (Hanabi, CoQA) are not available via verified URLs.
    """
    if dataset_name == "synthetic_games":
        return generate_all_datasets()["games"]
    raise ValueError(f"Unknown dataset: {dataset_name}")

def load_experiment_results(filepath: str) -> List[Dict[str, Any]]:
    """Load experiment results from a CSV file."""
    df = pd.read_csv(filepath)
    return df.to_dict(orient="records")

def save_experiment_results(records: List[Dict[str, Any]], filepath: str):
    """Save experiment results to a CSV file."""
    df = pd.DataFrame(records)
    df.to_csv(filepath, index=False)

def get_dataset_spec() -> Dict[str, Any]:
    """Get the specification for available datasets."""
    return {
        "synthetic_games": {
            "description": "Synthetic game data for social memory experiments",
            "num_games": 1000,
            "fields": ["game_id", "agent_actions", "memory_states", "outcomes"]
        }
    }

def generate_all_datasets(output_dir: str = "data"):
    """
    Generate all synthetic datasets needed for the experiment.
    
    This is the primary data source as real datasets are unavailable.
    """
    from .synthetic import generate_all_datasets as gen_all
    return gen_all(output_dir)
