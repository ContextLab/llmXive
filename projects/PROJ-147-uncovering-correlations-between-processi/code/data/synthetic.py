import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from code.utils.logging import get_logger, log_warning_structured

def generate_synthetic_dataset(n_samples: int = 150, families: List[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a synthetic dataset with known ground truth.
    Ensures >= 50 samples per family.
    """
    if families is None:
        families = ["Al-Mg", "Al-Zn", "Al-Cu"]

    logger = get_logger()
    samples_per_family = n_samples // len(families)
    if samples_per_family < 50:
        samples_per_family = 50
        n_samples = samples_per_family * len(families)
        log_warning_structured("Adjusted sample count to meet minimum per family", {"min_per_family": 50})

    X = []
    y = []
    labels = []

    for i, family in enumerate(families):
        # Generate processing conditions (Temperature, Strain Rate, etc.)
        # Mock physics-based generation
        n_fam = samples_per_family
        temp = np.random.uniform(300, 500, n_fam) # Kelvin
        strain_rate = np.random.uniform(0.1, 10.0, n_fam)
        
        # Mock texture coefficients (ODF intensities)
        # Correlated with processing conditions + family-specific offset
        offset = (i + 1) * 10.0
        odf_100 = 0.5 * temp + 2.0 * strain_rate + offset + np.random.normal(0, 5, n_fam)
        odf_110 = 0.3 * temp + 1.5 * strain_rate + offset + np.random.normal(0, 5, n_fam)
        odf_111 = 0.4 * temp + 1.8 * strain_rate + offset + np.random.normal(0, 5, n_fam)

        X.extend(list(zip(temp, strain_rate)))
        y.extend(list(zip(odf_100, odf_110, odf_111)))
        labels.extend([family] * n_fam)

    X = np.array(X)
    y = np.array(y)
    labels = np.array(labels)
    
    return X, y, labels

def validate_ground_truth(labels: np.ndarray, min_samples_per_family: int = 50) -> bool:
    """Validate that the generated dataset meets family count constraints."""
    unique, counts = np.unique(labels, return_counts=True)
    valid = True
    for fam, count in zip(unique, counts):
        if count < min_samples_per_family:
            valid = False
            get_logger().warning(f"Family {fam} has {count} samples, less than {min_samples_per_family}")
    return valid
