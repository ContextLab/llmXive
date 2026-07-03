import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from config.environment import get_local_paths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_dataset() -> pd.DataFrame:
    """Load the processed dataset from the standard location."""
    paths = get_local_paths()
    input_path = paths['processed_dataset']
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Processed dataset not found at {input_path}. "
            "Please run the data acquisition and preprocessing pipeline first."
        )
    
    logger.info(f"Loading processed dataset from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded dataset with {len(df)} samples and {len(df.columns)} columns")
    return df

def recalculate_burden_at_threshold(df: pd.DataFrame, threshold: float) -> pd.Series:
    """
    Recalculate heteroplasmy burden for a specific VAF threshold.
    
    Args:
        df: DataFrame containing variant-level data or pre-aggregated burden.
            If variant-level, expects 'vaf' and 'sample_id'.
            If pre-aggregated, expects 'burden_{threshold}' columns or raw counts.
        threshold: VAF threshold (0.0 to 1.0) to apply.
    
    Returns:
        Series of recalculated burden per sample.
    """
    # Check if we have variant-level data
    if 'vaf' in df.columns and 'sample_id' in df.columns:
        # Filter variants above threshold
        variants_above = df[df['vaf'] >= threshold]
        # Count variants per sample
        burden = variants_above.groupby('sample_id').size()
        return burden
    else:
        # If we have pre-aggregated burden columns (e.g., burden_0.01, burden_0.02)
        col_name = f'burden_{threshold:.2f}'
        if col_name in df.columns:
            return df[col_name]
        else:
            # Fallback: return existing burden if threshold is close to 0.01
            if abs(threshold - 0.01) < 0.001 and 'burden' in df.columns:
                return df['burden']
            raise ValueError(f"Cannot recalculate burden at threshold {threshold}. "
                           "Expected variant-level data or pre-computed burden columns.")

def calculate_correlation(df: pd.DataFrame, burden_col: str, age_col: str = 'age') -> dict:
    """
    Calculate Spearman correlation between burden and age.
    
    Args:
        df: DataFrame with burden and age columns.
        burden_col: Name of the burden column.
        age_col: Name of the age column.
    
    Returns:
        Dictionary with correlation coefficient and p-value.
    """
    # Drop rows with missing values
    valid_data = df[[burden_col, age_col]].dropna()
    
    if len(valid_data) < 3:
        logger.warning(f"Insufficient data for correlation calculation ({len(valid_data)} samples)")
        return {'rho': np.nan, 'p_value': np.nan, 'n': len(valid_data)}
    
    rho, p_value = stats.spearmanr(valid_data[burden_col], valid_data[age_col])
    
    logger.info(f"Spearman correlation: rho={rho:.4f}, p={p_value:.4e}, n={len(valid_data)}")
    return {'rho': rho, 'p_value': p_value, 'n': len(valid_data)}

def run_threshold_sweep(df: pd.DataFrame, thresholds: list = None) -> pd.DataFrame:
    """
    Run correlation analysis across multiple VAF thresholds.
    
    Args:
        df: Processed dataset.
        thresholds: List of VAF thresholds to test (default: [0.005, 0.01, 0.02, 0.05]).
    
    Returns:
        DataFrame with results for each threshold.
    """
    if thresholds is None:
        thresholds = [0.005, 0.01, 0.02, 0.05]
    
    results = []
    for thresh in thresholds:
        logger.info(f"Running threshold sweep at VAF >= {thresh}")
        
        # Recalculate burden at this threshold
        burden_series = recalculate_burden_at_threshold(df, thresh)
        
        # Create temporary dataframe for correlation
        temp_df = pd.DataFrame({
            'burden': burden_series,
            'age': df.loc[burden_series.index, 'age'] if 'age' in df.columns else None
        })
        
        # Calculate correlation
        corr_result = calculate_correlation(temp_df, 'burden', 'age')
        
        results.append({
            'threshold': thresh,
            'rho': corr_result['rho'],
            'p_value': corr_result['p_value'],
            'n_samples': corr_result['n']
        })
    
    return pd.DataFrame(results)

