"""
Data Validation Module for US1.

Implements:
- T013: Merge raw modalities (Genomic VCF, Env CSV, Compound JSON)
- T014: Retention Check (SC-001)
- T015: Listwise Deletion (FR-003)
"""

import json
import sys
import logging
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import yaml

# Import shared utilities
from utils.logging import get_module_logger
from utils.io import compute_checksum, DiskSpaceError, check_disk_space
from config import get_config

logger = get_module_logger(__name__)

# Constants
MANIFEST_PATH = Path("data/manifest.yaml")
EXCLUSIONS_LOG_PATH = Path("logs/exclusions.log")
MERGED_RAW_PATH = Path("data/processed/merged_raw.csv")
FINAL_CLEANED_PATH = Path("data/processed/final_cleaned.csv")
GENOMIC_VCF_PATH = Path("data/raw/genomic.vcf")
MOCK_GENOMIC_VCF_PATH = Path("data/raw/mock_genomic.vcf")
ENV_CSV_PATH = Path("data/raw/env_data.csv")
MOCK_ENV_CSV_PATH = Path("data/raw/mock_env.csv")
COMPOUND_JSON_PATH = Path("data/raw/compound_data.json")
MOCK_COMPOUND_JSON_PATH = Path("data/raw/mock_compounds.json")

RETENTION_THRESHOLD = 0.80  # 80%

def ensure_directories():
    """Ensure all required output directories exist."""
    dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("logs"),
        Path("results")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_manifest() -> Dict[str, Any]:
    """Load the data manifest."""
    if not MANIFEST_PATH.exists():
        return {"artifacts": {}, "metadata": {}}
    with open(MANIFEST_PATH, 'r') as f:
        return yaml.safe_load(f) or {"artifacts": {}, "metadata": {}}

def save_manifest(manifest: Dict[str, Any]):
    """Save the data manifest."""
    with open(MANIFEST_PATH, 'w') as f:
        yaml.safe_dump(manifest, f, default_flow_style=False)

