"""
Generate pixel‑wise salience maps for stimulus images using DeepGaze II.

This script iterates over all image files located in
``data/raw/ds003123/stimuli``, computes a salience map for each image using
the DeepGaze II model in CPU‑only mode (on a 224 × 224 down‑sampled
version), up‑scales the map back to the original image resolution, and
writes the result as a ``.npy`` file into ``data/interim/salience_maps/``.

Metadata for each image is recorded in ``data/interim/salience_metadata.json``
conforming to ``contracts/salience.schema.yaml``.

Errors for individual images are logged to ``logs/salience_errors.log``.
If the DeepGaze II model cannot be loaded, the script aborts with a
``RuntimeError``, as required by FR‑001.
"""

import json
import sys
import logging
from pathlib import Path
from typing import List

import cv2

# Import torch *before* numpy to avoid NumPy‑ABI mismatches that can arise
# when torch is compiled against an older NumPy version.  This ordering
# mitigates the “module compiled using NumPy 1.x cannot be run in NumPy 2.x”
# error observed on the CI runner.
import torch

import numpy as np

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
# DeepGaze II model handling
# ----------------------------------------------------------------------
def _load_deepgaze_model() -> torch.nn.Module:
    """
    Load the DeepGaze II model (CPU‑only).

    Returns
    -------
    torch.nn.Module
        The pretrained DeepGaze II model.

    Raises
    ------
    RuntimeError
        If the model cannot be loaded.
    """
    try:
        # Restrict Torch to a single thread on the limited CI runner
        torch.set_num_threads(1)

        # Prefer the pip‑installed wrapper if available
        try:
            from deepgaze2_pytorch import DeepGazeII  # type: ignore
            model = DeepGazeII(pretrained=True)
            logger.info("DeepGaze II model loaded via deepgaze2_pytorch package.")
        except Exception as inner_exc:
            # Fallback to torch.hub (may require internet)
            logger.info("deepgaze2_pytorch not available, trying torch.hub.")
            model = torch.hub.load(
                "deepgaze/deepgaze-ii",
                "deepgaze_ii",
                pretrained=True,
                source="github",
            )
            logger.info("DeepGaze II model loaded via torch.hub.")

        model.eval()
        model.to(torch.device("cpu"))
        return model
    except Exception as exc:
        logger.error(f"Failed to load DeepGaze II model: {exc}")
        raise RuntimeError(f"DeepGaze II model loading failed: {exc}") from exc

# ----------------------------------------------------------------------
# Image preprocessing & salience computation
# ----------------------------------------------------------------------
def _preprocess_image(image_path: Path, target_size: int = 224) -> torch.Tensor:
    """
    Load an image, resize it to ``target_size`` × ``target_size``,
    convert to RGB, normalise to [0, 1], and return a torch tensor of shape
    (1, 3, H, W).

    Parameters
    ----------
    image_path : Path
        Path to the image file.
    target_size : int, optional
        Desired width/height after resizing (default 224).

    Returns
    -------
    torch.Tensor
        Tensor ready for model inference.
    """
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image file: {image_path}")

    # Resize to target size (aspect ratio not required for DeepGaze II)
    img_resized = cv2.resize(
        img_bgr, (target_size, target_size), interpolation=cv2.INTER_AREA
    )

    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_float = img_rgb.astype(np.float32) / 255.0

    # (H, W, C) -> (C, H, W) -> (1, C, H, W)
    img_tensor = torch.from_numpy(img_float).permute(2, 0, 1).unsqueeze(0)
    return img_tensor

def _compute_salience_deepgaze(
    model: torch.nn.Module, img_tensor: torch.Tensor
) -> np.ndarray:
    """
    Run the DeepGaze II model on ``img_tensor`` and return a salience map
    as a NumPy array (2‑D, values in the model's native range).

    Parameters
    ----------
    model : torch.nn.Module
        Loaded DeepGaze II model.
    img_tensor : torch.Tensor
        Pre‑processed image tensor (1, 3, H, W).

    Returns
    -------
    np.ndarray
        Salience map (H, W).
    """
    with torch.no_grad():
        output = model(img_tensor)

    # DeepGaze II may return a dict or a tensor
    if isinstance(output, dict):
        if "saliency_map" in output:
            sal_map = output["saliency_map"]
        else:
            raise RuntimeError("Unexpected DeepGaze II output dictionary.")
    elif isinstance(output, torch.Tensor):
        sal_map = output
    else:
        raise RuntimeError(f"Unsupported DeepGaze II output type: {type(output)}")

    # Reduce dimensions to (H, W)
    if sal_map.dim() == 4:
        sal_map = sal_map.squeeze(0)  # (1, H, W)
    if sal_map.dim() == 3:
        sal_map = sal_map.squeeze(0)  # (H, W)

    if sal_map.dim() != 2:
        raise RuntimeError(f"Salience map has unexpected shape: {sal_map.shape}")

    return sal_map.cpu().numpy()

def _upscale_salience(sal_map: np.ndarray, target_shape: tuple) -> np.ndarray:
    """
    Upscale a salience map to ``target_shape`` (height, width) using bilinear
    interpolation.

    Parameters
    ----------
    sal_map : np.ndarray
        Salience map produced at 224 × 224.
    target_shape : tuple
        Desired (height, width) of the up‑scaled map.

    Returns
    -------
    np.ndarray
        Upscaled salience map with shape ``target_shape``.
    """
    height, width = target_shape
    upscaled = cv2.resize(sal_map, (width, height), interpolation=cv2.INTER_LINEAR)
    return upscaled

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
        # Paths
        raw_images_dir = paths.data("raw", "ds003123", "stimuli")
        interim_maps_dir = paths.interim("salience_maps")
        metadata_path = paths.interim("salience_metadata.json")
        err_logger = _setup_error_logger()

        if not raw_images_dir.exists():
            raise RuntimeError(
                f"DATA_MISSING_002: Stimuli directory not found at {raw_images_dir}"
            )

        # Load DeepGaze II (must succeed)
        deepgaze_model = _load_deepgaze_model()

        # Gather image files
        image_paths: List[Path] = sorted(
            [
                p
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff")
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

            # Load original image to obtain its resolution
            img_original = cv2.imread(str(img_path))
            if img_original is None:
                height, width = 0, 0
            else:
                height, width = img_original.shape[:2]

            try:
                # Pre‑process (down‑sample) and run inference
                img_tensor = _preprocess_image(img_path, target_size=224)
                sal_map_small = _compute_salience_deepgaze(deepgaze_model, img_tensor)

                # Upscale back to original resolution
                if height > 0 and width > 0:
                    sal_map = _upscale_salience(sal_map_small, (height, width))
                else:
                    # If original image could not be read, keep the small map
                    sal_map = sal_map_small

                # Save .npy file
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
                            (interim_maps_dir / f"{stimulus_id}.npy").relative_to(paths.root)
                        ),
                        "resolution": {"height": int(height), "width": int(width)},
                        "generation_method": "deepgaze_ii",
                        "status": "failed",
                        "excluded_reason": str(img_err),
                    }
                )
                # Abort the whole pipeline as required by FR‑001
                raise RuntimeError(
                    f"DeepGaze II processing failed for image {img_path.name}: {img_err}"
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
