import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
import os
from typing import Tuple, List, Dict, Optional

# Configure logging at module level to ensure it's active before main runs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/preprocessing.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def match_accessions(genomic_df: pd.DataFrame, phenotypic_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str], List[str]]:
    """
    Match genomic and phenotypic data by accession ID.
    
    Returns:
        Tuple of (matched_genomic, matched_phenotypic, excluded_genomic, excluded_phenotypic)
        Logs excluded accessions and reasons for exclusion.
    """
    logger.info(f"Starting accession matching. Genomic rows: {len(genomic_df)}, Phenotypic rows: {len(phenotypic_df)}")
    
    # Normalize accession columns for comparison
    gen_acc_col = 'accession_id'
    phen_acc_col = 'accession'
    
    if gen_acc_col not in genomic_df.columns:
        raise KeyError(f"Genomic DataFrame missing column '{gen_acc_col}'")
    if phen_acc_col not in phenotypic_df.columns:
        raise KeyError(f"Phenotypic DataFrame missing column '{phen_acc_col}'")
    
    # Normalize to string and strip whitespace to handle naming inconsistencies
    genomic_df = genomic_df.copy()
    phenotypic_df = phenotypic_df.copy()
    
    genomic_df[gen_acc_col] = genomic_df[gen_acc_col].astype(str).str.strip().str.upper()
    phenotypic_df[phen_acc_col] = phenotypic_df[phen_acc_col].astype(str).str.strip().str.upper()
    
    # Find matching accessions
    gen_accessions = set(genomic_df[gen_acc_col])
    phen_accessions = set(phenotypic_df[phen_acc_col])
    
    matched_set = gen_accessions.intersection(phen_accessions)
    excluded_genomic = list(gen_accessions - matched_set)
    excluded_phenotypic = list(phen_accessions - matched_set)
    
    logger.info(f"Found {len(matched_set)} matching accessions.")
    logger.info(f"Excluded from genomic data: {len(excluded_genomic)} accessions")
    logger.info(f"Excluded from phenotypic data: {len(excluded_phenotypic)} accessions")
    
    if len(excluded_genomic) > 0:
        logger.warning(f"Excluded genomic accessions (missing in phenotypic data): {excluded_genomic[:10]}{'...' if len(excluded_genomic) > 10 else ''}")
    if len(excluded_phenotypic) > 0:
        logger.warning(f"Excluded phenotypic accessions (missing in genomic data): {excluded_phenotypic[:10]}{'...' if len(excluded_phenotypic) > 10 else ''}")
    
    matched_genomic = genomic_df[genomic_df[gen_acc_col].isin(matched_set)]
    matched_phenotypic = phenotypic_df[phenotypic_df[phen_acc_col].isin(matched_set)]
    
    return matched_genomic, matched_phenotypic, excluded_genomic, excluded_phenotypic

