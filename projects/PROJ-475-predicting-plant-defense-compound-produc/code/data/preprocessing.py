import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from utils.logging import get_module_logger
from utils.io import check_disk_space

# Initialize logger
logger = get_module_logger(__name__)


def calculate_missingness_by_environment(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missingness percentage per environmental column."""
    missing_counts = df.isnull().sum()
    total_rows = len(df)
    if total_rows == 0:
        return {col: 0.0 for col in df.columns}
    return {col: (count / total_rows) * 100 for col, count in missing_counts.items()}


def exclude_rows_by_env_missingness(df: pd.DataFrame, threshold: float = 0.2) -> pd.DataFrame:
    """Exclude rows where environmental missingness exceeds threshold per population."""
    # Assuming 'population_id' is the grouping key for genomic data context
    if 'population_id' not in df.columns:
        logger.warning("No 'population_id' column found; skipping population-level exclusion.")
        return df

    def row_missingness(row):
        # Calculate missingness for environmental columns only (exclude IDs and targets)
        env_cols = [c for c in df.columns if c not in ['population_id', 'env_id', 'compound_id', 'source_study']]
        if not env_cols:
            return 0.0
        missing = row[env_cols].isnull().sum()
        return missing / len(env_cols)

    missingness_series = df.apply(row_missingness, axis=1)
    excluded_mask = missingness_series > threshold
    excluded_count = excluded_mask.sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows due to environmental missingness > {threshold*100}%")
        # Log specific populations excluded for Constitution Principle VI
        excluded_populations = df.loc[excluded_mask, 'population_id'].unique().tolist()
        logger.info(f"Excluded populations: {excluded_populations}")
    
    return df[~excluded_mask]


def flag_missing_env_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Flag rows with missing environmental metadata."""
    env_cols = [c for c in df.columns if c.startswith('env_') or c in ['temp', 'precip', 'humidity']]
    if not env_cols:
        logger.info("No environmental columns detected to flag.")
        return df

    missing_flag = df[env_cols].isnull().any(axis=1)
    df['env_metadata_missing'] = missing_flag
    logger.info(f"Flagged {missing_flag.sum()} rows with missing environmental metadata.")
    return df


def preprocess_environmental_data(df: pd.DataFrame) -> pd.DataFrame:
    """Main entry point for environmental data preprocessing."""
    logger.info("Starting environmental data preprocessing.")
    
    # 1. Calculate missingness
    missingness = calculate_missingness_by_environment(df)
    logger.debug(f"Missingness stats: {missingness}")
    
    # 2. Flag missing metadata
    df = flag_missing_env_metadata(df)
    
    # 3. Exclude high missingness rows
    df = exclude_rows_by_env_missingness(df, threshold=0.2)
    
    logger.info(f"Preprocessing complete. Final shape: {df.shape}")
    return df


def calculate_heterozygosity(genotypes: pd.Series) -> float:
    """Calculate heterozygosity for a population given genotype series (0, 1, 2)."""
    # Heterozygosity is often 1 - sum(p^2) where p is allele frequency
    # For simplicity in this context, assuming genotypes are 0,1,2 (AA, Aa, aa)
    # H = 1 - (p^2 + q^2) where p = freq(A), q = freq(a)
    # p = (2*count(AA) + count(Aa)) / (2*N)
    
    valid = genotypes.dropna()
    if len(valid) == 0:
        return np.nan
    
    n = len(valid)
    count_aa = (valid == 0).sum()
    count_aA = (valid == 1).sum()
    count_aa_2 = (valid == 2).sum()
    
    p = (2 * count_aa + count_aA) / (2 * n)
    q = 1 - p
    
    return 1 - (p**2 + q**2)


def calculate_nucleotide_diversity(genotypes: pd.Series) -> float:
    """Calculate nucleotide diversity (pi) as average pairwise differences."""
    # Simplified: using variance of allele counts scaled
    valid = genotypes.dropna()
    if len(valid) < 2:
        return np.nan
    
    # Allele frequency p
    n = len(valid)
    # Mean genotype value approximates 2p
    mean_g = valid.mean()
    p = mean_g / 2.0
    if p <= 0 or p >= 1:
        return 0.0
        
    # Pi = 2 * p * q * (N / (N-1))
    q = 1 - p
    return 2 * p * q * (n / (n - 1))


def calculate_genomic_diversity_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate heterozygosity and nucleotide diversity per population."""
    if 'population_id' not in df.columns or 'genotype_mean' not in df.columns:
        logger.warning("Missing required columns for genomic diversity calculation.")
        return df

    def apply_metrics(group):
        het = calculate_heterozygosity(group['genotype_mean'])
        pi = calculate_nucleotide_diversity(group['genotype_mean'])
        group['heterozygosity'] = het
        group['nucleotide_diversity'] = pi
        return group

    # If data is already aggregated to population level, apply directly
    if df['population_id'].nunique() == len(df):
        df = df.groupby('population_id', group_keys=False).apply(apply_metrics)
    else:
        # Aggregate first if not already
        logger.info("Aggregating to population level before diversity calculation.")
        agg_df = df.groupby('population_id')['genotype_mean'].mean().reset_index()
        agg_df = agg_df.groupby('population_id', group_keys=False).apply(apply_metrics)
        # Merge back if necessary, but for this function we return the metrics df
        return agg_df

    return df


def aggregate_to_population_level(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate all data to population level (FR-009)."""
    if 'population_id' not in df.columns:
        logger.error("Missing 'population_id' for aggregation.")
        return df

    # Identify numeric columns for averaging
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude IDs from aggregation
    id_cols = ['population_id', 'env_id', 'compound_id', 'source_study']
    agg_cols = [c for c in numeric_cols if c not in id_cols]

    agg_dict = {c: 'mean' for c in agg_cols}
    
    # Handle categorical/nominal columns if needed (e.g., keep first or mode)
    # For now, assume we only need numeric aggregation
    
    result = df.groupby('population_id', as_index=False).agg(agg_dict)
    
    # Preserve study info if needed for later checks (T020/T021)
    # We'll keep a count of unique studies per population
    study_counts = df.groupby('population_id')['source_study'].nunique().reset_index()
    study_counts.columns = ['population_id', 'unique_studies']
    
    result = result.merge(study_counts, on='population_id', how='left')
    
    logger.info(f"Aggregated to {len(result)} populations.")
    return result


def calculate_vif(df: pd.DataFrame, features: Optional[List[str]] = None) -> pd.DataFrame:
    """Calculate Variance Inflation Factor (VIF) for predictors.
    
    Flags predictors with VIF > 5 as per Spec Assumption 6.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    if features is None:
        # Select numeric columns excluding IDs and target
        exclude_cols = ['population_id', 'compound_id', 'target']
        features = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.float64, np.int64]]
    
    if len(features) == 0:
        logger.warning("No features provided or found for VIF calculation.")
        return pd.DataFrame()

    X = df[features].copy()
    X = X.dropna() # VIF requires complete cases
    
    if X.empty:
        logger.warning("No complete cases for VIF calculation.")
        return pd.DataFrame()

    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    vif_data = []
    for col in X.columns:
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, X.columns.get_loc(col))
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
    
    vif_df = pd.DataFrame(vif_data)
    if not vif_df.empty:
        high_vif = vif_df[vif_df['vif'] > 5]
        if not high_vif.empty:
            logger.warning(f"High VIF detected (>5) for features: {high_vif['feature'].tolist()}")
            logger.warning(f"Specific VIF values: {dict(zip(high_vif['feature'], high_vif['vif']))}")
            
    return vif_df


def apply_normalization(df: pd.DataFrame, unique_studies_count: int) -> pd.DataFrame:
    """Aggregate environmental variables per population and normalize.
    
    Implements conditional logic per FR-010, FR-011:
    - If unique_studies >= N-1 (global context), use global Z-score and exclude 'source_study' covariate.
    - Else, use per-study Z-score.
    
    Args:
        df: DataFrame with population-level data. Must contain 'source_study' and numeric env columns.
        unique_studies_count: The value of N (total unique studies in the full dataset) passed from T020.
        
    Returns:
        DataFrame with normalized environmental variables.
    """
    import pandas as pd
    import numpy as np
    from utils.logging import get_module_logger
    
    logger = get_module_logger(__name__)
    
    if df.empty:
        logger.warning("Empty DataFrame passed to apply_normalization.")
        return df

    # Identify environmental columns (heuristic: starts with 'env_' or common names)
    # We assume the caller has already aggregated to population level
    env_cols = [c for c in df.columns if c.startswith('env_') or c in ['temp', 'precip', 'humidity', 'soil_ph']]
    
    if not env_cols:
        logger.warning("No environmental columns found for normalization.")
        return df

    df = df.copy()
    N = unique_studies_count
    
    # Determine normalization strategy
    # We check the number of unique studies in THIS dataframe (which represents the population set)
    # However, the condition "unique_studies >= N-1" usually refers to the global N.
    # The task says: "if unique_studies >= N-1 (determined in T020)". 
    # We assume 'unique_studies' column in df might not represent the global N.
    # The prompt implies we are given N (unique_studies_count) from T020.
    # We need to know the number of unique studies in the current dataset to compare?
    # Re-reading: "if unique_studies >= N-1". 
    # Interpretation: If the number of unique studies in the dataset is high (>= N-1, where N is total possible or total in set?), use global.
    # Actually, T020 calculates VIF and likely determines N (total unique studies).
    # The condition is likely: If the number of unique studies present in the data is >= (Total Unique Studies - 1), then it's "global".
    # Let's assume the passed `unique_studies_count` IS the total N.
    # We need to count unique studies in the current df to check the condition?
    # Or is the condition: If the number of unique studies in the dataset is high enough to cover almost all?
    # Let's assume the logic is: If the dataset contains almost all studies (>= N-1), treat as global.
    
    current_unique_studies = df['source_study'].nunique() if 'source_study' in df.columns else 0
    
    logger.info(f"Normalization check: Current unique studies = {current_unique_studies}, Total N = {N}")
    
    if current_unique_studies >= (N - 1):
        logger.info("Condition met (unique_studies >= N-1): Using Global Z-score.")
        
        # Exclude 'source_study' covariate if present
        if 'source_study' in df.columns:
            logger.info("Excluding 'source_study' covariate as per FR-010.")
            df = df.drop(columns=['source_study'])
        
        # Global Z-score
        for col in env_cols:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    df[f'{col}_z'] = (df[col] - mean) / std
                else:
                    df[f'{col}_z'] = 0.0
                logger.debug(f"Applied global Z-score to {col} (mean={mean:.2f}, std={std:.2f})")
    
    else:
        logger.info("Condition not met: Using Per-Study Z-score.")
        
        # Per-study Z-score
        for col in env_cols:
            if col in df.columns:
                # Group by source_study
                def z_score_group(group):
                    m = group[col].mean()
                    s = group[col].std()
                    if s > 0:
                        return (group[col] - m) / s
                    return 0.0
                
                df[f'{col}_z'] = df.groupby('source_study', group_keys=False).apply(z_score_group)
                logger.debug(f"Applied per-study Z-score to {col}")
    
    # Drop original env columns if we want to keep only normalized ones? 
    # Usually we keep both or drop originals. Let's drop originals to avoid collinearity in next steps.
    # But the task says "aggregate... and normalize".
    # Let's keep the normalized versions with suffix and drop originals if they exist.
    # Actually, to be safe and explicit, let's rename or keep both? 
    # Standard practice: Drop raw, keep normalized for modeling.
    # We will drop the original env_cols now that we have _z versions.
    cols_to_drop = [c for c in env_cols if c in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        logger.info(f"Dropped original environmental columns: {cols_to_drop}")

    return df


def main():
    """Main entry point for preprocessing script."""
    logger.info("Running preprocessing pipeline main.")
    
    # Check disk space
    try:
        check_disk_space(estimated_size=1024 * 1024 * 500) # 500MB estimate
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        sys.exit(1)
    
    # Load data (example path, should be configured)
    data_path = Path("data/processed/filtered.csv")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    # Preprocess environmental data
    df = preprocess_environmental_data(df)
    
    # Aggregate to population level
    df = aggregate_to_population_level(df)
    
    # Calculate genomic diversity
    df = calculate_genomic_diversity_metrics(df)
    
    # Calculate VIF (for T020/T026 context)
    vif_df = calculate_vif(df)
    vif_path = Path("data/processed/features_vif.csv")
    vif_df.to_csv(vif_path, index=False)
    logger.info(f"VIF results saved to {vif_path}")
    
    # Apply Normalization (T021 logic)
    # We need N (total unique studies). 
    # Assuming we can derive this from the original data or it's passed. 
    # For this script, we'll calculate it from the current df before aggregation if possible, 
    # but since we aggregated, we might have lost the raw count. 
    # Let's assume the 'unique_studies' column in the aggregated df holds the count per population? 
    # No, T020 determines N. Let's assume we pass the max unique studies found in the dataset.
    # In a real pipeline, this would be passed from T020. Here we infer it.
    # If 'source_study' exists in the original df before aggregation, we count unique.
    # Since we are in the same script flow, we can't easily access the pre-aggregated df unless we reload.
    # Let's assume the input df to this function (if called externally) has the count.
    # For the script, we'll assume the input file has 'source_study' and count unique.
    # But we just aggregated. Let's reload the raw filtered data to get N.
    
    raw_df = pd.read_csv(data_path)
    N = raw_df['source_study'].nunique() if 'source_study' in raw_df.columns else 1
    
    logger.info(f"Total unique studies (N) detected: {N}")
    
    df = apply_normalization(df, unique_studies_count=N)
    
    # Save output
    output_path = Path("data/processed/normalized_features.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"Normalized features saved to {output_path}")
    
    return df


if __name__ == "__main__":
    main()