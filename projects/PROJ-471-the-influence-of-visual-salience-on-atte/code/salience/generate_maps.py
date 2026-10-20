"""
Generate pixel‑wise salience maps for stimulus images using DeepGaze II.

This script iterates over all image files located in
``data/raw/ds003123/stimuli``, computes a salience map for each image using
the DeepGaze II model in CPU‑only mode, and writes the result as a ``.npy``
file into ``data/interim/salience_maps/``.

Metadata for each image is recorded in ``data/interim/salience_metadata.json``
conforming to ``contracts/salience.schema.yaml``.

Errors for individual images are logged to ``logs/salience_errors.log``.
If the DeepGaze II model cannot be loaded, the script aborts with a
RuntimeError, as per the requirement to guarantee DeepGaze II usage.
"""

import json
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch

from llmxive_toolkit import paths, get_logger

# Initialize main logger
logger = get_logger(__name__)

def _setup_error_logger() -> logging.Logger:
    """
    Configures a specific logger to write errors to logs/salience_errors.log.
    """
    error_log_path = paths.log("salience_errors.log")
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    err_logger = logging.getLogger("salience_errors")
    err_logger.setLevel(logging.ERROR)
    
    # Avoid duplicate handlers if main() is called multiple times in tests
    if not err_logger.handlers:
        fh = logging.FileHandler(str(error_log_path))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        err_logger.addHandler(fh)
    
    return err_logger

def _load_deepgaze_model() -> torch.nn.Module:
    """
    Load the DeepGaze II model from the public Hugging‑Face hub / Torch Hub.
    Must run on CPU.

    Returns
    -------
    torch.nn.Module
        The pretrained model.

    Raises
    -------
    RuntimeError
        If the model cannot be loaded.
    """
    try:
        # Set CPU threads to avoid resource contention on small runners
        torch.set_num_threads(1)
        
        # Load model via torch hub
        # DeepGaze II implementation requires timm (added to requirements.txt)
        model = torch.hub.load(
            "deepgaze/deepgaze-ii",
            "deepgaze_ii",
            pretrained=True,
            source="github",
        )
        model.eval()
        model.to(torch.device("cpu"))
        logger.info("DeepGaze II model loaded successfully (CPU).")
        return model
    except Exception as exc:
        logger.error(f"Critical failure loading DeepGaze II: {exc}")
        raise RuntimeError(f"DeepGaze II model loading failed: {exc}") from exc

def _preprocess_image(image_path: Path) -> torch.Tensor:
    """
    Load an image, convert to RGB, normalize to [0, 1], and transform 
    into a torch tensor of shape (1, 3, H, W).
    """
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image file: {image_path}")
    
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_float = img_rgb.astype(np.float32) / 255.0
    
    # (H, W, C) -> (C, H, W) -> (1, C, H, W)
    img_tensor = torch.from_numpy(img_float).permute(2, 0, 1).unsqueeze(0)
    return img_tensor

def _compute_salience_deepgaze(model: torch.nn.Module, img_tensor: torch.Tensor) -> np.ndarray:
    """
    Run DeepGaze II inference and return the salience map as a NumPy array.
    """
    with torch.no_grad():
        output = model(img_tensor)

    # Handle output types (dict or tensor)
    if isinstance(output, dict):
        if "saliency_map" in output:
            sal_map = output["saliency_map"]
        else:
            raise RuntimeError("Unexpected model output dictionary structure.")
    elif isinstance(output, torch.Tensor):
        sal_map = output
    else:
        raise RuntimeError(f"Model returned unsupported output type: {type(output)}")

    # Squeeze to (H, W)
    # DeepGaze II usually outputs (1, 1, H, W) or (1, H, W)
    if sal_map.dim() == 4:
        sal_map = sal_map.squeeze(0)  # (1, H, W)
    if sal_map.dim() == 3:
        sal_map = sal_map.squeeze(0)  # (H, W)

    if sal_map.dim() != 2:
        raise RuntimeError(f"Salience map has unexpected dimensions: {sal_map.shape}")

    return sal_map.cpu().numpy()

def main() -> int:
    """
    Entry point for salience map generation.
    """
    try:
        # 1. Setup paths and logging
        raw_images_dir = paths.data("raw", "ds003123", "stimuli")
        interim_maps_dir = paths.interim("salience_maps")
        metadata_path = paths.interim("salience_metadata.json")
        err_logger = _setup_error_logger()

        if not raw_images_dir.exists():
            # Fail loudly if dataset missing as per T002/T003 spec
            raise RuntimeError(f"DATA_MISSING_002: Stimuli directory not found at {raw_images_dir}")

        # 2. Load model (Guaranteed DeepGaze II)
        deepgaze_model = _load_deepgaze_model()

        # 3. Collect images
        image_paths = sorted(
            [p for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff")
             for p in raw_images_dir.glob(ext)]
        )
        
        if not image_paths:
            logger.warning(f"No images found in {raw_images_dir}. Nothing to process.")
            return 0

        logger.info(f"Found {len(image_paths)} images. Processing on CPU...")

        metadata_entries = []

        # 4. Process images
        for idx, img_path in enumerate(image_paths, start=1):
            stimulus_id = img_path.stem
            logger.info(f"[{idx}/{len(image_paths)}] Processing {img_path.name}")

            # Determine resolution early for metadata
            img_bgr = cv2.imread(str(img_path))
            if img_bgr is None:
                height, width = 0, 0
            else:
                height, width = img_bgr.shape[:2]

            try:
                # Preprocess and Infer
                img_tensor = _preprocess_image(img_path)
                sal_map = _compute_salience_deepgaze(deepgaze_model, img_tensor)

                # Save .npy map
                map_filename = f"{stimulus_id}.npy"
                map_path = interim_maps_dir / map_filename
                map_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(str(map_path), sal_map)

                # Record Success
                metadata_entries.append({
                    "stimulus_id": stimulus_id,
                    "map_path": str(map_path.relative_to(paths.root)),
                    "resolution": {"height": int(sal_map.shape[0]), "width": int(sal_map.shape[1])},
                    "generation_method": "deepgaze_ii",
                    "status": "success",
                    "excluded_reason": None,
                })

            except Exception as img_err:
                # Log to the specific error log file
                err_logger.error(f"Image {img_path.name} failed: {str(img_err)}")
                
                # Record Failure in metadata
                metadata_entries.append({
                    "stimulus_id": stimulus_id,
                    "map_path": str((interim_maps_dir / f"{stimulus_id}.npy").relative_to(paths.root)),
                    "resolution": {"height": height, "width": width},
                    "generation_method": "deepgaze_ii",
                    "status": "failed",
                    "excluded_reason": str(img_err),
                })
                continue

        # 5. Write metadata
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_entries, f, indent=2)

        logger.info(f"Salience generation complete. Metadata: {metadata_path}")
        return 0

    except Exception as e:
        logger.exception(f"Fatal error in salience generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
