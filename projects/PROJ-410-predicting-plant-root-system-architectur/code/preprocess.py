import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
import os
import json
from typing import Dict, Any, Optional, Tuple, List

from config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def match_accessions(
    phenotypes_df: pd.DataFrame,
    genotypes_df: pd.DataFrame,
    id_col_pheno: str = 'accession',
    id_col_geno: str = 'accession'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Match accessions between phenotype and genotype datasets.
    Returns filtered DataFrames containing only matched accessions.
    """
    logger.info("Matching accessions between phenotype and genotype data...")
    
    common_accessions = set(phenotypes_df[id_col_pheno].unique()) & set(genotypes_df[id_col_geno].unique())
    logger.info(f"Found {len(common_accessions)} common accessions out of "
               f"{len(phenotypes_df[id_col_pheno].unique())} phenotypes and "
               f"{len(genotypes_df[id_col_geno].unique())} genotypes.")

    matched_pheno = phenotypes_df[phenotypes_df[id_col_pheno].isin(common_accessions)].reset_index(drop=True)
    matched_geno = genotypes_df[genotypes_df[id_col_geno].isin(common_accessions)].reset_index(drop=True)

    return matched_pheno, matched_geno

def filter_missingness(
    df: pd.DataFrame,
    threshold: float = 0.05,
    axis: int = 0
) -> pd.DataFrame:
    """
    Filter rows or columns with missingness > threshold.
    axis=0: filter rows
    axis=1: filter columns (features)
    """
    logger.info(f"Filtering missingness > {threshold*100}% (axis={axis})...")
    
    if axis == 0:
        # Filter rows
        missing_counts = df.isna().sum(axis=1)
        mask = missing_counts / df.shape[1] <= threshold
        filtered_df = df[mask].reset_index(drop=True)
        dropped = df.shape[0] - filtered_df.shape[0]
    else:
        # Filter columns
        missing_counts = df.isna().sum(axis=0)
        mask = missing_counts / df.shape[0] <= threshold
        filtered_df = df.loc[:, mask].reset_index(drop=True)
        dropped = df.shape[1] - filtered_df.shape[1]

    logger.info(f"Dropped {dropped} entries due to missingness.")
    return filtered_df

def encode_genotypes(
    genotype_df: pd.DataFrame,
    id_col: str = 'accession',
    snp_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Encode genotypes as 0, 1, 2 (homozygous ref, heterozygous, homozygous alt).
    Assumes input is in VCF-like format or similar where alleles are encoded.
    If input is already numeric, this acts as a pass-through after validation.
    """
    logger.info("Encoding genotypes to 0, 1, 2 format...")
    
    # Identify SNP columns if not provided
    if snp_cols is None:
        snp_cols = [col for col in genotype_df.columns if col != id_col]
    
    # Create a copy to avoid modifying original
    encoded_df = genotype_df.copy()
    
    # Check if already numeric
    if encoded_df[snp_cols].apply(lambda x: pd.api.types.is_numeric_dtype(x)).all():
        logger.info("Genotypes appear to be already numeric. Validating range...")
        # Ensure values are 0, 1, 2
        valid_mask = encoded_df[snp_cols].isin([0, 1, 2]).all(axis=1)
        if not valid_mask.all():
            logger.warning(f"{(~valid_mask).sum()} rows contain values outside [0, 1, 2]. "
                         "Replacing invalid values with NaN for imputation later.")
            encoded_df.loc[~valid_mask, snp_cols] = np.nan
        return encoded_df

    # If string/alleles, attempt conversion
    # Assuming common formats: "A/A" -> 0, "A/T" -> 1, "T/T" -> 2
    # This is a simplified mapping; real implementation might need allele frequency data
    logger.info("Attempting to parse allele strings...")
    
    for col in snp_cols:
        def parse_allele(val):
            if pd.isna(val):
                return np.nan
            if isinstance(val, (int, float)):
                return val
            s = str(val).upper()
            if '/' in s or '|' in s:
                alleles = s.replace('|', '/').split('/')
                if len(alleles) == 2:
                    if alleles[0] == alleles[1]:
                        return 0 if alleles[0] != 'N' else np.nan
                    else:
                        return 1
            # Fallback: try to interpret as numeric
            try:
                return int(val)
            except ValueError:
                return np.nan
        
        encoded_df[col] = encoded_df[col].apply(parse_allele)

    logger.info("Genotype encoding complete.")
    return encoded_df

def save_unified_dataset(
    pheno_df: pd.DataFrame,
    geno_df: pd.DataFrame,
    id_col: str = 'accession',
    output_path: str = 'data/processed/unified_dataset.parquet',
    is_real_data: bool = True
) -> str:
    """
    Merge phenotype and genotype data, save to parquet, and write metadata.
    
    Args:
        pheno_df: Processed phenotype DataFrame
        geno_df: Processed genotype DataFrame (already encoded)
        id_col: Column name for accession ID
        output_path: Path for the output parquet file
        is_real_data: Boolean flag indicating if data is real (True) or mock (False)
    
    Returns:
        Path to the saved parquet file
    """
    logger.info(f"Merging datasets and saving to {output_path}...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Merge on accession ID
    # Drop duplicate ID columns if they exist in both
    geno_df = geno_df.drop(columns=[id_col], errors='ignore')
    
    unified_df = pheno_df.merge(geno_df, on=id_col, how='inner')
    
    if unified_df.empty:
        raise ValueError("Merged dataset is empty. Check accession matching logic.")
    
    logger.info(f"Unified dataset shape: {unified_df.shape}")
    
    # Save to parquet
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    unified_df.to_parquet(output_path, index=False)
    logger.info(f"Saved unified dataset to {output_path}")
    
    # Save metadata
    metadata = {
        "source": "real" if is_real_data else "mock",
        "row_count": int(unified_df.shape[0]),
        "col_count": int(unified_df.shape[1]),
        "columns": list(unified_df.columns),
        "timestamp": pd.Timestamp.now().isoformat(),
        "missingness_summary": {
            "total_missing": int(unified_df.isna().sum().sum()),
            "missing_pct": float(unified_df.isna().sum().sum() / (unified_df.shape[0] * unified_df.shape[1]))
        }
    }
    
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")
    
    return str(output_path)

def stratified_split(
    df: pd.DataFrame,
    target_col: str,
    id_col: str = 'accession',
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    random_state: int = 42,
    output_prefix: str = 'data/processed'
) -> Dict[str, str]:
    """
    Perform stratified split of the dataset by nutrient condition (or other target).
    Splits are saved as separate parquet files.
    """
    logger.info(f"Performing stratified split by '{target_col}'...")
    
    ensure_directories()
    
    # Group by target and split
    splits = {}
    rng = np.random.default_rng(random_state)
    
    # Get unique conditions
    conditions = df[target_col].unique()
    
    train_parts = []
    val_parts = []
    test_parts = []
    
    for condition in conditions:
        subset = df[df[target_col] == condition]
        
        # Stratified split within condition
        indices = subset.index.tolist()
        rng.shuffle(indices)
        
        n = len(indices)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        train_idx = indices[:n_train]
        val_idx = indices[n_train:n_train + n_val]
        test_idx = indices[n_train + n_val:]
        
        train_parts.append(subset.loc[train_idx])
        val_parts.append(subset.loc[val_idx])
        test_parts.append(subset.loc[test_idx])
    
    train_df = pd.concat(train_parts, ignore_index=True)
    val_df = pd.concat(val_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)
    
    # Shuffle final datasets
    train_df = train_df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    val_df = val_df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    test_df = test_df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    
    # Save splits
    paths = {}
    for name, split_df in [('train', train_df), ('val', val_df), ('test', test_df)]:
        out_path = f"{output_prefix}/{name}.parquet"
        split_df.to_parquet(out_path, index=False)
        paths[name] = out_path
        logger.info(f"Saved {name} split: {out_path} (n={len(split_df)})")
    
    return paths

def main():
    """
    Main entry point for preprocessing pipeline.
    Expects pre-downloaded data in data/raw/ or generated mock data.
    """
    parser = argparse.ArgumentParser(description="Preprocess genomic and phenotypic data")
    parser.add_argument("--phenotype", type=str, default="data/raw/phenotypes.csv", help="Path to phenotype data")
    parser.add_argument("--genotype", type=str, default="data/raw/genotypes.csv", help="Path to genotype data")
    parser.add_argument("--output", type=str, default="data/processed/unified_dataset.parquet", help="Output path")
    parser.add_argument("--is-real", action="store_true", default=True, help="Flag indicating real data source")
    parser.add_argument("--missing-threshold", type=float, default=0.05, help="Missingness threshold for filtering")
    args = parser.parse_args()

    logger.info("Starting preprocessing pipeline...")

    # Load data
    try:
        pheno_df = pd.read_csv(args.phenotype)
        geno_df = pd.read_csv(args.genotype)
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)

    # Match accessions
    pheno_df, geno_df = match_accessions(pheno_df, geno_df)

    # Filter missingness
    pheno_df = filter_missingness(pheno_df, threshold=args.missing_threshold, axis=0)
    geno_df = filter_missingness(geno_df, threshold=args.missing_threshold, axis=1)

    # Encode genotypes
    geno_df = encode_genotypes(geno_df)

    # Save unified dataset
    save_unified_dataset(
        pheno_df,
        geno_df,
        output_path=args.output,
        is_real_data=args.is_real
    )

    # Perform stratified split
    # Assuming 'nutrient_condition' is the column name; adjust if different
    stratified_split(
        pd.read_parquet(args.output),
        target_col='nutrient_condition',
        output_prefix='data/processed'
    )

    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()