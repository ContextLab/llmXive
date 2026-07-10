import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError

logger = get_module_logger(__name__)

def calculate_missingness_by_environment(df: pd.DataFrame, env_cols: List[str]) -> Dict[str, float]:
    """Calculate missingness percentage for each environmental column."""
    missingness = {}
    for col in env_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            total_count = len(df)
            missingness[col] = (missing_count / total_count) * 100 if total_count > 0 else 0.0
        else:
            logger.warning(f"Column {col} not found in dataframe")
            missingness[col] = 100.0
    return missingness

def exclude_rows_by_env_missingness(df: pd.DataFrame, env_cols: List[str], threshold: float = 20.0) -> pd.DataFrame:
    """Exclude rows where environmental metadata missingness exceeds threshold per population."""
    if not env_cols:
        return df

    # Calculate missingness per row for env columns
    row_missingness = df[env_cols].isna().mean(axis=1) * 100
    excluded_mask = row_missingness > threshold
    excluded_count = excluded_mask.sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows due to environmental metadata missingness > {threshold}%")
        # Log which populations were excluded for transparency (Constitution Principle VI)
        excluded_indices = df[excluded_mask].index.tolist()
        logger.debug(f"Excluded row indices: {excluded_indices}")
    
    return df[~excluded_mask].reset_index(drop=True)

def flag_missing_env_metadata(df: pd.DataFrame, env_cols: List[str]) -> pd.DataFrame:
    """Flag rows with missing environmental metadata."""
    if not env_cols:
        return df
    
    missing_flags = df[env_cols].isna().any(axis=1)
    df = df.copy()
    df['env_metadata_missing'] = missing_flags
    return df

def preprocess_environmental_data(df: pd.DataFrame, env_cols: List[str], threshold: float = 20.0) -> pd.DataFrame:
    """Full preprocessing pipeline for environmental data."""
    logger.info("Preprocessing environmental data")
    df = exclude_rows_by_env_missingness(df, env_cols, threshold)
    df = flag_missing_env_metadata(df, env_cols)
    return df

