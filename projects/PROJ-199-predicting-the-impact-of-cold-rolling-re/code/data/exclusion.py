"""
Exclusion logic for EBSD data processing.

Implements the logic to flag samples where >50% of points are filtered
as "low reliability" and exclude them from the final training set.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger
from config import get_reductions

# Initialize logger
logger = get_logger(__name__)

def calculate_reliability_metrics(df: pd.DataFrame, confidence_col: str = "confidence_index") -> pd.DataFrame:
    """
    Calculate reliability metrics for each sample based on the confidence index.

    A sample is considered "low reliability" if >50% of its points have a confidence index < 0.1.
    This threshold aligns with the preprocessing step in T012.

    Args:
        df: DataFrame containing EBSD data with 'sample_id' and 'confidence_index' columns.
        confidence_col: Name of the confidence index column.

    Returns:
        DataFrame with sample_id, total_points, filtered_points, reliability_ratio, and is_reliable.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty metrics.")
        return pd.DataFrame(columns=["sample_id", "total_points", "filtered_points", "reliability_ratio", "is_reliable"])

    if confidence_col not in df.columns:
        raise ValueError(f"Column '{confidence_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")

    # Group by sample_id
    sample_stats = df.groupby("sample_id").agg(
        total_points=(confidence_col, "count"),
        filtered_points=(confidence_col, lambda x: (x < 0.1).sum())
    ).reset_index()

    # Calculate reliability ratio (1 - fraction of filtered points)
    # If >50% are filtered (filtered_points / total_points > 0.5), the sample is unreliable.
    sample_stats["reliability_ratio"] = 1.0 - (sample_stats["filtered_points"] / sample_stats["total_points"])

    # Flag as unreliable if reliability_ratio < 0.5 (i.e., >50% filtered)
    sample_stats["is_reliable"] = sample_stats["reliability_ratio"] >= 0.5

    logger.info(f"Calculated reliability metrics for {len(sample_stats)} samples.")
    return sample_stats

def apply_exclusion_logic(
    df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Apply exclusion logic to filter out low-reliability samples.

    Args:
        df: Original DataFrame with EBSD data.
        metrics_df: DataFrame with reliability metrics (from calculate_reliability_metrics).
        output_path: Optional path to save the exclusion report.

    Returns:
        Filtered DataFrame containing only reliable samples.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    if metrics_df.empty:
        logger.warning("Metrics DataFrame is empty. Returning original DataFrame.")
        return df

    # Merge metrics with original data
    merged = df.merge(
        metrics_df[["sample_id", "is_reliable"]],
        on="sample_id",
        how="left"
    )

    # Identify unreliable samples
    unreliable_samples = metrics_df[~metrics_df["is_reliable"]]["sample_id"].tolist()
    reliable_samples = metrics_df[metrics_df["is_reliable"]]["sample_id"].tolist()

    logger.info(f"Excluding {len(unreliable_samples)} low-reliability samples: {unreliable_samples}")
    logger.info(f"Keeping {len(reliable_samples)} reliable samples: {reliable_samples}")

    # Filter the original DataFrame
    filtered_df = merged[merged["is_reliable"]].drop(columns=["is_reliable", "reliability_ratio", "total_points", "filtered_points"])

    # Log exclusion statistics
    if output_path:
        exclusion_report = metrics_df[~metrics_df["is_reliable"]][["sample_id", "total_points", "filtered_points", "reliability_ratio"]]
        exclusion_report.to_csv(output_path, index=False)
        logger.info(f"Exclusion report saved to {output_path}")

    return filtered_df

def main():
    """
    Main entry point for the exclusion logic script.
    Reads processed data, calculates reliability, applies exclusion, and saves the result.
    """
    logger.info("Starting exclusion logic process.")

    # Define paths
    processed_data_path = Path("data/processed/cleaned_ebsd.parquet")
    exclusion_report_path = Path("data/processed/exclusion_report.csv")
    output_path = Path("data/processed/cleaned_ebsd_final.parquet")

    if not processed_data_path.exists():
        logger.error(f"Processed data file not found at {processed_data_path}. "
                     "Please run T015 (consolidate) first to generate the input file.")
        raise FileNotFoundError(f"Input file not found: {processed_data_path}")

    # Load processed data
    logger.info(f"Loading processed data from {processed_data_path}")
    df = pd.read_parquet(processed_data_path)

    # Calculate reliability metrics
    logger.info("Calculating reliability metrics...")
    metrics_df = calculate_reliability_metrics(df)

    # Apply exclusion logic
    logger.info("Applying exclusion logic...")
    filtered_df = apply_exclusion_logic(df, metrics_df, exclusion_report_path)

    # Save final dataset
    logger.info(f"Saving final dataset to {output_path}")
    filtered_df.to_parquet(output_path, index=False)

    logger.info("Exclusion logic process completed successfully.")
    return filtered_df

if __name__ == "__main__":
    main()
