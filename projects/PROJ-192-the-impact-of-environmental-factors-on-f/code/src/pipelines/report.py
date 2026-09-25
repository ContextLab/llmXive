import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import fdr_bh
from typing import List, Tuple, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

def load_permanova_results(file_path: str) -> pd.DataFrame:
    """Load PERMANOVA results from a CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PERMANOVA results file not found: {file_path}")
    df = pd.read_csv(path)
    required_cols = ['term', 'R2', 'p-value', 'p-value_adj', 'biome']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {missing}")
    return df

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction to a list of p-values."""
    if not p_values:
        return []
    return list(fdr_bh(p_values))

def generate_permanova_summary(input_file: str, output_file: str) -> pd.DataFrame:
    """Generate a summary of PERMANOVA results with FDR correction."""
    df = load_permanova_results(input_file)
    # Apply FDR if not already present or re-calculate
    if 'p-value_adj' not in df.columns:
        df['p-value_adj'] = apply_fdr_correction(df['p-value'].tolist())
    
    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved PERMANOVA summary to {output_file}")
    return df

def generate_db_rda_variance(input_file: str, output_file: str) -> pd.DataFrame:
    """Generate variance partitioning results from db-RDA."""
    # Assuming input is similar to permanova or a specific varpart output
    # For this implementation, we load and ensure formatting
    path = Path(input_file)
    if path.exists():
        df = pd.read_csv(path)
    else:
        # Fallback to permanova if varpart file missing, or create empty
        logger.warning(f"Input file {input_file} not found. Creating empty variance file.")
        df = pd.DataFrame(columns=['term', 'R2_unique', 'R2_shared'])
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved db-RDA variance to {output_file}")
    return df

def check_and_handle_null_results(df: pd.DataFrame, output_file: str) -> bool:
    """Check if any significant results exist. If not, generate a null report."""
    if df.empty:
        logger.warning("No PERMANOVA results found.")
        return False
    
    significant = df[df['p-value_adj'] < 0.05]
    if significant.empty:
        logger.warning("No significant abiotic drivers detected (p > 0.05).")
        # Generate a specific null report file if needed, or just log
        with open(output_file, 'w') as f:
            f.write("No significant abiotic drivers detected.\n")
        return False
    return True

def run_report_pipeline_with_null_handling(permanova_file: str, variance_file: str, output_dir: str):
    """Run the full report generation pipeline."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    permanova_summary_file = output_path / "permanova_summary.csv"
    variance_file_out = output_path / "db_rda_variance.csv"
    null_report_file = output_path / "null_results.txt"

    df_permanova = generate_permanova_summary(permanova_file, str(permanova_summary_file))
    generate_db_rda_variance(variance_file, str(variance_file_out))
    
    check_and_handle_null_results(df_permanova, str(null_report_file))

def generate_db_rda_biome_results(stratum_results: Dict[str, pd.DataFrame], output_dir: str):
    """Generate db-RDA variance files for each biome stratum."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for biome, df in stratum_results.items():
        if df is None or df.empty:
            logger.warning(f"No results for biome {biome}, skipping.")
            continue
        
        out_file = output_path / f"db_rda_biome_{biome}.csv"
        df.to_csv(out_file, index=False)
        logger.info(f"Saved biome results for {biome} to {out_file}")

