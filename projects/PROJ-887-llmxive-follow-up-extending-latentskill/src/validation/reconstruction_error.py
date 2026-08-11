import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_npz_file(file_path: Path) -> Dict[str, np.ndarray]:
    """
    Load a .npz file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the .npz file.
        
    Returns:
        Dictionary containing the arrays stored in the .npz file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is corrupted or empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        data = np.load(str(file_path), allow_pickle=True)
        if len(data.files) == 0:
            raise ValueError(f"File is empty: {file_path}")
        return {key: data[key] for key in data.files}
    except Exception as e:
        raise ValueError(f"Failed to load {file_path}: {e}")

def compute_cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute the cosine distance between two vectors.
    
    Cosine distance = 1 - cosine_similarity
    Cosine similarity = (A . B) / (||A|| * ||B||)
    
    Args:
        vec1: First vector (1D or multi-dimensional flattened).
        vec2: Second vector (1D or multi-dimensional flattened).
        
    Returns:
        Cosine distance (float between 0 and 2).
        
    Raises:
        ValueError: If vectors have different shapes or are zero vectors.
    """
    if vec1.shape != vec2.shape:
        raise ValueError(f"Vector shapes must match: {vec1.shape} vs {vec2.shape}")
    
    # Flatten to 1D for distance calculation
    v1 = vec1.flatten().astype(np.float64)
    v2 = vec2.flatten().astype(np.float64)
    
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        raise ValueError("Cannot compute cosine distance for zero vectors")
    
    cosine_similarity = np.dot(v1, v2) / (norm1 * norm2)
    # Clip to [-1, 1] to handle floating point errors
    cosine_similarity = np.clip(cosine_similarity, -1.0, 1.0)
    
    return 1.0 - cosine_similarity

def calculate_reconstruction_error(
    synthesized_path: Path,
    ground_truth_path: Path
) -> Tuple[float, float, bool]:
    """
    Calculate the reconstruction error between synthesized and ground truth weights.
    
    This function:
    1. Loads both .npz files
    2. Computes cosine distance for each corresponding matrix (A and B)
    3. Returns mean and max error across all matrices
    4. Checks if max error exceeds the 0.05 threshold
    
    Args:
        synthesized_path: Path to the synthesized adapter .npz file.
        ground_truth_path: Path to the ground truth composite adapter .npz file.
        
    Returns:
        Tuple of (mean_error, max_error, validity_flag)
        - mean_error: Average cosine distance across all matrices
        - max_error: Maximum cosine distance found
        - validity_flag: True if max_error <= 0.05, False otherwise
        
    Raises:
        FileNotFoundError: If either input file is missing.
        ValueError: If file contents are invalid or shapes mismatch.
    """
    logger.info(f"Loading synthesized weights from: {synthesized_path}")
    synthesized_data = load_npz_file(synthesized_path)
    
    logger.info(f"Loading ground truth weights from: {ground_truth_path}")
    ground_truth_data = load_npz_file(ground_truth_path)
    
    # Validate that both files have the same keys
    syn_keys = set(synthesized_data.keys())
    gt_keys = set(ground_truth_data.keys())
    
    if syn_keys != gt_keys:
        missing_in_syn = gt_keys - syn_keys
        missing_in_gt = syn_keys - gt_keys
        error_msg = f"Key mismatch: "
        if missing_in_syn:
            error_msg += f"Missing in synthesized: {missing_in_syn}. "
        if missing_in_gt:
            error_msg += f"Missing in ground truth: {missing_in_gt}. "
        raise ValueError(error_msg)
    
    errors = []
    
    for key in syn_keys:
        syn_matrix = synthesized_data[key]
        gt_matrix = ground_truth_data[key]
        
        logger.debug(f"Calculating error for matrix: {key} (shape: {gt_matrix.shape})")
        
        try:
            error = compute_cosine_distance(syn_matrix, gt_matrix)
            errors.append(error)
            logger.debug(f"  Error: {error:.6f}")
        except ValueError as e:
            logger.error(f"Error computing distance for {key}: {e}")
            raise
    
    if not errors:
        raise ValueError("No errors calculated - check if matrices were processed")
    
    mean_error = float(np.mean(errors))
    max_error = float(np.max(errors))
    validity_flag = max_error <= 0.05
    
    logger.info(f"Reconstruction Error Results:")
    logger.info(f"  Mean Error: {mean_error:.6f}")
    logger.info(f"  Max Error: {max_error:.6f}")
    logger.info(f"  Validity Flag (max <= 0.05): {validity_flag}")
    
    return mean_error, max_error, validity_flag

def save_results(
    mean_error: float,
    max_error: float,
    validity_flag: bool,
    output_path: Path
) -> None:
    """
    Save the reconstruction error results to a JSON file.
    
    Args:
        mean_error: The mean reconstruction error.
        max_error: The maximum reconstruction error.
        validity_flag: True if max_error <= 0.05, False otherwise.
        output_path: Path to the output JSON file.
    """
    results = {
        "mean_error": mean_error,
        "max_error": max_error,
        "validity_flag": validity_flag,
        "threshold": 0.05,
        "description": "Cosine distance between synthesized and ground truth LoRA weights"
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_path}")

