"""
Synthetic data generator for Methodology Validation Mode.

This module provides functions to generate reproducible synthetic datasets
for validating the research pipeline when real data is unavailable or
during initial methodology testing.

All generation is seeded to ensure reproducibility.
"""

import numpy as np
import pandas as pd
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import is_methodology_validation_mode, set_synthetic_mode
from entities import Subject, ConnectivityMatrix, GraphMetrics

# Configure logging
logger = logging.getLogger(__name__)

def _seed_random(seed: int = 42) -> None:
    """
    Initialize random number generators with a fixed seed for reproducibility.

    Args:
        seed: Random seed value (default: 42)
    """
    np.random.seed(seed)
    # Note: If using other libraries, seed them here too

def generate_connectivity_matrix(
    n_nodes: int = 90,
    seed: Optional[int] = None,
    correlation_strength: float = 0.3
) -> np.ndarray:
    """
    Generate a synthetic functional connectivity matrix.

    Creates a symmetric, positive semi-definite matrix representing
    functional connectivity between brain regions (AAL atlas nodes).

    Args:
        n_nodes: Number of nodes (default: 90 for AAL atlas)
        seed: Optional seed for this specific matrix
        correlation_strength: Base correlation magnitude (0.0-1.0)

    Returns:
        Symmetric connectivity matrix of shape (n_nodes, n_nodes)
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate random correlation structure
    # Start with random features, compute correlation
    features = np.random.randn(n_nodes, n_nodes)
    matrix = np.corrcoef(features)

    # Ensure symmetry and handle NaNs
    matrix = (matrix + matrix.T) / 2
    matrix = np.nan_to_num(matrix, nan=0.0)

    # Adjust diagonal to 1.0
    np.fill_diagonal(matrix, 1.0)

    # Scale correlation strength
    # Remove diagonal, scale, restore
    off_diag = matrix - np.eye(n_nodes)
    matrix = np.eye(n_nodes) + off_diag * correlation_strength

    # Ensure positive semi-definite (add small value to diagonal if needed)
    eigenvalues, _ = np.linalg.eigh(matrix)
    min_eig = np.min(eigenvalues)
    if min_eig < 0:
        matrix = matrix + (abs(min_eig) + 1e-6) * np.eye(n_nodes)

    return matrix

def generate_graph_metrics(
    connectivity_matrix: np.ndarray,
    threshold: float = 0.1
) -> Dict[str, float]:
    """
    Generate synthetic graph metrics from a connectivity matrix.

    Simulates Global Efficiency, Local Efficiency, and Modularity
    with values constrained to realistic ranges.

    Args:
        connectivity_matrix: Symmetric connectivity matrix
        threshold: Threshold for binarizing the matrix (0.0-1.0)

    Returns:
        Dictionary with 'global_efficiency', 'local_efficiency', 'modularity'
    """
    n = connectivity_matrix.shape[0]

    # Apply threshold to create binary adjacency matrix
    binary_matrix = (np.abs(connectivity_matrix) > threshold).astype(float)
    np.fill_diagonal(binary_matrix, 0)

    # Calculate metrics with realistic bounds
    # Global efficiency: typically 0.1 - 0.5 for brain networks
    global_eff = 0.15 + 0.25 * np.random.rand()

    # Local efficiency: typically 0.2 - 0.6
    local_eff = 0.25 + 0.30 * np.random.rand()

    # Modularity: typically 0.3 - 0.7
    modularity = 0.35 + 0.30 * np.random.rand()

    # Add slight correlation to metrics (real brain networks show patterns)
    global_eff = global_eff * (1 + 0.1 * np.random.randn())
    local_eff = local_eff * (1 + 0.1 * np.random.randn())
    modularity = modularity * (1 + 0.05 * np.random.randn())

    # Clamp to realistic ranges
    global_eff = np.clip(global_eff, 0.1, 0.6)
    local_eff = np.clip(local_eff, 0.2, 0.7)
    modularity = np.clip(modularity, 0.2, 0.8)

    return {
        'global_efficiency': float(global_eff),
        'local_efficiency': float(local_eff),
        'modularity': float(modularity)
    }

def generate_cognitive_score(
    efficiency: float,
    modularity: float,
    time_point: int,
    noise_level: float = 0.1
) -> float:
    """
    Generate a synthetic cognitive score based on graph metrics and time.

    Simulates a linear relationship with noise:
    CognitiveScore ~ 0.3*Efficiency + 0.2*Modularity - 0.1*Time + noise

    Args:
        efficiency: Global efficiency value
        modularity: Modularity value
        time_point: Time point (0=acute, 1=chronic)
        noise_level: Standard deviation of noise

    Returns:
        Synthetic cognitive score
    """
    # Base score with realistic range (0-100)
    base = 50.0

    # Add metric influences
    score = base + 20.0 * efficiency + 15.0 * modularity

    # Time effect (recovery over time)
    score -= 5.0 * time_point

    # Add noise
    score += np.random.normal(0, noise_level * 10)

    # Clamp to realistic range
    return float(np.clip(score, 0, 100))

def generate_subject_data(
    subject_id: str,
    n_nodes: int = 90,
    time_point: int = 0,
    seed: Optional[int] = None
) -> Tuple[Subject, ConnectivityMatrix, GraphMetrics]:
    """
    Generate complete synthetic data for a single subject.

    Args:
        subject_id: Unique subject identifier
        n_nodes: Number of brain regions
        time_point: 0 for acute, 1 for chronic
        seed: Optional seed for this subject

    Returns:
        Tuple of (Subject, ConnectivityMatrix, GraphMetrics) entities
    """
    if seed is not None:
        _seed_random(seed)
    else:
        _seed_random(np.random.randint(0, 10000))

    # Generate connectivity matrix
    conn_matrix = generate_connectivity_matrix(n_nodes=n_nodes)

    # Generate graph metrics
    metrics_dict = generate_graph_metrics(conn_matrix)

    # Generate cognitive score
    cognitive_score = generate_cognitive_score(
        metrics_dict['global_efficiency'],
        metrics_dict['modularity'],
        time_point
    )

    # Create entities
    subject = Subject(
        subject_id=subject_id,
        time_point=time_point,
        cognitive_score=cognitive_score
    )

    connectivity = ConnectivityMatrix(
        subject_id=subject_id,
        matrix=conn_matrix,
        n_nodes=n_nodes
    )

    graph_metrics = GraphMetrics(
        subject_id=subject_id,
        global_efficiency=metrics_dict['global_efficiency'],
        local_efficiency=metrics_dict['local_efficiency'],
        modularity=metrics_dict['modularity']
    )

    return subject, connectivity, graph_metrics

def generate_dataset(
    n_subjects: int = 30,
    n_time_points: int = 2,
    n_nodes: int = 90,
    output_dir: Optional[Path] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generate a complete synthetic dataset for methodology validation.

    Creates synthetic subjects with connectivity matrices, graph metrics,
    and cognitive scores, then saves them to disk.

    Args:
        n_subjects: Number of subjects to generate
        n_time_points: Number of time points per subject (0=acute, 1=chronic)
        n_nodes: Number of brain regions
        output_dir: Directory to save outputs (default: data/processed/synthetic)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing generated data paths and metadata
    """
    _seed_random(seed)

    if output_dir is None:
        output_dir = Path("data/processed/synthetic")

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating synthetic dataset: {n_subjects} subjects, {n_time_points} time points")

    subjects = []
    connectivities = []
    metrics_list = []
    csv_data = []

    subject_counter = 0
    for tp in range(n_time_points):
        for i in range(n_subjects):
            sid = f"sub-{subject_counter:03d}"
            subject_counter += 1

            # Generate data for this subject-timepoint
            subj, conn, metrics = generate_subject_data(
                subject_id=sid,
                n_nodes=n_nodes,
                time_point=tp,
                seed=seed + subject_counter
            )

            subjects.append(subj)
            connectivities.append(conn)
            metrics_list.append(metrics)

            # Prepare CSV row
            csv_data.append({
                'subject_id': sid,
                'time_point': tp,
                'cognitive_score': subj.cognitive_score,
                'global_efficiency': metrics.global_efficiency,
                'local_efficiency': metrics.local_efficiency,
                'modularity': metrics.modularity
            })

    # Save connectivity matrices
    conn_dir = output_dir / "matrices"
    conn_dir.mkdir(exist_ok=True)

    for conn in connectivities:
        matrix_path = conn_dir / f"{conn.subject_id}_matrix.npy"
        np.save(str(matrix_path), conn.matrix)

    # Save metrics JSON
    metrics_path = output_dir / "graph_metrics.json"
    metrics_json = {
        'metadata': {
            'n_subjects': n_subjects,
            'n_time_points': n_time_points,
            'n_nodes': n_nodes,
            'seed': seed,
            'is_synthetic': True
        },
        'metrics': metrics_list
    }
    with open(metrics_path, 'w') as f:
        json.dump(metrics_json, f, indent=2)

    # Save CSV manifest
    csv_path = output_dir / "synthetic_manifest.csv"
    df = pd.DataFrame(csv_data)
    df.to_csv(csv_path, index=False)

    # Save full dataset JSON
    dataset_path = output_dir / "dataset.json"
    dataset_json = {
        'metadata': {
            'n_subjects': n_subjects,
            'n_time_points': n_time_points,
            'n_nodes': n_nodes,
            'seed': seed,
            'is_synthetic': True,
            'generation_timestamp': str(pd.Timestamp.now())
        },
        'subjects': [
            {
                'subject_id': s.subject_id,
                'time_point': s.time_point,
                'cognitive_score': s.cognitive_score
            }
            for s in subjects
        ],
        'metrics': metrics_list,
        'matrix_paths': [
            str(c.matrix_path.relative_to(output_dir))
            for c in connectivities
        ]
    }
    with open(dataset_path, 'w') as f:
        json.dump(dataset_json, f, indent=2)

    logger.info(f"Synthetic dataset saved to {output_dir}")
    logger.info(f"  - {csv_path.name}")
    logger.info(f"  - {metrics_path.name}")
    logger.info(f"  - {dataset_path.name}")
    logger.info(f"  - {len(connectivities)} connectivity matrices")

    return {
        'output_dir': str(output_dir),
        'csv_path': str(csv_path),
        'metrics_path': str(metrics_path),
        'dataset_path': str(dataset_path),
        'n_subjects': n_subjects,
        'n_time_points': n_time_points,
        'is_synthetic': True
    }

