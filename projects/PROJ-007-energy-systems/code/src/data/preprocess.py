"""
Data preprocessing module.
Implements filtering, winsorization, treatment construction, and missing value handling.
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple

from src.utils.logging import get_logger

logger = get_logger(__name__)


class PowerError(Exception):
    """Raised when insufficient adopters remain after filtering."""
    pass


def filter_low_income(df: pd.DataFrame, income_col: str = 'income', threshold_pct: float = 150) -> pd.DataFrame:
    """
    Filter households in census tracts with median income < 150% of FPL.
    (Note: This assumes the input df already has tract-level median income or a proxy).

    For this implementation, we assume 'income' is household income and we filter
    based on a proxy for low-income status (e.g., income < 150% of a base FPL).
    Since FPL varies by household size, we use a simplified threshold here.

    Args:
        df: Input DataFrame.
        income_col: Column name for income.
        threshold_pct: Percentage of FPL threshold (default 150).

    Returns:
        Filtered DataFrame.
    """
    # Simplified: Assume FPL base is $14,000 for a single person, scale by household size if available.
    # If not, we just use a raw income threshold for demonstration.
    # In a real scenario, we would join with ACS tract data.
    # Here, we assume the data is already filtered or we use a simple heuristic.
    # Let's assume we have a column 'fpl_percentage' or calculate it.
    # If not present, we skip and warn.

    if 'fpl_percentage' not in df.columns:
        logger.warning("Column 'fpl_percentage' not found. Assuming all data is low-income for this step.")
        return df

    threshold = threshold_pct
    mask = df['fpl_percentage'] <= threshold
    logger.info(f"Filtered to {mask.sum()} low-income households (FPL <= {threshold}%).")
    return df[mask]


def winsorize(df: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    """
    Winsorize continuous variables to handle outliers.

    Args:
        df: Input DataFrame.
        lower: Lower percentile.
        upper: Upper percentile.

    Returns:
        DataFrame with winsorized numeric columns.
    """
    df_out = df.copy()
    numeric_cols = df_out.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        if col in ['treatment', 'id', 'fpl_percentage']:
            continue
        lower_val = df_out[col].quantile(lower)
        upper_val = df_out[col].quantile(upper)
        df_out[col] = df_out[col].clip(lower_val, upper_val)

    logger.info(f"Winsorized numeric columns at {lower*100}% and {upper*100}% percentiles.")
    return df_out


def construct_treatment(df: pd.DataFrame, solar_col: str = 'solar_installation') -> pd.DataFrame:
    """
    Construct binary treatment variable.

    Args:
        df: Input DataFrame.
        solar_col: Column indicating solar/microgrid installation.

    Returns:
        DataFrame with 'treatment' column.
    """
    df_out = df.copy()
    if solar_col in df_out.columns:
        df_out['treatment'] = (df_out[solar_col] > 0).astype(int)
    else:
        logger.warning(f"Column '{solar_col}' not found. Creating empty treatment column.")
        df_out['treatment'] = 0

    logger.info(f"Constructed treatment variable. Adopters: {df_out['treatment'].sum()}")
    return df_out


def check_adopter_power(df: pd.DataFrame, min_adopters: int = 50) -> None:
    """
    Check if sufficient adopters remain.

    Args:
        df: DataFrame with 'treatment' column.
        min_adopters: Minimum required adopters.

    Raises:
        PowerError: If adopters < min_adopters.
    """
    n_adopters = df[df['treatment'] == 1].shape[0]
    if n_adopters < min_adopters:
        raise PowerError(f"Insufficient adopters ({n_adopters} < {min_adopters})")
    logger.info(f"Power check passed: {n_adopters} adopters.")


def preprocess_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline.

    1. Filter low income.
    2. Construct treatment.
    3. Check power.
    4. Winsorize.
    5. Handle missing values.

    Args:
        df: Raw input data.

    Returns:
        Preprocessed DataFrame.
    """
    logger.info("Starting preprocessing pipeline...")

    # 1. Filter
    df = filter_low_income(df)

    # 2. Construct Treatment
    df = construct_treatment(df)

    # 3. Power Check
    check_adopter_power(df)

    # 4. Winsorize
    df = winsorize(df)

    # 5. Missing Value Handling
    df = handle_missing_values(df)

    logger.info("Preprocessing pipeline completed.")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values: Median Imputation for continuous, 'Missing' flag for categorical.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with imputed values.
    """
    df_out = df.copy()
    numeric_cols = df_out.select_dtypes(include=[np.number]).columns
    categorical_cols = df_out.select_dtypes(include=['object', 'category']).columns

    # Numeric: Median Imputation
    for col in numeric_cols:
        if df_out[col].isnull().any():
            median_val = df_out[col].median()
            df_out[col] = df_out[col].fillna(median_val)
            logger.info(f"Imputed missing values in '{col}' with median {median_val:.2f}.")

    # Categorical: 'Missing' flag
    for col in categorical_cols:
        if df_out[col].isnull().any():
            df_out[col] = df_out[col].fillna('Missing')
            logger.info(f"Flagged missing values in '{col}' as 'Missing'.")

    # Verify no silent data loss
    if df_out.isnull().any().any():
        logger.warning("Some missing values remain after imputation.")
    else:
        logger.info("No missing values remaining.")

    return df_out
