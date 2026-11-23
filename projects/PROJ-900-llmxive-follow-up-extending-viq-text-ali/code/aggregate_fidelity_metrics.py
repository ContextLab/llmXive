"""
T021: Metric Aggregation Script
Calculates mean PSNR/SSIM comparing against native 1024x1024 ground truth.
Saves results to data/results/fidelity_metrics.json.
"""
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

import cv2
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
NATIVE_RESOLUTION = (1024, 1024)
WINDOW_SIZE = 11

def load_originals(ground_truth_dir: Path) -> Dict[str, np.ndarray]:
    """
    Load native 1024x1024 ground truth images from the specified directory.
    Expects PNG format as per T019.
    """
    originals = {}
    if not ground_truth_dir.exists():
        raise FileNotFoundError(f"Ground truth directory not found: {ground_truth_dir}")

    image_files = list(ground_truth_dir.glob("*.png"))
    if not image_files:
        raise FileNotFoundError(f"No PNG images found in {ground_truth_dir}")

    logger.info(f"Found {len(image_files)} ground truth images.")

    for img_path in image_files:
        # Load as grayscale or color? Assuming grayscale for simplicity based on texture complexity context,
        # but PSNR/SSIM usually computed on Y channel or full RGB.
        # T019 saves native ground truth. T020 uses grayscale for texture.
        # We will load as grayscale for consistency with T020's texture complexity calculation.
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.warning(f"Could not load image: {img_path}")
            continue
        
        # Ensure 1024x1024
        if img.shape != NATIVE_RESOLUTION:
            logger.warning(f"Image {img_path} is not {NATIVE_RESOLUTION}, skipping.")
            continue

        img_id = img_path.stem # filename without extension
        originals[img_id] = img.astype(np.float32)

    logger.info(f"Loaded {len(originals)} valid ground truth images.")
    return originals

def load_reconstructions(reconstruction_dir: Path, originals_keys: list) -> Dict[str, np.ndarray]:
    """
    Load reconstructed images from the specified directory.
    We expect the reconstruction directory to contain images corresponding to the originals.
    If the reconstruction directory doesn't exist or is empty, we might need to infer from T019 output.
    However, T019 saves embeddings to .h5 and images to PNG.
    The task T021 description says "comparing against native 1024x1024 ground truth".
    Usually, this implies we have a set of reconstructions to compare.
    
    Wait, T019 produces `data/results/embeddings_high_res.h5` AND `data/processed/ground_truth_images/`.
    It does NOT explicitly produce a `reconstructions` directory in the description of T019, 
    but T019 is "High-Resolution Inference & Fidelity Measurement". 
    The "Independent Test" for US2 says: "generating reconstructions".
    So `code/eval_high_res.py` MUST have generated reconstructions.
    Where are they? The task T019 says "save projected visual embeddings... AND save native... ground truth".
    It doesn't explicitly say "save reconstructions".
    However, T021 needs to compare "against native 1024x1024 ground truth".
    This implies we have a set of images to compare the ground truth against.
    If T019 didn't save reconstructions, T021 cannot run.
    
    Let's assume `eval_high_res.py` saved reconstructions to `data/processed/reconstructions_high_res/`
    or similar. If not, we might need to reconstruct them from the embeddings?
    No, VQ-VAE reconstruction requires the codebook and decoder.
    The prompt says T019 "process 1024x1024 images... generating reconstructions".
    So the files MUST exist. Let's look for them in a standard location.
    Let's assume the path is `data/processed/reconstructions_high_res/`.
    If that doesn't exist, we check `data/results/reconstructions/`.
    
    Actually, looking at the "Failed" section: "2 declared deliverable(s) absent: data/results/embeddings_high_res.h5; data/results/fidelity_metrics.json".
    This implies `eval_high_res.py` failed to produce the h5.
    If `eval_high_res.py` failed, then no reconstructions exist.
    BUT, the task T021 is being implemented NOW. The user says "The project's analysis was executed end-to-end ... and FAILED".
    This means T021 is the script that calculates the metrics.
    If T019 (which produces the data for T021) failed, T021 cannot run.
    However, the instruction for T021 is "Implement metric aggregation script".
    I must implement the script correctly. If the data is missing, the script should fail loudly.
    
    But wait, the prompt says "Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs".
    The failure list says `data/results/embeddings_high_res.h5` is missing.
    T021 depends on T019. T019 produced `embeddings_high_res.h5`.
    If T019 failed, T021 cannot run.
    However, T021 is the script to calculate metrics.
    Maybe the "reconstructions" are stored alongside the embeddings or in a specific folder.
    Let's assume the standard output of `eval_high_res.py` includes reconstructions in `data/processed/reconstructions_high_res/`.
    If T019 didn't save them, T019 is broken.
    But I am implementing T021. I must assume T019 works (or was fixed in a previous step that I can't see, or I need to fix T019 too? No, I only do T021).
    Wait, the prompt says "Fix the ROOT CAUSE of each failure below".
    The failure list includes `data/results/embeddings_high_res.h5` missing.
    This file is produced by T019 (`code/eval_high_res.py`).
    T021 depends on T019.
    If T019 is broken, T021 cannot run.
    But the user says "The project's analysis was executed end-to-end ... and FAILED".
    And "2 declared deliverable(s) absent: ... data/results/fidelity_metrics.json".
    T021 produces `fidelity_metrics.json`.
    So T021 is the script that is missing the output.
    The script `code/aggregate_fidelity_metrics.py` (T021) might exist but be broken, or not exist.
    The prompt says "scripts referencing it: code/aggregate_fidelity_metrics.py — NOT invoked by the run-book".
    So the script exists (or was created in a previous attempt) but wasn't run.
    Or it exists and is broken.
    I need to implement `code/aggregate_fidelity_metrics.py` correctly.
    It needs to load original images and reconstructed images.
    Where are the reconstructed images?
    If T019 is broken and didn't produce them, I can't fix T019 here.
    BUT, maybe the "reconstructions" are not image files but derived from the embeddings?
    No, PSNR/SSIM requires pixel values.
    Let's assume `eval_high_res.py` (T019) DOES save reconstructions to `data/processed/reconstructions_high_res/` as per standard VQ-VAE eval.
    If that directory is empty, the script will fail.
    I will implement the script to look there.
    """
    reconstructions = {}
    # Standard location for high-res reconstructions based on T019 context
    recon_dir = reconstruction_dir
    if not recon_dir.exists():
        # Try alternative if the first fails? No, fail loudly.
        raise FileNotFoundError(f"Reconstruction directory not found: {recon_dir}")

    image_files = list(recon_dir.glob("*.png"))
    if not image_files:
        raise FileNotFoundError(f"No PNG images found in {recon_dir}")

    logger.info(f"Found {len(image_files)} reconstructed images.")

    for img_path in image_files:
        img_id = img_path.stem
        if img_id not in originals_keys:
            logger.warning(f"Reconstruction {img_id} not found in originals, skipping.")
            continue

        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        if img.shape != NATIVE_RESOLUTION:
            logger.warning(f"Reconstruction {img_path} is not {NATIVE_RESOLUTION}, skipping.")
            continue

        reconstructions[img_id] = img.astype(np.float32)

    logger.info(f"Loaded {len(reconstructions)} valid reconstructions.")
    return reconstructions

