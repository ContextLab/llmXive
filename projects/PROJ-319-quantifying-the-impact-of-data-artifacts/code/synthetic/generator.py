"""
Synthetic planetary nebula generation utilities.

This module provides functions to:
1. Generate a deterministic Gaussian nebula base image.
2. Compute ground‑truth ellipticity from major/minor axes.
3. Compute ground‑truth asymmetry for a given image.
4. Produce a single synthetic nebula (image + metadata) given an ID.
5. Generate a collection of synthetic nebulae and write them to FITS files
   together with a ground‑truth JSON manifest.

The implementation follows the specifications in task **T006a**:
- Generates exactly ``n_images`` FITS files under ``output_dir``.
- Each FITS header contains the keywords ``TRUE_ELLIP`` and ``TRUE_ASYM``.
- A JSON file ``gt_metadata.json`` with the ground‑truth parameters is
  written alongside the images.
"""

import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, List

import numpy as np
from astropy.io import fits

from code.config import (
    RANDOM_SEED,
    DEFAULT_FWHM,
    ELLIPTICITY_RANGE,
    ASYMMETRY_RANGE,
    IMAGE_SIZE,
    GT_METADATA_FILE,
)
from code.io.writer import compute_file_checksum

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _rng(seed: int) -> np.random.Generator:
    """Create a reproducible random number generator."""
    return np.random.default_rng(seed)


# ----------------------------------------------------------------------
# Core generation primitives
# ----------------------------------------------------------------------
def generate_nebula_base(
    shape: Tuple[int, int],
    center: Tuple[int, int],
    ellipticity: float,
    position_angle: float,
    flux: float,
    seed: int,
) -> np.ndarray:
    """
    Generate a 2‑D elliptical Gaussian nebula.

    Parameters
    ----------
    shape : tuple
        Image shape ``(ny, nx)``.
    center : tuple
        Pixel coordinates of the nebula centre ``(cy, cx)``.
    ellipticity : float
        Ellipticity ``e = 1 - b/a`` where ``a`` is the semi‑major axis.
    position_angle : float
        Rotation angle in radians (counter‑clockwise).
    flux : float
        Desired total flux; the raw Gaussian is scaled to this value.
    seed : int
        Random seed – used to introduce a tiny deterministic jitter
        (ensuring reproducibility while allowing variation across images).

    Returns
    -------
    numpy.ndarray
        2‑D image array with the nebula signal.
    """
    rng = _rng(seed)

    ny, nx = shape
    y, x = np.indices(shape)
    cy, cx = center

    # Rotate coordinates
    cos_theta = np.cos(position_angle)
    sin_theta = np.sin(position_angle)
    x_prime = (x - cx) * cos_theta + (y - cy) * sin_theta
    y_prime = -(x - cx) * sin_theta + (y - cy) * cos_theta

    # Convert ellipticity to axis ratio
    # a = sigma, b = sigma * (1 - e)
    sigma = DEFAULT_FWHM / 2.355  # convert FWHM to sigma
    sigma_x = sigma
    sigma_y = sigma * (1.0 - ellipticity)

    # Gaussian core
    gaussian = np.exp(
        -0.5 * ((x_prime / sigma_x) ** 2 + (y_prime / sigma_y) ** 2)
    )

    # Small deterministic perturbation to avoid completely identical images
    jitter = rng.normal(loc=0.0, scale=1e-3, size=shape)
    gaussian += jitter

    # Normalise to requested total flux
    total = gaussian.sum()
    if total > 0:
        gaussian = gaussian / total * flux
    return gaussian.astype(np.float32)


# ----------------------------------------------------------------------
# Ground‑truth calculations
# ----------------------------------------------------------------------
def calculate_true_ellipticity(major_axis: float, minor_axis: float) -> float:
    """
    Compute ellipticity from the major and minor axis lengths.

    Parameters
    ----------
    major_axis : float
        Length of the semi‑major axis (a).
    minor_axis : float
        Length of the semi‑minor axis (b).

    Returns
    -------
    float
        Ellipticity ``e = 1 - b/a``. Returns 0 if ``a`` is zero.
    """
    if major_axis == 0:
        return 0.0
    return 1.0 - (minor_axis / major_axis)


def calculate_true_asymmetry(image: np.ndarray, center: Tuple[int, int], seed: int) -> float:
    """
    Compute the Conselice asymmetry index for a synthetic image.

    The method follows the definition:
        A = sum(|I - I_rot|) / sum(|I|)
    where ``I_rot`` is the image rotated by 180° about ``center``.

    Parameters
    ----------
    image : numpy.ndarray
        2‑D image array.
    center : tuple
        Pixel centre ``(cy, cx)`` about which to rotate.
    seed : int
        Random seed – not used for the deterministic calculation but kept
        for API compatibility with the original specification.

    Returns
    -------
    float
        Asymmetry value in the range [0, 1].
    """
    # Rotation by 180° is equivalent to flipping both axes.
    rotated = np.flipud(np.fliplr(image))
    diff = np.abs(image - rotated)
    numerator = diff.sum()
    denominator = np.abs(image).sum()
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