def filter_missingness(df: pd.DataFrame, threshold: float = 0.05) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter columns with missingness > threshold.
    
    Args:
        df: Input DataFrame
        threshold: Fraction of missing values allowed (default 0.05)
        
    Returns:
        Tuple of (filtered_df, missingness_stats)
    """
    logger.info(f"Applying missingness filter with threshold {threshold*100}%")
    
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df, {}
        
    missing_stats = df.isnull().sum()
    missing_fraction = missing_stats / len(df)
    
    columns_to_drop = missing_fraction[missing_fraction > threshold].index.tolist()
    missingness_stats = {col: int(missing_stats[col]) for col in columns_to_drop}
    
    if columns_to_drop:
        logger.warning(f"Dropping {len(columns_to_drop)} columns due to high missingness (> {threshold*100}%):")
        for col, count in missingness_stats.items():
            logger.warning(f"  - {col}: {count} missing values ({missing_fraction[col]*100:.2f}%)")
        
        filtered_df = df.drop(columns=columns_to_drop)
    else:
        logger.info("No columns dropped due to missingness.")
        filtered_df = df.copy()
        
    return filtered_df, missingness_stats

def encode_genotypes(df: pd.DataFrame, genotype_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Encode genotypes as 0, 1, 2 (homozygous ref, heterozygous, homozygous alt).
    
    Args:
        df: Input DataFrame with genotype data
        genotype_cols: List of columns to encode. If None, auto-detect.
        
    Returns:
        Tuple of (encoded_df, encoding_stats)
    """
    logger.info("Starting genotype encoding (0, 1, 2)...")
    
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df, {}
    
    if genotype_cols is None:
        # Auto-detect genotype columns (assume they start with 'SNP' or 'genotype')
        genotype_cols = [col for col in df.columns if col.startswith(('SNP', 'genotype', 'snp'))]
        logger.info(f"Auto-detected {len(genotype_cols)} genotype columns.")
    
    if not genotype_cols:
        logger.warning("No genotype columns found to encode.")
        return df, {}
        
    encoded_df = df.copy()
    encoding_stats = {}
    
    for col in genotype_cols:
        if col not in encoded_df.columns:
            logger.warning(f"Genotype column '{col}' not found in DataFrame. Skipping.")
            continue
            
        # Map common genotype representations
        # Assume input is string: '0/0', '0/1', '1/1', or similar
        mapping = {
            '0/0': 0, '0|0': 0, '0': 0, 'AA': 0, 'a/a': 0,
            '0/1': 1, '1/0': 1, '0|1': 1, '1|0': 1, 'Aa': 1, 'a/A': 1, 'A/a': 1,
            '1/1': 2, '1|1': 1, '1': 2, 'aa': 2, 'a/a': 2, 'AA': 2 # Note: AA/aa ambiguity resolved by context usually
        }
        
        # Handle potential 'N' or NaN for missing
        # We will keep NaN as NaN, but log count
        original_counts = encoded_df[col].value_counts(dropna=False).to_dict()
        unique_vals = encoded_df[col].unique()
        
        encoded_df[col] = encoded_df[col].map(mapping)
        
        missing_after = encoded_df[col].isnull().sum()
        original_missing = original_counts.get(np.nan, 0) + original_counts.get('N', 0) + original_counts.get('nan', 0)
        
        if missing_after > 0:
            logger.warning(f"Column '{col}': {missing_after} values could not be encoded (kept as NaN). Unique values: {list(unique_vals)[:10]}")
        
        encoding_stats[col] = {
            'original_unique': len(unique_vals),
            'missing_after_encoding': int(missing_after)
        }
        
    logger.info(f"Encoded {len(genotype_cols)} genotype columns.")
    return encoded_df, encoding_stats

def save_unified_dataset(df: pd.DataFrame, output_path: Path, is_real_data: bool = True) -> None:
    """
    Save the unified dataset to parquet format with metadata.
    
    Args:
        df: DataFrame to save
        output_path: Path to save the file
        is_real_data: Flag indicating if data is from real source or mock
    """
    logger.info(f"Saving unified dataset to {output_path} (Real data: {is_real_data})")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata column
    df_with_meta = df.copy()
    df_with_meta['data_source'] = 'real' if is_real_data else 'mock'
    
    df_with_meta.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df_with_meta)} rows to {output_path}")