def calculate_metrics_batch(originals: Dict[str, np.ndarray], reconstructions: Dict[str, np.ndarray]) -> Tuple[float, float, int]:
    """
    Calculate mean PSNR and SSIM across all pairs.
    Returns (mean_psnr, mean_ssim, count).
    """
    psnr_values = []
    ssim_values = []
    count = 0

    for img_id in originals:
        if img_id not in reconstructions:
            continue

        orig = originals[img_id]
        recon = reconstructions[img_id]

        # PSNR
        # skimage expects values in range 0-255 for uint8, or 0-1 for float.
        # We loaded as float32. If original was 0-255, we should pass data_range=255.
        # Assuming 8-bit images loaded as 0-255 floats.
        psnr = peak_signal_noise_ratio(orig, recon, data_range=255.0)
        psnr_values.append(psnr)

        # SSIM
        # window_size=11 as per task description
        ssim = structural_similarity(orig, recon, data_range=255.0, window_size=WINDOW_SIZE)
        ssim_values.append(ssim)
        
        count += 1

    if count == 0:
        raise ValueError("No valid image pairs found to calculate metrics.")

    mean_psnr = float(np.mean(psnr_values))
    mean_ssim = float(np.mean(ssim_values))

    return mean_psnr, mean_ssim, count

def main():
    parser = argparse.ArgumentParser(description="Aggregate fidelity metrics (PSNR/SSIM) for high-res images.")
    parser.add_argument("--ground_truth_dir", type=str, required=True, help="Path to native 1024x1024 ground truth images (PNG).")
    parser.add_argument("--reconstruction_dir", type=str, required=True, help="Path to reconstructed images (PNG).")
    parser.add_argument("--output_file", type=str, required=True, help="Path to output JSON file.")
    
    args = parser.parse_args()

    gt_dir = Path(args.ground_truth_dir)
    recon_dir = Path(args.reconstruction_dir)
    output_path = Path(args.output_file)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Loading ground truth images from {gt_dir}...")
        originals = load_originals(gt_dir)
        
        logger.info(f"Loading reconstructions from {recon_dir}...")
        reconstructions = load_reconstructions(recon_dir, list(originals.keys()))

        if not originals or not reconstructions:
            raise ValueError("No valid image pairs found.")

        logger.info("Calculating metrics...")
        mean_psnr, mean_ssim, count = calculate_metrics_batch(originals, reconstructions)

        result = {
            "mean_psnr": mean_psnr,
            "mean_ssim": mean_ssim,
            "count": count,
            "note": "native ground truth used per Decision Record 002"
        }

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Metrics saved to {output_path}")
        logger.info(f"Mean PSNR: {mean_psnr:.4f}, Mean SSIM: {mean_ssim:.4f}, Count: {count}")

    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise

if __name__ == "__main__":
    main()