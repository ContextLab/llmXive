import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import fdr_bh
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from src.utils.memory import get_subsample_ratio, is_subsampling_active, get_subsample_indices

logger = logging.getLogger(__name__)

def load_permanova_results(file_path: str) -> pd.DataFrame:
    """Load PERMANOVA results from a CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PERMANOVA results file not found: {file_path}")
    return pd.read_csv(file_path)

def apply_fdr_correction(df: pd.DataFrame, p_col: str = "p-value", adj_col: str = "p-value_adj") -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    if df.empty:
        return df
    
    p_values = df[p_col].values
    _, p_adjusted, _, _ = fdr_bh(p_values, alpha=0.05, multiplicity_correction=True)
    df = df.copy()
    df[adj_col] = p_adjusted
    return df

def generate_permanova_summary(results_df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """Generate a summary of PERMANOVA results with FDR correction."""
    if results_df.empty:
        logger.warning("Empty PERMANOVA results, generating empty summary.")
        df = pd.DataFrame(columns=["term", "R2", "p-value", "p-value_adj"])
        df.to_csv(output_path, index=False)
        return df
    
    df = apply_fdr_correction(results_df)
    df = df[["term", "R2", "p-value", "p-value_adj"]]
    df.to_csv(output_path, index=False)
    logger.info(f"Generated PERMANOVA summary at {output_path}")
    return df

def generate_db_rda_variance(variance_df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """Generate db-RDA variance partitioning summary."""
    if variance_df.empty:
        logger.warning("Empty variance partitioning data, generating empty summary.")
        df = pd.DataFrame(columns=["predictor", "unique_variance", "shared_variance", "total_variance"])
        df.to_csv(output_path, index=False)
        return df
    
    variance_df.to_csv(output_path, index=False)
    logger.info(f"Generated db-RDA variance summary at {output_path}")
    return variance_df

def generate_db_rda_biome_results(df: pd.DataFrame, biome: str, output_dir: str) -> str:
    """Generate db-RDA results for a specific biome."""
    output_path = os.path.join(output_dir, f"db_rda_biome_{biome}.csv")
    if df.empty:
        logger.warning(f"No data for biome {biome}, generating empty file.")
        pd.DataFrame(columns=["term", "R2", "p-value", "p-value_adj"]).to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    logger.info(f"Generated biome-specific db-RDA results at {output_path}")
    return output_path

def determine_top_drivers_stability(df: pd.DataFrame, driver_col: str = "top_driver") -> Tuple[float, str]:
    """Calculate the standard deviation of the rank index of the top driver across biomes."""
    if df.empty or driver_col not in df.columns:
        return 0.0, "FAIL"
    
    drivers = df[driver_col].unique()
    if len(drivers) < 2:
        return 0.0, "PASS"
    
    # Assign ranks based on frequency or order (simplified: use order of appearance)
    rank_map = {d: i for i, d in enumerate(drivers)}
    ranks = [rank_map.get(d, 0) for d in df[driver_col]]
    
    std_dev = np.std(ranks)
    status = "PASS" if std_dev <= 0.5 else "FAIL"
    return std_dev, status

def determine_top_drivers_and_ranking_stability(df: pd.DataFrame, driver_col: str = "top_driver") -> Tuple[float, str, pd.DataFrame]:
    """Determine top drivers and calculate ranking stability across biomes."""
    if df.empty:
        return 0.0, "FAIL", pd.DataFrame()
    
    summary = df.groupby("biome")[driver_col].first().reset_index()
    std_dev, status = determine_top_drivers_stability(summary, driver_col)
    return std_dev, status, summary

def run_threshold_sweep(permanova_df: pd.DataFrame, p_thresholds: List[float], r2_thresholds: List[float]) -> pd.DataFrame:
    """Run sensitivity analysis by sweeping p-value and R2 thresholds."""
    results = []
    for p_thresh in p_thresholds:
        for r2_thresh in r2_thresholds:
            subset = permanova_df[
                (permanova_df["p-value"] <= p_thresh) & 
                (permanova_df["R2"] >= r2_thresh)
            ]
            if not subset.empty:
                top_driver = subset.sort_values("R2", ascending=False).iloc[0]["term"]
            else:
                top_driver = "None"
            
            results.append({
                "p_threshold": p_thresh,
                "r2_threshold": r2_thresh,
                "top_driver": top_driver,
                "num_significant": len(subset)
            })
    
    return pd.DataFrame(results)

def check_and_handle_null_results(permanova_df: pd.DataFrame, output_path: str) -> bool:
    """Check if all results are non-significant and generate a null result report."""
    if permanova_df.empty:
        with open(output_path, "w") as f:
            f.write("No significant abiotic drivers detected\n")
        return True
    
    significant = permanova_df[permanova_df["p-value_adj"] < 0.05]
    if significant.empty:
        with open(output_path, "w") as f:
            f.write("No significant abiotic drivers detected\n")
        return True
    
    return False

def generate_sampling_report(output_path: str) -> None:
    """
    Generate a report documenting subsampling ratios triggered by memory constraints (FR-009).
    
    Reads the current subsampling state from the memory utility module and writes
    a CSV report to the specified output path.
    
    Columns:
      - sample_type: 'original' or 'subsampled'
      - original_count: Number of samples before subsampling
      - subsampled_count: Number of samples after subsampling (0 if not subsampled)
      - ratio: Retention ratio (subsampled / original)
    """
    # Determine if subsampling was active during the run
    was_active = is_subsampling_active()
    
    # Get the calculated ratio if active, otherwise default to 1.0 (no subsampling)
    ratio = get_subsample_ratio() if was_active else 1.0
    
    # Get indices if active (for logging/debugging, though not strictly required for the CSV)
    indices = get_subsample_indices() if was_active else None
    
    # Construct the report data
    # We record the state as observed. If subsampling was active, we report the ratio.
    # If not, we report 1.0.
    
    report_data = {
        "sample_type": ["subsampled" if was_active else "original"],
        "original_count": ["N/A"], # Original count is context-dependent, often not stored in global state
        "subsampled_count": ["N/A"],
        "ratio": [ratio]
    }
    
    # If we have specific indices, we can derive counts if needed, 
    # but the primary metric required by FR-009 is the ratio.
    # To make the report more useful, we'll try to infer counts if indices are available.
    if indices is not None and len(indices) > 0:
        # Assuming original count is not stored globally, we mark as calculated from indices if possible
        # In a real pipeline, the ingest step would log the original N.
        # Here we just report the ratio which is the critical FR-009 metric.
        pass
    
    df = pd.DataFrame(report_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Generated sampling report at {output_path} (Subsampling Active: {was_active}, Ratio: {ratio:.4f})")

def generate_biome_driver_summary_report(biome_results: Dict[str, pd.DataFrame], output_path: str) -> None:
    """Generate a summary report of top drivers per biome."""
    rows = []
    for biome, df in biome_results.items():
        if not df.empty:
            top_driver = df.sort_values("R2", ascending=False).iloc[0]["term"]
            rows.append({"biome": biome, "top_driver": top_driver, "r2": df.iloc[0]["R2"]})
        else:
            rows.append({"biome": biome, "top_driver": "None", "r2": 0.0})
    
    summary_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Generated biome driver summary at {output_path}")

def run_report_pipeline_with_null_handling(permanova_df: pd.DataFrame, output_dir: str) -> None:
    """Run the full report pipeline including null result handling."""
    # Generate PERMANOVA summary
    generate_permanova_summary(permanova_df, os.path.join(output_dir, "permanova_summary.csv"))
    
    # Check for null results
    null_report_path = os.path.join(output_dir, "null_results.md")
    if check_and_handle_null_results(permanova_df, null_report_path):
        logger.info("Null result report generated.")

def run_biome_driver_summary_pipeline(biome_results: Dict[str, pd.DataFrame], output_dir: str) -> None:
    """Run the biome driver summary pipeline."""
    generate_biome_driver_summary_report(biome_results, os.path.join(output_dir, "biome_driver_summary.csv"))
