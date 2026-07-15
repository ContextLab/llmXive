"""
Data Preprocessing Module for Plant Defense Compound Prediction.

This module handles:
- Loading processed data
- Handling missing genotypes
- Aggregating data to population level
- Calculating VIF for collinearity check
- Running the full preprocessing pipeline
"""

import logging
import sys
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError
from config import get_config

logger = get_module_logger(__name__)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def load_processed_data(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the filtered and validated data from the processed directory.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        FileNotFoundError: If the processed data file does not exist.
    """
    config = get_config()
    data_path = Path(config.paths.processed) / "filtered.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")

    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def handle_missing_genotypes(df: pd.DataFrame, threshold: float = 0.2) -> pd.DataFrame:
    """
    Handle missing genotype data by imputation or exclusion.

    For each population:
    - If missingness > threshold (20%), exclude the row.
    - Otherwise, impute missing values with the mean of the column.

    Args:
        df: Input DataFrame with genotype columns.
        threshold: Maximum allowed missingness fraction (default 0.2).

    Returns:
        pd.DataFrame: DataFrame with missing genotypes handled.
    """
    logger.info("Handling missing genotypes...")
    config = get_config()
    genotype_cols = [col for col in df.columns if col.startswith("genotype_")]

    if not genotype_cols:
        logger.warning("No genotype columns found. Skipping imputation.")
        return df

    # Identify genotype columns to process
    # Assuming columns are named genotype_<variant_id>
    # We need to identify which columns are numeric and represent genotypes
    numeric_genotype_cols = df[genotype_cols].select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_genotype_cols:
        logger.warning("No numeric genotype columns found. Skipping imputation.")
        return df

    # Check missingness per population (row)
    missing_counts = df[numeric_genotype_cols].isna().sum(axis=1)
    total_cols = len(numeric_genotype_cols)
    missing_fractions = missing_counts / total_cols

    # Identify populations to exclude
    exclude_mask = missing_fractions > threshold
    excluded_count = exclude_mask.sum()

    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} populations with missingness > {threshold*100}%")
        # Log which populations are excluded
        excluded_populations = df[exclude_mask]["population_id"].tolist()
        for pop_id in excluded_populations[:10]:  # Log first 10
            logger.debug(f"Excluding population {pop_id} due to high missingness")
        if excluded_count > 10:
            logger.debug(f"... and {excluded_count - 10} more")

    # Filter out excluded populations
    df_filtered = df[~exclude_mask].copy()

    # Impute remaining missing values with mean
    for col in numeric_genotype_cols:
        col_mean = df_filtered[col].mean()
        if pd.isna(col_mean):
            col_mean = 0  # Fallback if all values are NaN
        df_filtered[col] = df_filtered[col].fillna(col_mean)

    # Log imputation stats
    remaining_missing = df_filtered[numeric_genotype_cols].isna().sum().sum()
    logger.info(f"Imputation complete. Remaining missing values: {remaining_missing}")

    return df_filtered


def aggregate_to_population_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate all data to population level (FR-009).

    This function:
    1. Groups by population_id
    2. Aggregates genomic data (mean of genotype columns)
    3. Aggregates environmental data (mean of env columns)
    4. Aggregates compound data (mean of compound columns)
    5. Keeps population-level metadata

    Args:
        df: Input DataFrame with individual-level data.

    Returns:
        pd.DataFrame: Aggregated population-level DataFrame.
    """
    logger.info("Aggregating data to population level...")

    if "population_id" not in df.columns:
        raise ValueError("Input DataFrame must contain 'population_id' column")

    # Identify column types
    genotype_cols = [col for col in df.columns if col.startswith("genotype_")]
    env_cols = [col for col in df.columns if col.startswith("env_") or col in ["temp_mean", "precip_mean", "humidity_mean", "soil_ph", "elevation"]]
    compound_cols = [col for col in df.columns if col.startswith("compound_") or col in ["compound_concentration", "defense_score"]]
    metadata_cols = [col for col in df.columns if col not in genotype_cols + env_cols + compound_cols and col != "population_id"]

    # Define aggregation functions
    agg_dict = {}

    # Genotype columns: mean
    for col in genotype_cols:
        agg_dict[col] = "mean"

    # Environmental columns: mean
    for col in env_cols:
        agg_dict[col] = "mean"

    # Compound columns: mean
    for col in compound_cols:
        agg_dict[col] = "mean"

    # Metadata columns: first (or mode for categorical)
    for col in metadata_cols:
        if df[col].dtype == "object":
            agg_dict[col] = lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
        else:
            agg_dict[col] = "first"

    # Perform aggregation
    aggregated_df = df.groupby("population_id").agg(agg_dict).reset_index()

    logger.info(f"Aggregated {len(df)} rows to {len(aggregated_df)} populations")
    return aggregated_df


def calculate_vif(df: pd.DataFrame, feature_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for collinearity check.

    Explicitly flags and logs predictors with VIF > 5 as required by Spec Assumption 6.

    Args:
        df: DataFrame containing features.
        feature_cols: List of feature column names. If None, all numeric columns are used.

    Returns:
        pd.DataFrame: DataFrame with feature names and their VIF values.
    """
    logger.info("Calculating VIF for collinearity check...")

    if feature_cols is None:
        # Select numeric columns excluding target and ID columns
        exclude_cols = ["population_id", "compound_id", "env_id", "target", "compound_concentration", "defense_score"]
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col not in exclude_cols]

    if not feature_cols:
        logger.warning("No feature columns found for VIF calculation.")
        return pd.DataFrame(columns=["feature", "vif"])

    # Remove columns with zero variance
    feature_cols = [col for col in feature_cols if df[col].std() > 0]

    if len(feature_cols) < 2:
        logger.warning("Need at least 2 features to calculate VIF.")
        return pd.DataFrame(columns=["feature", "vif"])

    from statsmodels.stats.outliers_influence import variance_inflation_factor

    vif_results = []

    for feature in feature_cols:
        try:
            # Create design matrix (add constant for intercept)
            X = df[feature_cols].copy()
            X = sm.add_constant(X)

            # Calculate VIF
            vif = variance_inflation_factor(X.values, feature_cols.index(feature) + 1)
            vif_results.append({"feature": feature, "vif": vif})

            # Flag high VIF
            if vif > 5:
                logger.warning(f"High VIF detected for '{feature}': {vif:.2f} > 5.0")
            elif vif > 10:
                logger.error(f"Critical VIF detected for '{feature}': {vif:.2f} > 10.0 - severe multicollinearity")

        except Exception as e:
            logger.error(f"Error calculating VIF for '{feature}': {e}")
            vif_results.append({"feature": feature, "vif": np.nan})

    vif_df = pd.DataFrame(vif_results)
    vif_df = vif_df.sort_values("vif", ascending=False)

    # Log summary
    high_vif_count = (vif_df["vif"] > 5).sum()
    logger.info(f"VIF calculation complete. {high_vif_count} features have VIF > 5")

    return vif_df


def run_preprocessing_pipeline() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the full preprocessing pipeline:
    1. Load processed data
    2. Handle missing genotypes
    3. Aggregate to population level
    4. Calculate VIF
    5. Save outputs

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (filtered_df, vif_df)
    """
    logger.info("Starting preprocessing pipeline...")

    # Check disk space before processing
    config = get_config()
    estimated_size = 100 * 1024 * 1024  # 100 MB estimate
    try:
        check_disk_space(estimated_size)
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

    # Step 1: Load processed data
    try:
        df = load_processed_data()
    except FileNotFoundError as e:
        logger.error(f"Failed to load processed data: {e}")
        # Try to generate mock data if in test mode
        if config.mode == "test":
            logger.info("Running in test mode, generating mock data...")
            from data.mock_generator import generate_all_mock_data
            mock_data = generate_all_mock_data()
            # Combine mock data
            df = pd.concat([
                mock_data.get("genomic", pd.DataFrame()),
                mock_data.get("env", pd.DataFrame()),
                mock_data.get("compound", pd.DataFrame())
            ], axis=1, join="inner")
            if df.empty:
                raise RuntimeError("Failed to generate mock data for preprocessing")
        else:
            raise

    # Step 2: Handle missing genotypes
    df_filtered = handle_missing_genotypes(df)

    # Step 3: Aggregate to population level
    df_aggregated = aggregate_to_population_level(df_filtered)

    # Step 4: Calculate VIF
    vif_df = calculate_vif(df_aggregated)

    # Step 5: Save outputs
    output_dir = Path(config.paths.processed)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save filtered data
    filtered_path = output_dir / "filtered.csv"
    df_filtered.to_csv(filtered_path, index=False)
    logger.info(f"Saved filtered data to {filtered_path}")

    # Save VIF results
    vif_path = output_dir / "features_vif.csv"
    vif_df.to_csv(vif_path, index=False)
    logger.info(f"Saved VIF results to {vif_path}")

    # Check disk space after processing
    try:
        check_disk_space(estimated_size)
    except DiskSpaceError as e:
        logger.warning(f"Disk space check after processing: {e}")

    return df_filtered, vif_df


def main():
    """Main entry point for preprocessing module."""
    configure_root_logger()
    try:
        df_filtered, vif_df = run_preprocessing_pipeline()
        logger.info("Preprocessing pipeline completed successfully")
        print(f"Filtered data shape: {df_filtered.shape}")
        print(f"VIF results shape: {vif_df.shape}")
        return 0
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
