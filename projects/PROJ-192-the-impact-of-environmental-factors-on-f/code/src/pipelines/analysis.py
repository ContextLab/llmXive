import os
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from scipy.stats import fdr_bh
import skbio
from skbio.stats.distance import permanova
from skbio.stats.ordination import pcoa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants (defaults, can be overridden by config)
DEFAULT_PERMANOVA_PERMUTATIONS = 999
MIN_SAMPLES_FOR_PERMANOVA = 10
MIN_SAMPLES_FOR_EXACT_TEST = 20
EXACT_TEST_PERMUTATIONS = 9999
VIF_THRESHOLD = 5.0

def load_cleaned_data(metadata_path: str, asv_table_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load cleaned metadata and ASV table.
    
    Args:
        metadata_path: Path to cleaned metadata CSV
        asv_table_path: Path to ASV table TSV
        
    Returns:
        Tuple of (metadata_df, asv_df)
    """
    logger.info(f"Loading cleaned metadata from {metadata_path}")
    metadata_df = pd.read_csv(metadata_path)
    
    logger.info(f"Loading ASV table from {asv_table_path}")
    asv_df = pd.read_csv(asv_table_path, sep='\t', index_col=0)
    
    return metadata_df, asv_df

def stratify_by_biome(metadata_df: pd.DataFrame, asv_df: pd.DataFrame) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Split data by biome column.
    
    Args:
        metadata_df: Cleaned metadata dataframe
        asv_df: ASV table dataframe
        
    Returns:
        Dictionary mapping biome names to (metadata_subset, asv_subset) tuples
    """
    if 'biome' not in metadata_df.columns:
        raise ValueError("Metadata must contain 'biome' column for stratification")
    
    biomes = metadata_df['biome'].dropna().unique()
    stratified_data = {}
    
    for biome in biomes:
        biome_mask = metadata_df['biome'] == biome
        biome_metadata = metadata_df[biome_mask].copy()
        biome_asv = asv_df.loc[biome_metadata.index]
        
        # Filter ASV table to only include samples present in metadata
        common_samples = biome_metadata.index.intersection(biome_asv.index)
        biome_asv = biome_asv.loc[common_samples]
        biome_metadata = biome_metadata.loc[common_samples]
        
        stratified_data[biome] = (biome_metadata, biome_asv)
    
    return stratified_data

def perform_power_check(metadata_df: pd.DataFrame, stratum_name: str, log_path: Optional[str] = None) -> bool:
    """
    Check if stratum has sufficient sample size for analysis.
    
    Args:
        metadata_df: Metadata dataframe for the stratum
        stratum_name: Name of the stratum (biome)
        log_path: Optional path to log skipped strata
        
    Returns:
        True if stratum has enough samples, False otherwise
    """
    sample_count = len(metadata_df)
    
    if sample_count < MIN_SAMPLES_FOR_PERMANOVA:
        logger.warning(f"Stratum '{stratum_name}' has {sample_count} samples (< {MIN_SAMPLES_FOR_PERMANOVA}). Skipping PERMANOVA.")
        
        if log_path:
            log_dir = Path(log_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a') as f:
                f.write(f"{stratum_name},{sample_count}\n")
        
        return False
    
    logger.info(f"Stratum '{stratum_name}' has {sample_count} samples. Proceeding with analysis.")
    return True

def calculate_vif(df: pd.DataFrame, exclude_cols: List[str] = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for numeric columns.
    
    Args:
        df: DataFrame with numeric columns
        exclude_cols: Columns to exclude from VIF calculation
        
    Returns:
        DataFrame with VIF values
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    if exclude_cols is None:
        exclude_cols = []
    
    # Select only numeric columns not in exclude_cols
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    vif_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if len(vif_cols) == 0:
        return pd.DataFrame(columns=['variable', 'VIF'])
    
    # Add constant for regression
    X = df[vif_cols].dropna()
    if len(X) < 2:
        return pd.DataFrame(columns=['variable', 'VIF'])
        
    X = X.values
    vif_data = []
    
    for i, col in enumerate(vif_cols):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data.append({'variable': col, 'VIF': vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({'variable': col, 'VIF': np.nan})
    
    return pd.DataFrame(vif_data)

def execute_analysis_for_stratum(
    metadata_df: pd.DataFrame,
    asv_df: pd.DataFrame,
    stratum_name: str,
    output_dir: str,
    env_cols: List[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Run PERMANOVA and variance partitioning for a single stratum.
    
    Args:
        metadata_df: Metadata dataframe for the stratum
        asv_df: ASV table dataframe for the stratum
        stratum_name: Name of the stratum
        output_dir: Directory to save results
        env_cols: List of environmental variable columns to use
        
    Returns:
        Dictionary with results dataframes
    """
    logger.info(f"Running analysis for stratum: {stratum_name}")
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Determine environmental columns if not specified
    if env_cols is None:
        # Exclude common non-environmental columns
        exclude = ['sample_id', 'biome', 'location', 'latitude', 'longitude']
        env_cols = [col for col in metadata_df.columns if col not in exclude and pd.api.types.is_numeric_dtype(metadata_df[col])]
    
    if len(env_cols) == 0:
        logger.warning(f"No environmental columns found for {stratum_name}. Skipping analysis.")
        return {}
    
    # Prepare environmental data
    env_data = metadata_df[env_cols].dropna()
    if len(env_data) < MIN_SAMPLES_FOR_PERMANOVA:
        logger.warning(f"Not enough samples after dropping NaNs for {stratum_name}. Skipping.")
        return {}
    
    # Align ASV table with environmental data
    common_samples = env_data.index.intersection(asv_df.index)
    env_data = env_data.loc[common_samples]
    asv_subset = asv_df.loc[common_samples]
    
    if len(common_samples) < MIN_SAMPLES_FOR_PERMANOVA:
        logger.warning(f"Too few common samples for {stratum_name}. Skipping.")
        return {}
    
    # Calculate Bray-Curtis distance matrix
    logger.info(f"Calculating Bray-Curtis distance for {stratum_name}...")
    try:
        # Convert ASV table to numpy array for skbio
        asv_matrix = asv_subset.values
        
        # Calculate distance matrix
        distance_matrix = skbio.diversity.beta.braycurtis(asv_matrix)
        distance_matrix = skbio.DistanceMatrix(distance_matrix, ids=common_samples)
    except Exception as e:
        logger.error(f"Failed to calculate distance matrix for {stratum_name}: {e}")
        return {}
    
    # Determine permutation count based on sample size
    n_samples = len(common_samples)
    n_permutations = DEFAULT_PERMANOVA_PERMUTATIONS
    if n_samples < MIN_SAMPLES_FOR_EXACT_TEST:
        n_permutations = EXACT_TEST_PERMUTATIONS
        logger.info(f"Using {n_permutations} permutations for exact test ({n_samples} samples)")
    
    # Run PERMANOVA for each environmental variable
    permanova_results = []
    for col in env_cols:
        try:
            formula = f"{col} ~ 1"
            result = permanova(
                distance_matrix,
                metadata=env_data,
                formula=formula,
                permutations=n_permutations
            )
            
            permanova_results.append({
                'stratum': stratum_name,
                'term': col,
                'R2': result['r2'],
                'p-value': result['p_value'],
                'n_permutations': n_permutations
            })
        except Exception as e:
            logger.warning(f"PERMANOVA failed for {col} in {stratum_name}: {e}")
    
    if not permanova_results:
        logger.warning(f"No PERMANOVA results for {stratum_name}")
        return {}
    
    permanova_df = pd.DataFrame(permanova_results)
    
    # Apply FDR correction
    if len(permanova_df) > 0:
        p_values = permanova_df['p-value'].values
        _, p_adjusted, _, _ = fdr_bh(p_values, alpha=0.05, returnsorted=False)
        permanova_df['p-value_adj'] = p_adjusted
    
    # Save PERMANOVA results
    permanova_path = os.path.join(output_dir, f"permanova_{stratum_name}.csv")
    permanova_df.to_csv(permanova_path, index=False)
    logger.info(f"Saved PERMANOVA results to {permanova_path}")
    
    # Variance Partitioning (simplified - unique contribution of each variable)
    varpart_results = []
    for col in env_cols:
        # Calculate R2 as unique contribution (simplified approach)
        r2_val = permanova_df[permanova_df['term'] == col]['R2'].values
        if len(r2_val) > 0:
            varpart_results.append({
                'stratum': stratum_name,
                'predictor': col,
                'unique_variance': r2_val[0],
                'p_value_adj': permanova_df[permanova_df['term'] == col]['p-value_adj'].values[0]
            })
    
    varpart_df = pd.DataFrame(varpart_results)
    
    # Save variance partitioning results
    varpart_path = os.path.join(output_dir, f"varpart_{stratum_name}.csv")
    varpart_df.to_csv(varpart_path, index=False)
    logger.info(f"Saved variance partitioning results to {varpart_path}")
    
    return {
        'permanova': permanova_df,
        'varpart': varpart_df
    }

def run_stratification_pipeline(
    metadata_path: str,
    asv_path: str,
    output_dir: str,
    env_cols: List[str] = None,
    log_skipped_path: Optional[str] = None
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Run the full stratified analysis pipeline.
    
    Args:
        metadata_path: Path to cleaned metadata CSV
        asv_path: Path to ASV table TSV
        output_dir: Directory to save results
        env_cols: List of environmental variable columns
        log_skipped_path: Path to log skipped strata
        
    Returns:
        Dictionary mapping stratum names to their results
    """
    # Load data
    metadata_df, asv_df = load_cleaned_data(metadata_path, asv_path)
    
    # Stratify by biome
    logger.info("Stratifying data by biome...")
    stratified_data = stratify_by_biome(metadata_df, asv_df)
    
    all_results = {}
    
    for stratum_name, (stratum_metadata, stratum_asv) in stratified_data.items():
        logger.info(f"Processing stratum: {stratum_name} ({len(stratum_metadata)} samples)")
        
        # Power check
        if not perform_power_check(stratum_metadata, stratum_name, log_skipped_path):
            continue
        
        # Run analysis
        results = execute_analysis_for_stratum(
            stratum_metadata,
            stratum_asv,
            stratum_name,
            output_dir,
            env_cols
        )
        
        if results:
            all_results[stratum_name] = results
    
    logger.info(f"Stratification pipeline complete. Processed {len(all_results)} strata.")
    return all_results