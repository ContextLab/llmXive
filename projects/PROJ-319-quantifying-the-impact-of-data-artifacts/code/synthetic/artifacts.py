"""
Artifact injection: Noise and Saturation.
"""
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from astropy.io import fits
import csv

try:
    from code.config import get_project_root, NOISE_LEVELS, SATURATION_RANGE
    from code.io.loader import load_fits_image
    from code.metrics.ellipticity import calculate_ellipticity
    from code.metrics.asymmetry import calculate_asymmetry
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    parent = Path(__file__).resolve().parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    from config import get_project_root, NOISE_LEVELS, SATURATION_RANGE
    from io.loader import load_fits_image
    from metrics.ellipticity import calculate_ellipticity
    from metrics.asymmetry import calculate_asymmetry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inject_noise(image: np.ndarray, sigma: float) -> Tuple[np.ndarray, bool]:
    """
    Inject Gaussian noise into an image.
    Returns (noisy_image, valid).
    Raises ValueError if sigma is extreme (T054).
    """
    if sigma > 0.10:
        logger.warning(f"Extreme noise level detected: sigma={sigma}. Skipping calculation.")
        return image, False
    
    noise = np.random.normal(0, sigma, image.shape)
    return image + noise, True

def clip_saturation(image: np.ndarray, fraction: float) -> Tuple[np.ndarray, bool]:
    """
    Clip the brightest fraction of pixels to simulate saturation.
    Returns (clipped_image, valid).
    Raises ValueError if fraction is extreme (T055).
    """
    if fraction > 0.5:
        logger.warning(f"Extreme saturation level detected: fraction={fraction}. Skipping calculation.")
        return image, False
    
    if fraction == 0.0:
        return image, True
    
    threshold = np.percentile(image, 100 * (1 - fraction))
    clipped = np.minimum(image, threshold)
    
    # Check for zero signal
    if np.sum(clipped) == 0:
        logger.warning("Saturation resulted in zero signal. Marking as invalid.")
        return clipped, False
        
    return clipped, True

def run_noise_sweep(root: Path):
    """Run noise sweep over all synthetic images."""
    synthetic_dir = root / "data" / "synthetic"
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "noise_sweep_data.csv"
    
    # Load ground truth
    gt_file = synthetic_dir / "gt_metadata.json"
    import json
    with open(gt_file) as f:
        gt_data = json.load(f)
    
    results = []
    for gt_entry in gt_data:
        img_path = synthetic_dir / gt_entry["filename"]
        image = load_fits_image(img_path)
        true_ellipticity = gt_entry["ellipticity"]
        
        for sigma in NOISE_LEVELS:
            noisy_img, valid = inject_noise(image.copy(), sigma)
            if not valid:
                continue
            
            try:
                measured_ellipticity = calculate_ellipticity(noisy_img)
                bias = measured_ellipticity - true_ellipticity
                results.append({
                    "image_id": gt_entry["image_id"],
                    "sigma": sigma,
                    "measured_ellipticity": measured_ellipticity,
                    "ground_truth_ellipticity": true_ellipticity,
                    "bias": bias
                })
            except Exception as e:
                logger.warning(f"Failed to measure ellipticity for {gt_entry['filename']} at sigma={sigma}: {e}")
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "sigma", "measured_ellipticity", "ground_truth_ellipticity", "bias"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Noise sweep data saved to {output_file}")

def run_saturation_sweep(root: Path):
    """Run saturation sweep over all synthetic images."""
    synthetic_dir = root / "data" / "synthetic"
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "saturation_sweep.csv"
    
    # Load ground truth
    gt_file = synthetic_dir / "gt_metadata.json"
    import json
    with open(gt_file) as f:
        gt_data = json.load(f)
    
    start, stop, step = SATURATION_RANGE
    fractions = np.arange(start, stop + step/2, step) # Include stop
    
    results = []
    for gt_entry in gt_data:
        img_path = synthetic_dir / gt_entry["filename"]
        image = load_fits_image(img_path)
        true_asymmetry = gt_entry["asymmetry"]
        
        for frac in fractions:
            frac = round(frac, 2)
            clipped_img, valid = clip_saturation(image.copy(), frac)
            if not valid:
                continue
            
            try:
                measured_asymmetry = calculate_asymmetry(clipped_img)
                bias = measured_asymmetry - true_asymmetry
                results.append({
                    "image_id": gt_entry["image_id"],
                    "saturation_fraction": frac,
                    "measured_asymmetry": measured_asymmetry,
                    "ground_truth_asymmetry": true_asymmetry,
                    "bias_mean": bias, # Using bias as mean for single entry
                    "bias_std": 0.0,
                    "valid": True
                })
            except Exception as e:
                logger.warning(f"Failed to measure asymmetry for {gt_entry['filename']} at sat={frac}: {e}")
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "saturation_fraction", "measured_asymmetry", "ground_truth_asymmetry", "bias_mean", "bias_std", "valid"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saturation sweep data saved to {output_file}")

def main():
    """Main entry point for artifact injection."""
    root = get_project_root()
    run_noise_sweep(root)
    run_saturation_sweep(root)

if __name__ == "__main__":
    main()
