"""Synthetic data generation utilities for fallback scenarios only.

This module provides a controlled mechanism for generating synthetic data
when real datasets are unavailable. Per the project constraints, synthetic
data is ONLY used as a fallback and must be clearly marked in outputs.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional


def generate_synthetic_dataset(
    name: str,
    num_records: int = 10,
    agent_counts: Optional[List[int]] = None,
    context_conditions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset for testing and fallback purposes.

    Parameters
    ----------
    name : str
        Name of the dataset (used in record IDs).
    num_records : int
        Number of synthetic records to generate.
    agent_counts : list of int, optional
        Possible agent counts to use. Defaults to [3, 5, 7].
    context_conditions : list of str, optional
        Possible context conditions. Defaults to ["full", "limited"].

    Returns
    -------
    List[Dict[str, Any]]
        A list of synthetic records, each marked with is_synthetic=True.
    """
    if agent_counts is None:
        agent_counts = [3, 5, 7]
    if context_conditions is None:
        context_conditions = ["full", "limited"]

    records = []
    for i in range(num_records):
        record = {
            "game_id": f"synthetic_{name}_{i:04d}",
            "agent_count": random.choice(agent_counts),
            "context_condition": random.choice(context_conditions),
            "specialization_index": round(random.uniform(0.1, 0.9), 4),
            "retrieval_efficiency": round(random.uniform(0.2, 0.95), 4),
            "is_synthetic": True,
            "source": "synthetic_fallback"
        }
        records.append(record)
    
    return records


def verify_datasets() -> bool:
    """Verify that required datasets exist on disk or can be generated.
    
    This function checks for the existence of data files. If they are missing,
    it returns False to signal that synthetic fallback should be considered.
    
    Returns:
        True if real data files exist, False otherwise
    """
    data_dir = Path("data")
    
    if not data_dir.exists():
        return False
    
    # Check for common dataset files
    dataset_files = list(data_dir.glob("*.csv"))
    if not dataset_files:
        return False
    
    return True


def save_synthetic_dataset(
    records: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save a synthetic dataset to a CSV file.

    Parameters
    ----------
    records : list of dict
        The synthetic records to save.
    output_path : Path
        Destination file path.
    """
    if not records:
        raise ValueError("No records to save.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0].keys())
    
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
