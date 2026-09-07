import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PowerError(Exception):
    """Raised when the number of adopters is insufficient for analysis."""
    pass


def filter_low_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter households based on low-income criteria.

    According to the project specifications (US1), this filters for households
    in census tracts with median income < 150% of the Federal Poverty Line (FPL).
    It expects a column indicating income relative to FPL (e.g., 'income_fpl_ratio').

    Args:
        df: Input DataFrame containing household data.

    Returns:
        Filtered DataFrame containing only low-income households.

    Raises:
        NotImplementedError: If this is a stub implementation.
        KeyError: If required columns are missing.
    """
    logger.info("Starting low-income filtering...")

    if 'income_fpl_ratio' not in df.columns:
        raise KeyError(
            "Required column 'income_fpl_ratio' missing for low-income filtering. "
            "Ensure ingestion step calculated this ratio."
        )

    # Filter: income < 150% of FPL (ratio < 1.5)
    low_income_mask = df['income_fpl_ratio'] < 1.5
    filtered_df = df[low_income_mask].copy()

    logger.info(
        f"Filtered {len(df) - len(filtered_df)} households. "
        f"Remaining: {len(filtered_df)} low-income households."
    )

    return filtered_df


def winsorize(df: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    """
    Winsorize continuous variables to handle outliers and zero energy costs.

    This function caps values at the specified percentiles (default 1st and 99th)
    to reduce the influence of extreme outliers before regression analysis.

    Args:
        df: Input DataFrame.
        lower: Lower percentile bound (e.g., 0.01 for 1st percentile).
        upper: Upper percentile bound (e.g., 0.99 for 99th percentile).

    Returns:
        DataFrame with winsorized continuous variables.

    Raises:
        NotImplementedError: If this is a stub implementation.
    """
    logger.info(f"Starting winsorization at {lower*100}% and {upper*100}% percentiles.")

    # Identify continuous numeric columns that are likely to need winsorization
    # Exclude boolean, object, and ID columns
    continuous_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Specific columns to winsorize based on domain knowledge (energy cost, income)
    target_cols = [col for col in continuous_cols if col not in ['treatment', 'pair_id']]

    winsorized_df = df.copy()

    for col in target_cols:
        lower_bound = df[col].quantile(lower)
        upper_bound = df[col].quantile(upper)

        # Handle cases where all values are the same (lower == upper)
        if lower_bound == upper_bound:
            logger.debug(f"Column {col} has no variance; skipping winsorization.")
            continue

        winsorized_df[col] = winsorized_df[col].clip(lower=lower_bound, upper=upper_bound)
        logger.debug(f"Winsorized {col}: [{lower_bound:.2f}, {upper_bound:.2f}]")

    logger.info("Winsorization complete.")
    return winsorized_df


def construct_treatment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct the binary treatment variable.

    Creates a 'treatment' column (1 if solar/microgrid adopter, 0 otherwise).
    The logic depends on the presence of specific installation columns (e.g., 'solar_installation').

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with a new 'treatment' column.

    Raises:
        NotImplementedError: If this is a stub implementation.
        KeyError: If required columns for treatment determination are missing.
    """
    logger.info("Constructing treatment variable...")

    # Check for expected columns that indicate treatment status
    # Based on US1 spec: solar_installation is a key indicator
    treatment_candidates = ['solar_installation', 'microgrid_installation', 'treatment_flag']
    available_candidate = next((col for col in treatment_candidates if col in df.columns), None)

    if available_candidate is None:
        raise KeyError(
            "No treatment indicator column found. Expected one of: "
            f"{treatment_candidates}. Ensure ingestion step populated these fields."
        )

    treatment_df = df.copy()

    # Assume 1 (or True) indicates treatment
    treatment_df['treatment'] = (treatment_df[available_candidate] == 1).astype(int)

    n_adopters = treatment_df['treatment'].sum()
    logger.info(
        f"Treatment constructed. Adopters: {n_adopters}, Controls: {len(treatment_df) - n_adopters}"
    )

    return treatment_df


def check_adopter_power(df: pd.DataFrame, min_adopters: int = 50) -> None:
    """
    Check if the number of adopters meets the minimum power requirement.

    Args:
        df: DataFrame containing the 'treatment' column.
        min_adopters: Minimum required number of adopters (default 50).

    Raises:
        PowerError: If the number of adopters is below the threshold.
    """
    if 'treatment' not in df.columns:
        raise KeyError("Cannot check power: 'treatment' column missing.")

    n_adopters = df['treatment'].sum()

    if n_adopters < min_adopters:
        logger.error(f"Insufficient adopters: {n_adopters} < {min_adopters}")
        raise PowerError(f"Insufficient adopters ({n_adopters} < {min_adopters})")

    logger.info(f"Power check passed: {n_adopters} adopters found.")


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values using Median Imputation for continuous and 'Missing' flag for categorical.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with missing values handled.
    """
    logger.info("Handling missing values...")
    missing_df = df.copy()

    # Identify numeric and categorical columns
    numeric_cols = missing_df.select_dtypes(include=[np.number]).columns
    categorical_cols = missing_df.select_dtypes(include=['object', 'category']).columns

    # Median Imputation for continuous variables
    for col in numeric_cols:
        if missing_df[col].isnull().any():
            median_val = missing_df[col].median()
            missing_df[col] = missing_df[col].fillna(median_val)
            logger.debug(f"Imputed {col} with median {median_val}")

    # Flag 'Missing' for categorical variables
    for col in categorical_cols:
        if missing_df[col].isnull().any():
            missing_df[col] = missing_df[col].fillna('Missing')
            logger.debug(f"Flagged missing values in {col} as 'Missing'")

    return missing_df


def preprocess_pipeline(df: pd.DataFrame, config: Optional[dict] = None) -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline.

    1. Handle missing values
    2. Filter low income
    3. Construct treatment
    4. Check power
    5. Winsorize

    Args:
        df: Raw input DataFrame.
        config: Optional configuration dictionary for thresholds.

    Returns:
        Preprocessed DataFrame ready for PSM.
    """
    logger.info("Starting full preprocessing pipeline.")

    # 1. Handle Missing Values
    df = handle_missing_values(df)

    # 2. Filter Low Income
    df = filter_low_income(df)

    # 3. Construct Treatment
    df = construct_treatment(df)

    # 4. Check Power (Fail loudly if insufficient)
    check_adopter_power(df)

    # 5. Winsorize
    winsorize_bounds = (0.01, 0.99)
    if config and 'winsorize_bounds' in config:
        winsorize_bounds = tuple(config['winsorize_bounds'])
    df = winsorize(df, lower=winsorize_bounds[0], upper=winsorize_bounds[1])

    logger.info("Preprocessing pipeline complete.")
    return df
