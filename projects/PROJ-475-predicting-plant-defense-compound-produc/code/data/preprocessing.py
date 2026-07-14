"""
Preprocessing module for handling missing data, imputation, filtering, and VIF analysis.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from utils.logging import get_module_logger, configure_root_logger
from data.validation import load_json_data, merge_datasets
from config import get_config

logger = get_module_logger(__name__)

# Output paths
PROCESSED_DIR = Path("data/processed")
FILTERED_CSV_PATH = PROCESSED_DIR / "filtered.csv"
VIF_OUTPUT_PATH = PROCESSED_DIR / "features_vif.csv"

def load_processed_data() -> pd.DataFrame:
    """
    Loads the merged dataset from the validation step.
    Expects data/processed/merged.csv to exist (produced by T013).
    Falls back to raw JSONs if merged.csv is missing.
    """
    merged_path = PROCESSED_DIR / "merged.csv"
    if not merged_path.exists():
        logger.warning(f"Merged file {merged_path} not found. Attempting fallback to raw JSONs.")
        genomic = load_json_data("data/raw/genomic_vcf.json")
        env_data = load_json_data("data/raw/env_data.json")
        compound = load_json_data("data/raw/compound_data.json")
        
        if genomic is None or env_data is None or compound is None:
            raise FileNotFoundError("Required raw data files not found for fallback merge.")
        
        df = merge_datasets(genomic, env_data, compound)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(merged_path, index=False)
        logger.info(f"Re-generated and saved merged data at {merged_path}")
    else:
        df = pd.read_csv(merged_path)
    
    return df

def handle_missing_genotypes(df: pd.DataFrame, threshold: float = 0.20) -> pd.DataFrame:
    """
    Handles missing genotype data per population.
    
    Logic:
    1. Identify genotype columns (numeric, not ID columns).
    2. Calculate missingness percentage per row.
    3. If > threshold: Exclude row and log (Constitution Principle VI).
    4. If <= threshold: Impute with column mean.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return df

    id_cols = ['population_id', 'env_id', 'compound_id']
    # Identify numeric columns that are not ID columns
    genotype_cols = [col for col in df.columns 
                     if col not in id_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not genotype_cols:
        logger.warning("No genotype columns found.")
        return df

    # Calculate missingness fraction per row
    missing_counts = df[genotype_cols].isna().sum(axis=1)
    total_cols = len(genotype_cols)
    missingness_frac = missing_counts / total_cols

    # Identify rows to exclude
    exclude_mask = missingness_frac > threshold
    rows_to_exclude = df[exclude_mask]['population_id'].tolist()
    
    if rows_to_exclude:
        logger.warning(f"Excluding {len(rows_to_exclude)} populations due to missingness > {threshold*100}%:")
        for pop_id in rows_to_exclude:
            mask = df['population_id'] == pop_id
            val = missingness_frac[mask].values[0]
            logger.warning(f"  - Excluding population_id: {pop_id} (Missingness: {val:.2%})")
        logger.info("Exclusion decisions logged per Constitution Principle VI.")

    df_filtered = df[~exclude_mask].copy()

    if df_filtered.empty:
        logger.error("All rows excluded. Returning empty DataFrame.")
        return df_filtered

    # Impute remaining missing values
    col_means = df_filtered[genotype_cols].mean()
    df_filtered[genotype_cols] = df_filtered[genotype_cols].fillna(col_means)
    
    logger.info(f"Imputed missing values for {len(df_filtered)} populations.")
    logger.info(f"Final shape after filtering/imputation: {df_filtered.shape}")

    return df_filtered

def aggregate_to_population_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates all data to the population level (FR-009).
    Assumes 'population_id' is the unique identifier.
    Numeric columns are aggregated by mean.
    """
    if df.empty:
        logger.warning("Input DataFrame empty for population aggregation.")
        return df

    # Identify numeric columns for aggregation
    id_cols = ['population_id', 'env_id', 'compound_id']
    numeric_cols = [col for col in df.columns 
                    if pd.api.types.is_numeric_dtype(df[col]) and col not in id_cols]
    
    if not numeric_cols:
        logger.warning("No numeric columns to aggregate.")
        return df

    # Group by population_id and aggregate
    # For ID columns that might be repeated per compound/env, we take the first occurrence
    agg_dict = {col: 'first' for col in id_cols}
    agg_dict.update({col: 'mean' for col in numeric_cols})
    
    # Ensure population_id is in the groupby keys
    group_cols = ['population_id']
    # Add other ID columns to groupby if they exist to avoid 'first' ambiguity
    for col in id_cols:
        if col != 'population_id' and col in df.columns:
            group_cols.append(col)
    
    df_agg = df.groupby(group_cols, as_index=False).agg(agg_dict)
    
    # If we grouped by extra IDs, drop them if they are not needed for population level analysis
    # but usually keeping them is safer for traceability. 
    # The task asks for "population level", so we ensure one row per population_id.
    # If env_id or compound_id varied, 'first' picked one. 
    # Let's ensure uniqueness by population_id only if possible, or keep the multi-index if data is sparse.
    # For FR-009, we assume one row per population_id.
    if len(df_agg) != df_agg['population_id'].nunique():
        logger.warning("Multiple rows per population_id after aggregation. Keeping all.")
    else:
        logger.info(f"Aggregated to {len(df_agg)} unique populations.")
        
    return df_agg

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> pd.DataFrame:
    """
    Calculates Variance Inflation Factor (VIF) for given predictors.
    Explicitly flags predictors with VIF > 5 as per Spec Assumption 6.
    
    Args:
        df: DataFrame containing the data.
        predictor_cols: List of column names to calculate VIF for.
        
    Returns:
        DataFrame with predictor names and their VIF values.
    """
    if df.empty:
        logger.warning("Empty DataFrame for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'VIF'])

    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Filter to only requested columns that exist
    valid_cols = [c for c in predictor_cols if c in df.columns]
    if not valid_cols:
        logger.warning("No valid predictor columns found.")
        return pd.DataFrame(columns=['feature', 'VIF'])

    # Handle constant columns (VIF undefined or infinite)
    # Replace constant columns with a small noise or skip them?
    # statsmodels raises error if column is constant.
    X = df[valid_cols].copy()
    
    # Check for constant columns
    constant_cols = []
    for col in X.columns:
        if X[col].std() == 0:
            constant_cols.append(col)
            logger.warning(f"Column '{col}' is constant. Skipping VIF calculation for it.")
    
    # Remove constant columns for calculation
    X_calc = X.drop(columns=constant_cols)
    
    if X_calc.empty:
        logger.warning("No columns left for VIF calculation after removing constants.")
        return pd.DataFrame(columns=['feature', 'VIF'])

    # Add intercept for statsmodels (though VIF calculation usually handles it or ignores it)
    # VIF formula: 1 / (1 - R^2_j) where R^2_j is from regressing X_j on all other Xs.
    # statsmodels vif function does not require intercept in the dataframe if we pass exog.
    
    vif_data = []
    for i, col in enumerate(X_calc.columns):
        try:
            # Regress this column on all OTHER columns in X_calc
            # We need to construct the design matrix excluding the current column
            other_cols = [c for c in X_calc.columns if c != col]
            if not other_cols:
                # Only one column left, VIF is 1.0 (or undefined depending on definition, usually 1)
                vif_val = 1.0
            else:
                y = X_calc[col]
                X_other = X_calc[other_cols]
                # Add constant for regression
                X_other_with_const = sm.add_constant(X_other)
                model = sm.OLS(y, X_other_with_const).fit()
                vif_val = 1.0 / (1.0 - model.rsquared)
            
            vif_data.append({'feature': col, 'VIF': vif_val})
            
            # Flagging logic (Assumption 6)
            if vif_val > 5.0:
                logger.warning(f"Predictor '{col}' has VIF = {vif_val:.2f} > 5.0 (High Collinearity).")
            elif vif_val > 10.0:
                logger.error(f"Predictor '{col}' has VIF = {vif_val:.2f} > 10.0 (Severe Collinearity).")
                
        except Exception as e:
            logger.error(f"Error calculating VIF for '{col}': {e}")
            vif_data.append({'feature': col, 'VIF': np.nan})

    vif_df = pd.DataFrame(vif_data)
    return vif_df

def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Orchestrates the preprocessing pipeline:
    1. Load merged data.
    2. Handle missing genotypes.
    3. Aggregate to population level.
    4. Calculate VIF and save to features_vif.csv.
    5. Save filtered data to filtered.csv.
    """
    logger.info("Starting preprocessing pipeline (T015, T020).")
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        df = load_processed_data()
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        raise

    # T015: Handle missing genotypes
    df_processed = handle_missing_genotypes(df)

    if df_processed.empty:
        logger.error("Data processing resulted in empty DataFrame. Stopping.")
        df_processed.to_csv(FILTERED_CSV_PATH, index=False)
        return df_processed

    # T020: Aggregate to population level (FR-009)
    df_agg = aggregate_to_population_level(df_processed)
    
    # Identify predictors for VIF (all numeric columns except IDs)
    id_cols = ['population_id', 'env_id', 'compound_id']
    predictor_cols = [col for col in df_agg.columns 
                      if pd.api.types.is_numeric_dtype(df_agg[col]) and col not in id_cols]
    
    if predictor_cols:
        logger.info(f"Calculating VIF for {len(predictor_cols)} predictors.")
        vif_df = calculate_vif(df_agg, predictor_cols)
        vif_df.to_csv(VIF_OUTPUT_PATH, index=False)
        logger.info(f"Saved VIF results to {VIF_OUTPUT_PATH}")
    else:
        logger.warning("No predictors found for VIF calculation.")
        pd.DataFrame(columns=['feature', 'VIF']).to_csv(VIF_OUTPUT_PATH, index=False)

    # Save filtered data (T015 output)
    df_processed.to_csv(FILTERED_CSV_PATH, index=False)
    logger.info(f"Saved filtered data to {FILTERED_CSV_PATH}")

    return df_processed

def main():
    """Entry point for the preprocessing script."""
    configure_root_logger()
    run_preprocessing_pipeline()

if __name__ == "__main__":
    main()
