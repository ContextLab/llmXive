"""
Generate pixel‑wise salience maps for stimulus images using DeepGaze II (CPU‑only).

This script iterates over all PNG images located in ``data/raw/ds003123/stimuli/``,
computes a salience map for each image with the DeepGaze II model, writes the
result as a ``.npy`` file into ``data/interim/salience_maps/`` and records
per‑image metadata in ``data/interim/salience_metadata.json`` that conforms
to ``contracts/salience.schema.yaml``.

The script **continues** on individual image failures, logging the error,
marking the image with ``status="failed"`` and providing an ``excluded_reason``.
It never falls back silently to a synthetic method; any unexpected exception
aborts the whole run with a clear message.
"""

import json
import sys
from pathlib import Path
from typing import List

import cv2
import numpy as np
import torch

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_deepgaze_model() -> torch.nn.Module:
    """
    Load the DeepGaze II model from the public Hugging‑Face hub.

    Returns
    -------
    torch.nn.Module
        The pretrained DeepGaze II model, set to evaluation mode and
        moved to the CPU device.
    """
    try:
        # ``torch.hub`` will download the model weights on first use.
        # The repository ``deepgaze/deepgaze-ii`` provides a callable
        # ``deepgaze_ii`` that returns a ready‑to‑use model.
        model = torch.hub.load(
            "deepgaze/deepgaze-ii",
            "deepgaze_ii",
            pretrained=True,
            source="github",
        )
        model.eval()
        model.to(torch.device("cpu"))
        logger.info("DeepGaze II model loaded successfully (CPU).")
        return model
    except Exception as exc:
        logger.error(f"Failed to load DeepGaze II model: {exc}")
        raise RuntimeError("MODEL_LOADING_ERROR") from exc

def _preprocess_image(image_path: Path) -> torch.Tensor:
    """
    Load an image with OpenCV, convert to RGB, normalise to [0, 1]
    and transform into a ``torch`` tensor of shape ``(1, 3, H, W)``.

    Parameters
    ----------
    image_path : Path
        Path to the input image.

    Returns
    -------
    torch.Tensor
        Normalised image tensor ready for the model.
    """
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image file: {image_path}")
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Convert to float32 and normalise
    img_float = img_rgb.astype(np.float32) / 255.0
    # HWC -> CHW
    img_tensor = torch.from_numpy(img_float).permute(2, 0, 1).unsqueeze(0)
    return img_tensor

def _compute_salience(model: torch.nn.Module, img_tensor: torch.Tensor) -> np.ndarray:
    """
    Run the DeepGaze II model on a pre‑processed image tensor and return
    the salience map as a NumPy array.

    Parameters
    ----------
    model : torch.nn.Module
        The pretrained DeepGaze II model.
    img_tensor : torch.Tensor
        Image tensor of shape ``(1, 3, H, W)`` on CPU.

    Returns
    -------
    np.ndarray
        Salience map of shape ``(H, W)``.
    """
    with torch.no_grad():
        output = model(img_tensor)

    if isinstance(output, dict):
        if "saliency_map" in output:
            sal_map = output["saliency_map"]
        else:
            raise RuntimeError("Unexpected model output dict structure.")
    elif isinstance(output, torch.Tensor):
        sal_map = output
    else:
        raise RuntimeError("Model returned unsupported type.")

    # Expected shape: (1, 1, H, W) or (1, H, W)
    if sal_map.dim() == 4:
        sal_map = sal_map.squeeze(0)  # (1, H, W)
    if sal_map.dim() == 3:
        sal_map = sal_map.squeeze(0)  # (H, W)

    if sal_map.dim() != 2:
        raise RuntimeError(f"Salience map has unexpected dimensions: {sal_map.shape}")

    return sal_map.cpu().numpy()

def _write_numpy_map(map_array: np.ndarray, output_path: Path) -> None:
    """
    Write a NumPy array to ``.npy`` format, creating parent directories as needed.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(output_path), map_array)

def _record_metadata(
    metadata_list: List[dict],
    stimulus_id: str,
    map_path: Path,
    height: int,
    width: int,
    generation_method: str = "deepgaze_ii",
    status: str = "success",
    excluded_reason: str | None = None,
) -> None:
    """
    Append a single metadata entry to the collection.
    """
    entry = {
        "stimulus_id": stimulus_id,
        "map_path": str(map_path),  # relative POSIX path
        "resolution": {"height": height, "width": width},
        "generation_method": generation_method,
        "status": status,
        "excluded_reason": excluded_reason,
    }
    metadata_list.append(entry)

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point for the salience‑map generation task.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = error).
    """
    try:
        # Resolve directories using the llmxive toolkit helpers.
        raw_images_dir = paths.data("raw", "ds003123", "stimuli")
        interim_maps_dir = paths.interim("salience_maps")
        metadata_path = paths.interim("salience_metadata.json")

        # Collect PNG files.
        image_paths = sorted(raw_images_dir.glob("*.png"))
        if not image_paths:
            logger.error(f"No PNG images found in {raw_images_dir}")
            raise RuntimeError("NO_IMAGES_FOUND")

        logger.info(f"Found {len(image_paths)} stimulus images to process.")

        # Load model once.
        model = _load_deepgaze_model()

        # Container for metadata entries.
        metadata_entries: List[dict] = []

        # Process each image.
        for idx, img_path in enumerate(image_paths, start=1):
            stimulus_id = img_path.stem
            logger.info(f"[{idx}/{len(image_paths)}] Processing {img_path.name}")

            # Try to read image dimensions early – useful even if salience fails.
            img_bgr = cv2.imread(str(img_path))
            if img_bgr is None:
                logger.error(f"Unable to read image for dimensions: {img_path}")
                # Record failure with unknown dimensions (set to 1 to satisfy schema)
                height, width = 1, 1
            else:
                height, width = img_bgr.shape[:2]

            try:
                img_tensor = _preprocess_image(img_path)
                sal_map = _compute_salience(model, img_tensor)

                # Save map.
                map_filename = f"{stimulus_id}.npy"
                map_path = interim_maps_dir / map_filename
                _write_numpy_map(sal_map, map_path)

                # Record metadata.
                rel_map_path = map_path.relative_to(paths.root)
                _record_metadata(
                    metadata_entries,
                    stimulus_id=stimulus_id,
                    map_path=rel_map_path,
                    height=sal_map.shape[0],
                    width=sal_map.shape[1],
                )
            except Exception as img_err:
                logger.error(f"Failed processing {img_path.name}: {img_err}")
                # Record failure metadata (use original dimensions)
                rel_map_path = (interim_maps_dir / f"{stimulus_id}.npy").relative_to(paths.root)
                _record_metadata(
                    metadata_entries,
                    stimulus_id=stimulus_id,
                    map_path=rel_map_path,
                    height=height,
                    width=width,
                    generation_method="deepgaze_ii",
                    status="failed",
                    excluded_reason=str(img_err),
                )
                # Continue to next image – do not abort the whole pipeline.
                continue

        # Write the accumulated metadata JSON.
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_entries, f, indent=2)

        logger.info(f"Salience‑map generation completed. Metadata written to {metadata_path}")
        return 0

    except Exception as e:
        logger.exception(f"Salience generation terminated with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
