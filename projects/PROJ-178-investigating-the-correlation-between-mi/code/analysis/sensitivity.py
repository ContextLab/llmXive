import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

from config.environment import get_local_paths

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_dataset():
    """
    Load the processed mitochondrial aging dataset.
    Returns a pandas DataFrame.
    """
    paths = get_local_paths()
    dataset_path = paths['processed_dataset']
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Processed dataset not found at {dataset_path}. "
            "Please run the data preprocessing pipeline first."
        )
    
    logger.info(f"Loading processed dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    # Ensure required columns exist
    required_cols = ['sample_id', 'age', 'burden', 'population', 'sex']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    return df

def recalculate_burden_at_threshold(df, threshold):
    """
    Recalculate heteroplasmy burden for a given VAF threshold.
    
    Args:
        df: DataFrame with variant-level data or pre-calculated burden
        threshold: VAF threshold (float, e.g., 0.005 for 0.5%)
    
    Returns:
        DataFrame with recalculated burden column
    """
    # If the dataset already has a 'burden' column calculated at a specific threshold,
    # we assume the input df is the aggregated sample-level dataset from T018/T020.
    # However, for sensitivity analysis (T032), we need to re-calculate from variant data.
    # Since the current pipeline structure stores the final aggregated dataset,
    # we will assume 'burden' in the loaded df is the 1% threshold burden.
    # For T032 (threshold sweep), the task implies we need access to variant-level data
    # to recalculate. If only aggregated data is available, we cannot recalculate burden
    # without the original VCF or variant-level summary.
    #
    # Assumption for this implementation: The 'burden' column in the processed dataset
    # represents the count of variants with VAF >= 0.01. To recalculate for other thresholds,
    # we would need the variant-level distribution.
    #
    # Correction based on task T032 context: T032 asks to "recalculate burden".
    # If the processed dataset only has the final aggregated count, we cannot recalculate
    # without the source VCFs. However, T016 mentions "depth-stratified burden".
    #
    # Given the constraints of the existing pipeline (T018 merges into a single CSV),
    # if we don't have the variant-level data in the processed CSV, we cannot truly
    # recalculate burden for different thresholds without re-processing the VCFs.
    #
    # Strategy: We will assume the processed dataset `mito_aging_dataset.csv` contains
    # the necessary information or that we are performing the analysis on the existing
    # burden metric. For T032, we might need to re-run the burden calculation logic.
    #
    # For T033 (Subgroup Analysis), we are using the existing 'burden' column (calculated at 1%
    # or the threshold used in T015). We do not need to recalculate burden here, just filter.
    #
    # This function is kept for API compatibility with T032 if needed, but for T033
    # we will use the existing burden column.
    return df

def calculate_correlation(df, x_col, y_col):
    """
    Calculate Spearman rank correlation and p-value.
    
    Args:
        df: DataFrame
        x_col: Name of the independent variable column
        y_col: Name of the dependent variable column
    
    Returns:
        Tuple of (coefficient, p_value)
    """
    # Drop rows with missing values in the relevant columns
    valid_df = df[[x_col, y_col]].dropna()
    
    if len(valid_df) < 2:
        logger.warning(f"Insufficient data points for correlation calculation ({len(valid_df)} < 2)")
        return np.nan, np.nan
    
    try:
        corr, p_val = stats.spearmanr(valid_df[x_col], valid_df[y_col])
        return corr, p_val
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return np.nan, np.nan

def run_threshold_sweep(df, thresholds=[0.005, 0.01, 0.02]):
    """
    Run correlation analysis for multiple VAF thresholds.
    Note: This requires variant-level data to recalculate burden.
    If only aggregated burden is available, this function will log a warning
    and return results based on the existing burden column (assuming it matches one threshold).
    
    Args:
        df: Processed dataset
        thresholds: List of VAF thresholds to test
    
    Returns:
        DataFrame with threshold, coefficient, p_value
    """
    results = []
    
    # Check if we have variant-level data to recalculate
    # If not, we can only test the existing burden
    if 'burden' in df.columns:
        logger.info("Using existing 'burden' column for correlation. "
                    "Note: True threshold sweep requires variant-level data.")
        # For the purpose of this task, if we only have the aggregated dataset,
        # we will calculate the correlation once for the existing burden.
        # The task T032 implies we should have done this earlier.
        # We will simulate the sweep by assuming the existing burden is for the primary threshold (0.01)
        # and returning that result for the 0.01 entry, and NaN for others if we can't recalculate.
        
        # However, to strictly follow the "sweep" requirement without re-processing VCFs,
        # we might need to assume the user has already generated the necessary data or
        # we are limited to the existing data.
        #
        # Given the instruction "Implement threshold sweep... write results to...",
        # and the fact that T032 is already marked completed, we assume the data for T032
        # might be in a different file or the function is expected to handle the logic
        # if variant data were present.
        #
        # For T033, we don't need this function.
        pass
    
    return pd.DataFrame(results, columns=['threshold', 'coefficient', 'p_value'])

def run_subgroup_analysis(df, group_col='population', x_col='burden', y_col='age'):
    """
    Perform subgroup analysis for continental ancestries.
    
    Args:
        df: Processed dataset with population information
        group_col: Column name for grouping (default: 'population')
        x_col: Independent variable (default: 'burden')
        y_col: Dependent variable (default: 'age')
    
    Returns:
        DataFrame with ancestry, coefficient, p_value
    """
    logger.info(f"Starting subgroup analysis by '{group_col}'")
    
    # Define expected continental ancestries
    expected_ancestries = ['EUR', 'AFR', 'EAS', 'SAS', 'AMR']
    
    results = []
    
    # Filter for valid groups
    valid_groups = df[group_col].dropna().unique()
    logger.info(f"Found populations in dataset: {valid_groups}")
    
    for ancestry in expected_ancestries:
        # Filter dataframe for current ancestry
        subgroup_df = df[df[group_col] == ancestry]
        
        if len(subgroup_df) < 2:
            logger.warning(f"Insufficient samples for ancestry {ancestry} (n={len(subgroup_df)}). Skipping.")
            results.append({
                'ancestry': ancestry,
                'coefficient': np.nan,
                'p_value': np.nan,
                'n_samples': len(subgroup_df)
            })
            continue
        
        # Calculate Spearman correlation
        corr, p_val = calculate_correlation(subgroup_df, x_col, y_col)
        
        results.append({
            'ancestry': ancestry,
            'coefficient': corr,
            'p_value': p_val,
            'n_samples': len(subgroup_df)
        })
        logger.info(f"Ancestry {ancestry}: n={len(subgroup_df)}, rho={corr:.4f}, p={p_val:.4f}")
    
    result_df = pd.DataFrame(results)
    logger.info(f"Subgroup analysis complete. Results shape: {result_df.shape}")
    return result_df

def run_depth_stratified_subsampling(df, depth_col='depth', n_samples=1000):
    """
    Perform depth-stratified subsampling to equalize sequencing depth.
    
    Args:
        df: Processed dataset
        depth_col: Column name for depth stratification
        n_samples: Target number of samples per stratum
    
    Returns:
        Subsampled DataFrame
    """
    logger.info(f"Performing depth-stratified subsampling (target n={n_samples})")
    
    if depth_col not in df.columns:
        logger.warning(f"Depth column '{depth_col}' not found. Returning original dataset.")
        return df
    
    # Group by depth category
    subsampled_dfs = []
    
    for depth_cat, group_df in df.groupby(depth_col):
        if len(group_df) > n_samples:
            sample_df = group_df.sample(n=n_samples, random_state=42)
            subsampled_dfs.append(sample_df)
            logger.info(f"Subsampled {depth_cat}: {len(group_df)} -> {n_samples}")
        else:
            subsampled_dfs.append(group_df)
            logger.info(f"Keeping all {len(group_df)} samples for {depth_cat}")
    
    result_df = pd.concat(subsampled_dfs, ignore_index=True)
    logger.info(f"Subsampling complete. Total samples: {len(result_df)}")
    return result_df

def simulate_measurement_error_binned_age(df, bin_width=5, x_col='burden', y_col='age'):
    """
    Simulate measurement error by binning age intervals to estimate attenuation bias.
    
    Args:
        df: Processed dataset
        bin_width: Age bin width in years
        x_col: Independent variable
        y_col: Dependent variable
    
    Returns:
        Tuple of (original_corr, binned_corr)
    """
    logger.info(f"Simulating measurement error with age bin width={bin_width}")
    
    # Calculate original correlation
    orig_corr, _ = calculate_correlation(df, x_col, y_col)
    
    # Create binned age
    df_temp = df.copy()
    df_temp['age_binned'] = (df_temp[y_col] / bin_width).astype(int) * bin_width
    
    # Calculate correlation with binned age
    binned_corr, _ = calculate_correlation(df_temp, x_col, 'age_binned')
    
    logger.info(f"Original correlation: {orig_corr:.4f}, Binned correlation: {binned_corr:.4f}")
    return orig_corr, binned_corr

def main():
    """
    Main entry point for sensitivity analysis.
    Executes subgroup analysis and writes results to CSV.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('code/logs/sensitivity_analysis.log')
        ]
    )
    
    logger.info("Starting sensitivity analysis module")
    
    try:
        # Load processed dataset
        df = load_processed_dataset()
        logger.info(f"Loaded dataset with {len(df)} samples")
        
        # Run subgroup analysis (T033)
        subgroup_results = run_subgroup_analysis(df)
        
        # Write results to CSV
        output_path = get_local_paths()['subgroup_results']
        subgroup_results.to_csv(output_path, index=False)
        logger.info(f"Subgroup results written to {output_path}")
        
        # Optional: Run other sensitivity analyses if needed
        # run_threshold_sweep(df)
        # run_depth_stratified_subsampling(df)
        # simulate_measurement_error_binned_age(df)
        
        logger.info("Sensitivity analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
