"""
Preprocessing module for plant defense compound prediction pipeline.
Handles data aggregation, feature engineering, VIF analysis, and normalization.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Iterator, Generator
import numpy as np
import pandas as pd
from scipy import stats

from config import get_config
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError

# Initialize logger
logger = get_module_logger(__name__)

def aggregate_to_population_level(
    genomic_df: pd.DataFrame,
    env_df: pd.DataFrame,
    compound_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Aggregate all data to population level (FR-009).
    
    Merges genomic, environmental, and compound data by population_id.
    For genomic data, calculates mean allele frequency per variant per population.
    For environmental data, averages variables per population.
    For compound data, averages concentrations per population.
    
    Args:
        genomic_df: DataFrame with columns including 'population_id', 'variant_id', 'allele_freq'
        env_df: DataFrame with columns including 'population_id', 'env_var_1', ...
        compound_df: DataFrame with columns including 'population_id', 'compound_id', 'concentration'
        
    Returns:
        Aggregated DataFrame at population level with all features.
    """
    logger.info("Aggregating data to population level...")
    
    # Aggregate genomic data: mean allele frequency per population per variant
    # First, pivot genomic data to wide format: rows=populations, cols=variants
    if 'variant_id' in genomic_df.columns and 'allele_freq' in genomic_df.columns:
        genomic_pivot = genomic_df.pivot_table(
            index='population_id', 
            columns='variant_id', 
            values='allele_freq', 
            aggfunc='mean',
            fill_value=0
        )
        genomic_pivot.columns = [f'geno_{col}' for col in genomic_pivot.columns]
        genomic_agg = genomic_pivot.reset_index()
    else:
        # Fallback: just group by population_id if no variant info
        genomic_agg = genomic_df.groupby('population_id').mean().reset_index()
        if 'population_id' not in genomic_agg.columns:
            genomic_agg.reset_index(inplace=True)
    
    # Aggregate environmental data: mean per population
    env_agg = env_df.groupby('population_id').mean().reset_index()
    if 'population_id' not in env_agg.columns:
        env_agg.reset_index(inplace=True)
    
    # Aggregate compound data: mean concentration per population per compound
    # Pivot to wide format: rows=populations, cols=compounds
    if 'compound_id' in compound_df.columns and 'concentration' in compound_df.columns:
        compound_pivot = compound_df.pivot_table(
            index='population_id',
            columns='compound_id',
            values='concentration',
            aggfunc='mean',
            fill_value=0
        )
        compound_pivot.columns = [f'comp_{col}' for col in compound_pivot.columns]
        compound_agg = compound_pivot.reset_index()
    else:
        compound_agg = compound_df.groupby('population_id').mean().reset_index()
        if 'population_id' not in compound_agg.columns:
            compound_agg.reset_index(inplace=True)
    
    # Merge all on population_id
    merged = genomic_agg.merge(env_agg, on='population_id', how='outer')
    merged = merged.merge(compound_agg, on='population_id', how='outer')
    
    # Drop any remaining NaN rows (populations with incomplete data)
    merged = merged.dropna()
    
    logger.info(f"Aggregated data shape: {merged.shape}")
    return merged

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    
    VIF measures multicollinearity. VIF > 5 indicates high collinearity.
    
    Args:
        df: DataFrame with predictor columns.
        feature_cols: List of column names to calculate VIF for.
        
    Returns:
        DataFrame with columns 'feature' and 'vif'.
    """
    logger.info("Calculating VIF for collinearity check...")
    
    if len(feature_cols) == 0:
        logger.warning("No features provided for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif'])
    
    # Ensure numeric data
    X = df[feature_cols].select_dtypes(include=[np.number]).copy()
    
    if X.shape[1] == 0:
        logger.warning("No numeric features found for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif'])
    
    vif_data = []
    
    for i, col in enumerate(X.columns):
        # R^2 from regressing this feature against all others
        y = X[col]
        X_other = X.drop(columns=[col])
        
        if X_other.shape[1] == 0:
            # Only one feature, VIF is 1 by definition
            vif = 1.0
        else:
            try:
                # Fit linear regression: X_col ~ X_others
                model = stats.linregress(X_other.values.flatten(), y.values)
                # For multivariate, use OLS manually
                # Add intercept
                X_other_with_intercept = np.column_stack([np.ones(X_other.shape[0]), X_other.values])
                beta = np.linalg.lstsq(X_other_with_intercept, y.values, rcond=None)[0]
                y_pred = X_other_with_intercept @ beta
                ss_res = np.sum((y.values - y_pred) ** 2)
                ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                vif = 1 / (1 - r_squared) if (1 - r_squared) > 1e-10 else np.inf
            except np.linalg.LinAlgError:
                logger.warning(f"Singular matrix for feature {col}, setting VIF to infinity.")
                vif = np.inf
            except Exception as e:
                logger.warning(f"Error calculating VIF for {col}: {e}. Setting VIF to infinity.")
                vif = np.inf
        
        vif_data.append({'feature': col, 'vif': vif})
    
    vif_df = pd.DataFrame(vif_data)
    vif_df = vif_df.sort_values(by='vif', ascending=False)
    
    return vif_df

def detect_model_instability(vif_df: pd.DataFrame, threshold: float = 5.0) -> List[str]:
    """
    Detect model instability based on VIF values.
    
    Args:
        vif_df: DataFrame with 'feature' and 'vif' columns.
        threshold: VIF threshold above which a feature is considered unstable.
        
    Returns:
        List of feature names with VIF > threshold.
    """
    unstable_features = vif_df[vif_df['vif'] > threshold]['feature'].tolist()
    if unstable_features:
        logger.warning(f"Model instability detected. Features with VIF > {threshold}: {unstable_features}")
    else:
        logger.info(f"No features with VIF > {threshold} detected.")
    return unstable_features

def run_vif_analysis(
    df: pd.DataFrame,
    feature_cols: List[str],
    output_path: str,
    log_threshold: float = 5.0
) -> pd.DataFrame:
    """
    Run full VIF analysis pipeline: calculate VIF, log unstable features, save results.
    
    Args:
        df: Input DataFrame.
        feature_cols: List of feature column names.
        output_path: Path to save the VIF results CSV.
        log_threshold: Threshold for logging unstable features.
        
    Returns:
        DataFrame with VIF results.
    """
    logger.info(f"Running VIF analysis on {len(feature_cols)} features...")
    
    # Calculate VIF
    vif_df = calculate_vif(df, feature_cols)
    
    # Detect and log unstable features
    unstable = detect_model_instability(vif_df, log_threshold)
    for feat in unstable:
        vif_val = vif_df[vif_df['feature'] == feat]['vif'].values[0]
        logger.warning(f"Predictor '{feat}' has VIF = {vif_val:.2f} (> {log_threshold}).")
    
    # Save to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    vif_df.to_csv(output_file, index=False)
    logger.info(f"VIF results saved to {output_path}")
    
    return vif_df

def main(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Main entry point for preprocessing tasks (T020, T021, T026).
    
    Orchestrates:
    1. Load processed data (from validation step).
    2. Aggregate to population level.
    3. Calculate VIF and flag collinear predictors.
    4. Save VIF results to data/processed/features_vif.csv.
    
    Args:
        config: Optional configuration dictionary. If None, loads from default.
        
    Returns:
        0 on success, non-zero on failure.
    """
    try:
        if config is None:
            config = get_config()
        
        logger.info("Starting preprocessing pipeline (T020, T021, T026)...")
        
        # Paths
        data_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
        raw_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
        
        # Load data from previous steps (T013 output)
        # Expected: data/processed/filtered.csv or data/raw/*.json
        filtered_path = data_dir / 'filtered.csv'
        genomic_path = raw_dir / 'genomic_vcf.json'
        env_path = raw_dir / 'env_data.json'
        compound_path = raw_dir / 'compound_data.json'
        
        # Check if we have the raw JSON files (from T010-T012)
        if genomic_path.exists() and env_path.exists() and compound_path.exists():
            logger.info("Loading raw JSON files for aggregation...")
            genomic_df = pd.read_json(genomic_path)
            env_df = pd.read_json(env_path)
            compound_df = pd.read_json(compound_path)
            
            # Aggregate to population level
            aggregated_df = aggregate_to_population_level(genomic_df, env_df, compound_df)
            
            # Save aggregated data for next steps
            aggregated_path = data_dir / 'aggregated.csv'
            aggregated_df.to_csv(aggregated_path, index=False)
            logger.info(f"Aggregated data saved to {aggregated_path}")
            
            # Prepare features for VIF analysis
            # Exclude non-feature columns (e.g., population_id, target variable)
            feature_cols = [col for col in aggregated_df.columns if col != 'population_id']
            
            # If there's a target variable (e.g., 'compound_concentration'), exclude it from predictors
            target_var = config.get('model', {}).get('target_variable', None)
            if target_var and target_var in feature_cols:
                feature_cols.remove(target_var)
            
            # Run VIF analysis
            vif_output_path = data_dir / 'features_vif.csv'
            vif_df = run_vif_analysis(aggregated_df, feature_cols, str(vif_output_path))
            
            # Check disk space
            check_disk_space(vif_output_path.stat().st_size)
            
            # Save filtered data (for T015/T016 consistency)
            # If no filtering was done, just save aggregated as filtered
            filtered_path = data_dir / 'filtered.csv'
            aggregated_df.to_csv(filtered_path, index=False)
            logger.info(f"Filtered data saved to {filtered_path}")
            
            return 0
        
        elif filtered_path.exists():
            # Fallback: load already aggregated/filtered data
            logger.info(f"Loading pre-aggregated data from {filtered_path}")
            df = pd.read_csv(filtered_path)
            
            # Identify feature columns
            feature_cols = [col for col in df.columns if col != 'population_id']
            target_var = config.get('model', {}).get('target_variable', None)
            if target_var and target_var in feature_cols:
                feature_cols.remove(target_var)
            
            # Run VIF analysis
            vif_output_path = data_dir / 'features_vif.csv'
            vif_df = run_vif_analysis(df, feature_cols, str(vif_output_path))
            
            return 0
        
        else:
            logger.error("No input data found. Expected data/raw/*.json or data/processed/filtered.csv")
            return 1
            
    except DiskSpaceError as e:
        logger.error(f"Disk space error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