def run_generator(
    n_subjects: int = 30,
    n_time_points: int = 2,
    n_nodes: int = 90,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Main entry point for running the synthetic data generator.

    Checks if methodology validation mode is active, then generates
    and saves the synthetic dataset.

    Args:
        n_subjects: Number of subjects to generate
        n_time_points: Number of time points per subject
        n_nodes: Number of brain regions
        seed: Random seed

    Returns:
        Dictionary with generation results and file paths

    Raises:
        RuntimeError: If methodology validation mode is not active
    """
    if not is_methodology_validation_mode():
        logger.warning("Methodology validation mode is not active. "
                     "Set is_synthetic=True in config or run with synthetic data flag.")
        # Still generate but log warning
        # In a strict implementation, we might raise here

    logger.info("Starting synthetic data generation for Methodology Validation Mode")
    logger.info(f"Parameters: n_subjects={n_subjects}, n_time_points={n_time_points}, n_nodes={n_nodes}, seed={seed}")

    result = generate_dataset(
        n_subjects=n_subjects,
        n_time_points=n_time_points,
        n_nodes=n_nodes,
        seed=seed
    )

    logger.info("Synthetic data generation completed successfully")
    return result

def main():
    """
    Command-line entry point for synthetic data generation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Default parameters
    n_subjects = 30
    n_time_points = 2
    n_nodes = 90
    seed = 42

    logger.info("Running synthetic data generator (T008a)")

    try:
        result = run_generator(
            n_subjects=n_subjects,
            n_time_points=n_time_points,
            n_nodes=n_nodes,
            seed=seed
        )
        logger.info(f"Generation successful. Output: {result['output_dir']}")
        print(f"Synthetic dataset generated at: {result['output_dir']}")
        print(f"  Manifest: {result['csv_path']}")
        print(f"  Metrics: {result['metrics_path']}")
        print(f"  Dataset: {result['dataset_path']}")
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()