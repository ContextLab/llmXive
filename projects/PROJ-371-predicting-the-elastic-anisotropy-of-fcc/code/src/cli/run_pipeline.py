import argparse
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import json

# Import from project structure
from src.utils.config import get_config, get_path, validate_api_keys, set_random_seed, get_seed, ensure_directories
from src.utils.logging import get_logger, log_info, log_error, log_warning, log_success
from src.data.ingest import ingest_elastic_data
from src.data.clean import clean_elastic_data
from src.data.features import compute_compositional_features

def validate_output_descriptors(output_path: Path) -> bool:
    """
    Validates that the output CSV has no null values in descriptor columns.
    
    Args:
        output_path: Path to the output CSV file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    logger = get_logger("pipeline")
    try:
        df = pd.read_csv(output_path)
        required_cols = ["C11", "C12", "C44", "A1"]
        
        for col in required_cols:
            if col not in df.columns:
                log_error(logger, f"Missing required column: {col}")
                return False
            if df[col].isnull().any():
                log_error(logger, f"Null values found in column: {col}")
                return False
        
        log_success(logger, f"Output validation passed for {output_path}")
        return True
    except Exception as e:
        log_error(logger, f"Validation failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run the Elastic Anisotropy Pipeline")
    parser.add_argument("--manifest", type=str, help="Path to the JSON manifest of material IDs")
    parser.add_argument("--sample-size", type=int, default=None, help="Limit processing to N entries for CI testing")
    parser.add_argument("--validate", action="store_true", help="Run validation on output after pipeline completion")
    
    args = parser.parse_args()
    
    # Setup
    set_random_seed(42)
    ensure_directories()
    logger = get_logger("pipeline")
    log_info(logger, "Starting Elastic Anisotropy Pipeline")
    
    # Validate API Keys
    if not validate_api_keys():
        log_error(logger, "API keys missing. Exiting.")
        sys.exit(1)
    
    # 1. Ingest
    log_info(logger, "Step 1: Ingesting data...")
    ingest_path = get_path("data_raw")
    output_raw = ingest_path / "elastic_raw.csv"
    
    # Determine manifest to use
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        # Default manifest if not provided
        manifest_path = ingest_path / "manifest.json"
        
    if not manifest_path.exists():
        log_warning(logger, f"Manifest {manifest_path} not found. Attempting to fetch all or using default.")
        # If no manifest, we might fetch a default set or fail. 
        # For this implementation, we assume the script handles missing manifest by fetching a small default set
        # or raising an error. Let's assume it fetches a default small set for demo if missing.
        log_warning(logger, "No manifest provided. Fetching default sample.")
        
    df_raw = ingest_elastic_data(manifest_path=manifest_path)
    
    if df_raw is None or df_raw.empty:
        log_error(logger, "Ingestion resulted in empty dataset.")
        sys.exit(1)
        
    # Apply sample size limit if requested (T017 constraint check)
    if args.sample_size:
        log_info(logger, f"Limiting dataset to {args.sample_size} entries for CI constraint test.")
        df_raw = df_raw.head(args.sample_size)
        
    df_raw.to_csv(output_raw, index=False)
    log_success(logger, f"Ingestion complete. Saved to {output_raw}")
    
    # 2. Clean
    log_info(logger, "Step 2: Cleaning data...")
    output_clean = get_path("data_processed") / "elastic_cleaned.csv"
    df_clean = clean_elastic_data(output_raw, output_clean)
    
    if df_clean is None or df_clean.empty:
        log_error(logger, "Cleaning resulted in empty dataset.")
        sys.exit(1)
    log_success(logger, f"Cleaning complete. Saved to {output_clean}")
    
    # 3. Features
    log_info(logger, "Step 3: Computing features...")
    output_features = get_path("data_processed") / "elastic_anisotropy.csv"
    df_final = compute_compositional_features(df_clean, output_features)
    
    if df_final is None or df_final.empty:
        log_error(logger, "Feature engineering resulted in empty dataset.")
        sys.exit(1)
    log_success(logger, f"Feature engineering complete. Saved to {output_features}")
    
    # 4. Validation
    if args.validate:
        log_info(logger, "Running output validation...")
        if not validate_output_descriptors(output_features):
            log_error(logger, "Output validation failed.")
            sys.exit(1)
    
    log_success(logger, "Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()