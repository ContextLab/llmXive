"""
Feature engineering module for llmXive entanglement analysis.
Calculates statistical descriptors and fidelity loss.
"""
import argparse
import json
import logging
import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# --- Logging Setup ---

def setup_logging() -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger("features")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logging()

# --- Statistical Helper Functions ---

def calculate_variance_and_range(values: List[float]) -> Tuple[float, float]:
    """
    Calculate variance and range of a list of values.
    Handles zero-variance cases gracefully.
    """
    if not values:
        return 0.0, 0.0
    arr = np.array(values)
    if len(arr) < 2:
        return 0.0, 0.0
    variance = float(np.var(arr))
    range_val = float(np.max(arr) - np.min(arr))
    return variance, range_val

def calculate_entropy(values: List[float]) -> float:
    """
    Calculate Shannon entropy of a distribution.
    Normalizes values to sum to 1. Handles zero-variance/zero-sum cases.
    """
    if not values:
        return 0.0
    arr = np.array(values)
    if np.all(arr == 0):
        return 0.0
    # Normalize to probability distribution
    total = np.sum(arr)
    if total == 0:
        return 0.0
    probs = arr / total
    # Filter out zeros to avoid log(0)
    probs = probs[probs > 0]
    entropy = -np.sum(probs * np.log(probs))
    return float(entropy)

