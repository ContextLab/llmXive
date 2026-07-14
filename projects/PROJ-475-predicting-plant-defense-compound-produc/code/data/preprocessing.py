import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Iterator, Generator
import numpy as np
import pandas as pd
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError
from config import get_config

logger = get_module_logger(__name__)

def stream_vcf_memory_efficient(vcf_path: str) -> Iterator[Dict[str, Any]]:
    """
    Stream VCF file line by line to avoid memory overflow.
    Returns a generator of dictionaries representing each variant.
    """
    import cyvcf2
    vcf = cyvcf2.VCF(vcf_path)
    for variant in vcf:
        yield {
            'chrom': variant.CHROM,
            'pos': variant.POS,
            'id': variant.ID,
            'ref': variant.REF,
            'alt': variant.ALT,
            'qual': variant.QUAL,
            'filter': variant.FILTER,
            'info': variant.INFO,
            'genotypes': variant.genotypes
        }
    vcf.close()

def calculate_missingness_by_environment(df: pd.DataFrame, env_col: str = 'env_id') -> pd.Series:
    """
    Calculate the percentage of missing values for each environment.
    """
    if env_col not in df.columns:
        raise ValueError(f"Environment column '{env_col}' not found in dataframe.")
    
    # Group by environment and calculate missingness for numeric columns
    missingness = df.groupby(env_col).apply(
        lambda x: x.select_dtypes(include=[np.number]).isnull().mean() * 100
    )
    return missingness

def exclude_rows_by_env_missingness(df: pd.DataFrame, threshold: float = 20.0) -> pd.DataFrame:
    """
    Exclude rows where the environment has > threshold% missingness.
    """
    missingness = calculate_missingness_by_environment(df)
    envs_to_exclude = missingness[missingness > threshold].index.tolist()
    
    logger.info(f"Excluding environments with > {threshold}% missingness: {envs_to_exclude}")
    return df[~df['env_id'].isin(envs_to_exclude)]

def flag_missing_env_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a flag column for rows with missing environmental metadata.
    """
    df['env_metadata_missing'] = df.isnull().any(axis=1)
    return df

def preprocess_environmental_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic preprocessing for environmental data: impute missing with mean per env.
    """
    df = exclude_rows_by_env_missingness(df)
    df = flag_missing_env_metadata(df)
    
    # Impute remaining missing values with mean per environment
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != 'env_metadata_missing':
            df[col] = df.groupby('env_id')[col].transform(lambda x: x.fillna(x.mean()))
    
    return df

def calculate_heterozygosity(genotypes: List[List[int]]) -> float:
    """
    Calculate observed heterozygosity from genotype calls.
    Genotypes are typically encoded as [0, 0] (ref/ref), [0, 1] (ref/alt), [1, 1] (alt/alt).
    Heterozygosity = count(het) / total_samples
    """
    if not genotypes:
        return 0.0
    hets = sum(1 for g in genotypes if len(g) >= 2 and g[0] != g[1] and g[0] != -1 and g[1] != -1)
    total = sum(1 for g in genotypes if len(g) >= 2 and g[0] != -1 and g[1] != -1)
    return hets / total if total > 0 else 0.0

def calculate_nucleotide_diversity(genotypes: List[List[int]]) -> float:
    """
    Simplified nucleotide diversity calculation (pi).
    """
    if not genotypes:
        return 0.0
    # Count allele frequencies
    alleles = []
    for g in genotypes:
        if len(g) >= 2 and g[0] != -1 and g[1] != -1:
            alleles.extend([g[0], g[1]])
    
    if len(alleles) < 2:
        return 0.0
    
    unique, counts = np.unique(alleles, return_counts=True)
    freqs = counts / len(alleles)
    # Pi = 1 - sum(p_i^2)
    pi = 1 - np.sum(freqs ** 2)
    return pi

def calculate_genomic_diversity_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate genomic diversity metrics (heterozygosity, nucleotide diversity) per population.
    Assumes df has a 'genotypes' column containing list of genotype calls.
    """
    if 'genotypes' not in df.columns:
        logger.warning("No 'genotypes' column found. Returning dataframe unchanged.")
        return df
    
    df['heterozygosity'] = df['genotypes'].apply(calculate_heterozygosity)
    df['nucleotide_diversity'] = df['genotypes'].apply(calculate_nucleotide_diversity)
    
    # Aggregate by population
    agg_df = df.groupby('population_id').agg({
        'heterozygosity': 'mean',
        'nucleotide_diversity': 'mean'
    }).reset_index()
    
    return agg_df

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    VIF = 1 / (1 - R^2) where R^2 is from regressing one predictor against others.
    """
    from sklearn.linear_model import LinearRegression
    
    vif_data = pd.Series(index=predictors, dtype=float)
    
    for i, var in enumerate(predictors):
        X = df[predictors[:i] + predictors[i+1:]]
        y = df[var]
        
        # Handle constant or single-value columns
        if X.nunique().min() < 2:
            vif_data[var] = np.inf
            continue
        
        model = LinearRegression()
        try:
            model.fit(X, y)
            r2 = model.score(X, y)
            if r2 >= 1.0:
                vif_data[var] = np.inf
            else:
                vif_data[var] = 1 / (1 - r2)
        except Exception as e:
            logger.error(f"Error calculating VIF for {var}: {e}")
            vif_data[var] = np.inf
    
    return vif_data

