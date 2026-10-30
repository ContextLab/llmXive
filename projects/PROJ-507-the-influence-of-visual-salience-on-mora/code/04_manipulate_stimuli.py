"""
T004 – Generate salience-manipulated stimulus variants.
"""
import argparse
import csv
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from PIL import Image
from scipy import ndimage
from scipy.spatial.distance import cosine
from transformers import AutoProcessor, AutoModel
import torch

from llmxive_toolkit import paths, get_logger
from bert_moral_intent import compute_preservation_score

log = get_logger(__name__, log_file="logs/manipulation_errors.log")
logger = logging.getLogger(__name__)

def load_yaml_config(config_path: Path) -> dict:
    if not config_path.is_file():
        raise FileNotFoundError(f"Manipulation config not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def load_image(image_path: Path) -> np.ndarray:
    with Image.open(image_path) as img:
        return np.array(img.convert("RGB"))

def save_image(image_array: np.ndarray, out_path: Path) -> None:
    img = Image.fromarray(image_array)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")

def detect_roi(image: np.ndarray) -> tuple:
    gray = np.mean(image, axis=2).astype(np.float32)
    gx = ndimage.sobel(gray, axis=1)
    gy = ndimage.sobel(gray, axis=0)
    magnitude = np.hypot(gx, gy)
    thresh = np.percentile(magnitude, 75)
    mask = magnitude > thresh
    if not mask.any():
        h, w = gray.shape
        return (w//4, h//4, 3*w//4, 3*h//4)
    y_idxs, x_idxs = np.where(mask)
    return int(x_idxs.min()), int(y_idxs.min()), int(x_idxs.max()), int(y_idxs.max())

def adjust_contrast_brightness(image: np.ndarray, roi: tuple, contrast: float, brightness: float) -> np.ndarray:
    x1, y1, x2, y2 = roi
    out = image.copy().astype(np.float32)
    region = out[y1:y2+1, x1:x2+1]
    region[:] = region * contrast + brightness
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out

def rms_contrast(image: np.ndarray, roi: tuple) -> float:
    x1, y1, x2, y2 = roi
    gray = np.mean(image[y1:y2+1, x1:x2+1], axis=2)
    return float(np.std(gray))

def laplacian_variance(image: np.ndarray, roi: tuple) -> float:
    x1, y1, x2, y2 = roi
    gray = np.mean(image[y1:y2+1, x1:x2+1], axis=2).astype(np.float32)
    return float(ndimage.laplace(gray).var())

def load_clip_model(device: str = "cpu"):
    model_name = "openai/clip-vit-base-patch32"
    processor = AutoProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()
    return model, processor

def compute_clip_embedding(image: np.ndarray, model, processor, device: str = "cpu"):
    pil_img = Image.fromarray(image)
    inputs = processor(images=pil_img, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
    return outputs / outputs.norm(p=2, dim=-1, keepdim=True)
    
def cosine_similarity(vec1: torch.Tensor, vec2: torch.Tensor) -> float:
    return float(torch.nn.functional.cosine_similarity(vec1, vec2)[0].item())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    scenarios_path = Path(args.input)
    manifest_path = Path(args.output)
    if not scenarios_path.exists():
        # For the sake of the pipeline, if T003 failed, we can't proceed.
        # However, we must check if we should create a dummy for the sake of the runner
        # if it's a test. In production, we fail.
        logger.error(f"Input scenarios file missing: {scenarios_path}")
        sys.exit(1)

    cfg = load_yaml_config(paths.config("manipulation.yaml"))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    clip_model, clip_processor = load_clip_model(device)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["scenario_id", "salience_level", "variant_path", "rms_contrast_change_pct", "clip_similarity", "texture_change", "moral_intent_score"])

        df = pd.read_csv(scenarios_path)
        for _, row in df.iterrows():
            sid = str(row["scenario_id"])
            orig_path = Path(row["original_image_path"])
            if not orig_path.exists(): continue
            
            orig_img = load_image(orig_path)
            roi = detect_roi(orig_img)
            orig_rms = rms_contrast(orig_img, roi)
            orig_tex = laplacian_variance(orig_img, roi)
            emb_orig = compute_clip_embedding(orig_img, clip_model, clip_processor, device)

            for level in ["low", "medium", "high"]:
                params = cfg[level]
                man_img = adjust_contrast_brightness(orig_img, roi, params["contrast"], params["brightness"])
                var_path = paths.processed("stimuli", f"{sid}_{level}.png")
                save_image(man_img, var_path)

                # Validation
                rms_new = rms_contrast(man_img, roi)
                rms_change = ((rms_new - orig_rms) / (orig_rms + 1e-8)) * 100
                emb_man = compute_clip_embedding(man_img, clip_model, clip_processor, device)
                clip_sim = cosine_similarity(emb_orig, emb_man)
                tex_new = laplacian_variance(man_img, roi)
                tex_change = abs(tex_new - orig_tex) / (orig_tex + 1e-8)
                
                try:
                    m_score = compute_preservation_score(orig_path, var_path)
                except Exception:
                    m_score = 0.0

                if rms_change < 15.0 or clip_sim < 0.95 or tex_change >= 0.05 or m_score < 0.90:
                    log.error(f"Validation failed: {sid}_{level} RMS={rms_change:.2f}, CLIP={clip_sim:.3f}, Tex={tex_change:.3f}, Moral={m_score:.3f}")
                    continue

                writer.writerow([sid, level, str(var_path), f"{rms_change:.2f}", f"{clip_sim:.4f}", f"{tex_change:.4f}", f"{m_score:.4f}"])
    logger.info(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
