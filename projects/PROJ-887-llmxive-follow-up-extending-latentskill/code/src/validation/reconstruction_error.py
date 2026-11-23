"""
Reconstruction Error Analysis (T022d)

Calculates cosine distance (reconstruction error) between synthesized LoRA weights
and true composite weights. Outputs mean/max error and validity flag.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_project_paths

logger = logging.getLogger(__name__)

def load_npz_safe(path: Path) -> Dict[str, np.ndarray]:
    """Load an npz file and return as a dictionary of arrays."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    data = np.load(path, allow_pickle=True)
    return dict(data)

def cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine distance between two vectors.
    Distance = 1 - cosine_similarity
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 1.0  # Maximum distance if either is zero vector
    
    cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
    # Clip to avoid numerical errors outside [-1, 1]
    cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
    return float(1.0 - cosine_sim)

def calculate_reconstruction_errors(
    synthesized_path: Path,
    ground_truth_path: Path
) -> Tuple[float, float, List[float]]:
    """
    Calculate reconstruction error between synthesized and ground truth weights.
    
    Args:
        synthesized_path: Path to synthesized adapter (from T022b)
        ground_truth_path: Path to ground truth composite adapter (from T022c)
        
    Returns:
        Tuple of (mean_error, max_error, list_of_individual_errors)
    """
    logger.info(f"Loading synthesized weights from: {synthesized_path}")
    syn_data = load_npz_safe(synthesized_path)
    
    logger.info(f"Loading ground truth weights from: {ground_truth_path}")
    gt_data = load_npz_safe(ground_truth_path)
    
    # Validate that both files have the same keys (A and B matrices)
    syn_keys = set(syn_data.keys())
    gt_keys = set(gt_data.keys())
    
    if syn_keys != gt_keys:
        raise ValueError(
            f"Key mismatch between synthesized and ground truth. "
            f"Synthesized: {syn_keys}, Ground Truth: {gt_keys}"
        )
    
    errors = []
    
    for key in syn_keys:
        syn_vec = syn_data[key]
        gt_vec = gt_data[key]
        
        # Ensure same shape
        if syn_vec.shape != gt_vec.shape:
            raise ValueError(
                f"Shape mismatch for key '{key}': "
                f"synthesized {syn_vec.shape} vs ground truth {gt_vec.shape}"
            )
        
        # Flatten for cosine distance calculation
        syn_flat = syn_vec.flatten().astype(np.float64)
        gt_flat = gt_vec.flatten().astype(np.float64)
        
        err = cosine_distance(syn_flat, gt_flat)
        errors.append(err)
        logger.debug(f"Error for {key}: {err:.6f}")
    
    mean_error = float(np.mean(errors))
    max_error = float(np.max(errors))
    
    return mean_error, max_error, errors

