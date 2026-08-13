"""
Synthesize the hypernetwork baseline adapter for known composite tasks.

This script implements the primary baseline for SC-001 by performing linear
interpolation of the top-k skills for known composite tasks (generated in T022g).
It uses the interpolation logic from T022a (strategies.py) to generate baseline
adapters.

Output: artifacts/baseline_adapter.pt
"""
import os
import sys
import logging
import torch
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.config import get_artifacts_path, get_data_path, ensure_directories
from src.retrieval.strategies import (
    load_skill_index,
    unweighted_mean,
    cosine_weighted_average
)
import numpy as np
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_known_composites_pairs(pairs_path: Path) -> List[Dict[str, Any]]:
    """Load the known composite task pairs from YAML."""
    if not pairs_path.exists():
        raise FileNotFoundError(f"Pairs file not found: {pairs_path}")

    with open(pairs_path, 'r') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        raise ValueError("Expected pairs file to contain a list of task pairs")

    return data


def load_true_weights(weights_path: Path) -> Dict[str, np.ndarray]:
    """Load the true composite weights from NPZ file."""
    if not weights_path.exists():
        raise FileNotFoundError(f"True weights file not found: {weights_path}")

    data = np.load(weights_path, allow_pickle=True)
    # Convert numpy arrays to dict for easier handling
    weights_dict = {}
    for key in data.files:
        weights_dict[key] = data[key]
    return weights_dict


def synthesize_baseline_adapter(
    skill_index: Dict[str, np.ndarray],
    composite_pairs: List[Dict[str, Any]],
    true_weights: Dict[str, np.ndarray],
    k: int = 3
) -> Tuple[Dict[str, np.ndarray], Dict[str, float]]:
    """
    Synthesize baseline adapters for all composite tasks using interpolation.

    For each composite task, we:
    1. Retrieve the top-k skills based on the task description
    2. Apply the same interpolation logic used in T022a
    3. Compare against the true weights to verify consistency

    Returns:
        synthesized_adapters: Dict mapping task_id to (A, B) matrices
        metrics: Dict of reconstruction errors for verification
    """
    synthesized_adapters = {}
    metrics = {}

    for pair in composite_pairs:
        task_id = pair.get('task_id')
        if not task_id:
            logger.warning(f"Skipping pair without task_id: {pair}")
            continue

        # Get the skill IDs for this composite task
        skill_ids = pair.get('skill_ids', [])
        if len(skill_ids) < k:
            logger.warning(f"Task {task_id} has only {len(skill_ids)} skills, using all")
            k_actual = len(skill_ids)
        else:
            k_actual = k

        # Get the skill vectors from the index
        skill_vectors = []
        for skill_id in skill_ids[:k_actual]:
            if skill_id in skill_index:
                skill_vectors.append(skill_index[skill_id])
            else:
                logger.warning(f"Skill {skill_id} not found in index, skipping")

        if not skill_vectors:
            logger.error(f"No valid skills found for task {task_id}")
            continue

        # Use unweighted mean as the baseline interpolation strategy
        # This matches the "original mechanism's logic" for the primary baseline
        synthesized_vector = unweighted_mean(skill_vectors)

        # Reconstruct A and B matrices from the synthesized vector
        # We need to know the original dimensions - get from first skill
        if skill_vectors:
            first_vector = skill_vectors[0]
            # Assuming the vector was flattened from (in_features, out_features)
            # We need to recover these dimensions
            # For now, we'll assume a standard size or extract from metadata
            # Since we don't have metadata here, we'll use a heuristic
            total_size = len(first_vector)
            # Common LoRA dimensions: in_features=4096, out_features=1024
            # Total = 4096 * 1024 = 4,194,304
            # We'll try to infer from the true weights if available
            if task_id in true_weights:
                # Extract dimensions from true weights
                if 'A' in true_weights[task_id] and 'B' in true_weights[task_id]:
                    A_true = true_weights[task_id]['A']
                    B_true = true_weights[task_id]['B']
                    in_features = A_true.shape[1]
                    out_features = A_true.shape[0]
                    expected_size = in_features * out_features * 2  # A and B combined

                    # Verify size matches
                    if len(synthesized_vector) == expected_size:
                        # Split into A and B
                        A_size = in_features * out_features
                        A_synth = synthesized_vector[:A_size].reshape(out_features, in_features)
                        B_synth = synthesized_vector[A_size:].reshape(out_features, in_features)

                        synthesized_adapters[task_id] = {
                            'A': A_synth,
                            'B': B_synth
                        }

                        # Calculate reconstruction error for verification
                        A_error = np.linalg.norm(A_synth - A_true) / np.linalg.norm(A_true)
                        B_error = np.linalg.norm(B_synth - B_true) / np.linalg.norm(B_true)
                        metrics[task_id] = {
                            'A_error': float(A_error),
                            'B_error': float(B_error),
                            'total_error': float(A_error + B_error)
                        }
                    else:
                        logger.error(f"Size mismatch for {task_id}: expected {expected_size}, got {len(synthesized_vector)}")
                else:
                    logger.error(f"True weights for {task_id} missing A or B matrices")
            else:
                logger.warning(f"No true weights for {task_id}, cannot verify dimensions")

    return synthesized_adapters, metrics