def determine_top_drivers_stability(results_df: pd.DataFrame, output_file: str) -> Tuple[float, bool]:
    """
    Determine the top driver per biome and calculate the standard deviation 
    of the rank index of the top driver across biomes.
    
    Metric: Standard deviation of the rank index of the top driver.
    Pass Condition: std_dev <= 0.5.
    
    Args:
        results_df: DataFrame with columns ['biome', 'term', 'R2', 'p-value_adj'].
                    Must contain results for multiple biomes.
        output_file: Path to the output CSV file.
                    
    Returns:
        Tuple of (std_dev, passed)
    """
    if results_df.empty:
        logger.warning("Results dataframe is empty. Cannot determine stability.")
        # Create a minimal output file indicating failure
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({'biome': ['N/A'], 'top_driver': ['N/A'], 'std_dev': [float('nan')], 'passed': [False]}).to_csv(output_file, index=False)
        return float('nan'), False

    # Ensure we have the necessary columns
    required = ['biome', 'term', 'R2', 'p-value_adj']
    if not all(c in results_df.columns for c in required):
        raise ValueError(f"Results dataframe missing columns. Required: {required}")

    # Filter for significant results if the task implies only significant drivers count
    # However, the task says "top driver", which usually implies the highest R2 regardless of significance 
    # unless specified. We will assume top by R2.
    # Group by biome and find the term with the highest R2
    top_drivers = results_df.loc[results_df.groupby('biome')['R2'].idxmax()]
    
    if top_drivers.empty:
        logger.warning("No top drivers found.")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({'biome': [], 'top_driver': [], 'std_dev': [], 'passed': []}).to_csv(output_file, index=False)
        return float('nan'), False

    # Get the list of unique drivers found across all biomes to establish a rank index
    # The "rank index" of a driver is its position in the sorted list of all unique drivers?
    # Or is it the rank of the driver *within* its biome?
    # Re-reading: "standard deviation of the rank index of the top driver across biomes".
    # Interpretation:
    # 1. Identify the top driver for each biome (e.g., Biome A -> pH, Biome B -> Moisture).
    # 2. We need a "rank index" for these drivers.
    #    If the set of all possible drivers is D = {pH, Moisture, Temp...}, we assign indices 0, 1, 2...
    #    But the task says "rank index", implying the rank of the driver in the sorted list of drivers by some metric (e.g. global R2).
    #    Let's assume global ranking by average R2 or sum of R2 across all data.
    
    # Calculate global importance (sum of R2) for all terms
    global_ranks = results_df.groupby('term')['R2'].sum().sort_values(ascending=False)
    rank_map = {term: idx for idx, term in enumerate(global_ranks.index)}
    
    # Map the top driver of each biome to its global rank index
    top_drivers['rank_index'] = top_drivers['term'].map(rank_map)
    
    if top_drivers['rank_index'].isna().any():
        logger.warning("Some top drivers not found in global rank map.")
        # Drop NaNs
        top_drivers = top_drivers.dropna(subset=['rank_index'])

    if len(top_drivers) < 2:
        logger.warning("Not enough biomes to calculate standard deviation.")
        std_dev = 0.0
    else:
        std_dev = top_drivers['rank_index'].std()

    passed = std_dev <= 0.5
    
    logger.info(f"Calculated std_dev of top driver rank index: {std_dev:.4f}. Pass: {passed}")
    
    # Prepare output dataframe
    output_df = pd.DataFrame({
        'biome': top_drivers['biome'],
        'top_driver': top_drivers['term'],
        'std_dev': [std_dev] * len(top_drivers),
        'passed': [passed] * len(top_drivers)
    })
    
    # Also add a summary row if needed, or just the per-biome rows. 
    # The task asks to "Log the calculated standard deviation and a Pass/Fail flag to results/biome_ranking_summary.csv".
    # We will write the per-biome breakdown and potentially a summary.
    # For simplicity, we write the per-biome rows.
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_file, index=False)
    
    return std_dev, passed

def determine_top_drivers_and_ranking_stability(permanova_summary_path: str, output_file: str):
    """
    Wrapper to load permanova results, determine top drivers, calculate stability,
    and write the summary CSV.
    """
    df = load_permanova_results(permanova_summary_path)
    std_dev, passed = determine_top_drivers_stability(df, output_file)
    return std_dev, passed

def run_threshold_sweep(results_path: str, thresholds: List[float], output_file: str):
    """Iterate p-value thresholds and re-evaluate top driver rankings."""
    # Placeholder for T033 implementation
    pass

def generate_sampling_report(sampling_log_path: str, output_file: str):
    """Generate a report on subsampling ratios."""
    # Placeholder for T038 implementation
    pass

def generate_biome_driver_summary_report(stratum_results: Dict[str, pd.DataFrame], output_file: str):
    """Generate a summary report indicating if top predictor changes across biomes."""
    # Placeholder for T030 implementation
    pass

def run_biome_driver_summary_pipeline(permanova_file: str, output_dir: str):
    """Run the full biome driver stability pipeline."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    summary_file = output_path / "biome_ranking_summary.csv"
    std_dev, passed = determine_top_drivers_and_ranking_stability(permanova_file, str(summary_file))
    logger.info(f"Biome ranking stability: std_dev={std_dev}, passed={passed}")
    
    return passed
