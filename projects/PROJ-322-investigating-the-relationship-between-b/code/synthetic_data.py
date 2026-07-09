"""
Synthetic Data Generator for Methodology Validation Mode.

This module generates realistic synthetic fMRI connectivity data and associated
behavioral/cognitive metrics to validate the research pipeline (US1-US3)
without requiring immediate access to large external datasets.

When `is_methodology_validation_mode()` is True (see config.py), this generator
produces data that mimics the statistical properties of real mTBI recovery data,
including:
- Longitudinal time points (Acute vs Chronic)
- Correlated graph metrics (Efficiency, Modularity)
- Cognitive scores that correlate with network reconfiguration
- Subject-level variability

All generation is seeded for reproducibility.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

# Import from project API surface
from config import (
    is_methodology_validation_mode,
    get_config,
    is_synthetic
)
from logging_config import get_logger

# Ensure logger is available
logger = get_logger(__name__)


def _seed_random(seed: int = 42) -> None:
    """Initialize random state for reproducibility."""
    np.random.seed(seed)
    logger.info(f"Synthetic data generator seeded with {seed}")


def generate_connectivity_matrix(
    n_nodes: int = 90,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a synthetic functional connectivity matrix.

    Simulates a correlation matrix for a brain network (e.g., AAL atlas 90 regions).
    Values are bounded [-1, 1] and symmetric.

    Args:
        n_nodes: Number of brain regions (default 90 for AAL).
        seed: Optional seed for this specific matrix.

    Returns:
        Symmetric correlation matrix (n_nodes x n_nodes).
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate random correlations with some structure
    # Create a base correlation structure to ensure positive semi-definiteness
    # by generating random vectors and computing correlations
    X = np.random.randn(n_nodes, 50)  # 50 time points
    corr_matrix = np.corrcoef(X)

    # Handle potential NaNs if perfect correlation occurs
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

    # Ensure symmetry
    corr_matrix = (corr_matrix + corr_matrix.T) / 2
    np.fill_diagonal(corr_matrix, 1.0)

    return corr_matrix


def generate_graph_metrics(
    conn_matrix: np.ndarray,
    threshold: float = 0.2
) -> Dict[str, float]:
    """
    Compute synthetic graph metrics from a connectivity matrix.

    Applies a simple thresholding and computes Global Efficiency, Local Efficiency,
    and Modularity (Q).

    Args:
        conn_matrix: Connectivity matrix.
        threshold: Correlation threshold for binarization.

    Returns:
        Dictionary with 'global_efficiency', 'local_efficiency', 'modularity'.
    """
    import networkx as nx

    # Binarize
    adj = (np.abs(conn_matrix) > threshold).astype(float)
    np.fill_diagonal(adj, 0)

    G = nx.Graph(adj)

    # Handle disconnected components gracefully
    if nx.is_connected(G):
        global_eff = nx.global_efficiency(G)
        local_eff = nx.local_efficiency(G)
        try:
            modularity = nx.community.modularity(G, nx.community.louvain_communities(G))
        except:
            modularity = 0.1
    else:
        # Fallback for disconnected graphs
        global_eff = 0.0
        local_eff = 0.0
        modularity = 0.0

    return {
        "global_efficiency": float(global_eff),
        "local_efficiency": float(local_eff),
        "modularity": float(modularity)
    }


def generate_subject_data(
    subject_id: str,
    time_point: str,
    is_tbi: bool = True,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate data for a single subject at a specific time point.

    Simulates the relationship between network reconfiguration and recovery.
    TBI subjects show lower efficiency acutely, which improves chronically.
    Control subjects remain stable.

    Args:
        subject_id: Unique subject identifier.
        time_point: 'acute' or 'chronic'.
        is_tbi: Whether the subject has mTBI.
        seed: Seed for this subject's generation.

    Returns:
        Dictionary containing subject data.
    """
    if seed is not None:
        np.random.seed(seed)

    base_efficiency = 0.45
    base_modularity = 0.35

    # Effect of injury and time
    if is_tbi:
        if time_point == 'acute':
            # Lower efficiency, higher modularity (segregation) acutely
            eff_drift = -0.05
            mod_drift = 0.05
        else:
            # Recovery: efficiency increases, modularity normalizes
            eff_drift = -0.02
            mod_drift = 0.02
    else:
        # Controls: stable
        eff_drift = 0.0
        mod_drift = 0.0

    # Add noise
    global_eff = base_efficiency + eff_drift + np.random.normal(0, 0.02)
    local_eff = base_efficiency * 0.9 + eff_drift + np.random.normal(0, 0.02)
    modularity = base_modularity + mod_drift + np.random.normal(0, 0.02)

    # Clamp values
    global_eff = np.clip(global_eff, 0.1, 0.9)
    local_eff = np.clip(local_eff, 0.1, 0.9)
    modularity = np.clip(modularity, 0.0, 0.8)

    # Cognitive score: correlated with efficiency
    # Higher efficiency -> higher cognitive score (0-100 scale)
    cognitive_score = 50 + (global_eff - 0.4) * 100 + np.random.normal(0, 5)
    cognitive_score = np.clip(cognitive_score, 20, 100)

    # Generate a synthetic connectivity matrix for this subject
    conn_matrix = generate_connectivity_matrix(seed=seed)

    return {
        "subject_id": subject_id,
        "time_point": time_point,
        "is_tbi": is_tbi,
        "global_efficiency": global_eff,
        "local_efficiency": local_eff,
        "modularity": modularity,
        "cognitive_score": cognitive_score,
        "connectivity_matrix": conn_matrix.tolist()
    }


