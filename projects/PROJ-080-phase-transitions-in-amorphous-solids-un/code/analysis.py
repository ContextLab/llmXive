import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# Import from utils for seed consistency
from utils import set_seed

def aggregate_to_shear_bands(input_file: str, output_file: str, k: int = 3, seed: int = 42) -> pd.DataFrame:
    """
    Aggregate D2_min values to shear bands using k-means clustering (k=3).
    
    This function reads the precursor metrics CSV, performs spatial clustering
    on particle coordinates to identify shear bands, and aggregates the D2_min
    values for each band.
    
    Args:
        input_file: Path to precursor_metrics.csv
        output_file: Path to write the shear band aggregation CSV
        k: Number of shear bands (default 3)
        seed: Random seed for reproducibility (default 42)
        
    Returns:
        DataFrame with columns: shear_band_id, mean_D2_min, particle_count
    """
    # Set seed for numerical determinism
    set_seed(seed)
    
    # Load precursor metrics
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    df = pd.read_csv(input_file)
    
    # Validate required columns
    required_cols = ['x', 'y', 'z', 'D2_min']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Remove rows with NaN in critical columns
    df_clean = df.dropna(subset=required_cols)
    
    if len(df_clean) == 0:
        raise ValueError("No valid data points after removing NaN values")
    
    # Prepare coordinates for clustering
    coordinates = df_clean[['x', 'y', 'z']].values
    
    # Perform k-means clustering
    kmeans = KMeans(n_clusters=k, random_state=seed, n_init=10)
    cluster_labels = kmeans.fit_predict(coordinates)
    
    # Assign cluster labels to dataframe
    df_clean['shear_band_id'] = cluster_labels
    
    # Aggregate by shear band
    aggregated = df_clean.groupby('shear_band_id').agg(
        mean_D2_min=('D2_min', 'mean'),
        particle_count=('D2_min', 'count')
    ).reset_index()
    
    # Ensure integer type for shear_band_id
    aggregated['shear_band_id'] = aggregated['shear_band_id'].astype(int)
    
    # Sort by shear_band_id for consistent output
    aggregated = aggregated.sort_values('shear_band_id')
    
    # Write output
    aggregated.to_csv(output_file, index=False)
    
    return aggregated

def perform_ks_test(brittle_file: str, ductile_file: str) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov test between brittle and ductile distributions.
    
    Args:
        brittle_file: Path to shear band aggregation CSV for brittle trajectories
        ductile_file: Path to shear band aggregation CSV for ductile trajectories
        
    Returns:
        Tuple of (statistic, p-value)
    """
    if not os.path.exists(brittle_file):
        raise FileNotFoundError(f"Brittle file not found: {brittle_file}")
    if not os.path.exists(ductile_file):
        raise FileNotFoundError(f"Ductile file not found: {ductile_file}")
        
    brittle_df = pd.read_csv(brittle_file)
    ductile_df = pd.read_csv(ductile_file)
    
    # Extract mean D2_min values
    brittle_values = brittle_df['mean_D2_min'].values
    ductile_values = ductile_df['mean_D2_min'].values
    
    # Perform KS test
    from scipy import stats
    statistic, p_value = stats.ks_2samp(brittle_values, ductile_values)
    
    return statistic, p_value

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of p-values to correct
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary with corrected p-values and significance status
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {'corrected_p_values': [], 'significance': []}
        
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significance = [p < alpha for p in corrected_p_values]
    
    return {
        'corrected_p_values': corrected_p_values,
        'significance': significance,
        'alpha': alpha,
        'n_tests': n_tests
    }

def generate_histograms(brittle_file: str, ductile_file: str, output_file: str) -> None:
    """
    Generate histogram overlay of brittle vs ductile distributions.
    
    Args:
        brittle_file: Path to brittle shear band aggregation CSV
        ductile_file: Path to ductile shear band aggregation CSV
        output_file: Path to save the histogram PNG
    """
    import matplotlib.pyplot as plt
    
    brittle_df = pd.read_csv(brittle_file)
    ductile_df = pd.read_csv(ductile_file)
    
    plt.figure(figsize=(10, 6))
    plt.hist(brittle_df['mean_D2_min'], bins=20, alpha=0.5, label='Brittle', color='red')
    plt.hist(ductile_df['mean_D2_min'], bins=20, alpha=0.5, label='Ductile', color='blue')
    plt.xlabel('Mean D2_min')
    plt.ylabel('Frequency')
    plt.title('Distribution of Mean D2_min: Brittle vs Ductile')
    plt.legend()
    plt.savefig(output_file)
    plt.close()

def main():
    """
    Main entry point for analysis pipeline.
    """
    parser = argparse.ArgumentParser(description='Analyze shear band precursors')
    parser.add_argument('--input-dir', type=str, required=True, help='Input directory containing precursor metrics')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory for analysis results')
    parser.add_argument('--brittle-file', type=str, default='brittle_precursor_metrics.csv', help='Name of brittle metrics file')
    parser.add_argument('--ductile-file', type=str, default='ductile_precursor_metrics.csv', help='Name of ductile metrics file')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Aggregate to shear bands for brittle
    brittle_input = input_dir / args.brittle_file
    brittle_output = output_dir / 'shear_bands_brittle.csv'
    
    if brittle_input.exists():
        aggregate_to_shear_bands(str(brittle_input), str(brittle_output))
        print(f"Aggregated brittle data to: {brittle_output}")
    else:
        print(f"Warning: Brittle input file not found: {brittle_input}")
    
    # Aggregate to shear bands for ductile
    ductile_input = input_dir / args.ductile_file
    ductile_output = output_dir / 'shear_bands_ductile.csv'
    
    if ductile_input.exists():
        aggregate_to_shear_bands(str(ductile_input), str(ductile_output))
        print(f"Aggregated ductile data to: {ductile_output}")
    else:
        print(f"Warning: Ductile input file not found: {ductile_input}")
    
    # Perform KS test if both files exist
    if brittle_output.exists() and ductile_output.exists():
        statistic, p_value = perform_ks_test(str(brittle_output), str(ductile_output))
        
        ks_results = {
            'statistic': float(statistic),
            'p_value': float(p_value),
            'method': 'Kolmogorov-Smirnov two-sample test',
            'description': 'Comparing mean D2_min distributions between brittle and ductile trajectories'
        }
        
        ks_output = output_dir / 'ks_test_results.json'
        with open(ks_output, 'w') as f:
            json.dump(ks_results, f, indent=2)
        
        print(f"KS test results written to: {ks_output}")
        
        # Generate histograms
        hist_output = output_dir / 'histograms.png'
        generate_histograms(str(brittle_output), str(ductile_output), str(hist_output))
        print(f"Histograms written to: {hist_output}")
    else:
        print("Skipping KS test: missing brittle or ductile shear band files")

if __name__ == '__main__':
    main()