def calculate_skewness_and_kurtosis(values: List[float]) -> Tuple[float, float]:
    """
    Calculate skewness and kurtosis.
    Returns (0, 0) if variance is zero or insufficient data.
    """
    if len(values) < 4:
        return 0.0, 0.0
    arr = np.array(values)
    if np.std(arr) == 0:
        return 0.0, 0.0
    try:
        skew = float(scipy.stats.skew(arr))
        kurt = float(scipy.stats.kurtosis(arr))
    except Exception:
        # Fallback if scipy not available or calculation fails
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return 0.0, 0.0
        n = len(arr)
        skew = (n / ((n - 1) * (n - 2))) * np.sum(((arr - mean) / std) ** 3)
        kurt = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(((arr - mean) / std) ** 4) - (3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
    return skew, kurtosis

# Import scipy here to avoid circular import if used in main block
try:
    import scipy.stats
except ImportError:
    logger.warning("scipy not found; using numpy fallback for skewness/kurtosis")
    scipy = None

# --- Per-Sample Statistics ---

def calculate_per_sample_stats(
    teacher_scores: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate variance, entropy, skewness, kurtosis for a single sample's teacher scores.
    """
    values = list(teacher_scores.values())
    variance, range_val = calculate_variance_and_range(values)
    entropy = calculate_entropy(values)
    skewness, kurtosis = calculate_skewness_and_kurtosis(values)

    return {
        "variance": variance,
        "entropy": entropy,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "range": range_val,
    }

def calculate_frobenius_norm_outer_product(
    teacher_scores: Dict[str, float]
) -> float:
    """
    Calculate the Frobenius norm of the outer product of the teacher's score vector.
    This serves as the per-sample entanglement metric.
    """
    values = list(teacher_scores.values())
    if not values:
        return 0.0
    vec = np.array(values)
    # Outer product: vec @ vec.T
    outer = np.outer(vec, vec)
    # Frobenius norm: sqrt(sum of squares of all elements)
    frob_norm = np.linalg.norm(outer, ord="fro")
    return float(frob_norm)

def calculate_global_covariance_and_eigenvalue(
    all_teacher_scores: List[Dict[str, float]]
) -> Tuple[np.ndarray, float]:
    """
    Compute the global covariance matrix and dominant eigenvalue across the dataset.
    Returns (covariance_matrix, dominant_eigenvalue).
    """
    if not all_teacher_scores:
        return np.zeros((4, 4)), 0.0
    
    # Assume 4 dimensions: Alignment, Realism, Aesthetics, Plausibility
    # We need to map these to indices. For now, assume consistent order or dict keys.
    # We will extract values in a consistent order based on sorted keys.
    keys = sorted(all_teacher_scores[0].keys())
    if len(keys) != 4:
        logger.warning(f"Expected 4 dimensions, found {len(keys)}. Using all available.")
    
    matrix_data = []
    for sample in all_teacher_scores:
        vec = [sample.get(k, 0.0) for k in keys]
        matrix_data.append(vec)
    
    arr = np.array(matrix_data)
    if arr.shape[0] < 2:
        return np.zeros((4, 4)), 0.0
    
    cov_matrix = np.cov(arr, rowvar=False)
    
    # Ensure it's 4x4 if we had 4 keys, else use actual shape
    if cov_matrix.shape[0] != 4:
        # Pad or trim if necessary, but ideally keys match
        pass 
        
    eigenvalues = np.linalg.eigvals(cov_matrix)
    dominant_eigenvalue = float(np.max(np.real(eigenvalues)))
    
    return cov_matrix, dominant_eigenvalue

def calculate_fidelity_loss(
    student_scalar: float,
    human_annotation: float,
) -> float:
    """
    Calculate the dimensional fidelity loss (MAE) between student scalar and human annotation.
    """
    return abs(student_scalar - human_annotation)

# --- JSON I/O Helpers ---

def load_features_from_json(path: str) -> List[Dict[str, Any]]:
    """Load features from a JSON file."""
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_features_to_json(data: List[Dict[str, Any]], path: str) -> None:
    """Save features to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def compute_global_stats(
    features: List[Dict[str, Any]], key: str = "teacher_scores"
) -> Dict[str, Any]:
    """
    Compute global statistics (covariance, eigenvalue) from a list of feature dicts.
    """
    scores_list = [item.get(key, {}) for item in features if item.get(key)]
    if not scores_list:
        return {"global_eigenvalue": 0.0, "covariance_matrix": []}
    
    cov_mat, eigenval = calculate_global_covariance_and_eigenvalue(scores_list)
    return {
        "global_eigenvalue": eigenval,
        "covariance_matrix": cov_mat.tolist(),
    }

# --- Main Entry Point for CLI ---

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate features and fidelity loss.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/aligned_data.json",
        help="Path to input aligned data JSON.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/features.json",
        help="Path to output features JSON.",
    )
    parser.add_argument(
        "--global-stats",
        type=str,
        default="data/processed/global_stats.json",
        help="Path to output global stats JSON.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logger.info(f"Loading data from {args.input}")
    
    # Load aligned data (assumed to have: sample_id, teacher_scores, student_scalar, human_annotations, primary_dimension)
    try:
        with open(args.input, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    if not isinstance(data, list):
        data = [data]
    
    logger.info(f"Processing {len(data)} samples...")
    
    processed_features = []
    global_stats = {"global_eigenvalue": 0.0}
    
    # First pass: Collect all teacher scores for global calculation
    all_teacher_scores = []
    for item in data:
        if "teacher_scores" in item and isinstance(item["teacher_scores"], dict):
            all_teacher_scores.append(item["teacher_scores"])
    
    if all_teacher_scores:
        cov_mat, eigenval = calculate_global_covariance_and_eigenvalue(all_teacher_scores)
        global_stats = {
            "global_eigenvalue": eigenval,
            "covariance_matrix": cov_mat.tolist(),
        }
        # Save global stats
        with open(args.global_stats, "w") as f:
            json.dump(global_stats, f, indent=2)
        logger.info(f"Global eigenvalue calculated: {eigenval}")
    
    # Second pass: Compute per-sample stats and fidelity loss
    for item in data:
        sample_id = item.get("sample_id", "unknown")
        teacher_scores = item.get("teacher_scores", {})
        student_scalar = item.get("student_scalar")
        human_annotations = item.get("human_annotations", {})
        primary_dimension = item.get("primary_dimension")
        
        # Calculate per-sample stats
        stats = calculate_per_sample_stats(teacher_scores)
        entanglement_score = calculate_frobenius_norm_outer_product(teacher_scores)
        
        # Calculate fidelity loss
        fidelity_loss_val = None
        if student_scalar is not None and primary_dimension and primary_dimension in human_annotations:
            human_score = human_annotations[primary_dimension]
            if human_score is not None:
                fidelity_loss_val = calculate_fidelity_loss(student_scalar, human_score)
            else:
                logger.warning(f"Missing human annotation for {primary_dimension} in sample {sample_id}")
        else:
            if not primary_dimension:
                logger.warning(f"Missing primary_dimension in sample {sample_id}")
            elif primary_dimension not in human_annotations:
                logger.warning(f"Missing human annotation for {primary_dimension} in sample {sample_id}")
            elif student_scalar is None:
                logger.warning(f"Missing student_scalar in sample {sample_id}")
        
        record = {
            "sample_id": sample_id,
            "variance": stats["variance"],
            "entropy": stats["entropy"],
            "skewness": stats["skewness"],
            "kurtosis": stats["kurtosis"],
            "entanglement_score": entanglement_score,
            "global_eigenvalue": global_stats["global_eigenvalue"],
            "fidelity_loss": fidelity_loss_val, # Can be None if data missing
        }
        processed_features.append(record)
    
    # Filter out records with None fidelity_loss if strictly required, 
    # but task says "flag and exclude", so we might keep them with null or drop them.
    # The task says "flag and exclude samples with missing human annotations".
    # We will keep them but mark fidelity_loss as null, or filter them out?
    # "flag and exclude" implies we should not use them for training.
    # For the JSON output, we include all but the model training step (T027a) 
    # will need to filter out nulls. 
    # However, the task says "Output key: fidelity_loss". 
    # Let's keep the record but set fidelity_loss to null if missing.
    
    logger.info(f"Saving features to {args.output}")
    save_features_to_json(processed_features, args.output)
    
    logger.info("Feature engineering complete.")

if __name__ == "__main__":
    main()