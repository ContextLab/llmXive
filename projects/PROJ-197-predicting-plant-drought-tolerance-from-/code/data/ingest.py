import os
import sys
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from config import get_config, validate_config, ensure_directories
from utils.logging import DataPipelineLog
from sklearn.impute import IterativeImputer

def load_try_data() -> pd.DataFrame:
    """Load TRY database CSVs from data/raw/."""
    config = get_config()
    raw_dir = Path(config['paths']['raw_data'])
    processed_dir = Path(config['paths']['processed_data'])
    
    # Ensure directories exist
    ensure_directories()
    
    # Find all CSV files in raw directory
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    
    # Load and concatenate all CSVs
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
        except Exception as e:
            logger = DataPipelineLog()
            logger.record_download_status(str(csv_file), status="failed", error=str(e))
            continue
    
    if not dfs:
        raise ValueError("No valid CSV files could be loaded from raw directory")
    
    try_data = pd.concat(dfs, ignore_index=True)
    return try_data

def load_synthetic_genomics() -> pd.DataFrame:
    """Load synthetic genomic features from data/processed/."""
    config = get_config()
    processed_dir = Path(config['paths']['processed_data'])
    genomics_path = processed_dir / "synthetic_genomics.csv"
    
    if not genomics_path.exists():
        raise FileNotFoundError(f"Synthetic genomics file not found: {genomics_path}")
    
    return pd.read_csv(genomics_path)

def merge_datasets(try_data: pd.DataFrame, genomics_data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Merge TRY traits and genomic data by species ID."""
    logger = DataPipelineLog()
    
    # Identify species in TRY but missing in genomic data
    try_species = set(try_data['species_id'].unique())
    genomic_species = set(genomics_data['species_id'].unique())
    
    missing_species = try_species - genomic_species
    
    if missing_species:
        logger.record_excluded_species(list(missing_species), reason="missing_genomic_data")
        logger.log_imputation_stats(
            stage="merge",
            imputed_count=0,
            dropped_columns=[],
            exclusion_events=len(missing_species)
        )
    
    # Merge datasets
    merged = try_data.merge(
        genomics_data,
        on='species_id',
        how='inner'
    )
    
    return merged, list(missing_species)

def apply_mice_imputation(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], Dict[str, int]]:
    """Apply MICE imputation for missing continuous traits."""
    logger = DataPipelineLog()
    config = get_config()
    
    # Separate numeric and non-numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
    
    if not numeric_cols:
        return df, [], {}
    
    # Identify columns with missing values
    missing_cols = [col for col in numeric_cols if df[col].isna().any()]
    
    if not missing_cols:
        return df, [], {}
    
    # Prepare data for imputation
    imputer = IterativeImputer(
        max_iter=10,
        random_state=config.get('random_state', 42)
    )
    
    # Fit and transform
    imputed_values = imputer.fit_transform(df[missing_cols])
    
    # Create imputed dataframe
    df_imputed = df.copy()
    df_imputed[missing_cols] = imputed_values
    
    # Track imputation counts
    imputation_counts = {}
    for col in missing_cols:
        original_missing = df[col].isna().sum()
        if original_missing > 0:
            imputation_counts[col] = int(original_missing)
    
    # Check for columns that couldn't be imputed (all NaN or constant)
    dropped_columns = []
    for col in missing_cols:
        if df_imputed[col].isna().any():
            logger.log_warning(f"Column {col} still has missing values after imputation, dropping")
            df_imputed = df_imputed.drop(columns=[col])
            dropped_columns.append(col)
    
    # Log imputation statistics
    logger.log_imputation_stats(
        stage="mice",
        imputed_count=sum(imputation_counts.values()),
        dropped_columns=dropped_columns,
        exclusion_events=0
    )
    
    return df_imputed, dropped_columns, imputation_counts

def main():
    """Main entry point for data ingestion pipeline."""
    logger = DataPipelineLog()
    logger.start_run(task="data_ingestion")
    
    try:
        # Load data
        try_data = load_try_data()
        genomics_data = load_synthetic_genomics()
        
        # Merge datasets
        merged_data, missing_species = merge_datasets(try_data, genomics_data)
        
        # Apply MICE imputation
        imputed_data, dropped_cols, imputation_counts = apply_mice_imputation(merged_data)
        
        # Save processed dataset
        config = get_config()
        processed_dir = Path(config['paths']['processed_data'])
        output_path = processed_dir / "merged_dataset.csv"
        
        imputed_data.to_csv(output_path, index=False)
        
        logger.log_imputation_stats(
            stage="final",
            imputed_count=sum(imputation_counts.values()),
            dropped_columns=dropped_cols,
            exclusion_events=len(missing_species)
        )
        
        logger.record_download_status(
            source="merged_dataset",
            status="success",
            row_count=len(imputed_data),
            column_count=len(imputed_data.columns)
        )
        
        print(f"Successfully processed {len(imputed_data)} species with {len(imputed_data.columns)} features")
        print(f"Imputed {sum(imputation_counts.values())} missing values")
        print(f"Dropped {len(dropped_cols)} columns: {dropped_cols}")
        print(f"Excluded {len(missing_species)} species due to missing genomic data")
        
    except Exception as e:
        logger.record_error(str(e))
        raise

if __name__ == "__main__":
    main()
