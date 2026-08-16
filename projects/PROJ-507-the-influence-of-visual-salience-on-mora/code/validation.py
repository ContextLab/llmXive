"""
Semantic Preservation Verification Module.

This module implements the verification logic to ensure that salience manipulation
(luminance changes) does not alter the semantic content of the image regions.

It uses CLIP embeddings to compare Regions of Interest (ROI) and Backgrounds
between original and manipulated images, and computes texture/edge density changes.
"""
import os
import sys
import math
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

import numpy as np
import cv2
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# Project imports
from config import seed_everything
from logging_config import get_logger

# Ensure reproducibility
seed_everything(42)

logger = get_logger(__name__)

# Thresholds defined in task specification
THRESHOLD_ROI_SIMILARITY = 0.95
THRESHOLD_BG_SIMILARITY = 0.99
THRESHOLD_TEXTURE_CHANGE = 0.05

class SemanticPreservationError(Exception):
    """Raised when semantic preservation checks fail."""
    pass

class CLIPInferenceError(Exception):
    """Raised when CLIP inference fails due to memory or other errors."""
    pass

def load_clip_model(device: str = "cpu") -> Tuple[CLIPModel, CLIPProcessor]:
    """
    Loads the CLIP model and processor.
    Uses default precision and specified device (CPU preferred for memory constraints).
    """
    logger.info(f"Loading CLIP model on device: {device}")
    try:
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        model.to(device)
        model.eval()
        logger.info("CLIP model loaded successfully.")
        return model, processor
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        raise CLIPInferenceError(f"CLIP model loading failed: {e}") from e

def crop_region(image: Image.Image, bbox: List[int]) -> Image.Image:
    """
    Crops a region from the image given a bounding box [x, y, w, h].
    """
    x, y, w, h = bbox
    # Ensure coordinates are within image bounds
    img_w, img_h = image.size
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(img_w, x + w)
    y2 = min(img_h, y + h)

    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid bounding box: {bbox} for image size {image.size}")

    return image.crop((x1, y1, x2, y2))

def compute_laplacian_variance(image: np.ndarray) -> float:
    """
    Computes the variance of the Laplacian of the image as a measure of texture/edge density.
    Input image should be grayscale (numpy array).
    """
    # Convert to float64 for precision
    img_float = image.astype(np.float32)
    # Compute Laplacian
    laplacian = cv2.Laplacian(img_float, cv2.CV_64F)
    # Compute variance
    variance = np.var(laplacian)
    return float(variance)

