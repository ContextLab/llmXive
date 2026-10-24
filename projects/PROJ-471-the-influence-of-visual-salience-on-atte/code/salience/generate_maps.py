"""
Generate pixel‑wise salience maps for stimulus images using the DeepGaze II model
(CPU‑only). The script iterates over all image files located in
``data/raw/ds003123/stimuli/``, downsamples each image to 224 × 224, runs
DeepGaze II inference, up‑scales the resulting salience map back to the
original resolution and saves it as ``<stimulus_id>.npy`` in
``data/interim/salience_maps/``. For every image a metadata entry is
appended to ``data/interim/salience_metadata.json`` that conforms to
``contracts/salience.schema.yaml`` with ``generation_method="deepgaze_ii"``
and ``status="success"``. If DeepGaze II fails for any image the pipeline
aborts with a clear error – no heuristic fallback is permitted.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List

import cv2
import numpy as np
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
# DeepGaze II model loader (CPU‑only)
# ----------------------------------------------------------------------
def _load_deepgaze_model() -> torch.nn.Module:
    """
    Load the DeepGaze II model using ``torch.hub`` in CPU‑only mode.

    Returns
    -------
    torch.nn.Module
        The pretrained DeepGaze II model ready for inference.

    Raises
    ------
    RuntimeError
        If the model cannot be loaded (e.g., network failure, missing repo).
    """
    try:
        # The official DeepGaze II repository provides a torch.hub entry point.
        # ``map_location='cpu'`` forces CPU‑only execution.
        model = torch.hub.load(
            "deepgaze/deepgaze2",
            "deepgaze2",
            pretrained=True,
            map_location="cpu",
        )
        model.eval()
        return model
    except Exception as exc:
        raise RuntimeError(f"Failed to load DeepGaze II model: {exc}") from exc

# ----------------------------------------------------------------------
# Salience computation using DeepGaze II
# ----------------------------------------------------------------------
def _compute_salience_deepgaze(img_bgr: np.ndarray, model: torch.nn.Module) -> np.ndarray:
    """
    Compute a saliency map for a BGR image using DeepGaze II.

    Parameters
    ----------
    img_bgr : np.ndarray
        Original image in OpenCV BGR format.
    model : torch.nn.Module
        Loaded DeepGaze II model.

    Returns
    -------
    np.ndarray
        Saliency map with values in the range [0, 1] and the same height and
        width as ``img_bgr``.
    """
    # Convert to RGB and normalize to [0, 1]
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

    # Convert to torch tensor (C, H, W)
    tensor = torch.from_numpy(img_rgb).permute(2, 0, 1).unsqueeze(0)  # (1, 3, H, W)

    with torch.no_grad():
        # DeepGaze II expects a tensor in the range [0, 1] on CPU.
        output = model(tensor)  # Expected shape: (1, 1, H, W) or (1, H, W)

    # Ensure output is a 2‑D map
    if isinstance(output, (list, tuple)):
        output = output[0]
    if output.dim() == 4:
        saliency = output.squeeze(0).squeeze(0)  # (H, W)
    elif output.dim() == 3:
        saliency = output.squeeze(0)            # (H, W)
    else:
        raise RuntimeError(
            f"Unexpected DeepGaze II output shape: {output.shape}"
        )

    # Convert to numpy, clamp to [0, 1] via min‑max normalisation
    sal_np = saliency.cpu().numpy()
    sal_min, sal_max = sal_np.min(), sal_np.max()
    if sal_max - sal_min > 0:
        sal_norm = (sal_np - sal_min) / (sal_max - sal_min)
    else:
        sal_norm = np.zeros_like(sal_np)

    return sal_norm.astype(np.float32)

# ----------------------------------------------------------------------
# Image preprocessing (down‑sample → saliency → up‑sample)
# ----------------------------------------------------------------------
def _preprocess_and_compute(
    img_path: Path,
    model: torch.nn.Module,
    target_size: int = 224,
) -> np.ndarray:
    """
    Load an image, down‑sample it, compute saliency with DeepGaze II,
    and up‑sample back to the original resolution.

    Parameters
    ----------
    img_path : Path
        Path to the stimulus image.
    model : torch.nn.Module
        Loaded DeepGaze II model.
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

    # Down‑sample (DeepGaze II expects square inputs)
    img_resized = cv2.resize(
        img_bgr,
        (target_size, target_size),
        interpolation=cv2.INTER_AREA,
    )

    # Compute saliency on the down‑sampled image
    sal_small = _compute_salience_deepgaze(img_resized, model)

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

        # Gather image files (common raster formats)
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

        logger.info(f"Found {len(image_paths)} images. Loading DeepGaze II model (CPU)...")
        model = _load_deepgaze_model()
        logger.info("DeepGaze II model loaded successfully.")

        metadata_entries: List[dict] = []

        for idx, img_path in enumerate(image_paths, start=1):
            stimulus_id = img_path.stem
            logger.info(f"[{idx}/{len(image_paths)}] Processing {img_path.name}")

            try:
                sal_map = _preprocess_and_compute(img_path, model, target_size=224)

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
