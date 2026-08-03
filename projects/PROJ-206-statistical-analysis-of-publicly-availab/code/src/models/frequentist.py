import logging
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from src.utils.config import get_data_root, resolve_path

logger = logging.getLogger(__name__)


def simple_average(polls: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate arithmetic mean of vote shares per weekly bin (FR-003).

    Args:
        polls: DataFrame containing 'date', 'vote_share', and 'week_bin' columns.

    Returns:
        DataFrame with 'week_bin' and 'simple_avg_forecast' columns.
    """
    if polls.empty:
        logger.warning("Input polls DataFrame is empty. Returning empty forecast.")
        return pd.DataFrame(columns=['week_bin', 'simple_avg_forecast'])

    if 'week_bin' not in polls.columns or 'vote_share' not in polls.columns:
        raise ValueError("Input DataFrame must contain 'week_bin' and 'vote_share' columns.")

    # Group by week_bin and calculate the mean
    result = polls.groupby('week_bin')['vote_share'].mean().reset_index()
    result.rename(columns={'vote_share': 'simple_avg_forecast'}, inplace=True)

    logger.info(f"Calculated simple average for {len(result)} weekly bins.")
    return result


def weighted_average(polls: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate inverse-RMSE weighted mean, normalizing weights to sum to 1.0 (FR-004).

    The weight for each poll is calculated as:
        w_i = (1 / rmse_i) / sum(1 / rmse_j for all j)

    If RMSE is 0 or NaN, the weight is treated as 0 (effectively excluding the poll).
    If all weights are 0, a uniform average is returned as a fallback.

    Args:
        polls: DataFrame containing 'date', 'vote_share', 'week_bin', and 'historical_rmse' columns.

    Returns:
        DataFrame with 'week_bin' and 'weighted_avg_forecast' columns.
    """
    if polls.empty:
        logger.warning("Input polls DataFrame is empty. Returning empty forecast.")
        return pd.DataFrame(columns=['week_bin', 'weighted_avg_forecast'])

    required_cols = ['week_bin', 'vote_share', 'historical_rmse']
    if not all(col in polls.columns for col in required_cols):
        missing = [col for col in required_cols if col not in polls.columns]
        raise ValueError(f"Input DataFrame missing required columns: {missing}")

    # Prepare a copy to avoid SettingWithCopyWarning
    df = polls.copy()

    # Handle RMSE: replace 0 and NaN with a large number so inverse is 0 (or handle explicitly)
    # Strategy: If RMSE is 0 or NaN, the weight should be 0.
    # We calculate raw weights = 1 / rmse. If rmse is 0 or NaN, raw_weight becomes inf or NaN.
    # We set inf/NaN raw_weights to 0.
    df['raw_weight'] = 1.0 / df['historical_rmse']
    
    # Replace inf and NaN with 0
    df['raw_weight'] = df['raw_weight'].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Check for the edge case where all raw_weights in a group are 0
    # In that case, we fallback to simple average (equal weights)
    
    def calc_weighted_mean(group):
        weights = group['raw_weight'].values
        votes = group['vote_share'].values
        
        weight_sum = np.sum(weights)
        
        if weight_sum == 0:
            # Fallback to simple average if all weights are 0
            return np.mean(votes)
        
        # Normalize weights to sum to 1.0
        normalized_weights = weights / weight_sum
        
        # Calculate weighted mean
        return np.sum(votes * normalized_weights)

    result = df.groupby('week_bin').apply(calc_weighted_mean).reset_index()
    result.rename(columns={0: 'weighted_avg_forecast'}, inplace=True)

    logger.info(f"Calculated weighted average for {len(result)} weekly bins.")
    return result


def run_frequentist_analysis(cleaned_data_path: Optional[Path] = None, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Orchestrates the frequentist analysis: loads data, computes simple and weighted averages,
    and saves the results.

    Args:
        cleaned_data_path: Path to the cleaned poll data CSV. If None, uses default config.
        output_path: Path for the output forecasts CSV. If None, uses default config.

    Returns:
        DataFrame containing both simple and weighted forecasts.
    """
    if cleaned_data_path is None:
        data_root = get_data_root()
        cleaned_data_path = data_root / "processed" / "poll_data_cleaned.csv"
    
    if output_path is None:
        data_root = get_data_root()
        output_path = data_root / "processed" / "frequentist_forecasts.csv"

    logger.info(f"Loading cleaned data from {cleaned_data_path}")
    if not cleaned_data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_data_path}")

    polls = pd.read_csv(cleaned_data_path)

    # Ensure numeric types
    polls['vote_share'] = pd.to_numeric(polls['vote_share'], errors='coerce')
    polls['historical_rmse'] = pd.to_numeric(polls['historical_rmse'], errors='coerce')

    # Calculate simple average
    simple_forecasts = simple_average(polls)

    # Calculate weighted average
    weighted_forecasts = weighted_average(polls)

    # Merge results
    final_forecasts = pd.merge(simple_forecasts, weighted_forecasts, on='week_bin', how='outer')
    
    # Sort by week_bin
    final_forecasts = final_forecasts.sort_values('week_bin').reset_index(drop=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving frequentist forecasts to {output_path}")
    final_forecasts.to_csv(output_path, index=False)

    logger.info("Frequentist analysis complete.")
    return final_forecasts


def main():
    """Entry point for running frequentist analysis."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        run_frequentist_analysis()
        logger.info("Task T018 (weighted_average) execution successful.")
    except Exception as e:
        logger.error(f"Task T018 failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()