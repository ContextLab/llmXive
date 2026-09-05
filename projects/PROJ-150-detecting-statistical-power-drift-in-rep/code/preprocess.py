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
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = Path("data/raw/data.csv")
CLEANED_DATA_PATH = Path("data/derived/cleaned_data.csv")
VALIDATION_OUTPUT_PATH = Path("data/derived/grouping_validation.json")

REQUIRED_COLUMNS = ['year', 'effect_size', 'sample_size', 'field']
GROUPING_COLUMNS = ['field', 'original_study_id']

class DataFetchError(Exception):
    """Raised when data cannot be fetched or found."""
    pass

def calculate_power_cohen_d(effect_size, n, alpha=0.05):
    """
    Calculate statistical power for a two-tailed t-test given Cohen's d and sample size.
    
    Args:
        effect_size: Cohen's d effect size.
        n: Sample size per group (assuming equal groups for simplicity, or total N adjusted).
           Note: In the context of the OSF data, 'sample_size' often refers to N per group
           or total N. The formula below assumes 'n' is the N per group for the t-test
           calculation: ncp = d * sqrt(n/2). If 'n' is total N, we might need n/2.
           Based on standard power analysis for independent t-tests: ncp = d * sqrt(n/2).
           We will assume the input 'sample_size' is the N per group as is common in meta-analysis
           summaries, or if it's total N, the formula n * sqrt(n/2) would be wrong.
           Let's assume standard formula: ncp = d * sqrt(n/2) where n is N per group.
           If the dataset provides total N, we might need to adjust. However, without specific
           metadata, we proceed with the standard interpretation for the OSF reproducibility project
           where 'sample_size' often denotes the effective N used in the power calculation context.
           *Correction*: In many OSF datasets, sample_size is the total N. For a t-test, if N is total,
           n_per_group = N/2. Then ncp = d * sqrt((N/2)/2) = d * sqrt(N/4).
           However, the task description in T011a used: `ncp = d * np.sqrt(n / 2)`.
           To maintain consistency with the pipeline's previous step (T011a), we use the exact same logic.
        alpha: Significance level.
    
    Returns:
        float: Power estimate (1 - beta), or NaN if inputs are invalid.
    """
    if pd.isna(effect_size) or pd.isna(n) or n < 2:
        return np.nan
    
    # Ensure n is integer for df calculation if needed, though float works for scipy
    n_float = float(n)
    
    # Cohen's d power calculation (Two-tailed t-test)
    # Non-centrality parameter
    d = float(effect_size)
    # Consistent with T011a logic
    ncp = d * np.sqrt(n_float / 2)
    df = n_float - 2
    
    if df <= 0:
        return np.nan
        
    # Critical t-value for two-tailed test
    critical_t = stats.t.ppf(1 - alpha/2, df)
    
    # Power = 1 - CDF(t_crit; df, ncp)
    power = 1 - stats.t.cdf(critical_t, df, ncp)
    
    return float(power)

def load_raw_data(input_path):
    """Load the raw CSV data."""
    if not os.path.exists(input_path):
        raise DataFetchError(f"Raw data file not found at {input_path}. Please run code/download_data.py first.")
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        return df
    except Exception as e:
        raise DataFetchError(f"Failed to read CSV {input_path}: {e}")

def filter_missing_rows(df, required_cols):
    """Filter out rows with missing values in required columns."""
    initial_count = len(df)
    # Drop rows where any of the required columns are NaN
    df_clean = df.dropna(subset=required_cols)
    skipped = initial_count - len(df_clean)
    
    if skipped > 0:
        logger.warning(f"Skipped {skipped} rows due to missing required columns ({', '.join(required_cols)})")
    
    return df_clean

def compute_power_estimates(df):
    """Compute power estimates for each row."""
    logger.info("Computing power estimates...")
    df['power_estimate'] = df.apply(
        lambda row: calculate_power_cohen_d(row['effect_size'], row['sample_size']),
        axis=1
    )
    
    # Drop rows where power calculation failed (e.g. NaN inputs)
    initial_count = len(df)
    df = df.dropna(subset=['power_estimate'])
    dropped = initial_count - len(df)
    
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to failed power calculation (NaN results)")
    
    return df

def save_cleaned_data(df, output_path):
    """Save the cleaned data with power estimates."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def validate_groupings(df, output_path):
    """
    Validate grouping variables for variance and cardinality.
    
    Checks:
    1. Each factor has > 1 unique level.
    2. For each level, variance of 'power_estimate' > 0.
    
    Returns:
        dict: Validation status per factor.
    """
    validation = {}
    
    for group_col in GROUPING_COLUMNS:
        if group_col not in df.columns:
            logger.warning(f"Grouping column '{group_col}' not found in data. Skipping.")
            validation[group_col] = {"status": "missing", "valid_levels": []}
            continue
        
        unique_levels = df[group_col].unique()
        
        # Check if factor has any levels
        if len(unique_levels) == 0:
            validation[group_col] = {"status": "single_level", "valid_levels": []}
            continue
        
        # Check for single level (only one category in the whole dataset)
        if len(unique_levels) == 1:
            validation[group_col] = {"status": "single_level", "valid_levels": list(unique_levels)}
            logger.warning(f"Factor {group_col} has only 1 level. It cannot be used as a random effect.")
            continue
        
        valid_levels = []
        for level in unique_levels:
            group_data = df[df[group_col] == level]
            
            # Skip single-item groups (zero variance by definition)
            if len(group_data) < 2:
                continue
            
            # Calculate variance of power_estimate for this level
            var_val = group_data['power_estimate'].var()
            
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

def save_validation(validation, output_path):
    """Save validation results to JSON."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation, f, indent=2)
    
    logger.info(f"Saved grouping validation to {output_path}")

def main():
    """Main pipeline execution."""
    logger.info("Starting preprocessing pipeline.")
    
    # 1. Load raw data
    try:
        df = load_raw_data(RAW_DATA_PATH)
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        sys.exit(1)
    
    # 2. Filter missing rows
    df = filter_missing_rows(df, REQUIRED_COLUMNS)
    
    if len(df) == 0:
        logger.error("No data remaining after filtering missing values.")
        sys.exit(1)
    
    # 3. Compute power estimates
    df = compute_power_estimates(df)
    
    if len(df) == 0:
        logger.error("No data remaining after power calculation.")
        sys.exit(1)
    
    # 4. Save cleaned data (T011a requirement, also needed for T011b validation)
    save_cleaned_data(df, CLEANED_DATA_PATH)
    
    # 5. Validate groupings (T011b specific)
    validation = validate_groupings(df, VALIDATION_OUTPUT_PATH)
    save_validation(validation, VALIDATION_OUTPUT_PATH)
    
    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()
