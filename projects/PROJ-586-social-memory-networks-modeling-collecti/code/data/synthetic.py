"""Synthetic data generation utilities for testing pipeline structure.

WARNING: This module is intended ONLY for structural testing when real data
sources are unavailable. The generated data is explicitly marked as synthetic
and must NOT be used for research conclusions or publication.

Per FR-011, synthetic data generation is a FALLBACK mechanism only.
The primary data sources must be real, programmatically accessible datasets.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import csv


@dataclass
class SyntheticDatasetSpec:
    """Specification for generating a synthetic dataset."""
    name: str
    num_records: int
    agent_counts: List[int]
    context_conditions: List[str]
    seed: int = 42


def generate_synthetic_dataset(spec: Optional[SyntheticDatasetSpec] = None) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset for structural testing.

    This function creates a minimal dataset that mimics the schema of real
    experiment results. It is designed to test pipeline connectivity, not
    to produce research-grade data.

    Parameters
    ----------
    spec : SyntheticDatasetSpec, optional
        Specification for the synthetic dataset. If None, uses defaults.

    Returns
    -------
    List[Dict[str, Any]]
        A list of synthetic records, each marked with 'is_synthetic': True.

    Raises
    ------
    ValueError
        If the specification is invalid.
    """
    if spec is None:
        spec = SyntheticDatasetSpec(
            name="test_fallback",
            num_records=10,
            agent_counts=[3, 5, 7],
            context_conditions=["full", "limited"],
            seed=42
        )

    if spec.num_records <= 0:
        raise ValueError("num_records must be positive")
    if not spec.agent_counts:
        raise ValueError("agent_counts must not be empty")
    if not spec.context_conditions:
        raise ValueError("context_conditions must not be empty")

    rng = random.Random(spec.seed)
    records = []

    for i in range(spec.num_records):
        record = {
            "game_id": f"synthetic_{spec.name}_{i:04d}",
            "agent_count": rng.choice(spec.agent_counts),
            "context_condition": rng.choice(spec.context_conditions),
            "specialization_index": rng.uniform(0.1, 0.9),
            "retrieval_efficiency": rng.uniform(0.2, 0.95),
            "is_synthetic": True,
            "source": "synthetic_generation",
            "spec_name": spec.name,
            "warning": "DO NOT USE FOR RESEARCH. This is synthetic test data."
        }
        records.append(record)

    return records


def verify_datasets(dataset_path: Path) -> bool:
    """
    Verify that a dataset file exists and has the expected structure.

    Parameters
    ----------
    dataset_path : Path
        Path to the dataset file (CSV or JSON).

    Returns
    -------
    bool
        True if the file exists and has valid structure, False otherwise.
    """
    if not dataset_path.exists():
        return False

    try:
        if dataset_path.suffix == ".csv":
            with dataset_path.open(newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows:
                    return False
                # Check for required fields
                required = {"game_id", "agent_count", "context_condition"}
                if not required.issubset(set(rows[0].keys())):
                    return False
        elif dataset_path.suffix == ".json":
            with dataset_path.open() as f:
                data = json.load(f)
                if not isinstance(data, list) or not data:
                    return False
                required = {"game_id", "agent_count", "context_condition"}
                if not required.issubset(set(data[0].keys())):
                    return False
        else:
            return False

        return True
    except Exception:
        return False


def save_synthetic_dataset(output_path: Path, records: List[Dict[str, Any]]) -> None:
    """
    Save a synthetic dataset to a file.

    Parameters
    ----------
    output_path : Path
        Destination path for the dataset.
    records : List[Dict[str, Any]]
        List of synthetic records to save.

    Raises
    ------
    ValueError
        If records is empty.
    """
    if not records:
        raise ValueError("Cannot save empty dataset")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine format from extension
    if output_path.suffix == ".csv":
        fieldnames = list(records[0].keys())
        with output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
    elif output_path.suffix == ".json":
        with output_path.open("w") as f:
            json.dump(records, f, indent=2, default=str)
    else:
        # Default to CSV
        fieldnames = list(records[0].keys())
        with output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)


def generate_synthetic_cue_response_pairs(
    num_pairs: int = 10,
    agent_count: int = 5,
    context_spans: Optional[List[str]] = None,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate synthetic cue-response pairs as a fallback when explicit cues are missing.

    Per FR-011, this function creates a set of synthetic cue-response pairs
    (minimum 10 per game) from available context spans if explicit cues are missing.
    The generated pairs are marked as synthetic and must not be used for research.

    Parameters
    ----------
    num_pairs : int
        Number of cue-response pairs to generate (minimum 10).
    agent_count : int
        Number of agents in the simulation (used to diversify responses).
    context_spans : List[str], optional
        Available context spans to draw from. If None, uses default spans.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    List[Dict[str, Any]]
        List of synthetic cue-response pairs, each marked with 'is_synthetic': True.

    Raises
    ------
    ValueError
        If num_pairs is less than 10.
    """
    if num_pairs < 10:
        raise ValueError(f"num_pairs must be at least 10, got {num_pairs}")

    if context_spans is None:
        context_spans = [
            "The capital of France is Paris.",
            "Water boils at 100 degrees Celsius at sea level.",
            "The speed of light is approximately 299,792,458 meters per second.",
            "Photosynthesis converts carbon dioxide and water into glucose and oxygen.",
            "The human body has 206 bones in adulthood.",
            "The Earth orbits the Sun in approximately 365.25 days.",
            "DNA stands for deoxyribonucleic acid.",
            "The largest planet in our solar system is Jupiter.",
            "Newton's first law states that an object at rest stays at rest.",
            "The chemical symbol for gold is Au."
        ]

    rng = random.Random(seed)
    pairs = []

    for i in range(num_pairs):
        # Select a context span
        context_span = rng.choice(context_spans)

        # Generate a cue based on the context
        words = context_span.split()
        if len(words) > 3:
            cue_start = rng.randint(0, len(words) - 3)
            cue = " ".join(words[cue_start:cue_start + 2])
        else:
            cue = words[0] if words else "unknown"

        # Generate a response (the full context or a variation)
        response = context_span

        # Assign to a random agent
        agent_id = rng.randint(0, agent_count - 1)

        pair = {
            "cue": cue,
            "response": response,
            "agent_id": agent_id,
            "context_span": context_span,
            "is_synthetic": True,
            "source": "synthetic_fallback",
            "pair_id": f"synthetic_pair_{i:04d}",
            "warning": "DO NOT USE FOR RESEARCH. This is synthetic fallback data."
        }
        pairs.append(pair)

    return pairs