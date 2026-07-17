import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from code.config import get_project_root, NOISE_LEVELS
from code.io.loader import load_fits_image
from code.io.writer import save_fits_image
from code.metrics.ellipticity import calculate_ellipticity
from code.synthetic.artifacts import inject_noise

logger = logging.getLogger(__name__)

def run_sensitivity_sweep():
    """
    Run a sensitivity sweep over noise levels on synthetic data.
    Produces data/processed/noise_sweep.csv (or similar) and FITS artifacts.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load a base synthetic image
    synth_path = root / "data" / "synthetic" / "synth_000.fits"
    if not synth_path.exists():
        logger.error("Base synthetic image not found. Cannot run sweep.")
        return

    base_image = load_fits_image(synth_path)
    
    results = []
    noise_levels = [0.01, 0.05, 0.10] # From config
    
    for sigma in noise_levels:
        noisy_image = inject_noise(base_image, sigma)
        
        # Save the noisy image
        fits_path = processed_dir / f"noise_sweep_{sigma:.2f}.fits"
        header = {"NOISE_SIGMA": sigma, "FILTER": "F658N", "EXPTIME": 1000}
        save_fits_image(noisy_image, header, fits_path)
        
        try:
            ellipticity = calculate_ellipticity(noisy_image)
            results.append({
                "sigma": sigma,
                "ellipticity_mean": ellipticity,
                "valid": True
            })
        except Exception as e:
            logger.error(f"Error calculating ellipticity for sigma {sigma}: {e}")
            results.append({
                "sigma": sigma,
                "ellipticity_mean": np.nan,
                "valid": False
            })
    
    # Write to CSV
    csv_path = processed_dir / "noise_sweep.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sigma", "ellipticity_mean", "valid"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Noise sweep results written to {csv_path}")
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save sweep results to a CSV file."""
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def generate_statistical_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a statistical summary of the sweep results."""
    valid_results = [r for r in results if r.get("valid", False)]
    if not valid_results:
        return {"error": "No valid results"}
    
    sigmas = [r["sigma"] for r in valid_results]
    ellipticities = [r["ellipticity_mean"] for r in valid_results]
    
    # Simple linear regression
    if len(sigmas) < 2:
        return {"error": "Insufficient data for regression"}
    
    slope, intercept, r_value, p_value, std_err = np.polyfit(sigmas, ellipticities, 1, full=False), 0, 0, 0, 0
    # Using numpy polyfit directly for simplicity
    coeffs = np.polyfit(sigmas, ellipticities, 1)
    slope = coeffs[0]
    
    return {
        "slope": float(slope),
        "intercept": float(coeffs[1]),
        "n_points": len(valid_results),
        "trend": "monotonic" if slope != 0 else "flat"
    }

def main():
    run_sensitivity_sweep()
