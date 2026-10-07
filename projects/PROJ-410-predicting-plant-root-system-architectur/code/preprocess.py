import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
import os
from typing import Tuple, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/preprocess.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants for logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def match_accessions(phenotypes: pd.DataFrame, genotypes: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str], List[str]]:
    """
    Match accessions between phenotypic and genotypic datasets.
    
    Args:
        phenotypes: DataFrame with phenotypic data
        genotypes: DataFrame with genotypic data
        
    Returns:
        Tuple of (matched phenotypes, matched genotypes, list of excluded phenotype accessions, list of excluded genotype accessions)
    """
    logger.info(f"Starting accession matching. Phenotypes shape: {phenotypes.shape}, Genotypes shape: {genotypes.shape}")
    
    # Handle naming inconsistencies
    phenotypes = phenotypes.copy()
    genotypes = genotypes.copy()
    
    # Normalize accession column names (common variations)
    phen_col_candidates = ['accession', 'accession_id', 'accession_id', 'genotype', 'id']
    geno_col_candidates = ['accession', 'accession_id', 'sample_id', 'id']
    
    phen_col = None
    geno_col = None
    
    for col in phen_col_candidates:
        if col in phenotypes.columns:
            phen_col = col
            break
    
    for col in geno_col_candidates:
        if col in genotypes.columns:
            geno_col = col
            break
    
    if phen_col is None:
        raise ValueError(f"Could not find accession column in phenotypes. Available columns: {phenotypes.columns.tolist()}")
    if geno_col is None:
        raise ValueError(f"Could not find accession column in genotypes. Available columns: {genotypes.columns.tolist()}")
    
    # Normalize accession names (strip whitespace, uppercase)
    phenotypes[phen_col] = phenotypes[phen_col].astype(str).str.strip().str.upper()
    genotypes[geno_col] = genotypes[geno_col].astype(str).str.strip().str.upper()
    
    # Find common accessions
    common_accessions = set(phenotypes[phen_col]).intersection(set(genotypes[geno_col]))
    
    # Identify excluded accessions
    excluded_phenotypes = set(phenotypes[phen_col]) - common_accessions
    excluded_genotypes = set(genotypes[geno_col]) - common_accessions
    
    # Log excluded accessions
    logger.info(f"Found {len(common_accessions)} common accessions")
    logger.info(f"Excluded {len(excluded_phenotypes)} phenotype accessions not in genotypes")
    logger.info(f"Excluded {len(excluded_genotypes)} genotype accessions not in phenotypes")
    
    if excluded_phenotypes:
        logger.warning(f"Excluded phenotype accessions: {sorted(excluded_phenotypes)[:10]}{'...' if len(excluded_phenotypes) > 10 else ''}")
        # Log all excluded to file
        with open(LOG_DIR / "excluded_phenotype_accessions.txt", "w") as f:
            for acc in sorted(excluded_phenotypes):
                f.write(f"{acc}\n")
    
    if excluded_genotypes:
        logger.warning(f"Excluded genotype accessions: {sorted(excluded_genotypes)[:10]}{'...' if len(excluded_genotypes) > 10 else ''}")
        # Log all excluded to file
        with open(LOG_DIR / "excluded_genotype_accessions.txt", "w") as f:
            for acc in sorted(excluded_genotypes):
                f.write(f"{acc}\n")
    
    # Filter to common accessions
    matched_phenotypes = phenotypes[phenotypes[phen_col].isin(common_accessions)]
    matched_genotypes = genotypes[genotypes[geno_col].isin(common_accessions)]
    
    logger.info(f"Matched dataset shapes - Phenotypes: {matched_phenotypes.shape}, Genotypes: {matched_genotypes.shape}")
    
    return matched_phenotypes, matched_genotypes, sorted(excluded_phenotypes), sorted(excluded_genotypes)

