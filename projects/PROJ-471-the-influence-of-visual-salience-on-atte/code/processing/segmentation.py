"""
Segmentation module for generating semantic masks for 'Face' regions.

Uses YOLOv8 to detect faces (or persons if a specific face model is unavailable)
and generates binary masks.

Logic:
1. Check if pre-segmented masks exist in the dataset.
2. If missing, run YOLOv8 (CPU mode) to generate masks.
3. Save masks to data/interim/segmentation_masks/

Note: "Weapons" (FR-008) are excluded per SCR (T020a-c). Only Face ROIs are processed.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Union

import numpy as np
import cv2
import torch

from config import get_paths
from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
MODEL_NAME = "yolov8n-face.pt"  # YOLOv8 Nano Face model
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
DEVICE = "cpu"  # Enforce CPU for stability in this pipeline

# COCO Class Mapping (if using standard YOLOv8n, 0 is person. 
# If using yolov8n-face.pt, 0 is face).
# We assume the face model is used, so class 0 = face.
FACE_CLASS_ID = 0 

MASKS_DIR_NAME = "segmentation_masks"

def load_image(image_path: Union[str, Path]) -> np.ndarray:
    """
    Load an image from disk.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Image as a numpy array (H, W, C).
        
    Raises:
        FileNotFoundError: If the image does not exist.
        ValueError: If the image cannot be loaded.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Convert BGR to RGB for consistency with typical deep learning inputs
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def run_yolo_segmentation(image_path: Union[str, Path]) -> List:
    """
    Run YOLOv8 segmentation on an image.
    
    Args:
        image_path: Path to the image.
        
    Returns:
        List of detection results from the model.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        raise ImportError("ultralytics package is required. Install with: pip install ultralytics")

    logger.info(f"Loading YOLOv8 model: {MODEL_NAME}")
    model = YOLO(MODEL_NAME)
    
    logger.info(f"Running segmentation on {image_path} (Device: {DEVICE})")
    results = model(
        source=str(image_path),
        conf=CONF_THRESHOLD,
        iou=IOU_THRESHOLD,
        device=DEVICE,
        verbose=False
    )
    
    return results

def generate_face_mask(image_path: Union[str, Path]) -> Optional[np.ndarray]:
    """
    Generate a binary mask for the 'Face' region in an image.
    
    Args:
        image_path: Path to the input image.
        
    Returns:
        Binary mask (H, W) where 255 indicates face, 0 otherwise.
        Returns None if no face is detected.
    """
    image_path = Path(image_path)
    img = load_image(image_path)
    h, w = img.shape[:2]
    
    results = run_yolo_segmentation(image_path)
    
    if not results or len(results) == 0:
        logger.warning(f"No detections found in {image_path}")
        return None
    
    result = results[0]
    
    if result.masks is None:
        logger.warning(f"No masks found in {image_path}")
        return None
    
    # Initialize empty mask
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Iterate over detections
    # result.masks.xy contains polygon coordinates
    # result.masks.data contains binary mask tensor (1, H, W) if available
    
    # Using masks.data is more direct if available
    if result.masks.data is not None:
        # result.masks.data shape: (N, H, W)
        # We need to combine all face detections (N detections)
        # Assuming class 0 is face
        if result.boxes.cls is not None:
            face_indices = np.where(result.boxes.cls == FACE_CLASS_ID)[0]
            if len(face_indices) > 0:
                # Combine masks for all face detections
                combined_mask = np.zeros((h, w), dtype=np.uint8)
                for idx in face_indices:
                    # Extract mask for this detection
                    # The mask data is typically normalized or binary
                    # ultralytics returns masks.data as bool or float
                    m = result.masks.data[idx].cpu().numpy()
                    # Resize if necessary (should match image size usually)
                    if m.shape != (h, w):
                        # Resize using nearest neighbor to preserve binary nature
                        m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
                    combined_mask = np.maximum(combined_mask, m)
                
                mask = (combined_mask * 255).astype(np.uint8)
                return mask
        else:
            logger.warning(f"No face class (ID {FACE_CLASS_ID}) detected in {image_path}")
            return None
    else:
        # Fallback to polygon coordinates if masks.data is missing
        logger.warning("masks.data not available, attempting polygon reconstruction")
        if result.masks.xy is not None:
            polygons = result.masks.xy
            classes = result.boxes.cls
            for i, poly in enumerate(polygons):
                if classes[i] == FACE_CLASS_ID:
                    pts = poly.astype(np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(mask, [pts], 255)
            return mask if np.any(mask > 0) else None
        
    return None

def process_image_for_masks(image_path: Union[str, Path]) -> Optional[Path]:
    """
    Process a single image to generate and save its face mask.
    
    Checks for existing mask first. If missing, generates one.
    
    Args:
        image_path: Path to the input image.
        
    Returns:
        Path to the saved mask file, or None if processing failed.
    """
    image_path = Path(image_path)
    paths = get_paths()
    
    # Define output path
    # Assuming the output directory structure matches the data model
    # data/interim/segmentation_masks/
    mask_dir = paths.data_interim / MASKS_DIR_NAME
    mask_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename: {original_name}_mask.npy
    stem = image_path.stem
    output_filename = f"{stem}_mask.npy"
    output_path = mask_dir / output_filename
    
    # Check if mask already exists
    if output_path.exists():
        logger.info(f"Mask already exists, skipping: {output_path}")
        return output_path
    
    # Generate mask
    try:
        mask = generate_face_mask(image_path)
        if mask is None:
            logger.warning(f"Failed to generate mask for {image_path} (no face detected)")
            return None
        
        # Save mask
        np.save(output_path, mask)
        logger.info(f"Saved mask: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating mask for {image_path}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for segmentation processing.
    Iterates over all images in data/raw and generates masks.
    """
    paths = get_paths()
    raw_images_dir = paths.data_raw / "images" # Assuming images are here
    
    if not raw_images_dir.exists():
        logger.error(f"Raw images directory not found: {raw_images_dir}")
        return
    
    image_files = list(raw_images_dir.glob("*.jpg")) + list(raw_images_dir.glob("*.png"))
    
    if not image_files:
        logger.warning(f"No images found in {raw_images_dir}")
        return
    
    logger.info(f"Found {len(image_files)} images to process.")
    
    for img_path in image_files:
        process_image_for_masks(img_path)
    
    logger.info("Segmentation processing complete.")

if __name__ == "__main__":
    main()