def detect_model_instability(df: pd.DataFrame, predictors: List[str], vif_threshold: float = 10.0) -> Tuple[List[str], bool]:
    """
    Detect model instability based on VIF > threshold or singular matrix conditions.
    Returns a list of predictors to remove and a boolean indicating instability was found.
    
    Assumption 6: If VIF > 10 or singular matrix detected, remove predictors conditionally.
    """
    logger.info(f"Checking for model instability with VIF threshold {vif_threshold}")
    
    # Filter to numeric predictors only
    numeric_predictors = [p for p in predictors if p in df.columns and np.issubdtype(df[p].dtype, np.number)]
    
    if len(numeric_predictors) < 2:
        logger.warning("Not enough numeric predictors to calculate VIF.")
        return [], False
    
    # Check for constant columns (singular matrix risk)
    constant_cols = [col for col in numeric_predictors if df[col].nunique() < 2]
    if constant_cols:
        logger.warning(f"Constant columns detected (singular matrix risk): {constant_cols}")
        return constant_cols, True
    
    # Calculate VIF
    try:
        vif_scores = calculate_vif(df, numeric_predictors)
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        return [], False
    
    # Identify high VIF predictors
    high_vif_predictors = vif_scores[vif_scores > vif_threshold].index.tolist()
    
    if high_vif_predictors:
        logger.warning(f"High VIF detected (> {vif_threshold}) for: {high_vif_predictors}")
        # Remove the one with the highest VIF first (iterative approach)
        return [high_vif_predictors[0]], True
    
    # Check for singular matrix via rank
    X = df[numeric_predictors].values
    try:
        rank = np.linalg.matrix_rank(X)
        if rank < X.shape[1]:
            logger.warning(f"Singular matrix detected (rank {rank} < {X.shape[1]})")
            # Remove the last column as a heuristic
            return [numeric_predictors[-1]], True
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix detected during rank check")
        return [numeric_predictors[-1]], True
    
    logger.info("No model instability detected.")
    return [], False

def apply_normalization(df: pd.DataFrame, unique_studies_count: int) -> pd.DataFrame:
    """
    Apply normalization (Z-score) conditionally based on study count.
    If unique_studies >= N-1, use global Z-score and exclude 'source_study'.
    Else, use per-study Z-score.
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove 'source_study' if condition met
    if unique_studies_count >= len(df) - 1 and 'source_study' in numeric_cols:
        logger.info("Excluding 'source_study' covariate due to high study diversity.")
        numeric_cols.remove('source_study')
    
    if 'source_study' in df.columns:
        # Per-study Z-score
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df.groupby('source_study')[col].transform(
                    lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
                )
    else:
        # Global Z-score
        for col in numeric_cols:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    df[col] = (df[col] - mean) / std
                else:
                    df[col] = 0
    
    return df

def aggregate_to_population_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate all data to population level (mean for numeric columns).
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude non-numeric grouping columns from aggregation if they exist
    agg_dict = {col: 'mean' for col in numeric_cols if col in df.columns}
    
    if not agg_dict:
        return df
    
    return df.groupby('population_id').agg(agg_dict).reset_index()

def main():
    """
    Main entry point for T026: Detect model instability and remove predictors.
    Loads processed data, detects instability, removes predictors, and saves updated feature set.
    """
    config = get_config()
    input_path = Path(config.get('paths', {}).get('processed_features', 'data/processed/features_vif.csv'))
    output_path = Path(config.get('paths', {}).get('cleaned_features', 'data/processed/features_cleaned.csv'))
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Identify predictor columns (exclude target and ID columns)
    exclude_cols = ['population_id', 'compound_id', 'target', 'env_id']
    predictors = [col for col in df.columns if col not in exclude_cols]
    
    logger.info(f"Predictors to check: {predictors}")
    
    # Detect instability
    to_remove, instability_found = detect_model_instability(df, predictors, vif_threshold=10.0)
    
    if instability_found and to_remove:
        logger.info(f"Removing predictors due to instability: {to_remove}")
        df = df.drop(columns=to_remove)
        logger.info(f"Updated features shape: {df.shape}")
    else:
        logger.info("No predictors removed.")
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned features to {output_path}")
    
    # Check disk space
    try:
        check_disk_space(output_path.stat().st_size * 2)
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()