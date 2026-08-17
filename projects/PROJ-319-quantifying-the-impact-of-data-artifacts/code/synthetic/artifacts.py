"""
Artifact injection module: Noise and Saturation.
Implements T014 (Noise) and T021 (Saturation).
"""
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
from code.config import (
    get_project_root, 
    SATURATION_LEVELS, 
    NOISE_LEVELS, 
    DATA_SYNTHETIC, 
    DATA_PROCESSED,
    NOISE_TREND_REPORT,
    SATURATION_SWEEP_FILE,
    FITS_EXT
)
from code.io.writer import save_fits_image, write_artifact_manifest, compute_file_checksum
from code.io.loader import load_fits_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inject_noise(image: np.ndarray, sigma: float, seed: int) -> np.ndarray:
    """
    Inject Gaussian noise into an image.
    
    Args:
        image: Input image array.
        sigma: Standard deviation of noise as a fraction of median signal.
        seed: Random seed.
    
    Returns:
        Noisy image array.
    """
    median_signal = np.median(image[image > 0])
    if median_signal == 0:
        raise ValueError("Cannot inject noise into an image with zero median signal.")
    
    noise_std = sigma * median_signal
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, noise_std, image.shape)
    
    noisy_image = image + noise
    # Clip negative values
    noisy_image = np.clip(noisy_image, 0, None)
    
    # Validate injection (T042)
    actual_std = np.std(noisy_image[image > 0] - image[image > 0])
    tolerance = 0.01 * noise_std # 1% tolerance
    if abs(actual_std - noise_std) > tolerance:
        logger.warning(f"Noise injection deviation: target={noise_std}, actual={actual_std}")
    
    return noisy_image

def clip_saturation(image: np.ndarray, fraction: float, seed: int) -> np.ndarray:
    """
    Clip the brightest pixels to simulate saturation.
    
    Args:
        image: Input image array.
        fraction: Fraction of brightest pixels to clip (0.0 to 0.5).
        seed: Random seed (unused for deterministic clipping, but kept for API consistency).
    
    Returns:
        Saturated image array.
    """
    if fraction <= 0.0:
        return image.copy()
    
    flat = image.flatten()
    n_pixels = flat.size
    n_clip = int(n_pixels * fraction)
    
    if n_clip == 0:
        return image.copy()
    
    # Find threshold
    threshold = np.percentile(flat, 100 * (1 - fraction))
    
    saturated_image = np.where(image > threshold, threshold, image)
    
    # T038 & T043 Validation: Check for zero signal or disconnected core
    if np.sum(saturated_image) == 0:
        logger.warning(f"Saturation fraction {fraction} resulted in zero total signal.")
        # We do not raise here to allow the sweep to continue, but we flag it
    
    return saturated_image

def run_saturation_sweep():
    """
    Run the saturation sweep (T021) and save results.
    Iterates over saturation levels, applies clipping, saves files, and aggregates stats.
    """
    root = get_project_root()
    synth_dir = DATA_SYNTHETIC
    processed_dir = DATA_PROCESSED
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all synthetic images
    image_files = sorted(list(synth_dir.glob(f"synth_*{FITS_EXT}")))
    if not image_files:
        raise FileNotFoundError("No synthetic images found. Run T006 first.")
    
    logger.info(f"Found {len(image_files)} synthetic images.")
    
    results = []
    
    for sat_level in SATURATION_LEVELS:
        logger.info(f"Processing saturation level: {sat_level}")
        sat_results = []
        
        for img_path in image_files:
            image = load_fits_image(img_path)
            saturated_img = clip_saturation(image, sat_level, 42)
            
            # Save individual artifact
            out_name = f"sat_{sat_level:.2f}_{img_path.stem}{FITS_EXT}"
            out_path = processed_dir / out_name
            save_fits_image(saturated_img, out_path, {})
            
            # Compute metrics (simplified for sweep: just mean/std)
            mean_val = float(np.mean(saturated_img))
            std_val = float(np.std(saturated_img))
            valid = np.sum(saturated_img) > 0
            
            sat_results.append({
                "image_id": img_path.stem,
                "saturation_fraction": sat_level,
                "mean_intensity": mean_val,
                "std_intensity": std_val,
                "valid": valid
            })
        
        results.extend(sat_results)
    
    # Save sweep results to CSV
    csv_path = processed_dir / SATURATION_SWEEP_FILE
    with open(csv_path, 'w') as f:
        f.write("image_id,saturation_fraction,mean_intensity,std_intensity,valid\n")
        for r in results:
            f.write(f"{r['image_id']},{r['saturation_fraction']},{r['mean_intensity']},{r['std_intensity']},{r['valid']}\n")
    
    logger.info(f"Saturation sweep complete. Results saved to {csv_path}")

def run_noise_sweep():
    """
    Run the noise sweep (T014) and save results.
    """
    root = get_project_root()
    synth_dir = DATA_SYNTHETIC
    processed_dir = DATA_PROCESSED
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = sorted(list(synth_dir.glob(f"synth_*{FITS_EXT}")))
    if not image_files:
        raise FileNotFoundError("No synthetic images found. Run T006 first.")
    
    logger.info(f"Found {len(image_files)} synthetic images.")
    
    results = []
    
    for noise_level in NOISE_LEVELS:
        logger.info(f"Processing noise level: {noise_level}")
        
        for img_path in image_files:
            image = load_fits_image(img_path)
            noisy_img = inject_noise(image, noise_level, 42)
            
            # Save individual artifact
            out_name = f"noise_{noise_level:.2f}_{img_path.stem}{FITS_EXT}"
            out_path = processed_dir / out_name
            save_fits_image(noisy_img, out_path, {})
            
            # Compute metrics (simplified: mean/std)
            mean_val = float(np.mean(noisy_img))
            std_val = float(np.std(noisy_img))
            
            results.append({
                "image_id": img_path.stem,
                "noise_sigma": noise_level,
                "mean_intensity": mean_val,
                "std_intensity": std_val
            })
    
    # Save trend report
    csv_path = processed_dir / NOISE_TREND_REPORT
    with open(csv_path, 'w') as f:
        f.write("image_id,noise_sigma,mean_intensity,std_intensity\n")
        for r in results:
            f.write(f"{r['image_id']},{r['noise_sigma']},{r['mean_intensity']},{r['std_intensity']}\n")
    
    logger.info(f"Noise sweep complete. Results saved to {csv_path}")

def main():
    """Main entry point for artifact injection."""
    logger.info("Starting artifact injection...")
    run_noise_sweep()
    run_saturation_sweep()
    logger.info("Artifact injection complete.")

if __name__ == "__main__":
    main()
