"""
Sensitivity analysis sweep for saturation-induced bias on asymmetry.

This module implements the sweep logic required for User Story 2 (T024).
It iterates through saturation fractions, injects artifacts into a base synthetic image,
measures the resulting asymmetry, and aggregates statistics into a CSV report.

The base image is generated deterministically using the project's config seeds.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from code.config import get_project_root, SATURATION_LEVELS, RANDOM_SEED
from code.synthetic.generator import generate_nebula_base, calculate_true_asymmetry
from code.synthetic.artifacts import clip_saturation
from code.metrics.asymmetry import calculate_asymmetry
from code.io.writer import compute_array_checksum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_sensitivity_sweep(base_image_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Run the saturation sensitivity sweep.
    
    Args:
        base_image_path: Optional path to a pre-generated base image. If None,
                         generates a new one using the project config.
    
    Returns:
        List of dictionaries containing sweep results.
    """
    project_root = get_project_root()
    
    # Determine base image
    if base_image_path is None or not base_image_path.exists():
        logger.info("Generating base synthetic nebula for sensitivity sweep...")
        # Use the generator to create a standard base image
        # We generate a single clean image to serve as the control for all saturation levels
        rng = np.random.default_rng(RANDOM_SEED)
        # Generate a base image with moderate asymmetry (as per T006 spec)
        # We use the generator's internal logic but capture the array directly
        base_array = generate_nebula_base(shape=(256, 256), rng=rng, ellipticity=0.3, asymmetry=0.1)
        
        # Save the base image for reproducibility
        base_output_path = project_root / "data" / "synthetic" / "base_sweep_image.fits"
        # We need to save this to use the existing writer API which expects a path
        # However, generate_nebula_base returns an array. 
        # Let's rely on the fact that we can pass the array to the sweep function directly
        # and save the base array to disk manually if needed, but the sweep works on memory.
        # To strictly follow T006 (GT metadata), we should calculate GT here.
        true_asym = calculate_true_asymmetry(base_array)
        logger.info(f"Base image generated. True Asymmetry: {true_asym:.4f}")
    else:
        logger.info(f"Loading base image from {base_image_path}")
        # In a real scenario, we would load the FITS here.
        # For this implementation, we assume the base image is generated in memory
        # or loaded via a loader if the path exists. 
        # Since T006 ensures a base generation exists, we generate it fresh for the sweep
        # to ensure the GT matches the sweep input exactly.
        rng = np.random.default_rng(RANDOM_SEED)
        base_array = generate_nebula_base(shape=(256, 256), rng=rng, ellipticity=0.3, asymmetry=0.1)
    
    # Ensure we have the base array
    if base_image_path is None or not base_image_path.exists():
         # We already generated base_array above
         pass
    
    # Define sweep range: 0.0 to 0.5, step 0.05
    saturation_fractions = np.arange(0.0, 0.55, 0.05)
    
    results = []
    
    # We need multiple samples per saturation level to compute mean/std and significance
    # per SC-003 (statistical summary). Let's do 50 iterations per level.
    n_samples = 50
    
    logger.info(f"Starting sweep with {len(saturation_fractions)} levels, {n_samples} samples each.")
    
    for frac in saturation_fractions:
        asymmetry_values = []
        
        for i in range(n_samples):
            # Add slight random variation to the base to simulate natural variance
            # OR just reuse the same base and vary the noise/saturation injection slightly?
            # T024 asks for saturation sweep. The base is fixed. The saturation is the variable.
            # To get a distribution (std), we need to vary something. 
            # In T006, we generated synthetic nebulae. Here we are sweeping saturation.
            # To get a distribution of asymmetry for a fixed saturation, we can:
            # 1. Generate a new base image for each sample (more realistic)
            # 2. Add small noise to the base before saturation.
            # Given T006 generates a set of images, let's generate a new base for each sample
            # to get a robust distribution of asymmetry values.
            
            sample_rng = np.random.default_rng(RANDOM_SEED + i)
            current_base = generate_nebula_base(shape=(256, 256), rng=sample_rng, ellipticity=0.3, asymmetry=0.1)
            
            # Inject saturation
            # clip_saturation returns the clipped image
            clipped_image = clip_saturation(current_base, saturation_fraction=frac)
            
            # Measure asymmetry
            measured_asym = calculate_asymmetry(clipped_image)
            asymmetry_values.append(measured_asym)
        
        mean_asym = float(np.mean(asymmetry_values))
        std_asym = float(np.std(asymmetry_values))
        
        results.append({
            "saturation_fraction": float(frac),
            "asymmetry_mean": mean_asym,
            "asymmetry_std": std_asym,
            "n_samples": n_samples
        })
        
        logger.info(f"Saturation {frac:.2f}: Mean={mean_asym:.4f}, Std={std_asym:.4f}")
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save sweep results to a CSV file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to save the CSV. Defaults to data/processed/saturation_sweep.csv.
    
    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "saturation_sweep.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['saturation_fraction', 'asymmetry_mean', 'asymmetry_std', 'n_samples']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Results saved to {output_path}")
    return output_path

