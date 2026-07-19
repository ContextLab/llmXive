"""
Feature Engineering Module for Z-Reward dataset.

This module calculates:
- Statistical descriptors (variance, entropy, skewness, kurtosis) per sample
- Global eigenvalue for the full dataset
- Dimensional fidelity loss
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def calculate_variance_and_range(data: np.ndarray) -> Tuple[float, float]:
    """
    Calculate variance and range for a 1D array.
    
    Args:
        data: 1D numpy array of values
        
    Returns:
        Tuple of (variance, range)
    """
    if len(data) == 0:
        return 0.0, 0.0
    
    variance = np.var(data)
    range_val = np.max(data) - np.min(data) if len(data) > 0 else 0.0
    
    return float(variance), float(range_val)

def calculate_entropy(data: np.ndarray) -> float:
    """
    Calculate entropy for a 1D array (normalized to probability distribution).
    
    Args:
        data: 1D numpy array of values
        
    Returns:
        Entropy value
    """
    if len(data) == 0 or np.all(data == 0):
        return 0.0
    
    # Normalize to probability distribution
    total = np.sum(data)
    if total == 0:
        return 0.0
    
    probs = data / total
    # Filter out zero probabilities to avoid log(0)
    probs = probs[probs > 0]
    
    entropy = -np.sum(probs * np.log(probs))
    return float(entropy)

def calculate_skewness_and_kurtosis(data: np.ndarray) -> Tuple[float, float]:
    """
    Calculate skewness and kurtosis for a 1D array.
    
    Args:
        data: 1D numpy array of values
        
    Returns:
        Tuple of (skewness, kurtosis)
    """
    if len(data) < 3:
        return 0.0, 0.0
    
    skewness = float(np.skew(data))
    kurtosis = float(np.kurtosis(data))
    
    return skewness, kurtosis

def calculate_per_sample_stats(samples: List[Dict]) -> Dict[str, Dict]:
    """
    Calculate per-sample statistics for all samples.
    
    Args:
        samples: List of sample dictionaries with teacher_logits
        
    Returns:
        Dictionary mapping sample_id to statistics
    """
    stats = {}
    
    for sample in samples:
        sample_id = sample.get("sample_id")
        teacher_logits = sample.get("teacher_logits")
        
        if not teacher_logits:
            continue
        
        # Convert to numpy array
        logits_array = np.array(teacher_logits, dtype=float)
        
        # Calculate statistics
        variance, range_val = calculate_variance_and_range(logits_array)
        entropy = calculate_entropy(logits_array)
        skewness, kurtosis = calculate_skewness_and_kurtosis(logits_array)
        
        stats[sample_id] = {
            "variance": variance,
            "range": range_val,
            "entropy": entropy,
            "skewness": skewness,
            "kurtosis": kurtosis
        }
    
    return stats

def calculate_global_entanglement_score(samples: List[Dict]) -> float:
    """
    Calculate global entanglement score using the dominant eigenvalue
    of the global covariance matrix across all samples.
    
    Args:
        samples: List of sample dictionaries with teacher_logits
        
    Returns:
        Dominant eigenvalue (global entanglement score)
    """
    # Extract teacher logits as a matrix (samples x dimensions)
    logits_matrix = []
    for sample in samples:
        teacher_logits = sample.get("teacher_logits")
        if teacher_logits:
            logits_matrix.append(teacher_logits)
    
    if len(logits_matrix) == 0:
        return 0.0
    
    logits_array = np.array(logits_matrix, dtype=float)
    
    # Calculate global covariance matrix
    # Shape: (4, 4) for 4 dimensions
    covariance_matrix = np.cov(logits_array, rowvar=False)
    
    # Calculate eigenvalues
    eigenvalues = np.linalg.eigvalsh(covariance_matrix)
    
    # Return the dominant (largest) eigenvalue
    dominant_eigenvalue = float(np.max(eigenvalues))
    
    return dominant_eigenvalue

def calculate_dimensional_fidelity_loss(samples: List[Dict]) -> List[float]:
    """
    Calculate dimensional fidelity loss for each sample.
    MAE between student scalar output and human-annotated score for the primary dimension.
    
    Args:
        samples: List of sample dictionaries
        
    Returns:
        List of fidelity loss values
    """
    fidelity_losses = []
    
    for sample in samples:
        student_score = sample.get("student_scores")
        primary_dimension = sample.get("primary_dimension", "Alignment")
        
        # Map primary dimension to human annotation column
        dimension_map = {
            "Alignment": "human_alignment",
            "Realism": "human_realism",
            "Aesthetics": "human_aesthetics",
            "Plausibility": "human_plausibility"
        }
        
        human_annotation_col = dimension_map.get(primary_dimension)
        
        if not human_annotation_col or human_annotation_col not in sample:
            # Skip samples with missing annotations
            continue
        
        human_score = sample.get(human_annotation_col)
        
        if human_score is None or student_score is None:
            continue
        
        # Calculate MAE (absolute difference)
        try:
            human_score = float(human_score)
            student_score = float(student_score)
            loss = abs(student_score - human_score)
            fidelity_losses.append(loss)
        except (ValueError, TypeError):
            # Skip samples with invalid scores
            continue
    
    return fidelity_losses

def load_aligned_data(filepath: str) -> List[Dict]:
    """
    Load aligned data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List of aligned data dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def compute_all_features(samples: List[Dict]) -> Dict[str, Any]:
    """
    Compute all features for the dataset.
    
    Args:
        samples: List of sample dictionaries
        
    Returns:
        Dictionary containing all computed features
    """
    # Per-sample statistics
    per_sample_stats = calculate_per_sample_stats(samples)
    
    # Global entanglement score
    global_entanglement = calculate_global_entanglement_score(samples)
    
    # Dimensional fidelity loss
    fidelity_loss = calculate_dimensional_fidelity_loss(samples)
    
    return {
        "per_sample_stats": per_sample_stats,
        "global_entanglement_score": global_entanglement,
        "fidelity_loss": fidelity_loss
    }

def save_features_to_json(features: Dict[str, Any], output_path: str):
    """
    Save computed features to a JSON file.
    
    Args:
        features: Dictionary of computed features
        output_path: Output path for the JSON file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=2)
    logger.info(f"Features saved to {output_path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Compute features from aligned data")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/aligned_data.json",
        help="Input JSON file with aligned data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/features.json",
        help="Output JSON file for computed features"
    )
    return parser.parse_args()

def main():
    """Main entry point for the feature engineering script."""
    args = parse_args()
    
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Load aligned data
    logger.info(f"Loading data from {args.input}")
    samples = load_aligned_data(args.input)
    
    # Compute features
    logger.info("Computing features...")
    features = compute_all_features(samples)
    
    # Save features
    logger.info(f"Saving features to {args.output}")
    save_features_to_json(features, args.output)
    
    # Print summary
    logger.info(f"Computed {len(features['per_sample_stats'])} per-sample stats")
    logger.info(f"Global entanglement score: {features['global_entanglement_score']:.4f}")
    logger.info(f"Fidelity loss samples: {len(features['fidelity_loss'])}")
    
    return 0

if __name__ == "__main__":
    exit(main())
