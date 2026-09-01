"""
Preprocessing module for statistical power drift analysis.
Validates grouping variables for variance and cardinality.
"""
import pandas as pd
import numpy as np
import json
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching errors."""
    pass

def load_raw_data(input_path: str) -> pd.DataFrame:
    """
    Load raw data from CSV.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        DataFrame with raw data.
        
    Raises:
        DataFetchError: If file not found.
    """
    if not os.path.exists(input_path):
        raise DataFetchError(f"Raw data file not found at {input_path}. Please run code/download_data.py first to fetch data.")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def filter_missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows with missing critical columns.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Filtered DataFrame.
    """
    initial_count = len(df)
    df = df.dropna(subset=['year', 'effect_size', 'sample_size'])
    skipped = initial_count - len(df)
    
    if skipped > 0:
        logger.warning(f"Skipped {skipped} rows due to missing data")
    else:
        logger.info("No rows skipped due to missing data")
        
    return df

def compute_power_estimates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute power estimates using Cohen's d.
    
    Args:
        df: DataFrame with effect_size and sample_size.
        
    Returns:
        DataFrame with power_estimate column.
    """
    def calculate_power(effect_size, n, alpha=0.05):
        """Calculate power for a two-tailed t-test."""
        if pd.isna(effect_size) or pd.isna(n) or n < 2:
            return np.nan
        
        d = float(effect_size)
        n_val = int(n)
        ncp = d * np.sqrt(n_val / 2)
        df_val = n_val - 2
        critical_t = stats.t.ppf(1 - alpha/2, df_val)
        power = 1 - stats.t.cdf(critical_t, df_val, ncp)
        return power

    from scipy import stats
    
    logger.info("Computing power estimates")
    df['power_estimate'] = df.apply(
        lambda row: calculate_power(row['effect_size'], row['sample_size']),
        axis=1
    )
    return df

def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """
    Save cleaned data to CSV.
    
    Args:
        df: DataFrame to save.
        output_path: Output file path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def validate_groupings(df: pd.DataFrame) -> dict:
    """
    Validate grouping variables for variance and cardinality.
    
    Args:
        df: DataFrame with grouping columns.
        
    Returns:
        Validation dictionary with status and valid levels.
    """
    validation = {}
    group_cols = ['field', 'original_study_id']
    
    for group_col in group_cols:
        if group_col not in df.columns:
            logger.warning(f"Column {group_col} not found in DataFrame. Skipping validation.")
            validation[group_col] = {"status": "missing", "valid_levels": []}
            continue
            
        unique_levels = df[group_col].unique()
        
        # Check if factor has any levels
        if len(unique_levels) == 0:
            validation[group_col] = {"status": "single_level", "valid_levels": []}
            logger.warning(f"Factor {group_col} has no levels.")
            continue
        
        if len(unique_levels) == 1:
            validation[group_col] = {"status": "single_level", "valid_levels": list(unique_levels)}
            logger.warning(f"Factor {group_col} has only one level: {unique_levels[0]}.")
            continue
        
        valid_levels = []
        for level in unique_levels:
            group_data = df[df[group_col] == level]
            
            # Skip single-item groups (zero variance by definition)
            if len(group_data) < 2:
                continue
            
            # Check if power_residual or power_estimate column exists
            target_col = 'power_residual' if 'power_residual' in df.columns else 'power_estimate'
            if target_col not in group_data.columns:
                logger.warning(f"Column {target_col} not found in DataFrame. Cannot compute variance.")
                continue
                
            var_val = group_data[target_col].var()
            
            # Check for NaN (single item) or 0 variance
            if pd.isna(var_val) or var_val == 0:
                continue
                
            valid_levels.append(level)
        
        if len(valid_levels) == 0:
            validation[group_col] = {"status": "single_level", "valid_levels": []}
            logger.warning(f"Factor {group_col} has no valid levels with variance > 0. Dropping from model.")
        else:
            validation[group_col] = {"status": "valid", "valid_levels": valid_levels}
            logger.info(f"Factor {group_col}: Valid with {len(valid_levels)} levels.")
    
    return validation

def save_validation(validation: dict, output_path: str):
    """
    Save validation results to JSON.
    
    Args:
        validation: Validation dictionary.
        output_path: Output file path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(validation, f, indent=2)
    logger.info(f"Saved grouping validation to {output_path}")

def main():
    """Main preprocessing pipeline."""
    logger.info("[START] preprocess_pipeline: Starting preprocessing pipeline.")
    
    # Define paths
    input_path = "data/raw/data.csv"
    output_csv = "data/derived/cleaned_data.csv"
    output_json = "data/derived/grouping_validation.json"
    
    # Load raw data
    try:
        df = load_raw_data(input_path)
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        sys.exit(1)
    
    # Filter missing rows
    df = filter_missing_rows(df)
    
    # Compute power estimates
    df = compute_power_estimates(df)
    
    # Calculate residuals (Pilot OLS to control for inputs)
    # This creates the 'power_residual' needed for downstream tasks
    if len(df) > 2 and 'power_estimate' in df.columns and 'effect_size' in df.columns and 'sample_size' in df.columns:
        import statsmodels.api as sm
        logger.info("Calculating power residuals using pilot OLS model")
        X = df[['effect_size', 'sample_size']].fillna(0)
        y = df['power_estimate'].fillna(0)
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        df['power_residual'] = df['power_estimate'] - model.predict(X)
    else:
        logger.warning("Insufficient data for residual calculation, setting residuals to 0")
        df['power_residual'] = 0.0
    
    # Save cleaned data
    save_cleaned_data(df, output_csv)
    
    # Validate groupings
    validation = validate_groupings(df)
    save_validation(validation, output_json)
    
    logger.info("[END] preprocess_pipeline: Pipeline completed successfully.")

if __name__ == "__main__":
    main()