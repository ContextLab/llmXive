"""
Artifact injection: Noise and Saturation.
"""
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from astropy.io import fits
import csv
from code.config import NOISE_LEVELS, SATURATION_FRACTIONS, RANDOM_SEED

def inject_noise(image: np.ndarray, sigma: float) -> np.ndarray:
    """
    Inject Gaussian noise with standard deviation sigma.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    noise = rng.normal(0, sigma, image.shape)
    return image + noise

def clip_saturation(image: np.ndarray, fraction: float) -> np.ndarray:
    """
    Clip the brightest 'fraction' of pixels to simulate saturation.
    """
    if fraction <= 0:
        return image
    
    threshold = np.percentile(image, 100 * (1 - fraction))
    clipped = np.clip(image, None, threshold)
    return clipped

def run_noise_sweep(input_dir: Path, output_dir: Path) -> None:
    """
    Run a sweep over noise levels on synthetic data.
    Produces data/processed/noise_sweep_data.csv.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load ground truth
    gt_file = input_dir / "gt_metadata.json"
    import json
    with open(gt_file) as f:
        gt_data = json.load(f)
    
    results = []
    
    for item in gt_data:
        img_path = input_dir / item['filename']
        with fits.open(img_path) as hdul:
            image = hdul[0].data.copy()
        
        gt_ell = item['ellipticity']
        
        # Import metric function
        from code.metrics.ellipticity import calculate_ellipticity
        
        for sigma in NOISE_LEVELS:
            noisy_image = inject_noise(image, sigma)
            measured_ell = calculate_ellipticity(noisy_image)
            bias = measured_ell - gt_ell
            
            results.append({
                "image_id": item['image_id'],
                "sigma": sigma,
                "measured_ellipticity": measured_ell,
                "ground_truth_ellipticity": gt_ell,
                "bias": bias
            })
    
    # Write CSV
    csv_path = output_dir / "noise_sweep_data.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "sigma", "measured_ellipticity", "ground_truth_ellipticity", "bias"])
        writer.writeheader()
        writer.writerows(results)
    
    logging.info(f"Noise sweep data written to {csv_path}")

def run_saturation_sweep(input_dir: Path, output_dir: Path) -> None:
    """
    Run a sweep over saturation levels on synthetic data.
    Produces data/processed/saturation_sweep.csv.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load ground truth
    gt_file = input_dir / "gt_metadata.json"
    import json
    with open(gt_file) as f:
        gt_data = json.load(f)
    
    results = []
    
    for item in gt_data:
        img_path = input_dir / item['filename']
        with fits.open(img_path) as hdul:
            image = hdul[0].data.copy()
        
        gt_asym = item['asymmetry']
        
        # Import metric function
        from code.metrics.asymmetry import calculate_asymmetry
        
        for fraction in SATURATION_FRACTIONS:
            if fraction == 0:
                clipped_image = image
            else:
                clipped_image = clip_saturation(image, fraction)
            
            measured_asym = calculate_asymmetry(clipped_image)
            bias = measured_asym - gt_asym
            
            results.append({
                "image_id": item['image_id'],
                "saturation_fraction": fraction,
                "measured_asymmetry": measured_asym,
                "ground_truth_asymmetry": gt_asym,
                "bias": bias
            })
    
    # Write CSV
    csv_path = output_dir / "saturation_sweep.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "saturation_fraction", "measured_asymmetry", "ground_truth_asymmetry", "bias"])
        writer.writeheader()
        writer.writerows(results)
    
    logging.info(f"Saturation sweep data written to {csv_path}")

def main():
    root = Path(__file__).resolve().parent.parent.parent
    input_dir = root / "data" / "synthetic"
    output_dir = root / "data" / "processed"
    run_noise_sweep(input_dir, output_dir)
    run_saturation_sweep(input_dir, output_dir)

if __name__ == "__main__":
    main()
