import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Configuration & Setup
# ---------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger("features")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger

# ---------------------------------------------------------------------------
# Data Loading Helpers
# ---------------------------------------------------------------------------

def load_aligned_data(
    input_path: str, logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Load the aligned dataset from the intermediate CSV produced by ingest.py.

    Expected columns (per schema):
    - sample_id: str
    - prompt: str
    - image_path: str
    - teacher_logits: list[float] (stored as JSON string or comma-separated)
    - student_scalar: float
    - human_annotations: dict (stored as JSON string)
    - primary_dimension: str

    Returns a list of dicts with parsed types.
    """
    logger.info(f"Loading aligned data from {input_path}")
    data = []

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        # Assuming CSV with header; if JSON lines, adjust accordingly
        # Based on T012/T013 output expectations, we assume CSV format
        import csv

        reader = csv.DictReader(f)
        for row in reader:
            # Parse teacher_logits if stored as string
            if isinstance(row.get("teacher_logits"), str):
                try:
                    row["teacher_logits"] = json.loads(row["teacher_logits"])
                except json.JSONDecodeError:
                    # Fallback for comma-separated if JSON load fails
                    row["teacher_logits"] = [float(x) for x in row["teacher_logits"].split(",")]

            # Parse human_annotations if stored as string
            if isinstance(row.get("human_annotations"), str):
                row["human_annotations"] = json.loads(row["human_annotations"])

            # Ensure numeric types
            row["student_scalar"] = float(row["student_scalar"])

            data.append(row)

    logger.info(f"Loaded {len(data)} samples")
    return data

# ---------------------------------------------------------------------------
# Statistical Calculations (Per-Sample & Global)
# ---------------------------------------------------------------------------

def calculate_variance_and_range(values: List[float]) -> Tuple[float, float]:
    """
    Calculate variance and range for a list of values.

    Returns:
        Tuple[float, float]: (variance, range)
    """
    if not values or len(values) < 2:
        return 0.0, 0.0

    arr = np.array(values, dtype=float)
    variance = float(np.var(arr))
    range_val = float(np.ptp(arr))  # peak-to-peak (max - min)
    return variance, range_val

def calculate_entropy(values: List[float]) -> float:
    """
    Calculate Shannon entropy for a list of values.
    Treats values as a probability distribution (normalized).

    Returns:
        float: Entropy value.
    """
    if not values:
        return 0.0

    arr = np.array(values, dtype=float)

    # Handle zero-variance or constant values
    if np.all(arr == arr[0]):
        return 0.0

    # Normalize to probability distribution
    # If values can be negative (logits), we shift to positive for probability interpretation
    # or use softmax. Given the context of "teacher distributions", we assume these are
    # logits that should be normalized via softmax, or they are already scores.
    # The task asks for entropy of "teacher distributions".
    # Strategy: Apply softmax to logits to get probs, then calculate entropy.
    # If values are already positive scores, we normalize by sum.
    # Let's assume input is logits -> apply softmax.

    # Stable softmax
    exp_arr = np.exp(arr - np.max(arr))
    probs = exp_arr / np.sum(exp_arr)

    # Avoid log(0)
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0

    entropy = -np.sum(probs * np.log(probs))
    return float(entropy)

def calculate_skewness_and_kurtosis(values: List[float]) -> Tuple[float, float]:
    """
    Calculate skewness and kurtosis for a list of values.

    Returns:
        Tuple[float, float]: (skewness, kurtosis)
    """
    if not values or len(values) < 3:
        return 0.0, 0.0

    arr = np.array(values, dtype=float)

    # Handle zero-variance
    if np.std(arr) == 0:
        return 0.0, 0.0

    skew = float(stats.skew(arr))
    kurt = float(stats.kurtosis(arr))  # Fisher's definition (excess kurtosis)

    return skew, kurt

def calculate_per_sample_stats(
    teacher_logits: List[float], logger: logging.Logger
) -> Dict[str, float]:
    """
    Calculate variance, range, entropy, skewness, and kurtosis for a single sample.

    Args:
        teacher_logits: List of float values (logits/scores).
        logger: Logger instance.

    Returns:
        Dict containing calculated stats.
    """
    variance, range_val = calculate_variance_and_range(teacher_logits)
    entropy = calculate_entropy(teacher_logits)
    skewness, kurtosis = calculate_skewness_and_kurtosis(teacher_logits)

    return {
        "variance": variance,
        "range": range_val,
        "entropy": entropy,
        "skewness": skewness,
        "kurtosis": kurtosis,
    }

def calculate_global_entanglement_score(
    all_teacher_distributions: List[List[float]], logger: logging.Logger
) -> float:
    """
    Calculate the global dominant eigenvalue of the covariance matrix
    across the entire dataset's teacher distributions.

    This implements the "Global Covariance Matrix" requirement.

    Args:
        all_teacher_distributions: List of lists, where each inner list is a sample's teacher distribution.
        logger: Logger instance.

    Returns:
        float: The dominant (largest) eigenvalue.
    """
    if not all_teacher_distributions or len(all_teacher_distributions) < 2:
        logger.warning("Insufficient data for global entanglement score.")
        return 0.0

    # Convert to numpy array (N_samples x N_dimensions)
    try:
        matrix = np.array(all_teacher_distributions, dtype=float)
    except ValueError as e:
        logger.error(f"Failed to convert teacher distributions to array: {e}")
        return float('nan')

    N, D = matrix.shape
    logger.info(f"Computing global covariance on {N} samples, {D} dimensions.")

    if D < 2:
        logger.warning("Less than 2 dimensions for covariance.")
        return 0.0

    # Compute covariance matrix (D x D)
    # We want the covariance of the score vector across samples.
    # np.cov expects variables in rows, observations in columns by default.
    # So we transpose: (D x N) -> cov -> (D x D)
    cov_matrix = np.cov(matrix.T)

    # Check for NaNs
    if np.any(np.isnan(cov_matrix)):
        logger.error("Covariance matrix contains NaN values.")
        return float('nan')

    # Compute eigenvalues
    eigenvalues = np.linalg.eigvalsh(cov_matrix)

    # Dominant eigenvalue is the largest
    dominant_eigenvalue = float(np.max(eigenvalues))

    logger.info(f"Global dominant eigenvalue: {dominant_eigenvalue}")
    return dominant_eigenvalue

def calculate_dimensional_fidelity_loss(
    student_scalar: float,
    human_annotations: Dict[str, float],
    primary_dimension: str,
    logger: logging.Logger,
) -> float:
    """
    Calculate Mean Absolute Error (MAE) between student scalar and human annotation
    for the primary dimension.

    Args:
        student_scalar: The student's predicted scalar score.
        human_annotations: Dict mapping dimension names to scores.
        primary_dimension: The key in human_annotations to use.
        logger: Logger instance.

    Returns:
        float: MAE (absolute difference).

    Raises:
        KeyError: If primary_dimension is missing from human_annotations.
    """
    if primary_dimension not in human_annotations:
        raise KeyError(
            f"Primary dimension '{primary_dimension}' not found in human_annotations: {list(human_annotations.keys())}"
        )

    human_score = human_annotations[primary_dimension]
    loss = abs(float(student_scalar) - float(human_score))
    return loss

# ---------------------------------------------------------------------------
# Main Feature Engineering Logic
# ---------------------------------------------------------------------------

def compute_all_features(
    data: List[Dict[str, Any]], logger: logging.Logger
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Compute all per-sample features and the global entanglement score.

    Args:
        data: List of aligned sample dictionaries.
        logger: Logger instance.

    Returns:
        Tuple[List[Dict], float]:
            - List of feature dictionaries (one per sample).
            - Global dominant eigenvalue.
    """
    processed_features = []
    all_teacher_distributions = []

    for idx, sample in enumerate(data):
        sample_id = sample.get("sample_id", f"sample_{idx}")
        teacher_logits = sample.get("teacher_logits", [])
        student_scalar = sample.get("student_scalar", 0.0)
        human_annotations = sample.get("human_annotations", {})
        primary_dimension = sample.get("primary_dimension", "Alignment")

        # 1. Per-sample stats (T020, T021, T022b)
        try:
            per_sample_stats = calculate_per_sample_stats(teacher_logits, logger)
        except Exception as e:
            logger.error(f"Error calculating stats for {sample_id}: {e}")
            # Handle zero-variance gracefully as per T023
            per_sample_stats = {
                "variance": 0.0,
                "range": 0.0,
                "entropy": 0.0,
                "skewness": 0.0,
                "kurtosis": 0.0,
            }

        # 2. Dimensional Fidelity Loss (T024)
        try:
            fidelity_loss = calculate_dimensional_fidelity_loss(
                student_scalar, human_annotations, primary_dimension, logger
            )
        except KeyError:
            logger.warning(
                f"Skipping sample {sample_id}: Missing primary dimension '{primary_dimension}' in annotations."
            )
            # Exclude samples with missing annotations as per T024 logic
            continue

        # 3. Store for global calculation
        all_teacher_distributions.append(teacher_logits)

        feature_record = {
            "sample_id": sample_id,
            "primary_dimension": primary_dimension,
            **per_sample_stats,
            "fidelity_loss": fidelity_loss,
        }
        processed_features.append(feature_record)

        if (idx + 1) % 1000 == 0:
            logger.info(f"Processed {idx + 1}/{len(data)} samples")

    # 4. Global Entanglement Score (T022a)
    dominant_eigenvalue = 0.0
    if all_teacher_distributions:
        dominant_eigenvalue = calculate_global_entanglement_score(
            all_teacher_distributions, logger
        )

    # Add global score to every record (or keep separate? T025 says "contains dominant_eigenvalue")
    # We will attach it to each record for convenience in downstream tasks, or just return it.
    # The contract likely expects it in the JSON. Let's add it to each record.
    for record in processed_features:
        record["dominant_eigenvalue"] = dominant_eigenvalue

    return processed_features, dominant_eigenvalue

def save_features_to_json(
    features: List[Dict[str, Any]], output_path: str, logger: logging.Logger
) -> None:
    """Save the computed features to a JSON file."""
    logger.info(f"Saving features to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(features, f, indent=2)
    logger.info("Features saved successfully.")

# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute entanglement features and fidelity loss."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the aligned CSV data from ingest.py",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the features JSON",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logger = setup_logging()
    logger.setLevel(getattr(logging, args.log_level))

    try:
        # Load data
        data = load_aligned_data(args.input, logger)

        if not data:
            logger.error("No data loaded. Exiting.")
            sys.exit(1)

        # Compute features
        features, global_eigenvalue = compute_all_features(data, logger)

        if not features:
            logger.warning("No valid features computed (possibly due to missing annotations).")
            # Still save empty or partial? T025 says "no null values".
            # If all failed, we might have an empty list.
            # We'll save what we have.
            save_features_to_json(features, args.output, logger)
            logger.info(f"Global dominant eigenvalue: {global_eigenvalue}")
            return

        # Save
        save_features_to_json(features, args.output, logger)

        logger.info(f"Global dominant eigenvalue: {global_eigenvalue}")
        logger.info(f"Total valid samples: {len(features)}")

    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Feature computation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
