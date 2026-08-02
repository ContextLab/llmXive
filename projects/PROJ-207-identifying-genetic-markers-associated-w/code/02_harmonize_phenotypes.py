"""
Harmonize phenotype data from raw sources into a clean, standardized format.

This script processes raw phenotype data (from synthetic generation or real data fetch),
validates it against the schema, handles missing values, encodes categorical variables,
and outputs a clean phenotype file compatible with PLINK and downstream analysis.

Input: 
  - data/raw/ncbi_metadata.json (if real data) OR
  - data/interim/synthetic_colonies.json (if synthetic data)
Output:
  - data/processed/phenotypes_cleaned.fam
  - data/processed/phenotypes_cleaned.pheno
  - data/processed/harmonization_log.txt
"""
import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_raw_phenotypes(input_source: str) -> pd.DataFrame:
    """Load raw phenotype data from JSON source."""
    source_path = Path(input_source)
    if not source_path.exists():
        raise FileNotFoundError(f"Input source not found: {source_path}")
    
    with open(source_path, 'r') as f:
        data = json.load(f)
    
    # Handle different data structures based on source
    if 'colonies' in data:
        # Synthetic data format from T009
        records = data['colonies']
    elif 'samples' in data:
        # Real data format from T012a
        records = data['samples']
    else:
        # Assume top-level list
        records = data if isinstance(data, list) else [data]
    
    df = pd.DataFrame(records)
    return df

def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Validate schema and clean phenotype data."""
    required_columns = ['colony_id', 'ccd_status', 'geographic_region', 'sampling_year', 'varroa_mite_count']
    
    # Check for required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Standardize column names
    df = df.rename(columns=lambda x: x.strip().lower().replace(' ', '_'))
    
    # Ensure colony_id is string
    df['colony_id'] = df['colony_id'].astype(str)
    
    # Handle CCD status (binary: 0=healthy, 1=CCD)
    if 'ccd_status' in df.columns:
        df['ccd_status'] = pd.to_numeric(df['ccd_status'], errors='coerce')
        df['ccd_status'] = df['ccd_status'].fillna(0).astype(int)
    
    # Handle geographic region (categorical)
    if 'geographic_region' in df.columns:
        df['geographic_region'] = df['geographic_region'].astype(str).fillna('UNKNOWN')
        df['geographic_region'] = df['geographic_region'].str.upper()
    
    # Handle sampling year
    if 'sampling_year' in df.columns:
        df['sampling_year'] = pd.to_numeric(df['sampling_year'], errors='coerce')
        current_year = datetime.now().year
        df = df[(df['sampling_year'] >= 2000) & (df['sampling_year'] <= current_year)]
    
    # Handle Varroa mite count
    if 'varroa_mite_count' in df.columns:
        df['varroa_mite_count'] = pd.to_numeric(df['varroa_mite_count'], errors='coerce')
        df['varroa_mite_count'] = df['varroa_mite_count'].fillna(0).astype(int)
    
    # Remove duplicate colony IDs
    df = df.drop_duplicates(subset=['colony_id'], keep='first')
    
    # Sort by colony_id for consistency
    df = df.sort_values('colony_id').reset_index(drop=True)
    
    return df

def write_plink_fam(df: pd.DataFrame, output_path: Path):
    """Write PLINK .fam file format."""
    # PLINK .fam format: Family ID, Individual ID, Paternal ID, Maternal ID, Sex, Phenotype
    fam_data = df[['colony_id']].copy()
    fam_data['paternal'] = 0
    fam_data['maternal'] = 0
    fam_data['sex'] = 0  # Unknown
    fam_data['phenotype'] = df['ccd_status'].replace({0: -9, 1: 1})  # PLINK uses -9 for missing
    
    fam_data.to_csv(output_path, sep=' ', header=False, index=False)

def write_pheno_file(df: pd.DataFrame, output_path: Path):
    """Write phenotype file with covariates."""
    pheno_data = df[['colony_id', 'ccd_status', 'geographic_region', 'sampling_year', 'varroa_mite_count']].copy()
    pheno_data.to_csv(output_path, sep='\t', index=False)

def write_harmonization_log(df_original: pd.DataFrame, df_cleaned: pd.DataFrame, output_path: Path):
    """Write harmonization log with statistics."""
    log_lines = [
        f"Phenotype Harmonization Log - {datetime.now().isoformat()}",
        "=" * 60,
        f"Original records: {len(df_original)}",
        f"Cleaned records: {len(df_cleaned)}",
        f"Records removed: {len(df_original) - len(df_cleaned)}",
        "",
        "Column statistics:",
        "-" * 40,
    ]
    
    for col in df_cleaned.columns:
        if df_cleaned[col].dtype == 'object':
            unique_count = df_cleaned[col].nunique()
            log_lines.append(f"  {col}: {unique_count} unique categories")
        else:
            mean_val = df_cleaned[col].mean()
            std_val = df_cleaned[col].std()
            log_lines.append(f"  {col}: mean={mean_val:.2f}, std={std_val:.2f}")
    
    log_lines.append("")
    log_lines.append("Data quality checks:")
    log_lines.append(f"  Missing values in CCD status: {df_cleaned['ccd_status'].isna().sum()}")
    log_lines.append(f"  Missing values in Varroa count: {df_cleaned['varroa_mite_count'].isna().sum()}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(log_lines))

def main():
    parser = argparse.ArgumentParser(description='Harmonize phenotype data for GWAS analysis')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to raw phenotype JSON file')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                      help='Output directory for cleaned files')
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading raw phenotypes from: {args.input}")
    df_raw = load_raw_phenotypes(args.input)
    print(f"Loaded {len(df_raw)} records")
    
    print("Validating and cleaning data...")
    df_cleaned = validate_and_clean(df_raw)
    print(f"Cleaned data: {len(df_cleaned)} records")
    
    # Write output files
    fam_path = output_dir / 'phenotypes_cleaned.fam'
    pheno_path = output_dir / 'phenotypes_cleaned.pheno'
    log_path = output_dir / 'harmonization_log.txt'
    
    print(f"Writing PLINK .fam file: {fam_path}")
    write_plink_fam(df_cleaned, fam_path)
    
    print(f"Writing phenotype file: {pheno_path}")
    write_pheno_file(df_cleaned, pheno_path)
    
    print(f"Writing harmonization log: {log_path}")
    write_harmonization_log(df_raw, df_cleaned, log_path)
    
    print("Phenotype harmonization complete.")

if __name__ == '__main__':
    main()