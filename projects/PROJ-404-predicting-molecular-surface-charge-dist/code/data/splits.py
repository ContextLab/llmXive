"""
Scaffolding and split generation utilities.
"""
import os
import json
import random
from typing import Dict, List, Optional
import logging

from utils import get_logger

logger = get_logger(__name__)

def generate_default_splits() -> Dict[str, List[int]]:
    """
    Generates default train/val/test split indices.
    """
    # Placeholder: return empty lists
    return {"train": [], "val": [], "test": []}

def save_split_indices(indices: Dict[str, List[int]], path: str):
    """
    Saves split indices to a JSON file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(indices, f)
    logger.info(f"Saved split indices to {path}")

def get_split_indices(path: str) -> Dict[str, List[int]]:
    """
    Loads split indices from a JSON file.
    """
    if not os.path.exists(path):
        logger.warning(f"Split file {path} not found. Generating defaults.")
        return generate_default_splits()
    
    with open(path, 'r') as f:
        return json.load(f)

def apply_scaffold_split(data_iterator, split_indices: Dict[str, List[int]], split_name: str):
    """
    Applies scaffold split to a data iterator.
    """
    # Placeholder logic
    return data_iterator
