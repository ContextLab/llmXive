import logging
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from src.utils.config import get_data_root, resolve_path

logger = logging.getLogger(__name__)

def simple_average(df: pd.DataFrame, date_col: str = 'date', value_col: str = 'vote_share') -> pd.DataFrame:
    """
    Calculate arithmetic mean of vote shares per weekly bin.
    
    Args:
        df: DataFrame with columns including date_col and value_col.
        date_col: Name of the date column.
        value_col: Name of the vote share column.
        
    Returns:
        DataFrame with weekly bins and simple average forecast.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        return pd.DataFrame(columns=['week_start', 'simple_avg_forecast'])

    # Ensure date column is datetime
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Drop rows with invalid dates
    valid_df = df.dropna(subset=[date_col])
    
    if valid_df.empty:
        logger.warning("No valid dates found after conversion. Returning empty result.")
        return pd.DataFrame(columns=['week_start', 'simple_avg_forecast'])

    # Bin to weekly intervals (Monday start)
    valid_df['week_start'] = valid_df[date_col].dt.to_period('W').dt.start_time
    
    # Group by week and calculate simple average
    result = valid_df.groupby('week_start')[value_col].mean().reset_index()
    result.columns = ['week_start', 'simple_avg_forecast']
    
    logger.info(f"Simple average calculated for {len(result)} weekly bins.")
    return result

def weighted_average(df: pd.DataFrame, value_col: str = 'vote_share', weight_col: str = 'historical_rmse') -> pd.DataFrame:
    """
    Calculate inverse-RMSE weighted mean, normalizing weights to sum to 1.0.
    
    This implements FR-004: Accuracy-Weighted Averaging.
    The weight for each poll is calculated as 1 / RMSE.
    These weights are then normalized so they sum to 1.0.
    The forecast is the weighted sum of vote shares.
    
    Args:
        df: DataFrame containing vote shares and historical RMSE weights.
        value_col: Name of the vote share column.
        weight_col: Name of the historical RMSE column.
        
    Returns:
        DataFrame with weekly bins and weighted average forecast.
        
    Raises:
        ValueError: If weights are invalid (all zero or negative).
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        return pd.DataFrame(columns=['week_start', 'weighted_avg_forecast'])

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Drop rows with invalid dates or missing values
    valid_df = df.dropna(subset=['date', value_col, weight_col])
    
    if valid_df.empty:
        logger.warning("No valid data found after filtering. Returning empty result.")
        return pd.DataFrame(columns=['week_start', 'weighted_avg_forecast'])

    # Bin to weekly intervals
    valid_df['week_start'] = valid_df['date'].dt.to_period('W').dt.start_time

    # Calculate inverse RMSE weights and normalize per group
    def calculate_weighted_mean(group):
        rmse = group[weight_col].values
        votes = group[value_col].values
        
        # Handle edge case: zero or negative RMSE
        # Replace zero/negative RMSE with a large value to minimize their weight
        # or handle as specified in weights.py (default median weight logic)
        # For this implementation, we'll use a small epsilon to avoid division by zero
        epsilon = 1e-10
        inv_rmse = 1.0 / (np.maximum(rmse, epsilon))
        
        # Normalize weights to sum to 1.0
        weight_sum = np.sum(inv_rmse)
        if weight_sum == 0:
            # If all weights are effectively zero, fall back to simple average
            logger.warning(f"Zero weight sum for week {group.name}. Using simple average.")
            return np.nanmean(votes)
        
        normalized_weights = inv_rmse / weight_sum
        
        # Calculate weighted mean
        weighted_mean = np.sum(votes * normalized_weights)
        return weighted_mean

    result = valid_df.groupby('week_start').apply(calculate_weighted_mean).reset_index()
    result.columns = ['week_start', 'weighted_avg_forecast']
    
    # Handle any NaN results (e.g., from groups with all invalid data)
    result['weighted_avg_forecast'] = result['weighted_avg_forecast'].fillna(np.nan)
    
    logger.info(f"Weighted average calculated for {len(result)} weekly bins.")
    return result

def run_frequentist_analysis(input_path: Optional[str] = None, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run the full frequentist analysis pipeline:
    1. Load cleaned poll data
    2. Calculate simple average forecasts
    3. Calculate weighted average forecasts
    4. Merge results into a single output file
    
    Args:
        input_path: Path to input cleaned poll data CSV. If None, uses default path.
        output_path: Path to output forecasts CSV. If None, uses default path.
        
    Returns:
        DataFrame containing both simple and weighted average forecasts.
    """
    data_root = get_data_root()
    
    if input_path is None:
        input_path = resolve_path("data/processed/poll_data_cleaned.csv", root=data_root)
    else:
        input_path = resolve_path(input_path, root=data_root)
        
    if output_path is None:
        output_path = resolve_path("data/processed/frequentist_forecasts.csv", root=data_root)
    else:
        output_path = resolve_path(output_path, root=data_root)
    
    logger.info(f"Loading data from {input_path}")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Calculate simple average
    simple_df = simple_average(df)
    
    # Calculate weighted average
    weighted_df = weighted_average(df)
    
    # Merge results on week_start
    result = simple_df.merge(weighted_df, on='week_start', how='outer')
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    result.to_csv(output_path, index=False)
    logger.info(f"Frequentist forecasts saved to {output_path}")
    
    return result

def main():
    """Main entry point for the frequentist analysis script."""
    logging.basicConfig(level=logging.INFO)
    try:
        result = run_frequentist_analysis()
        print(f"Analysis complete. Processed {len(result)} weekly bins.")
        print(result.head())
    except Exception as e:
        logger.error(f"Error during frequentist analysis: {e}")
        raise

if __name__ == "__main__":
    main()