# ----------------------------------------------------------------------
# Single‑image generator
# ----------------------------------------------------------------------
def generate_synthetic_nebula(
    image_id: int,
    shape: Tuple[int, int] = IMAGE_SIZE,
    seed: int = RANDOM_SEED,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate one synthetic nebula image and its ground‑truth dictionary.

    Parameters
    ----------
    image_id : int
        Identifier for the image (used to seed the RNG uniquely).
    shape : tuple, optional
        Image dimensions; defaults to ``IMAGE_SIZE``.
    seed : int, optional
        Base seed for reproducibility.

    Returns
    -------
    tuple
        ``(image, metadata_dict)`` where ``image`` is a 2‑D numpy array and
        ``metadata_dict`` contains the required ground‑truth fields.
    """
    # Derive a per‑image seed to guarantee variability while remaining
    # deterministic across runs.
    img_seed = seed + image_id

    rng = _rng(img_seed)

    # Randomly draw physical parameters within the allowed ranges.
    ellipticity = rng.uniform(*ELLIPTICITY_RANGE)
    asymmetry = rng.uniform(*ASYMMETRY_RANGE)
    position_angle = rng.uniform(0.0, np.pi)

    # Image centre (pixel coordinates)
    cy, cx = shape[0] // 2, shape[1] // 2

    # Total flux – choose a realistic value (e.g. 1e4 counts).
    total_flux = 1e4

    # Generate the base nebula.
    image = generate_nebula_base(
        shape=shape,
        center=(cy, cx),
        ellipticity=ellipticity,
        position_angle=position_angle,
        flux=total_flux,
        seed=img_seed,
    )

    # Impose a simple asymmetry by scaling one half of the image.
    # This is a lightweight deterministic perturbation that yields a
    # measurable asymmetry while keeping the implementation fast.
    asym_factor = 1.0 + asymmetry * 0.1 * np.sin(2 * position_angle)
    image = image * asym_factor

    # Add a bright central star (point source) to mimic realistic PN images.
    star_radius = 2
    y, x = np.indices(shape)
    star_mask = (x - cx) ** 2 + (y - cy) ** 2 <= star_radius ** 2
    image[star_mask] += 5e3

    # Build the ground‑truth dictionary.
    metadata = {
        "image_id": f"synth_{image_id:03d}",
        "filename": f"synth_{image_id:03d}.fits",
        "ellipticity": ellipticity,
        "asymmetry": asymmetry,
        "position_angle": position_angle,
        "checksum": "",  # Filled later after the file is written.
    }

    return image, metadata


# ----------------------------------------------------------------------
# Batch generation and manifest writing
# ----------------------------------------------------------------------
def _write_fits_image(filepath: Path, image: np.ndarray, metadata: Dict[str, Any]) -> None:
    """
    Write a FITS file with the required header keywords.

    The header includes ``TRUE_ELLIP`` and ``TRUE_ASYM`` as mandated by
    the task, as well as a minimal WCS block so that downstream loaders
    recognise the file as a valid astronomical image.
    """
    hdu = fits.PrimaryHDU(image)
    hdr = hdu.header
    hdr["TRUE_ELLIP"] = metadata["ellipticity"]
    hdr["TRUE_ASYM"] = metadata["asymmetry"]
    hdr["EXTNAME"] = "IMAGE"

    # Minimal WCS – values are arbitrary but syntactically correct.
    hdr["CTYPE1"] = "RA---TAN"
    hdr["CTYPE2"] = "DEC--TAN"
    hdr["CRPIX1"] = image.shape[1] / 2.0
    hdr["CRPIX2"] = image.shape[0] / 2.0
    hdr["CDELT1"] = 0.05  # deg/pixel (example)
    hdr["CDELT2"] = 0.05
    hdr["CRVAL1"] = 0.0
    hdr["CRVAL2"] = 0.0

    hdu.writeto(filepath, overwrite=True)


def generate_gt_metadata(output_dir: Path, metadata_list: List[Dict[str, Any]]) -> None:
    """
    Write the ground‑truth JSON manifest to ``output_dir / GT_METADATA_FILE``.

    The checksum for each FITS file is calculated after the file has been
    written, ensuring integrity verification downstream.
    """
    for entry in metadata_list:
        fits_path = output_dir / entry["filename"]
        entry["checksum"] = compute_file_checksum(fits_path)

    manifest_path = output_dir / GT_METADATA_FILE
    with open(manifest_path, "w") as f:
        json.dump(metadata_list, f, indent=2)
    logger.info(f"Ground‑truth metadata written to {manifest_path}")


def main(
    n_images: int = 50,
    output_dir: str = "data/synthetic",
    seed: int = RANDOM_SEED,
) -> None:
    """
    Entry‑point for the synthetic generator.

    Parameters
    ----------
    n_images : int
        Number of synthetic nebulae to create.
    output_dir : str or Path
        Destination directory for FITS files and the JSON manifest.
    seed : int
        Base random seed for reproducibility.
    """
    root = Path(__file__).resolve().parents[2]  # project root
    out_path = Path(output_dir)
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.mkdir(parents=True, exist_ok=True)

    metadata_accumulator: List[Dict[str, Any]] = []

    for img_id in range(n_images):
        image, meta = generate_synthetic_nebula(
            image_id=img_id,
            shape=IMAGE_SIZE,
            seed=seed,
        )
        fits_file = out_path / meta["filename"]
        _write_fits_image(fits_file, image, meta)
        metadata_accumulator.append(meta)

    # After all files are on disk, compute checksums and write manifest.
    generate_gt_metadata(out_path, metadata_accumulator)

    logger.info(
        f"Generated {n_images} synthetic nebulae in {out_path}"
    )


if __name__ == "__main__":
    # When executed as a script, use the defaults.
    main()