"""Analysis utilities for stability metrics of rotating dipolar BECs.

This module provides a collection of functions that compute quantitative
stability metrics from density maps produced by the GPE solver.  All
public functions and the :class:`MetricResult` dataclass are documented
with NumPy‑style docstrings to satisfy the ``pydocstyle`` contract.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from models.entities import StabilityMetric

@dataclass
class MetricResult:
    """Container for the calculated stability metrics of a single snapshot.

    Attributes
    ----------
    vortex_density : float
        Number of vortices per unit area.
    radial_variance : float
        Variance of the radial density profile.
    structure_factor_sharpness : float
        Sharpness of the first Bragg peak in the structure factor.
    """
    vortex_density: float
    radial_variance: float
    structure_factor_sharpness: float

def calculate_vortex_density(density_map: np.ndarray) -> float:
    """Calculate the vortex density from a density map.

    The vortex density is defined as the number of detected vortices
    divided by the physical area of the simulation domain.

    Parameters
    ----------
    density_map : numpy.ndarray
        2‑D array containing the condensate density.

    Returns
    -------
    float
        Vortex density (vortices per unit area).
    """
    # Placeholder implementation – the real implementation resides in
    # ``analysis.vortex_detector.detect_vortices_density``.  Here we
    # delegate to that function to keep a single source of truth.
    from analysis.vortex_detector import detect_vortices_density

    # Assume a uniform grid spacing of 1.0 (the caller provides the
    # correct spacing if needed).
    return detect_vortices_density(density_map, dx=1.0)

def calculate_radial_variance(density_map: np.ndarray) -> float:
    """Calculate the radial variance of a density map.

    Radial variance quantifies how much the density distribution deviates
    from perfect radial symmetry.  It is computed as the variance of the
    density values when binned in concentric annuli.

    Parameters
    ----------
    density_map : numpy.ndarray
        2‑D array containing the condensate density.

    Returns
    -------
    float
        Radial variance of the density profile.
    """
    # Compute radial coordinates relative to the centre of the array.
    ny, nx = density_map.shape
    y = np.arange(ny) - ny // 2
    x = np.arange(nx) - nx // 2
    X, Y = np.meshgrid(x, y, indexing="ij")
    r = np.sqrt(X**2 + Y**2)

    # Bin by integer radius.
    max_r = int(r.max()) + 1
    radial_means = np.zeros(max_r)
    counts = np.zeros(max_r, dtype=int)

    for rad in range(max_r):
        mask = (r >= rad) & (r < rad + 1)
        counts[rad] = mask.sum()
        if counts[rad] > 0:
            radial_means[rad] = density_map[mask].mean()

    # Compute variance of the radial means.
    return float(np.var(radial_means[counts > 0]))

def calculate_structure_factor_sharpness(density_map: np.ndarray) -> float:
    """Calculate the sharpness of the structure factor.

    The structure factor is obtained via a 2‑D Fourier transform of the
    density map.  Sharpness is measured as the ratio of the maximum peak
    height to the average background level.

    Parameters
    ----------
    density_map : numpy.ndarray
        2‑D array containing the condensate density.

    Returns
    -------
    float
        Sharpness metric (dimensionless, higher means sharper peaks).
    """
    # Perform Fourier transform.
    ft = np.fft.fftshift(np.fft.fft2(density_map))
    power_spectrum = np.abs(ft) ** 2

    # Identify the central peak and background.
    ny, nx = power_spectrum.shape
    center = (ny // 2, nx // 2)
    peak = power_spectrum[center]

    # Estimate background as the median of the outer ring.
    radius = min(ny, nx) // 4
    y, x = np.ogrid[:ny, :nx]
    mask = (x - center[1]) ** 2 + (y - center[0]) ** 2 > radius ** 2
    background = np.median(power_spectrum[mask])

    return float(peak / (background + 1e-12))

def classify_metastability(vortex_density: float, condensate_density: float) -> str:
    """Classify the stability of a condensate based on metrics.

    According to Constitution‑VII, a condensate is considered
    metastable if **either** the vortex density exceeds a configurable
    threshold **or** the condensate density drops below a configurable
    fraction of its initial value.

    Parameters
    ----------
    vortex_density : float
        Vortex density computed by :func:`calculate_vortex_density`.
    condensate_density : float
        Mean condensate density (or a reference density).

    Returns
    -------
    str
        One of ``"stable"``, ``"metastable"``, or ``"unstable"``.
    """
    # Thresholds are defined in the project configuration; for the
    # purpose of this module we use the canonical values.
    VORTEX_DENSITY_THRESHOLD = 0.2  # vortices per unit area
    DENSITY_DROP_FRACTION = 0.7     # 30 % drop allowed

    if vortex_density > VORTEX_DENSITY_THRESHOLD:
        return "metastable"
    if condensate_density < DENSITY_DROP_FRACTION:
        return "metastable"
    return "stable"

def calculate_false_positive_rate(predictions: List[str], ground_truth: List[str]) -> float:
    """Calculate the false‑positive rate for metastability predictions.

    The false‑positive rate is defined as

    ``FP / (FP + TN)``

    where *FP* is the number of predictions that incorrectly label an
    unstable run as metastable, and *TN* is the number of correctly
    labeled stable runs.

    Parameters
    ----------
    predictions : list of str
        Predicted class labels (e.g., ``["stable", "metastable", ...]``).
    ground_truth : list of str
        Ground‑truth class labels.

    Returns
    -------
    float
        False‑positive rate in the range ``[0, 1]``.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Prediction and ground‑truth lists must have the same length.")
    fp = sum(p == "metastable" and g != "metastable" for p, g in zip(predictions, ground_truth))
    tn = sum(p != "metastable" and g != "metastable" for p, g in zip(predictions, ground_truth))
    if (fp + tn) == 0:
        return 0.0
    return fp / (fp + tn)

