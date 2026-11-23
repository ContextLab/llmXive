import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Import shared constants and utilities
from utils import set_seed, save_json_output
from logging_config import get_logger

# Constants
SEED = 42
FIXED_K = 3  # Constitution Principle VII: Fixed k for determinism
OUTPUT_DIR = Path("data/processed")
SHEAR_BAND_AGGREGATION_FILE = OUTPUT_DIR / "shear_band_aggregation.csv"
KS_TEST_RESULTS_FILE = OUTPUT_DIR / "ks_test_results.json"
CORRECTED_P_VALUES_FILE = OUTPUT_DIR / "corrected_p_values.json"
SIGNIFICANCE_REPORT_FILE = OUTPUT_DIR / "significance_report.json"
HISTOGRAM_FILE = OUTPUT_DIR / "histograms.png"

logger = get_logger(__name__)

def aggregate_to_shear_bands(d2_min_values: np.ndarray, coordinates: np.ndarray) -> pd.DataFrame:
    """
    Aggregate D2_min values to shear bands using k-means clustering.
    
    Algorithm: Fixed k=3, seed=42 for determinism (Constitution Principle VII).
    
    Args:
        d2_min_values: 1D array of D2_min values for each particle
        coordinates: 2D array (N_particles, 3) of particle coordinates
    
    Returns:
        DataFrame with columns: shear_band_id, mean_D2_min, particle_count
    """
    set_seed(SEED)
    
    if len(d2_min_values) == 0:
        logger.warning("No D2_min values provided for aggregation.")
        return pd.DataFrame(columns=["shear_band_id", "mean_D2_min", "particle_count"])
    
    # Apply k-means clustering on coordinates to identify shear bands
    # Using FIXED k=3 as per Constitution Principle VII
    kmeans = KMeans(n_clusters=FIXED_K, random_state=SEED, n_init=10)
    cluster_labels = kmeans.fit_predict(coordinates)
    
    # Aggregate D2_min values by cluster
    df = pd.DataFrame({
        'shear_band_id': cluster_labels,
        'd2_min': d2_min_values
    })
    
    aggregated = df.groupby('shear_band_id').agg(
        mean_D2_min=('d2_min', 'mean'),
        particle_count=('d2_min', 'count')
    ).reset_index()
    
    # Sort by shear_band_id for consistency
    aggregated = aggregated.sort_values('shear_band_id').reset_index(drop=True)
    
    logger.info(f"Aggregated {len(d2_min_values)} particles into {FIXED_K} shear bands.")
    return aggregated