def main() -> None:
    """
    Main entry point for the reconstruction error calculation.
    
    This script:
    1. Loads synthesized adapters from artifacts/synthesized_adapters/
    2. Loads ground truth from data/processed/composite_ground_truth.npz
    3. Calculates reconstruction errors
    4. Saves results to data/results/reconstruction_error.json
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    synthesized_dir = project_root / "artifacts" / "synthesized_adapters"
    ground_truth_path = project_root / "data" / "processed" / "composite_ground_truth.npz"
    output_path = project_root / "data" / "results" / "reconstruction_error.json"
    
    logger.info("Starting reconstruction error calculation...")
    
    # Validate ground truth exists
    if not ground_truth_path.exists():
        logger.error(f"Ground truth file not found: {ground_truth_path}")
        logger.error("Please run T022c to generate composite_ground_truth.npz first.")
        sys.exit(1)
    
    # Find synthesized adapters
    if not synthesized_dir.exists():
        logger.error(f"Synthesized adapters directory not found: {synthesized_dir}")
        logger.error("Please run T022b to generate synthesized adapters first.")
        sys.exit(1)
    
    synthesized_files = list(synthesized_dir.glob("*.npz"))
    
    if not synthesized_files:
        logger.error(f"No synthesized adapter files found in: {synthesized_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(synthesized_files)} synthesized adapter files")
    
    # For this task, we compare against the single ground truth composite
    # In a more complex scenario, we might have multiple ground truths
    # Here we assume one synthesized adapter is the reconstruction of the composite
    # If multiple synthesized adapters exist, we process the first one that matches
    # the expected naming convention or just process all and aggregate?
    
    # Based on T022c, we have one composite ground truth.
    # T022b generates synthesized adapters for specific queries.
    # For the reconstruction error task, we assume there is a specific synthesized
    # adapter corresponding to the composite task, or we evaluate all synthesized
    # adapters against the composite (which might not be the intended design).
    
    # Re-reading T022d: "calculate the cosine distance ... between the synthesized 
    # LoRA weights (from T022b serialization) and the true weights of a known 
    # composite task (from T022c)."
    
    # It implies a one-to-one or one-to-many comparison.
    # Given T022c generates ONE composite ground truth, and T022b generates
    # synthesized adapters for queries, we need to identify which synthesized
    # adapter corresponds to the composite task.
    
    # However, T022c says "Pair the first two adapters alphabetically... generate
    # synthetic composite adapters". This creates a ground truth for a specific
    # composite task.
    
    # T022b saves synthesized adapters. We need to find the one that was generated
    # for the composite task. If the naming convention isn't explicit, we might
    # need to assume the first synthesized file or look for a specific pattern.
    
    # To be robust, let's assume:
    # 1. If there's only one synthesized file, use it.
    # 2. If there are multiple, we might need to check metadata or naming.
    # 3. For now, if multiple exist, we'll process the first one and log a warning.
    
    # Actually, looking at the task description again: "across the held-out set"
    # This suggests there might be multiple pairs/composites.
    # But T022c says "Pair the first two adapters... to ensure determinism."
    # So likely only ONE composite ground truth is generated.
    
    # Let's proceed with comparing the synthesized adapter(s) to the single ground truth.
    # If there are multiple synthesized adapters, we'll compute the error for each
    # and report the mean/max across all of them? Or just the one matching the composite?
    
    # Given the ambiguity, and the fact that T022c generates ONE composite,
    # let's assume we are validating the synthesis of THAT specific composite.
    # We'll look for a synthesized file that might match the composite task ID.
    # If not found, we'll use the first available synthesized file and warn.
    
    # For simplicity in this implementation, we'll take the first synthesized file
    # if only one is expected, or iterate if multiple are present.
    
    all_errors = []
    
    for syn_file in synthesized_files:
        logger.info(f"Processing: {syn_file.name}")
        try:
            mean_err, max_err, valid = calculate_reconstruction_error(
                syn_file, ground_truth_path
            )
            all_errors.append({
                "file": syn_file.name,
                "mean_error": mean_err,
                "max_error": max_err,
                "validity_flag": valid
            })
        except Exception as e:
            logger.error(f"Failed to process {syn_file.name}: {e}")
            # Continue with other files
            continue
    
    if not all_errors:
        logger.error("No valid error calculations performed. Exiting.")
        sys.exit(1)
    
    # Aggregate results
    # If multiple files, we take the mean of means and max of maxes?
    # Or report per file? The task says "across the held-out set"
    # Assuming the "held-out set" here refers to the set of synthesized adapters
    # compared against the ground truth.
    
    overall_mean = float(np.mean([e["mean_error"] for e in all_errors]))
    overall_max = float(np.max([e["max_error"] for e in all_errors]))
    
    # The validity flag is False if ANY individual error > 0.05
    overall_validity = all(e["validity_flag"] for e in all_errors)
    
    logger.info(f"Overall Results:")
    logger.info(f"  Mean Error (across all): {overall_mean:.6f}")
    logger.info(f"  Max Error (across all): {overall_max:.6f}")
    logger.info(f"  Overall Validity: {overall_validity}")
    
    # Save results
    save_results(overall_mean, overall_max, overall_validity, output_path)
    
    logger.info("Reconstruction error calculation completed successfully.")

if __name__ == "__main__":
    main()