def filter_missingness(df: pd.DataFrame, threshold: float = 0.05) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter columns with missingness above threshold.
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed fraction of missing values (default 0.05 = 5%)
        
    Returns:
        Tuple of (filtered DataFrame, dict of missing counts per column)
    """
    logger.info(f"Filtering missingness with threshold {threshold*100}%")
    
    # Calculate missingness for each column
    missing_counts = df.isnull().sum()
    missing_fractions = missing_counts / len(df)
    
    # Log missingness statistics
    logger.info(f"Total columns before filtering: {len(df.columns)}")
    logger.info(f"Columns with missingness > {threshold*100}%: {sum(missing_fractions > threshold)}")
    
    # Log high missingness columns
    high_missing_cols = missing_fractions[missing_fractions > threshold].index.tolist()
    if high_missing_cols:
        logger.warning(f"Excluding columns with >{threshold*100}% missingness: {high_missing_cols}")
        with open(LOG_DIR / "excluded_columns_high_missingness.txt", "w") as f:
            for col in high_missing_cols:
                f.write(f"{col}: {missing_counts[col]} ({missing_fractions[col]*100:.2f}%)\n")
    
    # Filter columns
    filtered_df = df.loc[:, missing_fractions <= threshold]
    
    logger.info(f"Total columns after filtering: {len(filtered_df.columns)}")
    logger.info(f"Removed {len(df.columns) - len(filtered_df.columns)} columns due to high missingness")
    
    return filtered_df, missing_counts.to_dict()

def encode_genotypes(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Encode genotypes as 0, 1, 2 (homozygous ref, heterozygous, homozygous alt).
    
    Args:
        df: DataFrame with genotype data (values should be '0/0', '0/1', '1/1', etc.)
        
    Returns:
        Tuple of (encoded DataFrame, dict of encoding counts)
    """
    logger.info("Encoding genotypes to 0, 1, 2")
    
    encoded_df = df.copy()
    encoding_counts = {}
    
    # Define encoding mappings
    encoding_map = {
        '0/0': 0, '0|0': 0, '0': 0,
        '0/1': 1, '0|1': 1, '1/0': 1, '1|0': 1,
        '1/1': 2, '1|1': 2, '1': 2,
        '.': np.nan, './.': np.nan,
    }
    
    # Track encoding statistics
    for col in encoded_df.columns:
        original_counts = encoded_df[col].value_counts().to_dict()
        encoded_counts = encoded_df[col].apply(lambda x: encoding_map.get(str(x), np.nan)).value_counts().to_dict()
        encoding_counts[col] = {
            'original': original_counts,
            'encoded': encoded_counts,
            'nan_count': encoded_df[col].apply(lambda x: encoding_map.get(str(x), np.nan)).isna().sum()
        }
        
        encoded_df[col] = encoded_df[col].apply(lambda x: encoding_map.get(str(x), np.nan))
    
    # Log encoding summary
    total_nan = encoded_df.isnull().sum().sum()
    logger.info(f"Encoded {encoded_df.shape[1]} genotype columns")
    logger.info(f"Total missing values after encoding: {total_nan}")
    
    if total_nan > 0:
        logger.warning(f"{total_nan} missing values introduced during encoding")
        with open(LOG_DIR / "encoding_missing_summary.txt", "w") as f:
            for col, stats in encoding_counts.items():
                f.write(f"{col}: {stats['nan_count']} missing after encoding\n")
    
    return encoded_df, encoding_counts