def aggregate_to_shear_bands_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate D2_min values from a DataFrame containing particle data.
    
    Args:
        df: DataFrame with columns 'd2_min', 'x', 'y', 'z' (or similar coordinate columns)
    
    Returns:
        DataFrame with columns: shear_band_id, mean_D2_min, particle_count
    """
    required_cols = {'d2_min', 'x', 'y', 'z'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"DataFrame must contain columns: {required_cols}")
    
    coordinates = df[['x', 'y', 'z']].values
    d2_min_values = df['d2_min'].values
    
    return aggregate_to_shear_bands(d2_min_values, coordinates)

def perform_ks_test(brittle_data: pd.DataFrame, ductile_data: pd.DataFrame) -> Dict:
    """
    Perform two-sample Kolmogorov-Smirnov test on shear-band aggregated data.
    
    Args:
        brittle_data: DataFrame of shear band metrics for brittle trajectories
        ductile_data: DataFrame of shear band metrics for ductile trajectories
    
    Returns:
        Dict containing statistic, p-value, and metadata
    """
    if brittle_data.empty or ductile_data.empty:
        logger.warning("Empty data provided for KS test.")
        return {"statistic": 0.0, "pvalue": 1.0, "note": "Empty data"}
    
    # Extract mean D2_min values for each group
    brittle_means = brittle_data['mean_D2_min'].values
    ductile_means = ductile_data['mean_D2_min'].values
    
    # Perform KS test
    statistic, pvalue = stats.ks_2samp(brittle_means, ductile_means)
    
    result = {
        "statistic": float(statistic),
        "pvalue": float(pvalue),
        "method": "Kolmogorov-Smirnov two-sample test",
        "description": "Associational finding comparing brittle vs ductile shear-band D2_min distributions"
    }
    
    logger.info(f"KS Test: statistic={statistic:.4f}, p-value={pvalue:.4f}")
    return result

def apply_bonferroni_correction(pvalue: float, num_tests: int) -> float:
    """
    Apply Bonferroni correction to p-value.
    
    Args:
        pvalue: Raw p-value
        num_tests: Number of hypothesis tests performed
    
    Returns:
        Corrected p-value
    """
    if num_tests <= 0:
        raise ValueError("num_tests must be positive")
    
    corrected = min(pvalue * num_tests, 1.0)
    logger.info(f"Bonferroni correction: {pvalue:.4f} * {num_tests} = {corrected:.4f}")
    return corrected

def generate_histograms(brittle_data: pd.DataFrame, ductile_data: pd.DataFrame, output_path: Path):
    """
    Generate histogram overlay of brittle vs ductile distributions.
    
    Args:
        brittle_data: DataFrame with shear band metrics for brittle trajectories
        ductile_data: DataFrame with shear band metrics for ductile trajectories
        output_path: Path to save the histogram figure
    """
    if brittle_data.empty or ductile_data.empty:
        logger.warning("Skipping histogram generation due to empty data.")
        return
    
    brittle_means = brittle_data['mean_D2_min'].values
    ductile_means = ductile_data['mean_D2_min'].values
    
    plt.figure(figsize=(10, 6))
    plt.hist(brittle_means, bins=30, alpha=0.5, label='Brittle', color='red', density=True)
    plt.hist(ductile_means, bins=30, alpha=0.5, label='Ductile', color='blue', density=True)
    plt.xlabel('Mean D2_min per Shear Band')
    plt.ylabel('Density')
    plt.title('Distribution of Shear Band D2_min: Brittle vs Ductile')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Histogram saved to {output_path}")

def main():
    """
    Main entry point for the analysis pipeline.
    Executes aggregation, KS test, Bonferroni correction, and visualization.
    """
    parser = argparse.ArgumentParser(description="Analyze shear band precursors")
    parser.add_argument("--input-dir", type=str, default="data/processed",
                      help="Input directory containing precursor_metrics.csv")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                      help="Output directory for results")
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load precursor metrics
    metrics_file = input_dir / "precursor_metrics.csv"
    if not metrics_file.exists():
        logger.error(f"Input file not found: {metrics_file}")
        sys.exit(1)
    
    logger.info(f"Loading data from {metrics_file}")
    df = pd.read_csv(metrics_file)
    
    # Ensure required columns exist
    required_cols = ['d2_min', 'x', 'y', 'z', 'trajectory_id', 'label']
    if not all(col in df.columns for col in required_cols):
        missing = set(required_cols) - set(df.columns)
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)
    
    # Split by label
    brittle_df = df[df['label'] == 'brittle'].copy()
    ductile_df = df[df['label'] == 'ductile'].copy()
    
    logger.info(f"Loaded {len(brittle_df)} brittle and {len(ductile_df)} ductile particles")
    
    # Aggregate to shear bands for each group
    # Note: In a real scenario, we would aggregate per trajectory then combine.
    # For this implementation, we aggregate all brittle particles together and all ductile together.
    brittle_agg = aggregate_to_shear_bands_from_df(brittle_df)
    ductile_agg = aggregate_to_shear_bands_from_df(ductile_df)
    
    # Save aggregation results
    shear_band_agg_path = output_dir / "shear_band_aggregation.csv"
    combined_agg = pd.concat([
        brittle_agg.assign(group='brittle'),
        ductile_agg.assign(group='ductile')
    ], ignore_index=True)
    combined_agg.to_csv(shear_band_agg_path, index=False)
    logger.info(f"Saved shear band aggregation to {shear_band_agg_path}")
    
    # Perform KS test
    ks_result = perform_ks_test(brittle_agg, ductile_agg)
    ks_result_path = output_dir / "ks_test_results.json"
    save_json_output(ks_result, ks_result_path)
    logger.info(f"Saved KS test results to {ks_result_path}")
    
    # Bonferroni correction (assume 1 test for now, logic for multiple tests handled in T024)
    # T024a provides the count of tests, here we assume 1 for the base case
    num_tests = 1  # This would be dynamic based on T024a output
    corrected_p = apply_bonferroni_correction(ks_result['pvalue'], num_tests)
    
    corrected_result = {
        "raw_pvalue": ks_result['pvalue'],
        "corrected_pvalue": corrected_p,
        "num_tests": num_tests,
        "method": "Bonferroni correction"
    }
    corrected_path = output_dir / "corrected_p_values.json"
    save_json_output(corrected_result, corrected_path)
    logger.info(f"Saved corrected p-values to {corrected_path}")
    
    # Generate histograms
    hist_path = output_dir / "histograms.png"
    generate_histograms(brittle_agg, ductile_agg, hist_path)
    
    # Generate significance report
    alpha = 0.05
    is_significant = corrected_p < alpha
    report = {
        "alpha": alpha,
        "corrected_pvalue": corrected_p,
        "is_significant": is_significant,
        "conclusion": "Significant difference found" if is_significant else "No significant difference found",
        "timestamp": str(pd.Timestamp.now())
    }
    report_path = output_dir / "significance_report.json"
    save_json_output(report, report_path)
    logger.info(f"Saved significance report to {report_path}")
    
    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()