def save_results(
    output_path: Path,
    mean_error: float,
    max_error: float,
    individual_errors: List[float],
    validity_flag: bool,
    metadata: Dict[str, Any]
) -> None:
    """Save results to JSON file."""
    result = {
        "mean_error": mean_error,
        "max_error": max_error,
        "individual_errors": individual_errors,
        "validity_flag": validity_flag,
        "threshold": 0.05,
        "metadata": metadata
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to: {output_path}")

def main() -> None:
    """
    Main entry point for T022d.
    
    Computes reconstruction error between synthesized adapters (T022b)
    and ground truth composites (T022c).
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    paths = get_project_paths()
    
    # Define paths based on task dependencies
    # T022b outputs synthesized adapters to artifacts/synthesized_adapters/
    # T022c outputs ground truth to data/processed/composite_ground_truth.npz
    # We need to match specific pairs. For this task, we assume a specific
    # composite task was generated and has a corresponding synthesized version.
    
    # The task description implies comparing synthesized weights against
    # the true weights of a known composite task.
    # Since T022c generates composite_ground_truth.npz, we need to find
    # the corresponding synthesized adapter.
    
    # For the held-out set, we need to iterate through pairs.
    # However, T022d specifically mentions "the held-out set" and outputting
    # mean/max error. We'll assume the ground truth file contains multiple
    # composites or we process a single pair as defined in the pipeline.
    
    # Based on the task flow:
    # 1. T022c generates composite_ground_truth.npz (single composite or multiple)
    # 2. T022b generates synthesized adapters for various queries
    # 3. We need to match the synthesized adapter for the composite task
    
    # For simplicity and correctness, we assume the pipeline has generated
    # a synthesized adapter for the composite task created in T022c.
    # Let's look for a synthesized adapter that matches the composite task.
    
    # The composite task ID is likely derived from the pair.
    # We'll check for a synthesized adapter in artifacts/synthesized_adapters/
    # that corresponds to the composite task.
    
    # Since T022c creates composite_ground_truth.npz, we'll load it and
    # assume the corresponding synthesized adapter is named consistently.
    
    ground_truth_path = paths["data_processed"] / "composite_ground_truth.npz"
    
    if not ground_truth_path.exists():
        raise FileNotFoundError(
            f"Ground truth file not found: {ground_truth_path}. "
            "Ensure T022c has been executed successfully."
        )
    
    # Load ground truth to get the composite task ID
    gt_data = load_npz_safe(ground_truth_path)
    # Assuming the metadata or keys contain the task ID
    # If not, we might need to infer from the file structure
    
    # For this implementation, we'll assume the synthesized adapter
    # is named 'composite_adapter.npz' in the synthesized_adapters folder
    # or we need to find the matching one.
    
    # Let's look for synthesized adapters
    synthesized_dir = paths["artifacts"] / "synthesized_adapters"
    if not synthesized_dir.exists():
        raise FileNotFoundError(
            f"Synthesized adapters directory not found: {synthesized_dir}. "
            "Ensure T022b has been executed."
        )
    
    # Find the synthesized adapter that corresponds to the composite task
    # We'll assume there's a file named 'composite_task_adapter.npz' or similar
    # If the ground truth contains multiple composites, we need to handle that.
    
    # For now, let's assume a single composite was generated in T022c
    # and we need to find its synthesized version.
    
    # Check for files in synthesized_dir
    synthesized_files = list(synthesized_dir.glob("*.npz"))
    if not synthesized_files:
        raise FileNotFoundError(
            f"No synthesized adapters found in {synthesized_dir}. "
            "Ensure T022b has generated adapters."
        )
    
    # We need to match the ground truth composite with a synthesized adapter.
    # Since the task description is slightly ambiguous about the exact pairing,
    # we'll assume the first synthesized adapter corresponds to the composite
    # task if there's only one, or we need metadata to match them.
    
    # For robustness, let's check if the ground truth file has metadata
    # that indicates the task ID, and match it with synthesized files.
    
    # If no metadata, we'll process all synthesized adapters against the
    # ground truth and report aggregate statistics.
    
    # However, the task says "between the synthesized LoRA weights ... and 
    # the true weights of a known composite task". This implies a 1:1 match.
    
    # Let's assume the composite task ID is stored in the ground truth file
    # or we can infer it. For now, we'll process the first synthesized adapter
    # against the ground truth if there's only one composite.
    
    # Actually, looking at T022c, it generates composite_ground_truth.npz
    # which might contain multiple composites. But the task T022d mentions
    # "the held-out set", implying we might need to process multiple.
    
    # Let's re-read the task: "calculate the cosine distance ... between the 
    # synthesized LoRA weights (from T022b serialization) and the true weights 
    # of a known composite task (from T022c)."
    
    # It seems we need to compare each synthesized adapter (for a composite task)
    # with its corresponding ground truth.
    
    # Since T022c generates pairs.yaml, we can use that to know which composites
    # to expect. But for simplicity, let's assume the ground truth file contains
    # the composite adapter(s) and we need to find the synthesized version.
    
    # For this implementation, we'll:
    # 1. Load ground truth composites
    # 2. Load synthesized adapters
    # 3. Match them (by name or order)
    # 4. Calculate errors
    
    # If there's a mismatch, we'll raise an error.
    
    # Let's assume the composite task ID is embedded in the filename or metadata.
    # We'll try to match based on the composite task ID from pairs.yaml if available.
    
    pairs_path = paths["data_processed"] / "pairs.yaml"
    composite_task_ids = []
    
    if pairs_path.exists():
        import yaml
        with open(pairs_path, 'r') as f:
            pairs_data = yaml.safe_load(f)
            if isinstance(pairs_data, list):
                for pair in pairs_data:
                    if 'composite_task_id' in pair:
                        composite_task_ids.append(pair['composite_task_id'])
    
    # Now, find synthesized adapters for these task IDs
    errors_all = []
    
    for task_id in composite_task_ids:
        # Look for synthesized adapter with this task ID
        # Assuming naming convention: {task_id}_adapter.npz or similar
        found_syn = None
        for syn_file in synthesized_files:
            if task_id in syn_file.name or syn_file.name.startswith(task_id):
                found_syn = syn_file
                break
        
        if not found_syn:
            logger.warning(f"No synthesized adapter found for task {task_id}. Skipping.")
            continue
        
        try:
            mean_err, max_err, indiv_errs = calculate_reconstruction_errors(
                found_syn, ground_truth_path
            )
            errors_all.extend(indiv_errs)
            logger.info(f"Task {task_id}: Mean={mean_err:.4f}, Max={max_err:.4f}")
        except Exception as e:
            logger.error(f"Error processing {task_id}: {e}")
            raise
    
    if not errors_all:
        raise ValueError("No errors calculated. Ensure synthesized adapters match ground truth composites.")
    
    # Calculate aggregate statistics
    overall_mean = float(np.mean(errors_all))
    overall_max = float(np.max(errors_all))
    
    # Apply validity flag rule: if ANY error > 0.05, flag is False
    validity_flag = overall_max <= 0.05
    
    # Prepare metadata
    metadata = {
        "source": "T022d Reconstruction Error Analysis",
        "threshold": 0.05,
        "num_errors_analyzed": len(errors_all),
        "ground_truth_file": str(ground_truth_path),
        "synthesized_dir": str(synthesized_dir),
        "composite_task_ids": composite_task_ids
    }
    
    # Save results
    output_path = paths["data_results"] / "reconstruction_error.json"
    save_results(
        output_path,
        overall_mean,
        overall_max,
        errors_all,
        validity_flag,
        metadata
    )
    
    # Log summary
    logger.info("=" * 50)
    logger.info("RECONSTRUCTION ERROR SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Mean Error: {overall_mean:.6f}")
    logger.info(f"Max Error: {overall_max:.6f}")
    logger.info(f"Validity Flag: {validity_flag}")
    logger.info(f"Threshold: 0.05")
    if not validity_flag:
        logger.warning("MAX ERROR EXCEEDS THRESHOLD! Validity flag is False.")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
