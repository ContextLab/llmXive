import os
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.pipelines.preprocess import load_harmonized_metadata
from src.utils.logging import log_event
from src.config.constants import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_cleaned_data() -> pd.DataFrame:
    """
    Load the cleaned and imputed metadata from the preprocessing pipeline.
    Returns the DataFrame containing sample data and environmental variables.
    """
    config = get_config()
    # Assuming the path is set in constants or defaults to the project structure
    # Based on T015 output: data/cleaned_metadata.csv
    path = Path(config.get('paths', {}).get('cleaned_metadata', 'data/cleaned_metadata.csv'))
    
    if not path.exists():
        raise FileNotFoundError(f"Cleaned metadata not found at {path}. Run preprocessing first.")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded cleaned metadata with {len(df)} samples from {path}")
    return df

def stratify_by_biome(df: pd.DataFrame, biome_col: str = 'biome') -> Dict[str, pd.DataFrame]:
    """
    Split the dataframe by the specified biome column.
    Returns a dictionary mapping biome name to the subset DataFrame.
    """
    if biome_col not in df.columns:
        raise ValueError(f"Column '{biome_col}' not found in data. Available: {list(df.columns)}")
    
    # Drop rows with missing biome info
    valid_df = df.dropna(subset=[biome_col])
    groups = valid_df.groupby(biome_col)
    
    stratified_data = {}
    for name, group in groups:
        stratified_data[name] = group.copy()
    
    logger.info(f"Stratified data into {len(stratified_data)} biomes: {list(stratified_data.keys())}")
    return stratified_data

def perform_power_check(stratified_data: Dict[str, pd.DataFrame], min_samples: int = 10, log_path: str = "results/skipped_strata.log") -> Tuple[List[str], List[str]]:
    """
    T026: Implement power check.
    If stratum sample count < min_samples, SKIP execution for that stratum.
    Log the skipped biome name to the specified log file.
    Returns a tuple of (valid_strata_names, skipped_strata_names).
    """
    config = get_config()
    # Allow override from config if needed, otherwise default to 10
    # FR-005 requirement: min 10 samples
    effective_min = config.get('constants', {}).get('min_samples', min_samples)
    
    valid_strata = []
    skipped_strata = []
    
    # Ensure results directory exists
    log_file_path = Path(log_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear the log file at the start of this check to ensure freshness for this run
    # Or append? The requirement says "log error to ... and verify log file contains biome name".
    # Usually, for a pipeline run, we might want to append or overwrite. Let's append to keep history.
    # However, to strictly verify the current run's skips, we'll append with a timestamp or just the name.
    # Given the strict requirement "verify log file contains biome name", we will append the name.
    
    with open(log_file_path, 'a') as log_file:
        for biome_name, group_df in stratified_data.items():
            count = len(group_df)
            if count < effective_min:
                skipped_strata.append(biome_name)
                msg = f"SKIPPED: Biome '{biome_name}' has {count} samples (< {effective_min}). Skipping PERMANOVA/varpart."
                logger.warning(msg)
                log_file.write(msg + "\n")
            else:
                valid_strata.append(biome_name)
                logger.info(f"VALID: Biome '{biome_name}' has {count} samples. Proceeding.")
    
    return valid_strata, skipped_strata

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor for features.
    Returns a Series of VIF values.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Ensure we have numeric data
    X = df[features].dropna()
    if X.empty:
        return pd.Series(dtype=float)
    
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    vif_data = pd.Series(
        [variance_inflation_factor(X_const.values, i) for i in range(X_const.shape[1])],
        index=X_const.columns
    )
    return vif_data

def execute_analysis_for_stratum(df: pd.DataFrame, biome_name: str, output_dir: Path) -> Dict:
    """
    Run PERMANOVA and variance partitioning for a single valid stratum.
    This is a placeholder for the actual statistical logic which depends on distance matrices.
    """
    logger.info(f"Executing analysis for biome: {biome_name}")
    # Placeholder for actual analysis logic (T018, T019)
    # In a real implementation, this would call run_permanova_analysis here
    return {"status": "executed", "biome": biome_name}

def apply_fdr_correction(results_df: pd.DataFrame, p_column: str = 'p-value') -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    """
    from scipy.stats import fdr_bh
    
    if p_column not in results_df.columns:
        raise ValueError(f"Column '{p_column}' not found in results.")
    
    pvals = results_df[p_column].values
    if len(pvals) == 0:
        results_df['p-value_adj'] = []
        return results_df
        
    _, pvals_adj, _, _ = fdr_bh(pvals, alpha=0.05, method='indep')
    results_df['p-value_adj'] = pvals_adj
    return results_df

def run_permanova_analysis(df: pd.DataFrame, distance_matrix: pd.DataFrame, formula: str) -> pd.DataFrame:
    """
    Run PERMANOVA analysis.
    """
    # Placeholder for adonis2 implementation
    logger.warning("PERMANOVA analysis placeholder called.")
    return pd.DataFrame()

def run_stratification_pipeline(
    data_path: Optional[str] = None,
    biome_col: str = 'biome',
    min_samples: int = 10,
    output_dir: str = 'results'
) -> Dict:
    """
    Main entry point for the stratification workflow (User Story 2).
    1. Load cleaned data.
    2. Stratify by biome.
    3. Perform power check (T026) - skip strata with < min_samples.
    4. Run analysis for valid strata.
    5. Aggregate results.
    """
    logger.info("Starting Stratification Pipeline (US2)")
    
    # 1. Load Data
    if data_path:
        df = pd.read_csv(data_path)
    else:
        df = load_cleaned_data()
    
    # 2. Stratify
    stratified = stratify_by_biome(df, biome_col=biome_col)
    
    # 3. Power Check (T026)
    valid_strata, skipped_strata = perform_power_check(
        stratified, 
        min_samples=min_samples, 
        log_path=os.path.join(output_dir, 'skipped_strata.log')
    )
    
    logger.info(f"Stratification complete. Valid: {len(valid_strata)}, Skipped: {len(skipped_strata)}")
    
    # 4. Execute Analysis for valid strata
    results = {}
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for biome in valid_strata:
        stratum_df = stratified[biome]
        # In a real flow, we would compute distance matrices here and call run_permanova_analysis
        # execute_analysis_for_stratum(stratum_df, biome, output_path)
        logger.info(f"Skipping full analysis execution for {biome} in this T026 implementation step.")
    
    return {
        "valid_strata": valid_strata,
        "skipped_strata": skipped_strata,
        "results": results
    }