def generate_dataset(
    n_subjects: int = 40,
    n_tbi: int = 20,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Generate a full synthetic dataset for the study.

    Creates paired longitudinal data (acute, chronic) for TBI and control subjects.

    Args:
        n_subjects: Total number of subjects.
        n_tbi: Number of TBI subjects (rest are controls).
        seed: Global seed.
        output_dir: Directory to save CSV and JSON files.

    Returns:
        Tuple of (DataFrame of metrics, List of full subject records).
    """
    _seed_random(seed)
    logger.info(f"Generating synthetic dataset: {n_subjects} subjects ({n_tbi} TBI)")

    subjects = []
    records = []

    # Generate TBI subjects
    for i in range(n_tbi):
        sid = f"sub-TBI-{i:03d}"
        # Acute
        data_acute = generate_subject_data(sid, "acute", is_tbi=True, seed=seed + i)
        subjects.append(data_acute)
        records.append({
            "subject_id": sid,
            "time_point": "acute",
            "group": "TBI",
            **{k: v for k, v in data_acute.items() if k != "connectivity_matrix"}
        })
        # Chronic
        data_chronic = generate_subject_data(sid, "chronic", is_tbi=True, seed=seed + n_tbi + i)
        subjects.append(data_chronic)
        records.append({
            "subject_id": sid,
            "time_point": "chronic",
            "group": "TBI",
            **{k: v for k, v in data_chronic.items() if k != "connectivity_matrix"}
        })

    # Generate Control subjects
    n_control = n_subjects - n_tbi
    for i in range(n_control):
        sid = f"sub-CTL-{i:03d}"
        # Acute
        data_acute = generate_subject_data(sid, "acute", is_tbi=False, seed=seed + n_subjects + i)
        subjects.append(data_acute)
        records.append({
            "subject_id": sid,
            "time_point": "acute",
            "group": "Control",
            **{k: v for k, v in data_acute.items() if k != "connectivity_matrix"}
        })
        # Chronic
        data_chronic = generate_subject_data(sid, "chronic", is_tbi=False, seed=seed + 2*n_subjects + i)
        subjects.append(data_chronic)
        records.append({
            "subject_id": sid,
            "time_point": "chronic",
            "group": "Control",
            **{k: v for k, v in data_chronic.items() if k != "connectivity_matrix"}
        })

    df = pd.DataFrame(records)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save CSV (metrics only)
        csv_path = output_dir / "synthetic_metrics.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved synthetic metrics to {csv_path}")

        # Save JSON (includes connectivity matrices)
        json_path = output_dir / "synthetic_full_data.json"
        with open(json_path, 'w') as f:
            json.dump(subjects, f, indent=2)
        logger.info(f"Saved full synthetic data to {json_path}")

    return df, subjects


def run_generator() -> None:
    """
    Entry point to generate synthetic data if in validation mode.
    Checks config and generates data if appropriate.
    """
    if not is_methodology_validation_mode() and not is_synthetic():
        logger.info("Methodology Validation Mode not active. Skipping synthetic data generation.")
        return

    logger.info("Methodology Validation Mode detected. Generating synthetic data.")

    # Default output location as per project structure
    output_dir = Path("data/processed")

    try:
        df, subjects = generate_dataset(
            n_subjects=40,
            n_tbi=20,
            seed=42,
            output_dir=output_dir
        )
        logger.info(f"Successfully generated synthetic data with {len(df)} records.")
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        raise


if __name__ == "__main__":
    run_generator()
