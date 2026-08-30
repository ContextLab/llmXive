"""
Phenotype Harmonization Module for Honeybee CCD GWAS.

This module maps raw CCD diagnosis codes to the standardized CCD Working Group criteria
as specified in FR-011. It ensures that only colonies meeting the strict diagnostic
criteria (dead adult bees, absence of dead pupae, low live bee population) are
classified as CCD cases.

Input: Raw phenotype data (JSON or CSV) from data/raw or data/interim.
Output: Harmonized .fam and .pheno files for PLINK, plus a harmonization log.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/harmonization.log')
    ]
)
logger = logging.getLogger(__name__)

# CCD Working Group Criteria Constants (FR-011)
# 1. Presence of dead adult bees in the hive (implied by collapse)
# 2. Absence of dead pupae (distinct from other collapse causes)
# 3. Live bee population < 10% relative to peak season
CCD_LIVE_POPULATION_THRESHOLD = 0.10
CCD_PUPAE_ABSENCE_REQUIRED = True

def load_raw_phenotypes(input_path: str) -> pd.DataFrame:
    """
    Load raw phenotype data from JSON or CSV.
    
    Args:
        input_path: Path to the input file.
        
    Returns:
        DataFrame containing raw phenotype data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading raw phenotypes from {input_path}")
    
    if path.suffix.lower() == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
        # Handle list of records or single object with 'records' key
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'records' in data:
            df = pd.DataFrame(data['records'])
        else:
            df = pd.DataFrame([data])
    elif path.suffix.lower() in ['.csv', '.tsv']:
        sep = '\t' if path.suffix.lower() == '.tsv' else ','
        df = pd.read_csv(path, sep=sep)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .json, .csv, or .tsv")
    
    logger.info(f"Loaded {len(df)} records")
    return df

def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean phenotype data against CCD Working Group criteria.
    
    FR-011 Criteria:
    1. Presence of dead adult bees (implied if 'status' indicates collapse/death)
    2. Absence of dead pupae (must be 0 or False)
    3. Live bee population < 10% of peak (live_population_ratio < 0.10)
    
    Args:
        df: Raw phenotype DataFrame.
        
    Returns:
        Cleaned DataFrame with harmonized 'ccd_case' column (1=Case, 0=Control).
        
    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = ['colony_id', 'status', 'live_population_ratio']
    optional_cols = ['dead_pupae_count', 'dead_pupae_present']
    
    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info("Validating CCD criteria (FR-011)...")
    
    # Initialize harmonized column
    df['ccd_case'] = 0  # Default to control
    
    # Normalize status column to handle variations
    # Expected values: 'collapse', 'dead', 'healthy', 'active', etc.
    df['status_normalized'] = df['status'].astype(str).str.lower().str.strip()
    
    # Identify potential CCD cases based on status
    # Criteria 1: Presence of dead adult bees (status indicates collapse/death)
    potential_cases = df['status_normalized'].isin(['collapse', 'dead', 'collapsed', 'ccdsuspected'])
    
    # Criteria 2: Absence of dead pupae
    # Check if dead_pupae_count exists, or dead_pupae_present is False/0
    pupae_clean = pd.Series(True, index=df.index)
    if 'dead_pupae_count' in df.columns:
        pupae_clean = (df['dead_pupae_count'] == 0) | (df['dead_pupae_count'].isna())
    elif 'dead_pupae_present' in df.columns:
        pupae_clean = (df['dead_pupae_present'] == False) | (df['dead_pupae_present'] == 0)
    
    # Criteria 3: Live bee population < 10% of peak
    low_population = df['live_population_ratio'] < CCD_LIVE_POPULATION_THRESHOLD
    
    # Combine all criteria: Must meet ALL three to be a confirmed CCD case
    # (Potential collapse) AND (No dead pupae) AND (Low live population)
    confirmed_ccd = potential_cases & pupae_clean & low_population
    
    # Update ccd_case column
    df.loc[confirmed_ccd, 'ccd_case'] = 1
    
    # Log validation results
    total = len(df)
    cases = df['ccd_case'].sum()
    controls = total - cases
    
    logger.info(f"Validation complete:")
    logger.info(f"  Total colonies: {total}")
    logger.info(f"  Confirmed CCD cases: {cases} ({100*cases/total:.2f}%)")
    logger.info(f"  Controls: {controls} ({100*controls/total:.2f}%)")
    
    # Log excluded records (potential cases that didn't meet all criteria)
    excluded_count = (potential_cases & ~confirmed_ccd).sum()
    if excluded_count > 0:
        logger.warning(f"  Excluded {excluded_count} potential cases that did not meet all FR-011 criteria")
    
    return df