def stratified_split(df: pd.DataFrame, target_col: str, nutrient_col: str, 
                     train_ratio: float = 0.8, val_ratio: float = 0.1) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split by nutrient condition.
    
    Args:
        df: Input DataFrame
        target_col: Column name for target variable
        nutrient_col: Column name for nutrient condition
        train_ratio: Fraction for training
        val_ratio: Fraction for validation
        
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    logger.info(f"Performing stratified split by '{nutrient_col}' with ratios {train_ratio}/{val_ratio}/{1-train_ratio-val_ratio}")
    
    if nutrient_col not in df.columns:
        raise KeyError(f"Nutrient column '{nutrient_col}' not found in DataFrame")
    
    # Group by nutrient condition
    groups = df.groupby(nutrient_col)
    
    train_dfs = []
    val_dfs = []
    test_dfs = []
    
    for name, group in groups:
        group = group.sample(frac=1, random_state=42) # Shuffle
        
        n = len(group)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        train_dfs.append(group.iloc[:n_train])
        val_dfs.append(group.iloc[n_train:n_train+n_val])
        test_dfs.append(group.iloc[n_train+n_val:])
        
        logger.debug(f"Nutrient '{name}': Total={n}, Train={n_train}, Val={n_val}, Test={n - n_train - n_val}")
    
    train_df = pd.concat(train_dfs, ignore_index=True) if train_dfs else pd.DataFrame(columns=df.columns)
    val_df = pd.concat(val_dfs, ignore_index=True) if val_dfs else pd.DataFrame(columns=df.columns)
    test_df = pd.concat(test_dfs, ignore_index=True) if test_dfs else pd.DataFrame(columns=df.columns)
    
    logger.info(f"Split complete: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    return train_df, val_df, test_df

def main():
    """
    Main execution flow for preprocessing with detailed logging.
    """
    logger.info("="*50)
    logger.info("Starting Preprocessing Pipeline (T024)")
    logger.info("="*50)
    
    # Ensure paths exist
    data_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data (Assuming T010/T011 have created these files)
    # If files don't exist, we log an error but do not crash immediately if mock is expected
    genomic_path = data_dir / "genomic_data.parquet"
    phenotypic_path = data_dir / "phenotypic_data.parquet"
    
    is_real_data = True
    
    if not genomic_path.exists() or not phenotypic_path.exists():
        logger.warning("Raw data files not found. Attempting to load mock data or generating error.")
        # In a real pipeline, this would trigger the mock data generation from T011/T012
        # For this specific task implementation, we assume the data files exist as per T021/T023 context
        # If they truly don't exist, we stop to avoid fabricating data
        if not genomic_path.exists():
            logger.error(f"Missing required file: {genomic_path}")
        if not phenotypic_path.exists():
            logger.error(f"Missing required file: {phenotypic_path}")
        # We proceed assuming the caller has ensured data exists or the pipeline handles the fallback
        # but we log the state clearly.
        return
    
    try:
        genomic_df = pd.read_parquet(genomic_path)
        phenotypic_df = pd.read_parquet(phenotypic_path)
        logger.info(f"Loaded genomic data: {len(genomic_df)} rows")
        logger.info(f"Loaded phenotypic data: {len(phenotypic_df)} rows")
    except Exception as e:
        logger.error(f"Failed to load data files: {e}")
        return

    # 1. Match Accessions
    matched_genomic, matched_phenotypic, excluded_gen, excluded_phen = match_accessions(genomic_df, phenotypic_df)
    
    # 2. Merge
    if matched_genomic.empty or matched_phenotypic.empty:
        logger.error("No matched accessions found. Cannot proceed.")
        return
        
    unified_df = pd.merge(matched_genomic, matched_phenotypic, on='accession_id') # Assuming normalized column name
    logger.info(f"Merged dataset size: {len(unified_df)} rows")
    
    # 3. Filter Missingness
    filtered_df, missing_stats = filter_missingness(unified_df, threshold=0.05)
    
    # 4. Encode Genotypes
    encoded_df, encoding_stats = encode_genotypes(filtered_df)
    
    # 5. Save Unified Dataset
    unified_output = processed_dir / "unified_dataset.parquet"
    save_unified_dataset(encoded_df, unified_output, is_real_data=is_real_data)
    
    # 6. Stratified Split
    # Assuming 'nutrient_condition' and a target like 'root_length' exist
    # If not, we skip split or log error
    nutrient_col = 'nutrient_condition'
    if nutrient_col not in encoded_df.columns:
        logger.warning(f"Nutrient column '{nutrient_col}' not found. Skipping stratified split.")
        train_df, val_df, test_df = encoded_df, pd.DataFrame(), pd.DataFrame()
    else:
        train_df, val_df, test_df = stratified_split(encoded_df, target_col='root_length', nutrient_col=nutrient_col)
        
        # Save splits
        train_path = processed_dir / "train.parquet"
        val_path = processed_dir / "val.parquet"
        test_path = processed_dir / "test.parquet"
        
        save_unified_dataset(train_df, train_path, is_real_data)
        save_unified_dataset(val_df, val_path, is_real_data)
        save_unified_dataset(test_df, test_path, is_real_data)
    
    logger.info("="*50)
    logger.info("Preprocessing Pipeline Completed Successfully")
    logger.info("="*50)

if __name__ == "__main__":
    main()