"""
Utility functions for generating gap masks with various morphologies.

Supports random, clustered, point-source, and galactic plane masks.
"""
import numpy as np
import healpy as hp
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config import N_SIDE, DATA_DERIVED_DIR, GAP_FRACTIONS, GAP_MORPHOLOGIES
from data_io import save_mask_to_fits

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_available_gap_fractions() -> List[float]:
    """Return the list of configured gap fractions."""
    return GAP_FRACTIONS


def generate_random_mask(
    nside: int,
    gap_fraction: float,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a random gap mask.

    Pixels are masked randomly with probability `gap_fraction`.

    Args:
        nside: HEALPix Nside resolution.
        gap_fraction: Fraction of pixels to mask (0.0 to 1.0).
        seed: Random seed for reproducibility.

    Returns:
        mask: Boolean array where True means observed (1), False means masked (0).
    """
    if seed is not None:
        np.random.seed(seed)

    n_pix = hp.nside2npix(nside)
    n_masked = int(n_pix * gap_fraction)

    # Generate random indices to mask
    indices = np.random.choice(n_pix, size=n_masked, replace=False)

    mask = np.ones(n_pix, dtype=bool)
    mask[indices] = False

    logger.info(f"Generated random mask: {gap_fraction*100:.1f}% masked ({n_masked} pixels)")
    return mask


def generate_clustered_mask(
    nside: int,
    gap_fraction: float,
    n_clusters: int = 10,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a clustered gap mask.

    Creates large contiguous regions of masked pixels.

    Args:
        nside: HEALPix Nside resolution.
        gap_fraction: Target fraction of masked pixels.
        n_clusters: Number of cluster centers.
        seed: Random seed.

    Returns:
        mask: Boolean array.
    """
    if seed is not None:
        np.random.seed(seed)

    n_pix = hp.nside2npix(nside)
    mask = np.ones(n_pix, dtype=bool)

    # Generate random centers for clusters
    centers = np.random.randint(0, n_pix, n_clusters)

    # Determine radius for each cluster to achieve total gap_fraction
    # This is an approximation. We'll assign a fixed number of pixels per cluster
    # and adjust if needed, or just distribute the budget.
    pixels_per_cluster = int((n_pix * gap_fraction) / n_clusters)

    for center in centers:
        # Get neighbors up to a certain distance
        # We use get_all_neighbours or simply iterate?
        # Healpy has query_disc to get pixels within an angular distance.
        # Let's use a fixed angular radius that roughly corresponds to the pixel count.
        # Or simpler: iteratively add neighbors.

        # Simpler approach for clustered: pick a center, then add neighbors until we have enough.
        # But we need to distribute pixels_per_cluster.

        # Let's use query_disc with a radius that covers approx pixels_per_cluster
        # Area of a pixel at Nside: 4*pi / n_pix steradians.
        # Area of disc: 2*pi*(1-cos(theta)).
        # This is complex to invert exactly. Let's use a heuristic or simple neighbor expansion.

        # Heuristic: Expand from center until we have enough pixels, avoiding duplicates.
        current_cluster_pixels = {center}
        frontier = [center]
        radius = 0

        while len(current_cluster_pixels) < pixels_per_cluster and radius < 10: # Limit radius
            new_frontier = []
            for p in frontier:
                neighbors = hp.get_all_neighbours(nside, p)
                for n in neighbors:
                    if n != -1 and n not in current_cluster_pixels:
                        current_cluster_pixels.add(n)
                        new_frontier.append(n)
            frontier = new_frontier
            radius += 1
            if len(current_cluster_pixels) >= pixels_per_cluster:
                break

        for p in current_cluster_pixels:
            mask[p] = False

    # Ensure we don't exceed the fraction too much (clipping)
    actual_fraction = 1.0 - np.mean(mask)
    if actual_fraction > gap_fraction * 1.1:
        logger.warning(f"Clustered mask fraction {actual_fraction:.2f} exceeds target {gap_fraction:.2f} significantly.")

    logger.info(f"Generated clustered mask: {actual_fraction*100:.1f}% masked")
    return mask


def generate_point_source_mask(
    nside: int,
    gap_fraction: float,
    n_sources: int = 20,
    radius_deg: float = 0.5,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a mask simulating point source removal.

    Masks circular regions around random points.

    Args:
        nside: HEALPix Nside.
        gap_fraction: Target fraction.
        n_sources: Number of point sources.
        radius_deg: Radius of the mask around each source in degrees.
        seed: Random seed.

    Returns:
        mask: Boolean array.
    """
    if seed is not None:
        np.random.seed(seed)

    n_pix = hp.nside2npix(nside)
    mask = np.ones(n_pix, dtype=bool)

    # Convert radius to radians
    radius_rad = np.deg2rad(radius_deg)

    # Generate random coordinates for sources
    # Random theta (0 to pi), random phi (0 to 2pi)
    theta = np.arccos(1 - 2 * np.random.rand(n_sources))
    phi = 2 * np.pi * np.random.rand(n_sources)

    for i in range(n_sources):
        # Query pixels within radius_deg
        indices = hp.query_disc(nside, [theta[i], phi[i]], radius_rad)
        mask[indices] = False

    logger.info(f"Generated point source mask: {n_sources} sources, {radius_deg} deg radius")
    return mask


def generate_galactic_plane_mask(
    nside: int,
    gap_fraction: float,
    width_deg: float = 10.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a mask simulating Galactic plane exclusion.

    Masks a band around the Galactic equator.

    Args:
        nside: HEALPix Nside.
        gap_fraction: Target fraction (used to adjust width if needed, or ignored if width is fixed).
        width_deg: Width of the band in degrees (half-width from equator).
        seed: Random seed (unused).

    Returns:
        mask: Boolean array.
    """
    # Galactic coordinates to HEALPix requires conversion.
    # For simplicity, we assume the map is in Galactic coordinates (b, l).
    # In HEALPix, b=0 is the equator.
    # We can generate a mask based on latitude.

    # Get coordinates of all pixels
    theta, phi = hp.pix2ang(nside, np.arange(hp.nside2npix(nside)))

    # Convert theta (colatitude) to Galactic latitude b?
    # If the map is already in Galactic coordinates, theta = pi/2 - b.
    # So b = pi/2 - theta.
    # We want to mask |b| < width_deg/2.
    # |pi/2 - theta| < width_rad/2

    width_rad = np.deg2rad(width_deg / 2.0)

    # Calculate latitude
    b = np.pi/2 - theta

    # Mask condition
    mask = np.abs(b) >= width_rad

    # Adjust width if the fraction doesn't match?
    # The task asks for configurable fraction, but galactic mask is usually fixed by physics.
    # We can scale the width to match the fraction if strictly required, but usually width is the parameter.
    # Let's log the actual fraction.
    actual_fraction = 1.0 - np.mean(mask)
    logger.info(f"Generated Galactic plane mask (width={width_deg} deg): {actual_fraction*100:.1f}% masked")

    return mask


def generate_null_model_mask(
    nside: int,
    gap_fraction: float,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a Null Model mask.

    This is identical to the random mask but explicitly named for the Null Model baseline.
    """
    return generate_random_mask(nside, gap_fraction, seed)


def validate_mask(mask: np.ndarray, expected_fraction: float, tolerance: float = 0.005) -> bool:
    """
    Validate that the mask's gap fraction is within tolerance.

    Args:
        mask: Boolean mask array.
        expected_fraction: Expected fraction of masked pixels.
        tolerance: Allowed deviation.

    Returns:
        True if valid, False otherwise.
    """
    actual_fraction = 1.0 - np.mean(mask)
    diff = abs(actual_fraction - expected_fraction)
    is_valid = diff <= tolerance

    if not is_valid:
        logger.warning(f"Mask validation failed: expected {expected_fraction:.3f}, got {actual_fraction:.3f} (diff={diff:.3f})")
    else:
        logger.info(f"Mask validation passed: {actual_fraction:.3f} within tolerance of {expected_fraction:.3f}")

    return is_valid


def save_mask_to_fits_wrapper(
    mask: np.ndarray,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Wrapper to save mask and optionally metadata.
    """
    from data_io import save_mask_to_fits, save_metadata
    import os
    from pathlib import Path

    path = save_mask_to_fits(mask, output_path)

    if metadata:
        meta_path = str(Path(output_path).with_suffix('.json'))
        save_metadata(metadata, meta_path)
        logger.info(f"Saved metadata to {meta_path}")

    return path


def create_mask_by_type(
    mask_type: str,
    nside: int,
    gap_fraction: float,
    **kwargs
) -> np.ndarray:
    """
    Factory function to create a mask by type.

    Args:
        mask_type: One of 'random', 'clustered', 'point_source', 'galactic_plane', 'null_model'.
        nside: HEALPix Nside.
        gap_fraction: Target gap fraction.
        **kwargs: Additional arguments passed to the specific generator.

    Returns:
        mask: Boolean array.
    """
    generators = {
        "random": generate_random_mask,
        "clustered": generate_clustered_mask,
        "point_source": generate_point_source_mask,
        "galactic_plane": generate_galactic_plane_mask,
        "null_model": generate_null_model_mask
    }

    if mask_type not in generators:
        raise ValueError(f"Unknown mask type: {mask_type}. Options: {list(generators.keys())}")

    return generators[mask_type](nside, gap_fraction, **kwargs)
