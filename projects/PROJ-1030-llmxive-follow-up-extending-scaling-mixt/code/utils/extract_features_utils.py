"""
Utility functions for feature extraction tasks.
This module provides helper functions used by extract_features.py
"""
import numpy as np
from typing import Tuple, Optional
import torch

def validate_feature_shapes(
    latent_vector: np.ndarray,
    expert_masks: np.ndarray,
    expected_latent_dim: int = 768,
    expected_num_experts: int = 8
) -> bool:
    """Validate that extracted features have expected shapes."""
    if latent_vector.shape[1] != expected_latent_dim:
        return False
    if expert_masks.shape[1] != expected_num_experts:
        return False
    if latent_vector.shape[0] != expert_masks.shape[0]:
        return False
    return True

def normalize_features(
    latent_vector: np.ndarray,
    method: str = "l2"
) -> np.ndarray:
    """Normalize feature vectors."""
    if method == "l2":
        norms = np.linalg.norm(latent_vector, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        return latent_vector / norms
    elif method == "zscore":
        mean = np.mean(latent_vector, axis=0, keepdims=True)
        std = np.std(latent_vector, axis=0, keepdims=True)
        std = np.where(std == 0, 1, std)
        return (latent_vector - mean) / std
    else:
        return latent_vector

def aggregate_expert_masks(
    expert_masks: np.ndarray,
    aggregation: str = "mean"
) -> np.ndarray:
    """Aggregate expert masks across samples."""
    if aggregation == "mean":
        return np.mean(expert_masks, axis=0)
    elif aggregation == "sum":
        return np.sum(expert_masks, axis=0)
    elif aggregation == "mode":
        return (np.mean(expert_masks, axis=0) > 0.5).astype(int)
    else:
        return expert_masks

def compute_feature_statistics(
    latent_vectors: np.ndarray,
    expert_masks: np.ndarray
) -> dict:
    """Compute basic statistics for extracted features."""
    stats = {
        "latent_mean": float(np.mean(latent_vectors)),
        "latent_std": float(np.std(latent_vectors)),
        "latent_min": float(np.min(latent_vectors)),
        "latent_max": float(np.max(latent_vectors)),
        "expert_activation_rate": float(np.mean(expert_masks)),
        "expert_sparsity": float(1.0 - np.mean(expert_masks)),
        "num_samples": int(latent_vectors.shape[0])
    }
    return stats
