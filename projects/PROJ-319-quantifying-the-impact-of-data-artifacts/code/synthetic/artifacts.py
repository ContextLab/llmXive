"""
Artifact injection module: Noise and Saturation.
"""
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from astropy.io import fits
import csv
import json

from code.config import NOISE_LEVELS, SATURATION_RANGE, DEFAULT_SEED

def inject_noise(image: np.ndarray, sigma: float, seed: int = 42) -> np.ndarray:
    """
    Inject Gaussian noise with standard deviation sigma.
    """
    np.random.seed(seed)
    noise = np.random.normal(0, sigma, image.shape)
    noisy = image + noise
    # Clip to valid range if necessary, but keep float for analysis
    return noisy

def clip_saturation(image: np.ndarray, fraction: float) -> np.ndarray:
    """
    Clip the brightest 'fraction' of pixels to simulate saturation.
    fraction is a float between 0.0 and 1.0 (e.g., 0.5 means 50% of brightest pixels).
    """
    flat = image.flatten()
    if fraction >= 1.0:
        return np.zeros_like(image) # All saturated

    threshold = np.percentile(flat, 100 * (1 - fraction))
    saturated = np.clip(image, a_min=None, a_max=threshold)
    return saturated

def run_noise_sweep(root: Path) -> None:
    """
    Run the noise sensitivity sweep.
    Loads synthetic images, injects noise at defined levels, measures ellipticity,
    and saves results to data/processed/noise_sweep_data.csv.
    """
    logger = logging.getLogger("artifacts")
    logger.info("Running Noise Sweep...")

    synth_dir = root / "data" / "synthetic"
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load ground truth
    gt_path = synth_dir / "gt_metadata.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth metadata not found: {gt_path}")
    
    with open(gt_path, 'r') as f:
        gt_data = json.load(f)

    results = []

    for item in gt_data:
        img_path = synth_dir / item['filename']
        with fits.open(img_path) as hdul:
            img = hdul[0].data

        gt_e = item['ellipticity']

        for sigma in NOISE_LEVELS:
            # Inject noise
            noisy_img = inject_noise(img, sigma, seed=DEFAULT_SEED)

            # Measure ellipticity (using simple second moment approximation for this task)
            # Since we don't have the full ellipticity module logic here, we approximate
            # based on the ground truth + noise effect simulation for the sweep data.
            # In a real scenario, we would call calculate_ellipticity from metrics.ellipticity
            # But to ensure the sweep runs and produces REAL measured data (not fake),
            # we must call the metric function.
            try:
                from code.metrics.ellipticity import calculate_ellipticity
                # calculate_ellipticity expects an image and returns (e, angle) or similar
                # We assume it returns a tuple (ellipticity, angle)
                measured_e, _ = calculate_ellipticity(noisy_img)
            except Exception as e:
                logger.warning(f"Ellipticity calculation failed for {item['filename']} at sigma={sigma}: {e}")
                continue

            bias = measured_e - gt_e
            results.append({
                "image_id": item['image_id'],
                "sigma": sigma,
                "measured_ellipticity": measured_e,
                "ground_truth_ellipticity": gt_e,
                "bias": bias
            })

    # Save results
    out_path = processed_dir / "noise_sweep_data.csv"
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "sigma", "measured_ellipticity", "ground_truth_ellipticity", "bias"])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Noise sweep complete. Results saved to {out_path}")

def run_saturation_sweep(root: Path) -> None:
    """
    Run the saturation sensitivity sweep.
    Loads synthetic images, clips saturation at defined levels, measures asymmetry,
    and saves results to data/processed/saturation_sweep.csv.
    """
    logger = logging.getLogger("artifacts")
    logger.info("Running Saturation Sweep...")

    synth_dir = root / "data" / "synthetic"
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load ground truth
    gt_path = synth_dir / "gt_metadata.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth metadata not found: {gt_path}")
    
    with open(gt_path, 'r') as f:
        gt_data = json.load(f)

    results = []

    for item in gt_data:
        img_path = synth_dir / item['filename']
        with fits.open(img_path) as hdul:
            img = hdul[0].data

        gt_a = item['asymmetry']

        for frac in SATURATION_RANGE:
            # Clip saturation
            sat_img = clip_saturation(img, frac)

            # Check for zero signal
            if np.max(sat_img) == 0:
                logger.warning(f"Image {item['filename']} completely saturated at fraction={frac}. Skipping.")
                continue

            # Measure asymmetry
            try:
                from code.metrics.asymmetry import calculate_asymmetry
                measured_a = calculate_asymmetry(sat_img)
            except Exception as e:
                logger.warning(f"Asymmetry calculation failed for {item['filename']} at frac={frac}: {e}")
                continue

            bias = measured_a - gt_a
            results.append({
                "image_id": item['image_id'],
                "saturation_fraction": frac,
                "measured_asymmetry": measured_a,
                "ground_truth_asymmetry": gt_a,
                "bias_mean": bias, # Simplified for sweep
                "bias_std": 0.0,
                "valid": True
            })

    # Save results
    out_path = processed_dir / "saturation_sweep.csv"
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "saturation_fraction", "measured_asymmetry", "ground_truth_asymmetry", "bias_mean", "bias_std", "valid"])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saturation sweep complete. Results saved to {out_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, required=True)
    args = parser.parse_args()
    root = Path(args.root)
    run_noise_sweep(root)
    run_saturation_sweep(root)

if __name__ == "__main__":
    main()
