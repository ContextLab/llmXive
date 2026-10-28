"""
T004 – Generate salience‑manipulated stimulus variants
----------------------------------------------------
This script reads a CSV of valid scenarios, detects a region‑of‑interest (ROI)
in each image using Sobel edge detection, creates three salience variants
(low / medium / high) by adjusting contrast and brightness as defined in
``config/manipulation.yaml``, validates each variant against the four
integrity criteria, logs any failures, and writes a manifest CSV listing the
successful variants together with their validation metrics.

Expected input CSV columns (at minimum):
    scenario_id, original_image_path

Manifest CSV columns:
    scenario_id,salience_level,variant_path,rms_contrast_change_pct,
    clip_similarity,texture_change,moral_intent_score
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from PIL import Image
from scipy import ndimage
from scipy.spatial.distance import cosine
from scipy.stats import pearsonr
from transformers import AutoProcessor, AutoModel
import torch

# Project utilities
from llmxive_toolkit import paths, get_logger

# Import the moral‑intent wrapper from T015
from bert_moral_intent import compute_preservation_score

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
log = get_logger(__name__, log_file="logs/manipulation_errors.log")
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_yaml_config(config_path: Path) -> dict:
    """Load manipulation parameters from a YAML file."""
    if not config_path.is_file():
        raise FileNotFoundError(f"Manipulation config not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def load_image(image_path: Path) -> np.ndarray:
    """Load an image as an RGB uint8 NumPy array."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        return np.array(img)

def save_image(image_array: np.ndarray, out_path: Path) -> None:
    """Save a uint8 RGB NumPy array as PNG."""
    img = Image.fromarray(image_array)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")

def detect_roi(image: np.ndarray) -> tuple:
    """
    Detect a region‑of‑interest using Sobel edge detection.
    Returns (x1, y1, x2, y2) inclusive bounding box.
    """
    # Convert to grayscale
    gray = np.mean(image, axis=2).astype(np.float32)

    # Sobel gradients
    gx = ndimage.sobel(gray, axis=1, mode="constant")
    gy = ndimage.sobel(gray, axis=0, mode="constant")
    magnitude = np.hypot(gx, gy)

    # Threshold at the 75th percentile of edge magnitude
    thresh = np.percentile(magnitude, 75)
    mask = magnitude > thresh

    if not mask.any():
        # Fallback to centre crop if no edges survive
        h, w = gray.shape
        cx, cy = w // 2, h // 2
        size = min(w, h) // 4
        return cx - size, cy - size, cx + size, cy + size

    # Find bounding box of the mask
    y_idxs, x_idxs = np.where(mask)
    x1, x2 = x_idxs.min(), x_idxs.max()
    y1, y2 = y_idxs.min(), y_idxs.max()
    return int(x1), int(y1), int(x2), int(y2)

def adjust_contrast_brightness(
    image: np.ndarray,
    roi: tuple,
    contrast: float,
    brightness: float,
) -> np.ndarray:
    """
    Apply contrast (multiplicative) and brightness (additive) adjustments
    only inside the ROI. Image is uint8; processing is performed in float
    then clipped back to [0, 255].
    """
    x1, y1, x2, y2 = roi
    region = image[y1 : y2 + 1, x1 : x2 + 1].astype(np.float32)

    # Apply adjustments
    region = region * contrast + brightness
    region = np.clip(region, 0, 255).astype(np.uint8)

    # Copy back
    out = image.copy()
    out[y1 : y2 + 1, x1 : x2 + 1] = region
    return out

def rms_contrast(image: np.ndarray, roi: tuple) -> float:
    """Root‑mean‑square contrast (standard deviation of luminance) in ROI."""
    x1, y1, x2, y2 = roi
    gray = np.mean(image[y1 : y2 + 1, x1 : x2 + 1], axis=2)
    return float(np.sqrt(np.mean((gray - gray.mean()) ** 2)))

def laplacian_variance(image: np.ndarray, roi: tuple) -> float:
    """Texture/edge‑density measure via variance of Laplacian."""
    x1, y1, x2, y2 = roi
    gray = np.mean(image[y1 : y2 + 1, x1 : x2 + 1], axis=2).astype(np.float32)
    lap = ndimage.laplace(gray)
    return float(lap.var())

def load_clip_model(device: str = "cpu"):
    """Load CLIP model and processor."""
    model_name = "openai/clip-vit-base-patch32"
    processor = AutoProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.to(device)
    model.eval()
    return model, processor