def save_baseline_adapter(
    adapters: Dict[str, np.ndarray],
    output_path: Path
) -> None:
    """Save the synthesized baseline adapter as a PyTorch checkpoint."""
    if not adapters:
        raise ValueError("No adapters to save")

    # Convert to PyTorch tensors
    adapter_tensors = {}
    for task_id, matrices in adapters.items():
        adapter_tensors[task_id] = {
            'A': torch.tensor(matrices['A'], dtype=torch.float32),
            'B': torch.tensor(matrices['B'], dtype=torch.float32)
        }

    # Save as .pt file
    torch.save(adapter_tensors, output_path)
    logger.info(f"Saved baseline adapter to {output_path}")


def main():
    """Main entry point for baseline synthesis."""
    logger.info("Starting baseline adapter synthesis for known composite tasks")

    # Ensure directories exist
    artifacts_path = get_artifacts_path()
    data_path = get_data_path()
    ensure_directories([artifacts_path])

    # Define paths
    pairs_path = data_path / 'processed' / 'known_composites_pairs.yaml'
    true_weights_path = data_path / 'processed' / 'known_composites_true_weights.npz'
    skill_index_path = data_path / 'processed' / 'skill_index.npz'
    output_path = artifacts_path / 'baseline_adapter.pt'

    # Load inputs
    logger.info(f"Loading skill index from {skill_index_path}")
    skill_index_data = np.load(skill_index_path, allow_pickle=True)
    skill_index = {}
    for key in skill_index_data.files:
        skill_index[key] = skill_index_data[key]

    logger.info(f"Loading composite pairs from {pairs_path}")
    composite_pairs = load_known_composites_pairs(pairs_path)

    logger.info(f"Loading true weights from {true_weights_path}")
    true_weights = load_true_weights(true_weights_path)

    # Synthesize baseline
    logger.info("Synthesizing baseline adapters using unweighted mean interpolation")
    synthesized_adapters, metrics = synthesize_baseline_adapter(
        skill_index=skill_index,
        composite_pairs=composite_pairs,
        true_weights=true_weights,
        k=3  # Default k value
    )

    if not synthesized_adapters:
        logger.error("Failed to synthesize any baseline adapters")
        sys.exit(1)

    # Save results
    logger.info(f"Saving baseline adapter to {output_path}")
    save_baseline_adapter(synthesized_adapters, output_path)

    # Log metrics
    if metrics:
        logger.info("Reconstruction error metrics:")
        for task_id, metric in metrics.items():
            logger.info(f"  {task_id}: A_error={metric['A_error']:.6f}, B_error={metric['B_error']:.6f}")

    logger.info("Baseline adapter synthesis completed successfully")
    logger.info(f"This is the primary baseline for SC-001, synthesized via the original mechanism's logic")

    return 0


if __name__ == '__main__':
    sys.exit(main())