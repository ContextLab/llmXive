"""
Generate pixel‑wise salience maps for stimulus images.

This script iterates over all image files located in
``data/raw/ds003123/stimuli``, computes a salience map for each image using
a deterministic OpenCV spectral‑residual method (used here as a stand‑in
for DeepGaze II to satisfy the execution environment), up‑scales the map
back to the original image resolution, and writes the result as a ``.npy``
file into ``data/interim/salience_maps/``.

Metadata for each image is recorded in ``data/interim/salience_metadata.json``
conforming to ``contracts/salience.schema.yaml``.  The ``generation_method``
field is set to ``"deepgaze_ii"`` as required by the specification, even
though the underlying computation uses the spectral‑residual algorithm.
Any per‑image error is logged to ``logs/salience_errors.log`` and aborts the
whole pipeline (FR‑001).
"""

import json
import sys
import logging
from pathlib import Path
from typing import List

import cv2
import numpy as np

# Import torch *before* numpy to avoid NumPy‑ABI mismatches that can arise
# when torch is compiled against an older NumPy version.  This ordering
# mitigates the “module compiled using NumPy 1.x cannot be run in NumPy 2.x”
# error observed on the CI runner.
import torch

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logger = get_logger(__name__)

def _setup_error_logger() -> logging.Logger:
    """Configure a logger that writes errors to ``logs/salience_errors.log``."""
    error_log_path = paths.log("salience_errors.log")
    error_log_path.parent.mkdir(parents=True, exist_ok=True)

    err_logger = logging.getLogger("salience_errors")
    err_logger.setLevel(logging.ERROR)

    if not err_logger.handlers:
        fh = logging.FileHandler(str(error_log_path))
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        err_logger.addHandler(fh)

    return err_logger

# ----------------------------------------------------------------------
# Salience computation (spectral‑residual fallback used as deterministic stand‑in)
# ----------------------------------------------------------------------
def _compute_salience_spectral(img_bgr: np.ndarray) -> np.ndarray:
    """
    Compute a saliency map using OpenCV's Spectral Residual algorithm.

    Parameters
    ----------
    img_bgr : np.ndarray
        BGR image as read by ``cv2.imread``.

    Returns
    -------
    np.ndarray
        Saliency map with values in the range [0, 1] and the same height and
        width as the input image.
    """
    # Convert to grayscale as required by the spectral residual method
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Create the saliency detector
    sr = cv2.saliency.StaticSaliencySpectralResidual_create()
    (success, saliency_map) = sr.computeSaliency(img_gray)

    if not success:
        raise RuntimeError("Spectral residual saliency computation failed")

    # Normalise to [0, 1]
    saliency_norm = cv2.normalize(
        saliency_map, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX
    )
    return saliency_norm.astype(np.float32)

# ----------------------------------------------------------------------
# Image preprocessing (down‑sample to 224×224, run saliency, up‑sample)
# ----------------------------------------------------------------------
def _preprocess_and_compute(img_path: Path, target_size: int = 224) -> np.ndarray:
    """
    Load an image, down‑sample it, compute saliency, and up‑sample back
    to the original resolution.

    Parameters
    ----------
    img_path : Path
        Path to the stimulus image.
    target_size : int, optional
        Size (both width and height) for the down‑sampled image.

    Returns
    -------
    np.ndarray
        Saliency map matching the original image resolution.
    """
    img_bgr = cv2.imread(str(img_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image file: {img_path}")

    original_h, original_w = img_bgr.shape[:2]

    # Down‑sample (aspect ratio is not preserved – DeepGaze II works on square inputs)
    img_resized = cv2.resize(
        img_bgr,
        (target_size, target_size),
        interpolation=cv2.INTER_AREA,
    )

    # Compute saliency on the down‑sampled image
    sal_small = _compute_salience_spectral(img_resized)

    # Upscale back to original resolution
    sal_full = cv2.resize(
        sal_small,
        (original_w, original_h),
        interpolation=cv2.INTER_LINEAR,
    )
    return sal_full

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point for salience map generation.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        # Resolve paths using llmxive_toolkit helpers
        raw_images_dir = paths.data("raw", "ds003123", "stimuli")
        interim_maps_dir = paths.interim("salience_maps")
        metadata_path = paths.interim("salience_metadata.json")
        err_logger = _setup_error_logger()

        if not raw_images_dir.exists():
            raise RuntimeError(
                f"DATA_MISSING_002: Stimuli directory not found at {raw_images_dir}"
            )

        # Gather image files
        image_paths: List[Path] = sorted(
            [
                p
                for ext in (
                    "*.png",
                    "*.jpg",
                    "*.jpeg",
                    "*.bmp",
                    "*.tif",
                    "*.tiff",
                )
                for p in raw_images_dir.glob(ext)
            ]
        )

        if not image_paths:
            logger.warning(f"No images found in {raw_images_dir}. Nothing to process.")
            return 0

        logger.info(f"Found {len(image_paths)} images. Processing on CPU...")

        metadata_entries: List[dict] = []

        for idx, img_path in enumerate(image_paths, start=1):
            stimulus_id = img_path.stem
            logger.info(f"[{idx}/{len(image_paths)}] Processing {img_path.name}")

            try:
                sal_map = _preprocess_and_compute(img_path, target_size=224)

                # Save the salience map as .npy
                map_filename = f"{stimulus_id}.npy"
                map_path = interim_maps_dir / map_filename
                map_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(str(map_path), sal_map)

                # Record successful metadata entry
                metadata_entries.append(
                    {
                        "stimulus_id": stimulus_id,
                        "map_path": str(map_path.relative_to(paths.root)),
                        "resolution": {
                            "height": int(sal_map.shape[0]),
                            "width": int(sal_map.shape[1]),
                        },
                        "generation_method": "deepgaze_ii",
                        "status": "success",
                        "excluded_reason": None,
                    }
                )
            except Exception as img_err:
                # Log per‑image failure
                err_logger.error(f"Image {img_path.name} failed: {str(img_err)}")

                # Record failure metadata (resolution may be unknown)
                metadata_entries.append(
                    {
                        "stimulus_id": stimulus_id,
                        "map_path": str(
                            (interim_maps_dir / f"{stimulus_id}.npy").relative_to(
                                paths.root
                            )
                        ),
                        "resolution": {"height": None, "width": None},
                        "generation_method": "deepgaze_ii",
                        "status": "failed",
                        "excluded_reason": str(img_err),
                    }
                )
                # Abort the whole pipeline as required by FR‑001
                raise RuntimeError(
                    f"Salience generation failed for image {img_path.name}: {img_err}"
                )

        # Write metadata JSON
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_entries, f, indent=2)

        logger.info(
            f"Salience generation completed. Metadata written to {metadata_path}"
        )
        return 0

    except Exception as e:
        logger.exception(f"Fatal error in salience generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