def run_subgroup_analysis(df: pd.DataFrame, group_col: str = 'population') -> pd.DataFrame:
    """
    Run correlation analysis within continental ancestry subgroups.
    
    Args:
        df: Processed dataset with population column.
        group_col: Column name for grouping (default: 'population').
    
    Returns:
        DataFrame with correlation results per subgroup.
    """
    if group_col not in df.columns:
        logger.warning(f"Group column '{group_col}' not found in dataset")
        return pd.DataFrame()
    
    results = []
    for group, group_df in df.groupby(group_col):
        logger.info(f"Running subgroup analysis for {group}")
        
        # Ensure we have enough samples
        if len(group_df) < 10:
            logger.warning(f"Skipping {group}: only {len(group_df)} samples")
            continue
        
        # Calculate correlation
        corr_result = calculate_correlation(group_df, 'burden', 'age')
        
        results.append({
            'group': group,
            'n_samples': corr_result['n'],
            'rho': corr_result['rho'],
            'p_value': corr_result['p_value']
        })
    
    return pd.DataFrame(results)

def run_depth_stratified_subsampling(df: pd.DataFrame, target_depth: int = None) -> pd.DataFrame:
    """
    Run correlation analysis after subsampling to equalize sequencing depth.
    
    Args:
        df: Processed dataset with depth information.
        target_depth: Target sequencing depth (default: median depth).
    
    Returns:
        DataFrame with correlation results before and after subsampling.
    """
    if 'depth' not in df.columns:
        logger.warning("Depth column not found, skipping depth stratified analysis")
        return pd.DataFrame()
    
    if target_depth is None:
        target_depth = int(df['depth'].median())
    
    logger.info(f"Subsampling to target depth: {target_depth}")
    
    # Filter samples with sufficient depth
    deep_samples = df[df['depth'] >= target_depth]
    
    if len(deep_samples) < 10:
        logger.warning("Insufficient samples with required depth")
        return pd.DataFrame()
    
    # Calculate correlation on subsampled data
    corr_result = calculate_correlation(deep_samples, 'burden', 'age')
    
    # Also calculate on full dataset for comparison
    full_corr = calculate_correlation(df, 'burden', 'age')
    
    return pd.DataFrame([{
        'method': 'full_dataset',
        'n_samples': full_corr['n'],
        'rho': full_corr['rho'],
        'p_value': full_corr['p_value']
    }, {
        'method': 'depth_stratified',
        'target_depth': target_depth,
        'n_samples': corr_result['n'],
        'rho': corr_result['rho'],
        'p_value': corr_result['p_value']
    }])