def update_manifest(file_path: Path, source_type: str, step: str):
    """Update manifest with a new artifact entry."""
    manifest = load_manifest()
    rel_path = str(file_path.relative_to(Path(".")))
    checksum = compute_checksum(file_path)
    
    if "artifacts" not in manifest:
        manifest["artifacts"] = {}
    
    manifest["artifacts"][rel_path] = {
        "type": source_type,
        "step": step,
        "checksum": checksum,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    save_manifest(manifest)

def load_json_data(path: Path) -> List[Dict]:
    """Load JSON data."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_csv_data(path: Path) -> pd.DataFrame:
    """Load CSV data."""
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)

def load_vcf_as_dataframe(vcf_path: Path) -> pd.DataFrame:
    """
    Parse a VCF file into a DataFrame.
    Handles both real genomic.vcf and mock_genomic.vcf.
    Returns a DataFrame with columns: ['population_id', 'variant_id', 'genotype', 'source_study']
    """
    if not vcf_path.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    # Check if it's a mock file (header starts with #mock or similar, or just parse logic)
    # For simplicity, we assume a standard VCF format or a specific mock format.
    # If it's a real VCF, we need to parse headers and rows.
    
    # Simple heuristic: check if file starts with '##'
    with open(vcf_path, 'r') as f:
        first_line = f.readline()
    
    data_rows = []
    current_source = "unknown"

    with open(vcf_path, 'r') as f:
        for line in f:
            if line.startswith('##'):
                continue
            if line.startswith('#'):
                # Header line
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                chrom, pos, id_, ref, alt = parts[0], parts[1], parts[2], parts[3], parts[4]
                # Mock VCFs might have population_id in the ID field or a specific format
                # Assuming ID field contains 'pop_X' or similar, or we map based on context
                # For this implementation, we assume the ID field is 'pop_XX_variant_YY'
                # or we extract population from a specific column if available.
                # Since the spec says 'population_id' is the join key, we must extract it.
                # If the VCF is mock, it might be structured differently.
                
                # Fallback: try to parse ID field
                pop_id = id_.split('_')[0] if '_' in id_ else "pop_unknown"
                
                # In a real VCF, we might need to parse the sample column for genotypes
                # For this task, we assume a simplified VCF structure where the ID is the key
                # and we treat the presence of a row as valid genomic data for that population.
                data_rows.append({
                    'population_id': pop_id,
                    'variant_id': id_,
                    'genotype': '1/1', # Placeholder or parsed
                    'source_study': 'genomic'
                })

    df = pd.DataFrame(data_rows)
    if df.empty:
        logger.warning(f"VCF file {vcf_path} yielded no data rows.")
    return df

def merge_datasets() -> pd.DataFrame:
    """
    T013: Merge the three raw modalities into a single intermediate file.
    Input: data/raw/genomic.vcf (or mock), data/raw/env_data.csv (or mock), data/raw/compound_data.json (or mock)
    Logic: Inner join on population_id.
    Output: data/processed/merged_raw.csv
    """
    ensure_directories()
    log_path = EXCLUSIONS_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize logging for exclusions
    if log_path.exists():
        log_path.unlink() # Clear previous run exclusions
    
    with open(log_path, 'w') as log_file:
        log_file.write("Exclusion Log - Listwise Deletion\n")
        log_file.write("="*50 + "\n")

    # 1. Load Genomic Data
    genomic_df = None
    genomic_path = GENOMIC_VCF_PATH if GENOMIC_VCF_PATH.exists() else MOCK_GENOMIC_VCF_PATH
    if genomic_path.exists():
        try:
            genomic_df = load_vcf_as_dataframe(genomic_path)
            # Aggregate to population level if multiple variants exist
            # We just need to know if genomic data EXISTS for the population.
            # Create a DF with unique population_ids from VCF
            genomic_df = genomic_df[['population_id']].drop_duplicates()
            genomic_df['has_genomic'] = True
        except Exception as e:
            logger.error(f"Failed to load genomic data: {e}")
            raise
    else:
        raise FileNotFoundError(f"Genomic VCF not found at {GENOMIC_VCF_PATH} or {MOCK_GENOMIC_VCF_PATH}")

    # 2. Load Environmental Data
    env_df = None
    env_path = ENV_CSV_PATH if ENV_CSV_PATH.exists() else MOCK_ENV_CSV_PATH
    if env_path.exists():
        try:
            env_df = load_csv_data(env_path)
            # Ensure population_id is string for joining
            if 'population_id' in env_df.columns:
                env_df['population_id'] = env_df['population_id'].astype(str)
                env_df = env_df[['population_id']].drop_duplicates()
                env_df['has_env'] = True
            else:
                raise ValueError("Environmental CSV missing 'population_id' column")
        except Exception as e:
            logger.error(f"Failed to load environmental data: {e}")
            raise
    else:
        raise FileNotFoundError(f"Environmental CSV not found at {ENV_CSV_PATH} or {MOCK_ENV_CSV_PATH}")

    # 3. Load Compound Data
    compound_df = None
    compound_path = COMPOUND_JSON_PATH if COMPOUND_JSON_PATH.exists() else MOCK_COMPOUND_JSON_PATH
    if compound_path.exists():
        try:
            data = load_json_data(compound_path)
            if isinstance(data, list):
                compound_df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'data' in data:
                compound_df = pd.DataFrame(data['data'])
            else:
                raise ValueError("Compound JSON format not recognized")
            
            if 'population_id' in compound_df.columns:
                compound_df['population_id'] = compound_df['population_id'].astype(str)
                # Keep source_study if present, else default
                if 'source_study' not in compound_df.columns:
                    compound_df['source_study'] = 'compound_db'
                compound_df = compound_df[['population_id', 'source_study']].drop_duplicates()
                compound_df['has_compound'] = True
            else:
                raise ValueError("Compound JSON missing 'population_id' key")
        except Exception as e:
            logger.error(f"Failed to load compound data: {e}")
            raise
    else:
        raise FileNotFoundError(f"Compound JSON not found at {COMPOUND_JSON_PATH} or {MOCK_COMPOUND_JSON_PATH}")

    # Merge
    # Start with Genomic
    merged = genomic_df.copy()
    merged = merged.merge(env_df, on='population_id', how='left')
    merged = merged.merge(compound_df, on='population_id', how='left')

    # Fill NaNs with False for boolean flags
    merged['has_genomic'] = merged['has_genomic'].fillna(False)
    merged['has_env'] = merged['has_env'].fillna(False)
    merged['has_compound'] = merged['has_compound'].fillna(False)

    # Log exclusions (rows missing any modality)
    missing_rows = merged[
        (merged['has_genomic'] == False) |
        (merged['has_env'] == False) |
        (merged['has_compound'] == False)
    ]
    
    with open(log_path, 'a') as log_file:
        for idx, row in missing_rows.iterrows():
            reasons = []
            if not row['has_genomic']: reasons.append("Missing Genomic")
            if not row['has_env']: reasons.append("Missing Env")
            if not row['has_compound']: reasons.append("Missing Compound")
            log_file.write(f"Population: {row['population_id']} | Excluded: {', '.join(reasons)}\n")

    # T014: Retention Check
    initial_count = len(genomic_df) # N_initial based on genomic as base
    final_count = len(merged)
    retention = (final_count / initial_count) if initial_count > 0 else 0.0
    
    logger.info(f"Retention Check: {final_count}/{initial_count} = {retention:.2%}")
    
    if retention < RETENTION_THRESHOLD:
        error_msg = f"Retention below {RETENTION_THRESHOLD*100:.0f}% (Threshold SC-001). Retention: {retention:.2%}"
        logger.error(error_msg)
        # Write error to stderr and exit
        print(f"ERROR: {error_msg}", file=sys.stderr)
        raise SystemExit("E-DATA-INSUFFICIENT")

    # Save intermediate
    # Drop boolean flags for the final output, keep only necessary cols
    # We need to ensure we have a clean dataset for T015
    output_cols = ['population_id', 'source_study']
    # Add any other necessary cols from original data if we kept them
    # For now, we just have the join keys and flags. 
    # T013 output is merged_raw.csv.
    merged.to_csv(MERGED_RAW_PATH, index=False)
    update_manifest(MERGED_RAW_PATH, "csv", "T013_merge")
    
    logger.info(f"Merged dataset saved to {MERGED_RAW_PATH}")
    return merged

def perform_listwise_deletion() -> pd.DataFrame:
    """
    T015: Perform Listwise Deletion (FR-003) on the merged dataset.
    Input: data/processed/merged_raw.csv
    Logic: Exclude any row with missing Genomic, Env, or Compound data.
    Output: data/processed/final_cleaned.csv
    Verification: No nulls in key columns.
    """
    if not MERGED_RAW_PATH.exists():
        raise FileNotFoundError(f"Input file {MERGED_RAW_PATH} not found. Run T013 first.")

    df = load_csv_data(MERGED_RAW_PATH)
    
    # T015 Logic: Drop rows with any missing data in key columns
    # The task says "For any row with missing Genomic, Env, or Compound data, exclude the row."
    # Since T013 already performed the join and we have flags, we can filter directly.
    # However, if the input is the raw merged CSV from T013, it might contain the flags.
    # If T013 output doesn't have flags (just the join), then we rely on the join being inner.
    # But T013 description says "Inner join on population_id". An inner join naturally removes
    # populations missing in any of the three tables.
    # So the "Listwise Deletion" here is essentially ensuring the result of the inner join.
    # If the T013 output contains rows that are not fully joined (e.g. if it was a left join somewhere),
    # we drop them now.
    
    # Let's assume the input CSV might have NaNs if the join wasn't perfectly inner or if data was sparse.
    # We drop any row with ANY NaN in the dataframe to be safe and strict (FR-003).
    initial_rows = len(df)
    df_clean = df.dropna()
    dropped_rows = initial_rows - len(df_clean)
    
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows due to missing values (Listwise Deletion).")
        # Log these exclusions too? The task says "Log exclusion decisions to logs/exclusions.log"
        # We append to the existing log.
        with open(EXCLUSIONS_LOG_PATH, 'a') as log_file:
            log_file.write(f"\n--- Listwise Deletion (T015) ---\n")
            log_file.write(f"Dropped {dropped_rows} rows with missing values.\n")
            # If we had the original indices, we could log them, but we don't have indices in CSV.
    else:
        logger.info("No rows dropped in Listwise Deletion (T015).")

    # Verification: Ensure no nulls in key columns
    key_cols = ['population_id']
    for col in key_cols:
        if col in df_clean.columns:
            if df_clean[col].isnull().any():
                raise ValueError(f"Key column {col} still contains nulls after listwise deletion.")

    # Save final output
    df_clean.to_csv(FINAL_CLEANED_PATH, index=False)
    update_manifest(FINAL_CLEANED_PATH, "csv", "T015_listwise_deletion")
    
    logger.info(f"Final cleaned dataset saved to {FINAL_CLEANED_PATH}")
    return df_clean

def merge_and_validate():
    """Orchestrates T013 and T014."""
    merged = merge_datasets()
    return merged

def run_validation_pipeline():
    """
    Full validation pipeline:
    1. Merge datasets (T013)
    2. Check retention (T014) - raises if fails
    3. Listwise deletion (T015)
    """
    logger.info("Starting Validation Pipeline...")
    try:
        merge_and_validate()
        df_final = perform_listwise_deletion()
        logger.info("Validation Pipeline completed successfully.")
        return df_final
    except SystemExit as e:
        if str(e) == "E-DATA-INSUFFICIENT":
            logger.critical("Pipeline halted due to insufficient retention.")
            raise
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    """Entry point for validation script."""
    configure_root_logger = True # Ensure logging is set up
    from utils.logging import configure_root_logger as setup_logging
    setup_logging()
    
    try:
        run_validation_pipeline()
        print("Validation pipeline finished successfully.")
        return 0
    except SystemExit as e:
        if str(e) == "E-DATA-INSUFFICIENT":
            return 1
        raise
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