def compute_embedding(model: CLIPModel, processor: CLIPProcessor, image: Image.Image, device: str) -> torch.Tensor:
    """
    Computes the CLIP embedding for a given image.
    """
    inputs = processor(images=image, return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.get_image_features(**inputs)

    # Normalize the embedding
    embedding = outputs / outputs.norm(dim=-1, keepdim=True)
    return embedding.squeeze(0)

def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
    """
    Computes the cosine similarity between two 1D tensors.
    """
    return float(torch.dot(a, b).item())

def verify_semantic_preservation(
    original_image_path: str,
    manipulated_image_path: str,
    roi_bbox: List[int],
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Verifies that the manipulation preserved semantic content.

    Logic:
    1. Crop ROI from original and manipulated. Compute CLIP embeddings.
       Verify cosine similarity >= 0.95.
    2. Crop Background (non-ROI) from original and manipulated. Compute CLIP embeddings.
       Verify cosine similarity >= 0.99.
    3. Compute Laplacian variance (texture) in ROI for both.
       Verify change < 0.05.

    Args:
        original_image_path: Path to the original image.
        manipulated_image_path: Path to the manipulated image.
        roi_bbox: Bounding box [x, y, w, h] for the Region of Interest.
        device: Device to run CLIP on ('cpu' or 'cuda').

    Returns:
        Dictionary with verification results and metrics.

    Raises:
        SemanticPreservationError: If any check fails.
    """
    logger.info(f"Verifying semantic preservation for: {original_image_path} vs {manipulated_image_path}")

    # Load images
    try:
        img_orig = Image.open(original_image_path).convert("RGB")
        img_manip = Image.open(manipulated_image_path).convert("RGB")
    except Exception as e:
        raise IOError(f"Failed to load images: {e}") from e

    # Load CLIP model
    model, processor = load_clip_model(device)

    # 1. ROI Check
    try:
        roi_orig = crop_region(img_orig, roi_bbox)
        roi_manip = crop_region(img_manip, roi_bbox)
    except ValueError as e:
        raise SemanticPreservationError(f"ROI cropping failed: {e}") from e

    emb_roi_orig = compute_embedding(model, processor, roi_orig, device)
    emb_roi_manip = compute_embedding(model, processor, roi_manip, device)
    sim_roi = cosine_similarity(emb_roi_orig, emb_roi_manip)

    logger.info(f"ROI Cosine Similarity: {sim_roi:.4f} (Threshold: {THRESHOLD_ROI_SIMILARITY})")

    # 2. Background Check
    # Create a mask for the background by cropping the whole image and masking out ROI
    # Since CLIP expects an image, we can crop the full image but we need to ensure
    # the ROI area is handled. A simple approach for "background" in this context
    # is to crop the full image but if the ROI is significant, we might need to mask it.
    # However, the task says "Crop background region (non-ROI)".
    # We will create a copy of the full image, paste black/neutral in ROI, and compare.
    # But simpler: Just compare the full image embeddings? No, task says "DO NOT compare full images".
    # So we must crop the background.
    # We'll create a background crop by taking the full image and masking the ROI with a neutral color (e.g., gray).
    # Or, if the ROI is small, we can just take the full image and hope the ROI doesn't dominate.
    # Better: Create a mask.
    bg_orig = img_orig.copy()
    bg_manip = img_manip.copy()

    # Paste a neutral gray patch over the ROI to simulate "background only"
    # This ensures the ROI content doesn't influence the embedding of the "background" crop.
    # However, the task says "Crop background region". If the ROI is a rectangle,
    # the background is the rest. We can crop the image to a bounding box that excludes the ROI?
    # No, that splits the image.
    # Let's interpret "Crop background region" as: Take the full image, but mask the ROI.
    # We will create a new image where the ROI is filled with the average color of the surrounding pixels or a neutral gray.
    # For simplicity and robustness, we will fill the ROI with a neutral gray (128, 128, 128).
    neutral_color = (128, 128, 128)
    x, y, w, h = roi_bbox
    bg_orig.paste(neutral_color, (x, y, x + w, y + h))
    bg_manip.paste(neutral_color, (x, y, x + w, y + h))

    emb_bg_orig = compute_embedding(model, processor, bg_orig, device)
    emb_bg_manip = compute_embedding(model, processor, bg_manip, device)
    sim_bg = cosine_similarity(emb_bg_orig, emb_bg_manip)

    logger.info(f"Background Cosine Similarity: {sim_bg:.4f} (Threshold: {THRESHOLD_BG_SIMILARITY})")

    # 3. Texture/Edge Density Check (Laplacian Variance)
    # Convert ROI crops to grayscale for Laplacian
    roi_orig_gray = cv2.cvtColor(np.array(roi_orig), cv2.COLOR_RGB2GRAY)
    roi_manip_gray = cv2.cvtColor(np.array(roi_manip), cv2.COLOR_RGB2GRAY)

    var_orig = compute_laplacian_variance(roi_orig_gray)
    var_manip = compute_laplacian_variance(roi_manip_gray)

    # Calculate relative change
    # Use absolute difference or relative? Task says "change < 0.05".
    # Assuming relative change: |var_orig - var_manip| / var_orig
    if var_orig == 0:
        texture_change = float('inf') if var_manip != 0 else 0.0
    else:
        texture_change = abs(var_orig - var_manip) / var_orig

    logger.info(f"ROI Texture Change (Laplacian Var): {texture_change:.4f} (Threshold: {THRESHOLD_TEXTURE_CHANGE})")

    # Verification Logic
    results = {
        "roi_similarity": sim_roi,
        "bg_similarity": sim_bg,
        "texture_change": texture_change,
        "passed_roi": sim_roi >= THRESHOLD_ROI_SIMILARITY,
        "passed_bg": sim_bg >= THRESHOLD_BG_SIMILARITY,
        "passed_texture": texture_change < THRESHOLD_TEXTURE_CHANGE,
        "overall_passed": True
    }

    if not results["passed_roi"]:
        msg = f"ROI similarity {sim_roi:.4f} < {THRESHOLD_ROI_SIMILARITY}"
        logger.error(msg)
        results["overall_passed"] = False
        raise SemanticPreservationError(msg)

    if not results["passed_bg"]:
        msg = f"Background similarity {sim_bg:.4f} < {THRESHOLD_BG_SIMILARITY}"
        logger.error(msg)
        results["overall_passed"] = False
        raise SemanticPreservationError(msg)

    if not results["passed_texture"]:
        msg = f"Texture change {texture_change:.4f} >= {THRESHOLD_TEXTURE_CHANGE}"
        logger.error(msg)
        results["overall_passed"] = False
        raise SemanticPreservationError(msg)

    logger.info("Semantic preservation verification PASSED.")
    return results

def main():
    """
    Main entry point for running semantic preservation verification.
    Expects command line arguments or environment configuration.
    For this task, we demonstrate the logic by running on a sample if paths are provided,
    or raising an error if no data is found.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Verify semantic preservation of manipulated images.")
    parser.add_argument("--original", type=str, required=True, help="Path to original image")
    parser.add_argument("--manipulated", type=str, required=True, help="Path to manipulated image")
    parser.add_argument("--x", type=int, required=True, help="ROI x coordinate")
    parser.add_argument("--y", type=int, required=True, help="ROI y coordinate")
    parser.add_argument("--w", type=int, required=True, help="ROI width")
    parser.add_argument("--h", type=int, required=True, help="ROI height")
    parser.add_argument("--device", type=str, default="cpu", help="Device for CLIP inference")

    args = parser.parse_args()

    roi_bbox = [args.x, args.y, args.w, args.h]

    try:
        results = verify_semantic_preservation(
            args.original,
            args.manipulated,
            roi_bbox,
            args.device
        )
        print("Verification Results:")
        for k, v in results.items():
            print(f"  {k}: {v}")
        sys.exit(0)
    except SemanticPreservationError as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