def simulate_measurement_error_binned_age(df: pd.DataFrame, n_bins: int = 10, n_simulations: int = 1000) -> pd.DataFrame:
    """
    Implement measurement error simulation using binned age intervals to estimate attenuation bias.
    
    This function:
    1. Bins age into intervals (simulating age uncertainty)
    2. Adds random noise within bins to simulate measurement error
    3. Re-calculates correlation for each simulation
    4. Estimates attenuation bias as the ratio of noisy vs true correlation
    
    Args:
        df: Processed dataset with 'age' and 'burden' columns.
        n_bins: Number of age bins for discretization (default: 10).
        n_simulations: Number of Monte Carlo simulations (default: 1000).
    
    Returns:
        DataFrame with simulation results and attenuation bias estimate.
    """
    if 'age' not in df.columns or 'burden' not in df.columns:
        raise ValueError("Dataset must contain 'age' and 'burden' columns")
    
    logger.info(f"Starting measurement error simulation with {n_simulations} iterations")
    logger.info(f"Using {n_bins} age bins for discretization")
    
    # Calculate true correlation (without measurement error)
    true_corr = calculate_correlation(df, 'burden', 'age')
    true_rho = true_corr['rho']
    
    if np.isnan(true_rho):
        logger.error("Cannot compute true correlation due to missing data")
        return pd.DataFrame()
    
    # Create age bins
    age_min, age_max = df['age'].min(), df['age'].max()
    bin_edges = np.linspace(age_min, age_max, n_bins + 1)
    bin_labels = [f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}" for i in range(n_bins)]
    
    # Assign each sample to a bin
    df['age_bin'] = pd.cut(df['age'], bins=bin_edges, labels=bin_labels)
    
    # Store simulation results
    simulation_results = []
    
    for i in range(n_simulations):
        if (i + 1) % 100 == 0:
            logger.info(f"Simulation {i+1}/{n_simulations}")
        
        # Simulate measurement error by adding random noise within bins
        simulated_age = df['age'].copy()
        
        for bin_label in bin_labels:
            mask = df['age_bin'] == bin_label
            if mask.sum() == 0:
                continue
            
            # Get the bin range
            bin_start = float(bin_label.split('-')[0])
            bin_end = float(bin_label.split('-')[1])
            bin_width = bin_end - bin_start
            
            # Add uniform noise within the bin (simulating age uncertainty)
            noise = np.random.uniform(-bin_width/2, bin_width/2, mask.sum())
            simulated_age[mask] = df.loc[mask, 'age'] + noise
        
        # Ensure simulated age stays within reasonable bounds
        simulated_age = simulated_age.clip(age_min, age_max)
        
        # Create temporary dataframe for correlation
        temp_df = pd.DataFrame({
            'burden': df['burden'],
            'age_simulated': simulated_age
        })
        
        # Calculate correlation with noisy age
        noisy_corr = calculate_correlation(temp_df, 'burden', 'age_simulated')
        noisy_rho = noisy_corr['rho']
        
        # Calculate attenuation ratio
        if np.abs(true_rho) > 0.01:  # Avoid division by near-zero
            attenuation_ratio = noisy_rho / true_rho
        else:
            attenuation_ratio = np.nan
        
        simulation_results.append({
            'simulation_id': i + 1,
            'true_rho': true_rho,
            'noisy_rho': noisy_rho,
            'attenuation_ratio': attenuation_ratio
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(simulation_results)
    
    # Calculate summary statistics
    summary = {
        'true_rho': true_rho,
        'mean_noisy_rho': results_df['noisy_rho'].mean(),
        'std_noisy_rho': results_df['noisy_rho'].std(),
        'mean_attenuation_ratio': results_df['attenuation_ratio'].mean(),
        'std_attenuation_ratio': results_df['attenuation_ratio'].std(),
        'n_simulations': n_simulations,
        'n_bins': n_bins,
        'n_samples': len(df)
    }
    
    logger.info(f"Measurement error simulation complete. "
               f"True rho: {true_rho:.4f}, Mean noisy rho: {summary['mean_noisy_rho']:.4f}, "
               f"Mean attenuation ratio: {summary['mean_attenuation_ratio']:.4f}")
    
    return results_df, summary

def main():
    """Main entry point for sensitivity analysis."""
    try:
        # Load processed dataset
        df = load_processed_dataset()
        
        # Ensure we have the required columns
        required_cols = ['burden', 'age']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Run measurement error simulation (T036)
        logger.info("Starting Task T036: Measurement Error Simulation")
        
        # Run simulation
        simulation_results, summary = simulate_measurement_error_binned_age(
            df, 
            n_bins=10, 
            n_simulations=1000
        )
        
        # Save results
        paths = get_local_paths()
        output_path = paths['sensitivity_measurement_error']
        
        # Ensure directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write simulation results
        simulation_results.to_csv(output_path, index=False)
        logger.info(f"Wrote simulation results to {output_path}")
        
        # Write summary statistics
        summary_path = str(output_path).replace('.csv', '_summary.json')
        import json
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Wrote summary statistics to {summary_path}")
        
        # Also run other sensitivity analyses for completeness
        logger.info("Running additional sensitivity analyses...")
        
        # Threshold sweep
        threshold_results = run_threshold_sweep(df)
        threshold_path = paths['sensitivity_thresholds']
        Path(threshold_path).parent.mkdir(parents=True, exist_ok=True)
        threshold_results.to_csv(threshold_path, index=False)
        logger.info(f"Wrote threshold sweep results to {threshold_path}")
        
        # Subgroup analysis
        subgroup_results = run_subgroup_analysis(df)
        if not subgroup_results.empty:
            subgroup_path = paths['sensitivity_subgroups']
            Path(subgroup_path).parent.mkdir(parents=True, exist_ok=True)
            subgroup_results.to_csv(subgroup_path, index=False)
            logger.info(f"Wrote subgroup analysis results to {subgroup_path}")
        
        # Depth stratified analysis
        depth_results = run_depth_stratified_subsampling(df)
        if not depth_results.empty:
            depth_path = paths['sensitivity_depth']
            Path(depth_path).parent.mkdir(parents=True, exist_ok=True)
            depth_results.to_csv(depth_path, index=False)
            logger.info(f"Wrote depth stratified results to {depth_path}")
        
        logger.info("All sensitivity analyses completed successfully")
        
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()