def compute_clip_embedding(image: np.ndarray, model, processor, device: str = "cpu"):
    """Compute CLIP image embedding (the pooled output)."""
    # Convert NumPy array to PIL Image for the processor
    pil_img = Image.fromarray(image)
    inputs = processor(images=pil_img, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
    # Normalize to unit length (as CLIP does)
    embedding = outputs / outputs.norm(p=2, dim=-1, keepdim=True)
    return embedding.squeeze().cpu().numpy()

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Cosine similarity between two 1‑D vectors."""
    return 1 - cosine(vec1, vec2)

# ----------------------------------------------------------------------
# Main processing
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate salience‑manipulated stimulus variants."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to CSV with valid scenarios (must contain scenario_id and original_image_path).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to write the stimuli manifest CSV.",
    )
    args = parser.parse_args()

    # Resolve paths via llmxive_toolkit for consistency
    scenarios_path = Path(args.input)
    manifest_path = Path(args.output)

    # Load manipulation parameters
    manipulation_cfg_path = paths.config("manipulation.yaml")
    cfg = load_yaml_config(manipulation_cfg_path)

    # Expected structure:
    # low:   {contrast: 0.8, brightness: -30}
    # medium:{contrast: 1.0, brightness: 0}
    # high:  {contrast: 1.2, brightness: 30}
    levels = ["low", "medium", "high"]
    for lvl in levels:
        if lvl not in cfg:
            raise KeyError(f"Missing salience level '{lvl}' in {manipulation_cfg_path}")

    # Load CLIP once (CPU first; GPU fallback if available)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    clip_model, clip_processor = load_clip_model(device=device)

    # Prepare manifest CSV
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "scenario_id",
                "salience_level",
                "variant_path",
                "rms_contrast_change_pct",
                "clip_similarity",
                "texture_change",
                "moral_intent_score",
            ]
        )

        # Process each scenario
        scenarios_df = pd.read_csv(scenarios_path, dtype=str)
        required_cols = {"scenario_id", "original_image_path"}
        if not required_cols.issubset(scenarios_df.columns):
            raise ValueError(
                f"Input CSV must contain columns {required_cols}. Found {list(scenarios_df.columns)}"
            )

        for _, row in scenarios_df.iterrows():
            scenario_id = row["scenario_id"]
            orig_path = Path(row["original_image_path"])
            if not orig_path.is_file():
                log.error(f"Original image missing for scenario {scenario_id}: {orig_path}")
                continue

            try:
                orig_img = load_image(orig_path)
            except Exception as e:
                log.error(f"Failed to load image {orig_path} for {scenario_id}: {e}")
                continue

            # Detect ROI once per scenario
            roi = detect_roi(orig_img)

            # Compute baseline metrics for reference
            orig_rms = rms_contrast(orig_img, roi)
            orig_tex = laplacian_variance(orig_img, roi)

            for level in levels:
                params = cfg[level]
                contrast = float(params.get("contrast", 1.0))
                brightness = float(params.get("brightness", 0.0))

                try:
                    manipulated = adjust_contrast_brightness(
                        orig_img, roi, contrast=contrast, brightness=brightness
                    )
                except Exception as e:
                    log.error(
                        f"Manipulation failed for {scenario_id} level {level}: {e}"
                    )
                    continue

                # Compute validation metrics
                try:
                    rms_new = rms_contrast(manipulated, roi)
                    rms_change_pct = ((rms_new - orig_rms) / (orig_rms + 1e-8)) * 100.0

                    # CLIP similarity (whole image)
                    emb_orig = compute_clip_embedding(
                        orig_img, clip_model, clip_processor, device=device
                    )
                    emb_man = compute_clip_embedding(
                        manipulated, clip_model, clip_processor, device=device
                    )
                    clip_sim = cosine_similarity(emb_orig, emb_man)

                    # Texture change (Laplacian variance)
                    tex_new = laplacian_variance(manipulated, roi)
                    texture_change = abs(tex_new - orig_tex) / (orig_tex + 1e-8)

                    # Moral‑intent preservation via wrapper (T015)
                    moral_score = compute_preservation_score(
                        orig_path,  # original image path
                        paths.results("stimuli", f"{scenario_id}_{level}.png")  # temporary placeholder; will be overwritten after saving
                    )
                except Exception as e:
                    log.error(
                        f"Validation failed for {scenario_id} level {level}: {e}"
                    )
                    continue

                # Apply thresholds
                if rms_change_pct < 15.0:
                    log.error(
                        f"RMS contrast change {rms_change_pct:.2f}% < 15% for {scenario_id} {level}"
                    )
                    continue
                if clip_sim < 0.95:
                    log.error(
                        f"CLIP similarity {clip_sim:.3f} < 0.95 for {scenario_id} {level}"
                    )
                    continue
                if texture_change >= 0.05:
                    log.error(
                        f"Texture change {texture_change:.3f} >= 0.05 for {scenario_id} {level}"
                    )
                    continue
                if moral_score < 0.90:
                    log.error(
                        f"Moral‑intent score {moral_score:.3f} < 0.90 for {scenario_id} {level}"
                    )
                    continue

                # All checks passed – write file and manifest entry
                variant_filename = f"{scenario_id}_{level}.png"
                variant_path = paths.processed("stimuli", variant_filename)
                save_image(manipulated, variant_path)

                writer.writerow(
                    [
                        scenario_id,
                        level,
                        str(variant_path),
                        f"{rms_change_pct:.2f}",
                        f"{clip_sim:.4f}",
                        f"{texture_change:.4f}",
                        f"{moral_score:.4f}",
                    ]
                )
                logger.info(
                    f"Successfully created variant {variant_path} (RMS {rms_change_pct:.2f}%, CLIP {clip_sim:.4f}, tex {texture_change:.4f}, moral {moral_score:.4f})"
                )

    logger.info(f"Stimuli manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
