"""
Correlation analysis and statistical testing pipeline.

Implements Pearson/Spearman correlation between complexity metrics and fatigue scores,
applies Benjamini-Hochberg correction, and validates data requirements.
"""
import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Import shared utilities
from utils.logging import get_logger
from benjamini_hochberg import run_benjamini_hochberg

def load_config(config_path="code/config.yaml"):
    """Load pipeline configuration."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def setup_logger(name="analysis"):
    """Setup logging infrastructure."""
    logger = get_logger(name)
    return logger

def validate_metadata(df, fatigue_col_pre="fatigue_pre", fatigue_col_post="fatigue_post"):
    """
    Validate that required metadata columns exist.

    Per FR-001 and FR-004, we require paired pre/post fatigue ratings.
    """
    required_cols = [fatigue_col_pre, fatigue_col_post]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required metadata columns: {missing}. "
                       f"Dataset must contain paired pre/post fatigue ratings per FR-001.")
    return True

def run_correlation_analysis(complexity_df, fatigue_df, method="spearman"):
    """
    Calculate correlations between complexity metrics and fatigue delta.

    Parameters
    ----------
    complexity_df : pd.DataFrame
        DataFrame with complexity metrics (LZC or PE) per channel.
    fatigue_df : pd.DataFrame
        DataFrame with fatigue ratings (pre and post).
    method : str
        Correlation method: 'pearson' or 'spearman'.

    Returns
    -------
    pd.DataFrame
        DataFrame with correlation statistics per channel.
    """
    # Calculate fatigue delta (Post - Pre)
    fatigue_delta = fatigue_df["fatigue_post"] - fatigue_df["fatigue_pre"]

    results = []

    for channel in complexity_df.columns:
        if channel in ["participant_id"]:
            continue

        if channel not in fatigue_df.columns:
            # Assume channel is in complexity_df but we match by participant_id
            # Join on participant_id
            pass

        # Extract data for this channel
        channel_data = complexity_df[channel]
        participant_ids = complexity_df["participant_id"]

        # Merge with fatigue delta
        merged = pd.DataFrame({
            "participant_id": participant_ids,
            "complexity": channel_data,
            "fatigue_delta": fatigue_delta.values
        })

        # Drop NaN
        merged = merged.dropna()

        if len(merged) < 3:
            results.append({
                "channel": channel,
                "correlation": np.nan,
                "p_value": np.nan,
                "n": len(merged)
            })
            continue

        # Calculate correlation
        if method == "pearson":
            corr, p_val = stats.pearsonr(merged["complexity"], merged["fatigue_delta"])
        else:
            corr, p_val = stats.spearmanr(merged["complexity"], merged["fatigue_delta"])

        results.append({
            "channel": channel,
            "correlation": corr,
            "p_value": p_val,
            "n": len(merged),
            "method": method
        })

    return pd.DataFrame(results)

def run_benjamini_hochberg_correction(results_df, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction to p-values in results.
    """
    if "p_value" not in results_df.columns:
        raise ValueError("Results DataFrame must contain 'p_value' column")

    p_values = results_df["p_value"]
    corrected = run_benjamini_hochberg(p_values, alpha)

    # Merge back
    results_df["adj_p_value"] = corrected["adj_p_value"]
    results_df["rejected"] = corrected["rejected"]

    return results_df

def write_validation_report(results_df, output_path):
    """Write validation report to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)

def main():
    """Main entry point for analysis pipeline."""
    logger = setup_logger()
    logger.info("Starting analysis pipeline.")

    # Load config
    config = load_config()
    logger.info(f"Loaded config: {config}")

    # Define paths
    lzc_path = Path("data/processed/lzc_metrics.csv")
    pe_path = Path("data/processed/pe_metrics.csv")
    fatigue_path = Path("data/processed/fatigue_ratings.csv")
    output_path = Path("data/analysis/correlation_results.csv")

    # Check for input files
    if not lzc_path.exists() and not pe_path.exists():
        logger.error("No complexity metrics found. Run code/features.py first.")
        sys.exit(1)

    if not fatigue_path.exists():
        logger.error("Fatigue ratings file not found. Ensure data download completed.")
        sys.exit(1)

    # Load fatigue data
    fatigue_df = pd.read_csv(fatigue_path)
    validate_metadata(fatigue_df)
    logger.info(f"Loaded fatigue data for {len(fatigue_df)} participants")

    # Load complexity data (prefer LZC if available)
    if lzc_path.exists():
        complexity_df = pd.read_csv(lzc_path)
        logger.info(f"Loaded LZC metrics for {len(complexity_df)} participants")
    else:
        complexity_df = pd.read_csv(pe_path)
        logger.info(f"Loaded PE metrics for {len(complexity_df)} participants")

    # Run correlation analysis
    logger.info("Running correlation analysis...")
    results = run_correlation_analysis(complexity_df, fatigue_df, method="spearman")

    # Apply BH correction
    alpha = config.get("alpha", 0.05)
    logger.info(f"Applying Benjamini-Hochberg correction (alpha={alpha})")
    results = run_benjamini_hochberg_correction(results, alpha)

    # Write output
    write_validation_report(results, output_path)
    logger.info(f"Analysis complete. Results saved to {output_path}")

    # Log summary
    n_sig = results["rejected"].sum()
    logger.info(f"Significant correlations: {n_sig}/{len(results)}")

    return results

if __name__ == "__main__":
    main()