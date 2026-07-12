import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Core Feature Calculations (US2 Implementation) ---

def calculate_variance_and_range(distribution: np.ndarray) -> Tuple[float, float]:
    """Calculate variance and range for a 1D distribution."""
    if distribution.size == 0:
        return 0.0, 0.0
    variance = float(np.var(distribution))
    range_val = float(np.max(distribution) - np.min(distribution))
    return variance, range_val

def calculate_entropy(distribution: np.ndarray) -> float:
    """Calculate Shannon entropy for a normalized probability distribution."""
    if distribution.size == 0 or np.all(distribution == 0):
        return 0.0
    # Ensure non-negative and normalized
    p = np.clip(distribution, 1e-10, None)
    p = p / np.sum(p)
    entropy = -np.sum(p * np.log(p))
    return float(entropy)

def calculate_skewness_and_kurtosis(distribution: np.ndarray) -> Tuple[float, float]:
    """Calculate skewness and kurtosis."""
    if distribution.size < 3:
        return 0.0, 0.0
    skewness = float(scipy.stats.skew(distribution))
    kurtosis = float(scipy.stats.kurtosis(distribution))
    return skewness, kurtosis

def calculate_per_sample_stats(distribution: np.ndarray) -> Dict[str, float]:
    """Compute all per-sample statistical descriptors."""
    variance, range_val = calculate_variance_and_range(distribution)
    entropy = calculate_entropy(distribution)
    skewness, kurtosis = calculate_skewness_and_kurtosis(distribution)
    
    return {
        "variance": variance,
        "range": range_val,
        "entropy": entropy,
        "skewness": skewness,
        "kurtosis": kurtosis
    }

def calculate_global_entanglement_score(data_matrix: np.ndarray) -> float:
    """
    Compute the global entanglement score as the dominant eigenvalue
    of the covariance matrix across all samples for the 4 dimensions.
    """
    if data_matrix.shape[0] < 2 or data_matrix.shape[1] != 4:
        logger.warning("Insufficient data or incorrect dimensions for global entanglement.")
        return 0.0
    
    try:
        cov_matrix = np.cov(data_matrix, rowvar=False)
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        dominant_eigenvalue = float(np.max(eigenvalues))
        return dominant_eigenvalue
    except np.linalg.LinAlgError:
        logger.error("Failed to compute eigenvalues for covariance matrix.")
        return 0.0

def calculate_dimensional_fidelity_loss(
    student_scores: np.ndarray,
    human_annotations: np.ndarray,
    primary_dimensions: List[str],
    rubric_keys: List[str]
) -> List[float]:
    """
    Compute MAE between student scalar output and human-annotated score
    for the primary dimension selected via metadata.
    """
    if len(student_scores) != len(human_annotations) or len(student_scores) != len(primary_dimensions):
        raise ValueError("Input arrays lengths must match.")
    
    fidelity_losses = []
    for i, dim in enumerate(primary_dimensions):
        if dim not in rubric_keys:
            fidelity_losses.append(float('nan'))
            continue
        
        idx = rubric_keys.index(dim)
        student_val = student_scores[i]
        human_val = human_annotations[i, idx]
        
        if np.isnan(human_val):
            fidelity_losses.append(float('nan'))
        else:
            loss = abs(student_val - human_val)
            fidelity_losses.append(float(loss))
    
    return fidelity_losses

# --- Pipeline Integration Functions ---

def load_aligned_data(input_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str], List[str]]:
    """
    Load aligned data from the ingest pipeline output (JSON).
    Returns:
        data_matrix: (N, 4) array of teacher distributions
        student_scores: (N,) array of student scalars
        human_annotations: (N, 4) array of human annotations
        primary_dimensions: List of primary dimension strings per sample
        rubric_keys: List of rubric dimension names (e.g., ['Alignment', ...])
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    samples = data.get("samples", [])
    if not samples:
        raise ValueError("No samples found in aligned data file.")
    
    # Extract rubric keys from the first sample
    first_sample = samples[0]
    rubric_keys = [k for k in first_sample.get("teacher_distribution", {}).keys()]
    
    data_list = []
    student_list = []
    human_list = []
    primary_list = []
    
    for sample in samples:
        # Teacher distribution
        dist = [sample["teacher_distribution"][k] for k in rubric_keys]
        data_list.append(dist)
        
        # Student score
        student_list.append(sample["student_score"])
        
        # Human annotations
        human_vals = [sample["human_annotations"].get(k, np.nan) for k in rubric_keys]
        human_list.append(human_vals)
        
        # Primary dimension
        primary_list.append(sample.get("primary_quality_dimension", ""))
    
    return (
        np.array(data_list),
        np.array(student_list),
        np.array(human_list),
        primary_list,
        rubric_keys
    )

def compute_all_features(aligned_data_path: str) -> Dict[str, Any]:
    """
    Orchestrate the computation of all features: per-sample stats, global entanglement,
    and dimensional fidelity loss.
    """
    logger.info(f"Loading aligned data from {aligned_data_path}")
    data_matrix, student_scores, human_annotations, primary_dims, rubric_keys = load_aligned_data(aligned_data_path)
    
    logger.info("Computing per-sample statistics...")
    per_sample_features = []
    for i in range(data_matrix.shape[0]):
        stats = calculate_per_sample_stats(data_matrix[i])
        stats["sample_id"] = i
        stats["primary_dimension"] = primary_dims[i]
        per_sample_features.append(stats)
    
    logger.info("Computing global entanglement score...")
    global_entanglement = calculate_global_entanglement_score(data_matrix)
    
    logger.info("Computing dimensional fidelity loss...")
    fidelity_losses = calculate_dimensional_fidelity_loss(
        student_scores, human_annotations, primary_dims, rubric_keys
    )
    
    # Attach fidelity loss to per-sample features
    for i, loss in enumerate(fidelity_losses):
        per_sample_features[i]["fidelity_loss"] = loss
    
    result = {
        "global_entanglement_score": global_entanglement,
        "rubric_keys": rubric_keys,
        "samples": per_sample_features,
        "total_samples": len(per_sample_features)
    }
    
    return result

def save_features_to_json(features: Dict[str, Any], output_path: str) -> None:
    """Save computed features to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(features, f, indent=2)
    logger.info(f"Features saved to {output_path}")

# --- CLI Entry Point ---

def parse_args():
    parser = argparse.ArgumentParser(description="Compute and save feature engineering results.")
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="data/processed/aligned_data.json",
        help="Path to the aligned data JSON file from ingest.py"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/processed/features.json",
        help="Path to save the computed features JSON"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info(f"Starting feature engineering pipeline. Input: {args.input}, Output: {args.output}")
    
    try:
        features = compute_all_features(args.input)
        save_features_to_json(features, args.output)
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
