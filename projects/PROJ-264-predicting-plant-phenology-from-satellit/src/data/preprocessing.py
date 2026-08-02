"""
Preprocessing module for creating lagged feature windows.

This module implements the logic to transform temporally aligned data into
supervised learning samples with lagged features, preventing data leakage
by ensuring that features from time T-k to T-1 are used to predict the
event at time T.
"""
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

from src.config import get_config
from src.lib.utils import load_csv, save_csv, setup_logging
from src.data.provenance import add_provenance_entry

logger = setup_logging(__name__)

# Constants for lag window configuration
DEFAULT_LAG_WINDOW_SIZE = 3  # Number of time steps to look back (e.g., 3 months)
DEFAULT_TARGET_OFFSET = 1    # Steps ahead to predict (e.g., next month)
LAG_FEATURE_SUFFIX = "_lag_{}"  # Format for lagged column names

def create_lagged_features(
    df: pd.DataFrame,
    feature_columns: List[str],
    time_column: str = "date",
    site_column: str = "site_id",
    lag_window_size: int = DEFAULT_LAG_WINDOW_SIZE,
    target_offset: int = DEFAULT_TARGET_OFFSET
) -> pd.DataFrame:
    """
    Create lagged feature windows for time-series prediction.

    For each site, this function shifts the feature values back by 1 to
    `lag_window_size` time steps to create a window of historical data
    that can be used to predict the target at the current time step.

    This prevents data leakage by ensuring that future information is
    never used to predict past events.

    Args:
        df: DataFrame with temporally aligned data, must be sorted by
            site_id and date.
        feature_columns: List of column names to create lagged features for.
        time_column: Name of the column containing time information.
        site_column: Name of the column containing site identifiers.
        lag_window_size: Number of previous time steps to include.
        target_offset: Number of time steps ahead to predict.

    Returns:
        DataFrame with lagged features and corresponding target values.
        Rows that cannot have complete lag windows (due to insufficient
        history) are dropped.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df.copy()

    # Ensure data is sorted by site and time
    df_sorted = df.sort_values(by=[site_column, time_column]).reset_index(drop=True)

    # Create a copy to avoid modifying the original
    result_df = df_sorted.copy()

    # Group by site to create lagged features independently for each site
    lagged_dfs = []

    for site_id, group in df_sorted.groupby(site_column):
        group_lagged = group.copy()

        # Create lagged features for each feature column
        for feature in feature_columns:
            for lag in range(1, lag_window_size + 1):
                lag_col_name = f"{feature}{LAG_FEATURE_SUFFIX.format(lag)}"
                # Shift the feature values back by `lag` steps
                group_lagged[lag_col_name] = group_lagged[feature].shift(lag)

        # Create the target column (shift features forward by target_offset)
        # For phenology prediction, the target might be a specific event date
        # or a derived value. Here we assume the target is in a column named
        # 'target' or we use the first non-feature, non-time, non-site column.
        if 'phenology_event_day' in group.columns:
            target_col = 'phenology_event_day'
        else:
            # Fallback: use the first available column that isn't a feature, time, or site
            target_col = None
            for col in group.columns:
                if col not in feature_columns and col not in [time_column, site_column]:
                    if not col.endswith('_lag_'):
                        target_col = col
                        break

        if target_col and target_col in group_lagged.columns:
            group_lagged[f"target_{target_col}"] = group_lagged[target_col].shift(-target_offset)
        else:
            # If no target column found, we'll just create the lagged features
            # The caller must handle the target assignment
            logger.warning(f"No target column found for site {site_id}. Skipping target creation.")

        lagged_dfs.append(group_lagged)

    # Concatenate all site results
    result_df = pd.concat(lagged_dfs, ignore_index=True)

    # Drop rows with NaN values in lagged features (insufficient history)
    # and rows with NaN in target (insufficient future data)
    lag_feature_cols = [col for col in result_df.columns if col.endswith('_lag_')]
    target_cols = [col for col in result_df.columns if col.startswith('target_')]

    drop_cols = lag_feature_cols + target_cols
    result_df = result_df.dropna(subset=drop_cols)

    logger.info(f"Created lagged features. Original rows: {len(df_sorted)}, "
                f"Final rows after dropping NaN: {len(result_df)}")

    return result_df

def exclude_gdd_cumulative(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude `gdd_cumulative` from raw inputs to avoid multicollinearity.

    Growing Degree Days (GDD) are often highly correlated with temperature,
    which can lead to multicollinearity issues in regression models.
    This function removes the `gdd_cumulative` column if it exists.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with `gdd_cumulative` column removed if present.
    """
    if 'gdd_cumulative' in df.columns:
        logger.info("Excluding 'gdd_cumulative' column to avoid multicollinearity.")
        return df.drop(columns=['gdd_cumulative'])
    else:
        logger.debug("'gdd_cumulative' column not found. No exclusion needed.")
        return df

def run_preprocessing(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Run the full preprocessing pipeline: load data, create lagged features,
    exclude multicollinear variables, and save the result.

    Args:
        input_path: Path to the input CSV file with aligned data.
        output_path: Path to save the processed output CSV.
        config: Configuration dictionary. If None, loads from singleton config.

    Returns:
        Path to the output file.
    """
    # Load configuration
    if config is None:
        config_obj = get_config()
        input_path = input_path or config_obj.paths.processed / "aligned_dataset.csv"
        output_path = output_path or config_obj.paths.processed / "lagged_features_dataset.csv"
    else:
        input_path = input_path or Path(config.get('input_path', 'data/processed/aligned_dataset.csv'))
        output_path = output_path or Path(config.get('output_path', 'data/processed/lagged_features_dataset.csv'))

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = load_csv(input_path)

    if df.empty:
        raise ValueError(f"Input file {input_path} is empty.")

    # Identify feature columns
    # Exclude time, site, and known target columns from lagging
    exclude_cols = ['date', 'site_id', 'phenology_event_day', 'gdd_cumulative']
    feature_columns = [col for col in df.columns if col not in exclude_cols]

    if not feature_columns:
        raise ValueError("No feature columns found in the input data.")

    logger.info(f"Creating lagged features for {len(feature_columns)} columns")

    # Create lagged features
    df_lagged = create_lagged_features(
        df,
        feature_columns=feature_columns,
        time_column='date',
        site_column='site_id',
        lag_window_size=3,
        target_offset=1
    )

    # Exclude multicollinear variable
    df_clean = exclude_gdd_cumulative(df_lagged)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving processed data to {output_path}")
    save_csv(df_clean, output_path)

    # Record provenance
    add_provenance_entry(
        operation="preprocessing_lagged_features",
        input_file=str(input_path),
        output_file=str(output_path),
        params={
            "lag_window_size": 3,
            "target_offset": 1,
            "excluded_columns": ["gdd_cumulative"]
        }
    )

    logger.info(f"Preprocessing complete. Output saved to {output_path}")
    return output_path

def main():
    """Main entry point for running preprocessing as a script."""
    logger.info("Starting preprocessing pipeline...")
    try:
        output_path = run_preprocessing()
        logger.info(f"Successfully created lagged features dataset at {output_path}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