def calculate_false_negative_rate(predictions: List[str], ground_truth: List[str]) -> float:
    """Calculate the false‑negative rate for metastability predictions.

    The false‑negative rate is defined as

    ``FN / (FN + TP)``

    where *FN* is the number of predictions that incorrectly label a
    metastable run as stable, and *TP* is the number of correctly
    identified metastable runs.

    Parameters
    ----------
    predictions : list of str
        Predicted class labels.
    ground_truth : list of str
        Ground‑truth class labels.

    Returns
    -------
    float
        False‑negative rate in the range ``[0, 1]``.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Prediction and ground‑truth lists must have the same length.")
    fn = sum(p != "metastable" and g == "metastable" for p, g in zip(predictions, ground_truth))
    tp = sum(p == "metastable" and g == "metastable" for p, g in zip(predictions, ground_truth))
    if (fn + tp) == 0:
        return 0.0
    return fn / (fn + tp)

def process_snapshot_file(file_path: str) -> MetricResult:
    """Process a single snapshot file and compute all metrics.

    Parameters
    ----------
    file_path : str
        Path to a ``.npy`` file containing the density snapshot.

    Returns
    -------
    MetricResult
        Dataclass instance with all computed metrics.
    """
    density_map = np.load(file_path)
    vortex_density = calculate_vortex_density(density_map)
    radial_variance = calculate_radial_variance(density_map)
    structure_factor_sharpness = calculate_structure_factor_sharpness(density_map)
    return MetricResult(
        vortex_density=vortex_density,
        radial_variance=radial_variance,
        structure_factor_sharpness=structure_factor_sharpness,
    )

def calculate_all_metrics(density_map: np.ndarray) -> MetricResult:
    """Convenience wrapper to compute all metrics from an in‑memory array.

    Parameters
    ----------
    density_map : numpy.ndarray
        2‑D density array.

    Returns
    -------
    MetricResult
        Container with the three stability metrics.
    """
    return MetricResult(
        vortex_density=calculate_vortex_density(density_map),
        radial_variance=calculate_radial_variance(density_map),
        structure_factor_sharpness=calculate_structure_factor_sharpness(density_map),
    )

def main() -> None:
    """Simple command‑line entry point for manual testing.

    The function parses a single positional argument – the path to a
    ``.npy`` density file – and prints the computed metrics as JSON.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Compute stability metrics for a GPE snapshot.")
    parser.add_argument("snapshot", help="Path to the .npy density snapshot.")
    args = parser.parse_args()
    result = process_snapshot_file(args.snapshot)
    print(json.dumps(result.__dict__, indent=2))

if __name__ == "__main__":
    main()