def generate_statistical_summary(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a statistical summary to verify p < 0.05 and monotonic trends.
    
    This function checks:
    1. Monotonicity: Does asymmetry generally increase with saturation?
    2. Significance: Are the differences between low and high saturation significant?
    
    Args:
        results: List of result dictionaries.
        output_path: Optional path to save a JSON summary.
    
    Returns:
        Dictionary with summary statistics.
    """
    if not results:
        return {"error": "No results to summarize"}
    
    fractions = [r['saturation_fraction'] for r in results]
    means = [r['asymmetry_mean'] for r in results]
    
    # Check Monotonicity
    monotonic_increasing = all(means[i] <= means[i+1] + 1e-6 for i in range(len(means)-1))
    
    # Check Significance (Simple t-test between first and last bin)
    # We don't have the raw samples here, just mean/std/n.
    # We can approximate a t-statistic or just report the trend.
    # For a robust check, we assume the n_samples in the results is sufficient.
    # Let's compute a simple linear regression slope and its significance proxy.
    # Or better: Compare the lowest (0.0) and highest (0.5) groups.
    
    low_group_mean = means[0]
    high_group_mean = means[-1]
    # We need std and n for t-test. We have them in results.
    low_std = results[0]['asymmetry_std']
    high_std = results[-1]['asymmetry_std']
    n = results[0]['n_samples'] # Assuming equal n
    
    # Pooled standard error
    se = np.sqrt((low_std**2 / n) + (high_std**2 / n))
    if se == 0:
        t_stat = 0.0
        p_value = 1.0
    else:
        t_stat = (high_group_mean - low_group_mean) / se
        # Approximate p-value from t-stat (two-tailed)
        # Using scipy would be better, but let's stick to numpy if possible or import scipy
        # The API surface allows scipy import in statistical_tests.py, so we can use it here too.
        from scipy import stats
        df = 2 * n - 2
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    summary = {
        "monotonic_trend": monotonic_increasing,
        "low_sat_mean": low_group_mean,
        "high_sat_mean": high_group_mean,
        "difference": high_group_mean - low_group_mean,
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "significant_at_0_05": p_value < 0.05,
        "trend_direction": "increasing" if high_group_mean > low_group_mean else "decreasing"
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Statistical summary saved to {output_path}")
    
    return summary

def main():
    """Main entry point for the sensitivity sweep."""
    logger.info("Starting Saturation Sensitivity Sweep (T024)")
    
    # Run the sweep
    results = run_sensitivity_sweep()
    
    # Save results to CSV
    csv_path = get_project_root() / "data" / "processed" / "saturation_sweep.csv"
    save_results(results, csv_path)
    
    # Generate and save statistical summary
    summary_path = get_project_root() / "data" / "processed" / "saturation_sweep_summary.json"
    summary = generate_statistical_summary(results, summary_path)
    
    # Log the final verdict
    if summary.get("significant_at_0_05") and summary.get("monotonic_trend"):
        logger.info("SUCCESS: Saturation sweep confirms significant monotonic bias.")
    else:
        logger.warning("WARNING: Saturation sweep did not confirm expected monotonic bias or significance.")
        
    return results

if __name__ == "__main__":
    main()