def calculate_heterozygosity(genotype_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate observed heterozygosity per population.
    Assumes genotype matrix is encoded as 0, 1, 2 (homozygous ref, heterozygous, homozygous alt).
    """
    # Heterozygosity is the proportion of heterozygous individuals (value == 1)
    heterozygous_counts = np.sum(genotype_matrix == 1, axis=1)
    total_individuals = genotype_matrix.shape[1]
    if total_individuals == 0:
        return np.zeros(genotype_matrix.shape[0])
    return heterozygous_counts / total_individuals

def calculate_nucleotide_diversity(genotype_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate nucleotide diversity (pi) per population.
    Simplified calculation based on allele frequencies.
    """
    # Allele frequency calculation (assuming diploid)
    # Total alleles = 2 * number of individuals
    allele_counts = np.sum(genotype_matrix, axis=1)
    total_alleles = 2 * genotype_matrix.shape[1]
    
    if total_alleles == 0:
        return np.zeros(genotype_matrix.shape[0])
    
    p = allele_counts / total_alleles
    q = 1 - p
    # Nucleotide diversity pi = 2pq (for biallelic sites)
    pi = 2 * p * q
    # Average across loci
    return np.mean(pi)

def calculate_genomic_diversity_metrics(genotype_df: pd.DataFrame, population_col: str = 'population_id') -> pd.DataFrame:
    """
    Calculate genomic diversity metrics (heterozygosity, nucleotide diversity) per population.
    """
    if population_col not in genotype_df.columns:
        raise ValueError(f"Population column '{population_col}' not found in dataframe")
    
    # Assume genotype columns are numeric and not the population column
    genotype_cols = [col for col in genotype_df.columns if col != population_col and genotype_df[col].dtype in ['int64', 'float64', 'int32', 'float32']]
    
    if not genotype_cols:
        logger.warning("No genotype columns found in dataframe")
        return pd.DataFrame()
    
    metrics = []
    for pop_id, group in genotype_df.groupby(population_col):
        genotypes = group[genotype_cols].values.astype(float)
        # Handle missing values by treating them as 0 for calculation (or could exclude)
        genotypes = np.nan_to_num(genotypes, nan=0.0)
        
        het = calculate_heterozygosity(genotypes)
        pi = calculate_nucleotide_diversity(genotypes)
        
        metrics.append({
            population_col: pop_id,
            'heterozygosity': het,
            'nucleotide_diversity': pi
        })
    
    return pd.DataFrame(metrics)

def aggregate_to_population_level(df: pd.DataFrame, population_col: str = 'population_id') -> pd.DataFrame:
    """
    Aggregate data to population level by taking mean of numeric columns.
    """
    if population_col not in df.columns:
        raise ValueError(f"Population column '{population_col}' not found in dataframe")
    
    # Group by population and aggregate numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if population_col in numeric_cols:
        numeric_cols = numeric_cols.drop(population_col)
    
    if len(numeric_cols) == 0:
        return df[[population_col]].drop_duplicates()
    
    aggregated = df.groupby(population_col)[numeric_cols].mean().reset_index()
    return aggregated

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    VIF > 5 indicates potential multicollinearity (per Spec Assumption 6).
    VIF > 10 indicates severe multicollinearity (model instability).
    """
    if not features:
        return pd.Series([], dtype=float)
    
    # Filter to only existing features
    available_features = [f for f in features if f in df.columns]
    if len(available_features) != len(features):
        missing = set(features) - set(available_features)
        logger.warning(f"Features not found in dataframe: {missing}")
    
    if len(available_features) < 2:
        logger.warning("Need at least 2 features to calculate VIF")
        return pd.Series([1.0] * len(features), index=features)
    
    # Prepare data
    X = df[available_features].copy()
    X = X.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(X) < len(available_features) + 1:
        logger.warning("Not enough samples to calculate VIF reliably")
        return pd.Series([np.nan] * len(features), index=features)
    
    vif_values = {}
    for i, feature in enumerate(available_features):
        # Regress feature against all other features
        y = X[feature]
        other_features = [f for f in available_features if f != feature]
        X_other = X[other_features]
        
        # Check for singular matrix
        try:
            # Add intercept
            X_other_with_intercept = np.column_stack([np.ones(len(X_other)), X_other.values])
            # Check condition number
            cond_num = np.linalg.cond(X_other_with_intercept)
            if cond_num > 1e10:
                logger.warning(f"Feature {feature}: Singular matrix detected (condition number: {cond_num:.2e})")
                vif_values[feature] = np.inf
                continue
            
            # OLS regression
            coeffs, residuals, rank, s = np.linalg.lstsq(X_other_with_intercept, y.values, rcond=None)
            
            # Calculate R-squared
            y_pred = X_other_with_intercept @ coeffs
            ss_res = np.sum((y.values - y_pred) ** 2)
            ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # VIF = 1 / (1 - R^2)
            if r_squared >= 1.0:
                vif_values[feature] = np.inf
            else:
                vif_values[feature] = 1 / (1 - r_squared)
        except np.linalg.LinAlgError as e:
            logger.warning(f"Feature {feature}: Linear algebra error during VIF calculation: {e}")
            vif_values[feature] = np.inf
    
    # Create series with original feature order
    result = pd.Series([vif_values.get(f, np.nan) for f in features], index=features)
    return result

def apply_normalization(df: pd.DataFrame, unique_studies_count: int, study_col: str = 'source_study') -> pd.DataFrame:
    """
    Apply normalization based on study diversity.
    If unique_studies >= N-1, use global Z-score and exclude 'source_study' covariate.
    Else, use per-study Z-score.
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove study_col from normalization if present
    if study_col in numeric_cols:
        numeric_cols.remove(study_col)
    
    if not numeric_cols:
        return df
    
    N = len(df)
    threshold = N - 1
    
    if unique_studies_count >= threshold:
        logger.info(f"High study diversity ({unique_studies_count} >= {threshold}): Using global Z-score, excluding '{study_col}' covariate")
        # Global Z-score
        for col in numeric_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()
            if std_val > 0:
                df[col] = (df[col] - mean_val) / std_val
            else:
                df[col] = 0.0
        # Exclude study column if present
        if study_col in df.columns:
            df = df.drop(columns=[study_col])
    else:
        logger.info(f"Low study diversity ({unique_studies_count} < {threshold}): Using per-study Z-score")
        # Per-study Z-score
        if study_col not in df.columns:
            logger.warning(f"Study column '{study_col}' not found for per-study normalization, falling back to global")
            for col in numeric_cols:
                mean_val = df[col].mean()
                std_val = df[col].std()
                if std_val > 0:
                    df[col] = (df[col] - mean_val) / std_val
                else:
                    df[col] = 0.0
        else:
            for study, group in df.groupby(study_col):
                mask = df[study_col] == study
                for col in numeric_cols:
                    mean_val = group[col].mean()
                    std_val = group[col].std()
                    if std_val > 0:
                        df.loc[mask, col] = (group[col] - mean_val) / std_val
                    else:
                        df.loc[mask, col] = 0.0
    
    return df

def detect_model_instability(df: pd.DataFrame, features: List[str], vif_threshold: float = 10.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Detect model instability and conditionally remove predictors.
    
    Instability conditions:
    1. VIF > vif_threshold (default 10.0) - severe multicollinearity
    2. Singular matrix detection during VIF calculation
    
    Args:
        df: DataFrame containing features
        features: List of feature column names to check
        vif_threshold: VIF threshold for instability (default 10.0)
    
    Returns:
        Tuple of (stable_features_df, removed_features_list)
    """
    logger.info(f"Detecting model instability for {len(features)} features with VIF threshold {vif_threshold}")
    
    if not features:
        return df, []
    
    # Calculate VIF for all features
    vif_series = calculate_vif(df, features)
    
    # Identify unstable features
    unstable_features = []
    stable_features = []
    
    for feature, vif_val in vif_series.items():
        if pd.isna(vif_val) or vif_val == np.inf or vif_val > vif_threshold:
            unstable_features.append(feature)
            logger.warning(f"Instability detected for feature '{feature}': VIF = {vif_val}")
        else:
            stable_features.append(feature)
    
    # Log summary
    if unstable_features:
        logger.warning(f"Removing {len(unstable_features)} unstable features: {unstable_features}")
        logger.info(f"Retaining {len(stable_features)} stable features: {stable_features}")
    else:
        logger.info("No model instability detected. All features retained.")
    
    # Return DataFrame with only stable features
    if not stable_features:
        logger.error("All features were unstable! Returning empty feature set.")
        return df[[col for col in df.columns if col not in features]], unstable_features
    
    stable_df = df[stable_features].copy()
    return stable_df, unstable_features

def main():
    """
    Main function to demonstrate model instability detection.
    Reads processed data, detects instability, and outputs stable features.
    """
    logger.info("Starting model instability detection (T026)")
    
    # Define paths
    input_path = Path("data/processed/features_vif.csv")
    output_path = Path("data/processed/features_stable.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Check disk space (estimate 100MB for processing)
    try:
        check_disk_space(100 * 1024 * 1024)  # 100MB
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    
    # Identify feature columns (exclude metadata columns)
    metadata_cols = ['population_id', 'env_id', 'compound_id', 'source_study']
    feature_cols = [col for col in df.columns if col not in metadata_cols and df[col].dtype in ['int64', 'float64', 'int32', 'float32']]
    
    if not feature_cols:
        logger.error("No feature columns found in input data")
        sys.exit(1)
    
    logger.info(f"Checking {len(feature_cols)} feature columns for instability")
    
    # Detect instability and remove unstable features
    stable_df, removed_features = detect_model_instability(df, feature_cols)
    
    # Save results
    logger.info(f"Saving stable features to {output_path}")
    stable_df.to_csv(output_path, index=False)
    
    # Log summary
    logger.info(f"Stability detection complete. Removed {len(removed_features)} features: {removed_features}")
    logger.info(f"Output saved to {output_path}")
    
    return stable_df, removed_features

if __name__ == "__main__":
    main()