def write_plink_fam(df: pd.DataFrame, output_dir: str) -> str:
    """
    Write PLINK .fam file.
    
    PLINK .fam format (6 columns):
    1. Family ID
    2. Individual ID
    3. Paternal ID (0 if unknown)
    4. Maternal ID (0 if unknown)
    5. Sex (1=male, 2=female, 0=unknown)
    6. Phenotype (-9=missing, 1=control, 2=case)
    
    Args:
        df: Cleaned DataFrame with 'colony_id' and 'ccd_case'.
        output_dir: Directory to write the .fam file.
        
    Returns:
        Path to the written .fam file.
    """
    fam_path = Path(output_dir) / 'harmonized.fam'
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare FAM data
    fam_data = pd.DataFrame({
        'FID': df['colony_id'],
        'IID': df['colony_id'],
        'PAT': 0,
        'MAT': 0,
        'SEX': 0,  # Unknown sex for colonies
        'PHENOTYPE': df['ccd_case'].map({0: 1, 1: 2}).fillna(-9)
    })
    
    fam_data.to_csv(fam_path, sep='\t', header=False, index=False)
    logger.info(f"Wrote PLINK .fam file to {fam_path}")
    return str(fam_path)

def write_pheno_file(df: pd.DataFrame, output_dir: str) -> str:
    """
    Write PLINK .pheno file (phenotype file).
    
    Format:
    #FID IID PHENOTYPE [optional columns...]
    
    Args:
        df: Cleaned DataFrame with 'colony_id' and 'ccd_case'.
        output_dir: Directory to write the .pheno file.
        
    Returns:
        Path to the written .pheno file.
    """
    pheno_path = Path(output_dir) / 'harmonized.pheno'
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare PHENO data
    pheno_data = pd.DataFrame({
        'FID': df['colony_id'],
        'IID': df['colony_id'],
        'PHENOTYPE': df['ccd_case'].map({0: 1, 1: 2}).fillna(-9)
    })
    
    # Add any additional covariates if present
    covariates = [col for col in df.columns if col not in ['colony_id', 'ccd_case', 'status', 'status_normalized']]
    for cov in covariates:
        if cov in df.columns:
            pheno_data[cov] = df[cov]
    
    pheno_data.to_csv(pheno_path, sep='\t', index=False)
    logger.info(f"Wrote PLINK .pheno file to {pheno_path}")
    return str(pheno_path)

def write_harmonization_log(df: pd.DataFrame, output_dir: str) -> str:
    """
    Write a detailed harmonization log in JSON format.
    
    Args:
        df: Cleaned DataFrame.
        output_dir: Directory to write the log file.
        
    Returns:
        Path to the written log file.
    """
    log_path = Path(output_dir) / 'harmonization_report.json'
    os.makedirs(output_dir, exist_ok=True)
    
    report = {
        'total_colonies': len(df),
        'ccd_cases': int(df['ccd_case'].sum()),
        'controls': int(len(df) - df['ccd_case'].sum()),
        'criteria_applied': {
            'dead_adult_beens': 'status in [collapse, dead, collapsed, ccdsuspected]',
            'no_dead_pupae': 'dead_pupae_count == 0 OR dead_pupae_present == False',
            'low_population': f'live_population_ratio < {CCD_LIVE_POPULATION_THRESHOLD}'
        },
        'sample_data': df.head(10).to_dict(orient='records')
    }
    
    with open(log_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Wrote harmonization report to {log_path}")
    return str(log_path)

def main():
    """Main entry point for phenotype harmonization."""
    parser = argparse.ArgumentParser(
        description='Harmonize CCD phenotype data to Working Group criteria (FR-011)'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to raw phenotype file (JSON, CSV, or TSV)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='data/processed',
        help='Directory to write harmonized files (default: data/processed)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load raw data
        df = load_raw_phenotypes(args.input)
        
        # Validate and clean against FR-011 criteria
        df_clean = validate_and_clean(df)
        
        # Write output files
        write_plink_fam(df_clean, args.output_dir)
        write_pheno_file(df_clean, args.output_dir)
        write_harmonization_log(df_clean, args.output_dir)
        
        logger.info("Phenotype harmonization completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()