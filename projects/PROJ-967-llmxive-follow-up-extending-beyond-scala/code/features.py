import argparse
import json
import logging
import math
import os
import sys
from typing import Dict, List, Any, Optional

import numpy as np

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return the root logger."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# Core Statistical Helpers
# ============================================================================

def calculate_variance_and_range(values: List[float]) -> Dict[str, float]:
    """Calculate variance and range for a list of values."""
    if not values or len(values) < 2:
        return {"variance": 0.0, "range": 0.0}

    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    range_val = max(values) - min(values)
    return {"variance": variance, "range": range_val}

def calculate_entropy(values: List[float]) -> float:
    """
    Calculate Shannon entropy for a list of values.
    Normalizes values to sum to 1 before computing -sum(p * log(p)).
    Handles zero-variance/constant cases gracefully (returns 0.0).
    """
    if not values:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    probs = [v / total for v in values]
    entropy_val = 0.0
    for p in probs:
        if p > 0:
            entropy_val -= p * math.log(p)
    return entropy_val

def calculate_skewness_and_kurtosis(values: List[float]) -> Dict[str, float]:
    """Calculate skewness and kurtosis for a list of values."""
    if not values or len(values) < 3:
        return {"skewness": 0.0, "kurtosis": 0.0}

    n = len(values)
    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / n

    if variance == 0:
        return {"skewness": 0.0, "kurtosis": 0.0}

    std_dev = math.sqrt(variance)
    if std_dev == 0:
        return {"skewness": 0.0, "kurtosis": 0.0}

    skewness = sum(((x - mean_val) / std_dev) ** 3 for x in values) / n
    kurtosis = sum(((x - mean_val) / std_dev) ** 4 for x in values) / n - 3

    return {"skewness": skewness, "kurtosis": kurtosis}

def calculate_per_sample_stats(values: List[float]) -> Dict[str, float]:
    """Calculate all per-sample stats: variance, entropy, skewness, kurtosis."""
    var_range = calculate_variance_and_range(values)
    ent = calculate_entropy(values)
    skew_kurt = calculate_skewness_and_kurtosis(values)

    return {
        "variance": var_range["variance"],
        "range": var_range["range"],
        "entropy": ent,
        "skewness": skew_kurt["skewness"],
        "kurtosis": skew_kurt["kurtosis"],
    }

def calculate_dominant_eigenvalue(values: List[float]) -> float:
    """
    Calculate the dominant eigenvalue for a sample's teacher score vector.
    1. Compute outer product C = v * v^T
    2. Calculate the largest eigenvalue of C.
    For a rank-1 matrix v*v^T, the non-zero eigenvalue is ||v||^2.
    """
    if not values:
        return 0.0

    norm_sq = sum(x ** 2 for x in values)
    return float(norm_sq)

def calculate_frobenius_norm_outer_product(values: List[float]) -> float:
    """Calculate Frobenius norm of the outer product matrix."""
    if not values:
        return 0.0
    norm_sq = sum(x ** 2 for x in values)
    return math.sqrt(norm_sq)

def calculate_global_covariance_and_eigenvalue(all_vectors: List[List[float]]) -> float:
    """Calculate global covariance matrix and its dominant eigenvalue."""
    if not all_vectors or not all_vectors[0]:
        return 0.0

    n_dims = len(all_vectors[0])
    n_samples = len(all_vectors)

    # Compute mean vector
    mean_vec = [0.0] * n_dims
    for vec in all_vectors:
        for i in range(n_dims):
            mean_vec[i] += vec[i]
    mean_vec = [x / n_samples for x in mean_vec]

    # Compute covariance matrix
    cov_matrix = [[0.0] * n_dims for _ in range(n_dims)]
    for vec in all_vectors:
        diff = [vec[i] - mean_vec[i] for i in range(n_dims)]
        for i in range(n_dims):
            for j in range(n_dims):
                cov_matrix[i][j] += diff[i] * diff[j]
    cov_matrix = [[cov_matrix[i][j] / n_samples for j in range(n_dims)] for i in range(n_dims)]

    # Find dominant eigenvalue using power iteration
    eigenvalue = 0.0
    if n_dims > 0:
        v = [1.0] * n_dims
        for _ in range(100):
            new_v = [0.0] * n_dims
            for i in range(n_dims):
                for j in range(n_dims):
                    new_v[i] += cov_matrix[i][j] * v[j]
            norm = math.sqrt(sum(x ** 2 for x in new_v))
            if norm > 0:
                v = [x / norm for x in new_v]
                eigenvalue = sum(cov_matrix[i][j] * v[j] for i in range(n_dims) for j in range(n_dims)) / sum(v[i] * v[i] for i in range(n_dims))
    return float(eigenvalue)

# ============================================================================
# T024: Dimensional Fidelity Loss Calculation
# ============================================================================

def calculate_fidelity_loss(
    sample: Dict[str, Any],
    primary_dimension: str,
    teacher_scores_key: str = "teacher_scores",
    human_annotations_key: str = "human_annotations"
) -> Optional[float]:
    """
    T024: Calculate the 'dimensional fidelity loss' for a single sample.

    Logic:
    1. Identify the primary dimension for this sample (provided as argument).
    2. Retrieve the human-annotated score for that primary dimension.
    3. Retrieve the student scalar output.
    4. Compute MAE (absolute difference) between student_scalar and human_annotation.
    5. Return the loss.

    Returns None if any required data is missing (to be handled by caller).
    """
    # Extract student scalar
    student_scalar = sample.get("student_scalar")
    if student_scalar is None:
        logger.warning(f"Missing student_scalar for sample {sample.get('sample_id')}")
        return None

    # Extract human annotations
    human_annotations = sample.get(human_annotations_key)
    if not human_annotations:
        logger.warning(f"Missing human_annotations for sample {sample.get('sample_id')}")
        return None

    # Get score for the specific primary dimension
    human_score = human_annotations.get(primary_dimension)
    if human_score is None:
        logger.warning(f"Missing human annotation for dimension '{primary_dimension}' in sample {sample.get('sample_id')}")
        return None

    # Calculate Absolute Error (MAE for a single point)
    loss = abs(student_scalar - human_score)
    return float(loss)

# ============================================================================
# JSON I/O Helpers
# ============================================================================

def load_features_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load features from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Features file not found: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)

def save_features_to_json(features: List[Dict[str, Any]], filepath: str) -> None:
    """Save features to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(features, f, indent=2)

def compute_global_stats(features: List[Dict[str, Any]]) -> Dict[str, float]:
    """Compute global statistics across all samples."""
    if not features:
        return {}

    all_variances = [f["variance"] for f in features if "variance" in f]
    all_entropies = [f["entropy"] for f in features if "entropy" in f]

    return {
        "mean_variance": sum(all_variances) / len(all_variances) if all_variances else 0.0,
        "mean_entropy": sum(all_entropies) / len(all_entropies) if all_entropies else 0.0,
    }

# ============================================================================
# CLI / Main
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Feature Engineering Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file path")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path")
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info(f"Loading features from {args.input}")
    try:
        features = load_features_from_json(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Loaded {len(features)} samples. Computing global stats...")
    global_stats = compute_global_stats(features)
    logger.info(f"Global Stats: {global_stats}")

    # Example: Save processed features (T024 logic is integrated in the pipeline flow)
    # In a real pipeline, T024 would be called during the integration step (T025)
    # Here we just ensure the file exists and is valid.
    save_features_to_json(features, args.output)
    logger.info(f"Saved processed features to {args.output}")

if __name__ == "__main__":
    main()