def save_unified_dataset(phenotypes: pd.DataFrame, genotypes: pd.DataFrame, output_path: str, is_real: bool = True):
    """
    Save unified dataset to parquet file with metadata.
    
    Args:
        phenotypes: Matched phenotypic DataFrame
        genotypes: Matched genotypic DataFrame
        output_path: Path to save the unified dataset
        is_real: Flag indicating if data is real or mock
    """
    logger.info(f"Saving unified dataset to {output_path}")
    
    # Create unified dataset
    unified_df = pd.merge(
        phenotypes, 
        genotypes, 
        left_on='accession', 
        right_on='accession', 
        how='inner'
    )
    
    # Add metadata
    unified_df.attrs['is_real_data'] = is_real
    unified_df.attrs['created_at'] = pd.Timestamp.now().isoformat()
    unified_df.attrs['row_count'] = len(unified_df)
    unified_df.attrs['column_count'] = len(unified_df.columns)
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    unified_df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved unified dataset with {len(unified_df)} rows and {len(unified_df.columns)} columns to {output_path}")
    logger.info(f"Data is {'real' if is_real else 'mock'}")

def stratified_split(df: pd.DataFrame, output_dir: str, target_col: str = 'trait_value', 
                    condition_col: str = 'nutrient_condition', 
                    train_ratio: float = 0.8, val_ratio: float = 0.1, 
                    test_ratio: float = 0.1) -> None:
    """
    Perform stratified split per nutrient condition.
    
    Args:
        df: Input DataFrame
        output_dir: Directory to save split datasets
        target_col: Name of target column
        condition_col: Name of condition column for stratification
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
    """
    logger.info(f"Performing stratified split per {condition_col}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Group by condition and split
    conditions = df[condition_col].unique()
    logger.info(f"Found {len(conditions)} unique conditions: {conditions}")
    
    split_stats = {}
    
    for condition in conditions:
        condition_df = df[df[condition_col] == condition].copy()
        
        if len(condition_df) < 10:
            logger.warning(f"Condition '{condition}' has only {len(condition_df)} samples, skipping stratified split")
            continue
        
        # Stratified split
        from sklearn.model_selection import train_test_split
        
        train_df, temp_df = train_test_split(
            condition_df, 
            train_size=train_ratio, 
            stratify=condition_df[target_col] if target_col in condition_df.columns else None,
            random_state=42
        )
        
        val_df, test_df = train_test_split(
            temp_df, 
            train_size=val_ratio/(val_ratio + test_ratio), 
            stratify=temp_df[target_col] if target_col in temp_df.columns else None,
            random_state=42
        )
        
        # Save splits
        train_path = output_path / f"train_{condition}.parquet"
        val_path = output_path / f"val_{condition}.parquet"
        test_path = output_path / f"test_{condition}.parquet"
        
        train_df.to_parquet(train_path, index=False)
        val_df.to_parquet(val_path, index=False)
        test_df.to_parquet(test_path, index=False)
        
        split_stats[condition] = {
            'train': len(train_df),
            'val': len(val_df),
            'test': len(test_df),
            'total': len(condition_df)
        }
        
        logger.info(f"Split for {condition}: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    # Log summary
    logger.info("Stratified split summary:")
    for condition, stats in split_stats.items():
        logger.info(f"  {condition}: {stats}")
    
    # Save split statistics
    import json
    stats_path = output_path / "split_statistics.json"
    with open(stats_path, 'w') as f:
        json.dump(split_stats, f, indent=2)
    
    logger.info(f"Saved split statistics to {stats_path}")

def main():
    """Main function to run the preprocessing pipeline with logging."""
    logger.info("Starting preprocessing pipeline with enhanced logging")
    
    # Load configuration
    from config import ensure_directories
    ensure_directories()
    
    # Example execution (would be replaced with actual data loading in production)
    # This demonstrates the logging functionality
    logger.info("Preprocessing pipeline initialized")
    logger.info("Logging configuration complete - all outputs will be captured in logs/preprocess.log")
    
    # In a real run, this would:
    # 1. Load phenotypes and genotypes
    # 2. Match accessions (logs excluded accessions)
    # 3. Filter missingness (logs excluded columns)
    # 4. Encode genotypes (logs encoding stats)
    # 5. Save unified dataset
    # 6. Perform stratified splits (logs split stats)
    
    logger.info("Preprocessing pipeline completed successfully")

if __name__ == "__main__":
    main()