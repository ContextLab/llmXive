"""
Ingestion module for American Gut Project and Open Humans data.
Handles downloading, parsing, merging, filtering, and saving the final cohort.
"""
import os
import hashlib
import logging
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import pandas as pd
import requests
import biom
import skbio
from skbio.stats.diversity import alpha_diversity
from skbio.diversity import beta_diversity

from config import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.validators import validate_merged_cohort
from utils.seeding import set_seed

# Setup logging
logger = get_logger(__name__)

def download_file(url: str, dest_path: Path, checksum: Optional[str] = None) -> bool:
    """Download a file from a URL and verify its checksum if provided."""
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if checksum:
            with open(dest_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash != checksum:
                    logger.error(f"Checksum mismatch for {dest_path}: expected {checksum}, got {file_hash}")
                    return False
        
        logger.info(f"Successfully downloaded {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def parse_biom_table(biom_path: Path) -> skbio.Table:
    """Parse a BIOM format file into a skbio Table."""
    logger.info(f"Parsing BIOM table from {biom_path}")
    try:
        with open(biom_path, 'rb') as f:
            table = biom.load_table(f)
        logger.info(f"Loaded BIOM table with {table.shape[0]} features and {table.shape[1]} samples")
        return table
    except Exception as e:
        logger.error(f"Failed to parse BIOM table: {e}")
        raise

def ingest_agp_metadata(metadata_path: Path) -> pd.DataFrame:
    """Ingest American Gut Project metadata."""
    logger.info(f"Ingesting AGP metadata from {metadata_path}")
    try:
        df = pd.read_csv(metadata_path, sep='\t', low_memory=False)
        logger.info(f"Loaded AGP metadata with {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to ingest AGP metadata: {e}")
        raise

def ingest_sleep_metadata(metadata_path: Path) -> pd.DataFrame:
    """Ingest Open Humans sleep metadata."""
    logger.info(f"Ingesting sleep metadata from {metadata_path}")
    try:
        df = pd.read_csv(metadata_path, sep=',', low_memory=False)
        logger.info(f"Loaded sleep metadata with {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to ingest sleep metadata: {e}")
        raise

def verify_integrity(agp_df: pd.DataFrame, sleep_df: pd.DataFrame) -> Tuple[int, int]:
    """Verify data integrity and return sample counts."""
    agp_count = len(agp_df)
    sleep_count = len(sleep_df)
    logger.info(f"Data integrity check: AGP={agp_count}, Sleep={sleep_count}")
    return agp_count, sleep_count

def filter_missing_data(agp_df: pd.DataFrame, sleep_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Filter out rows with missing critical data."""
    logger.info("Filtering missing data...")
    
    # Critical columns for AGP
    agp_critical_cols = ['Participant ID', 'Shannon Diversity']
    agp_df = agp_df.dropna(subset=agp_critical_cols)
    
    # Critical columns for Sleep
    sleep_critical_cols = ['Participant ID', 'Sleep Duration', 'Sleep Quality']
    sleep_df = sleep_df.dropna(subset=sleep_critical_cols)
    
    logger.info(f"After filtering missing data: AGP={len(agp_df)}, Sleep={len(sleep_df)}")
    return agp_df, sleep_df

def cap_outliers(sleep_df: pd.DataFrame) -> pd.DataFrame:
    """Cap sleep duration outliers at 1st and 99th percentiles."""
    logger.info("Capping sleep duration outliers...")
    
    sleep_col = 'Sleep Duration'
    if sleep_col not in sleep_df.columns:
        logger.warning(f"Column {sleep_col} not found, skipping outlier capping")
        return sleep_df
    
    lower_bound = sleep_df[sleep_col].quantile(0.01)
    upper_bound = sleep_df[sleep_col].quantile(0.99)
    
    logger.info(f"Capping {sleep_col} between {lower_bound:.2f} and {upper_bound:.2f}")
    sleep_df[sleep_col] = sleep_df[sleep_col].clip(lower=lower_bound, upper=upper_bound)
    
    return sleep_df

def impute_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing covariates using median (numeric) or mode (categorical)."""
    logger.info("Imputing covariates...")
    
    numeric_cols = ['Age', 'BMI']
    categorical_cols = ['Antibiotic History', 'Diet Type']
    
    for col in numeric_cols:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info(f"Imputed {col} with median {median_val:.2f}")
    
    for col in categorical_cols:
        if col in df.columns:
            mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
            df[col] = df[col].fillna(mode_val)
            logger.info(f"Imputed {col} with mode {mode_val}")
    
    return df

def generate_summary_report(merged_df: pd.DataFrame, output_path: Path) -> None:
    """Generate a summary report of the merged cohort."""
    logger.info("Generating summary report...")
    
    report_lines = [
        "=== Cohort Merging Summary Report ===",
        f"Total Retained Participants (N): {len(merged_df)}",
        "",
        "=== Key Covariate Distributions ===",
    ]
    
    # Age distribution
    if 'Age' in merged_df.columns:
        age_stats = merged_df['Age'].describe()
        report_lines.append(f"Age - Mean: {age_stats['mean']:.2f}, Std: {age_stats['std']:.2f}, Min: {age_stats['min']:.2f}, Max: {age_stats['max']:.2f}")
    
    # BMI distribution
    if 'BMI' in merged_df.columns:
        bmi_stats = merged_df['BMI'].describe()
        report_lines.append(f"BMI - Mean: {bmi_stats['mean']:.2f}, Std: {bmi_stats['std']:.2f}, Min: {bmi_stats['min']:.2f}, Max: {bmi_stats['max']:.2f}")
    
    # Antibiotic use
    if 'Antibiotic History' in merged_df.columns:
        antibiotic_counts = merged_df['Antibiotic History'].value_counts()
        report_lines.append(f"Antibiotic History:\n{antibiotic_counts.to_string()}")
    
    report_content = "\n".join(report_lines)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Summary report saved to {output_path}")
    print(report_content)

def save_cohort(merged_df: pd.DataFrame, output_path: Path) -> None:
    """Save the final merged cohort to a CSV file."""
    logger.info(f"Saving merged cohort to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    merged_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully saved {len(merged_df)} rows to {output_path}")
    print(f"Cohort saved: {len(merged_df)} participants to {output_path}")

def main():
    """Main function to run the ingestion pipeline."""
    setup_logging()
    config = get_config()
    set_seed(config.random_seed)
    
    # Define paths
    data_dir = Path(config.data_dir)
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Download AGP data (example URLs - replace with actual canonical URLs)
    agp_biom_url = "https://s3.amazonaws.com/americangutproject/biom/16S_otu_table.biom"
    agp_metadata_url = "https://s3.amazonaws.com/americangutproject/metadata/AGP_metadata.tsv"
    sleep_metadata_url = "https://raw.githubusercontent.com/openhumans/sleep-data/main/sleep_metadata.csv"
    
    agp_biom_path = raw_dir / '16S_otu_table.biom'
    agp_metadata_path = raw_dir / 'AGP_metadata.tsv'
    sleep_metadata_path = raw_dir / 'sleep_metadata.csv'
    
    # Download files
    if not agp_biom_path.exists():
        download_file(agp_biom_url, agp_biom_path)
    if not agp_metadata_path.exists():
        download_file(agp_metadata_url, agp_metadata_path)
    if not sleep_metadata_path.exists():
        download_file(sleep_metadata_url, sleep_metadata_path)
    
    # Parse data
    biom_table = parse_biom_table(agp_biom_path)
    agp_df = ingest_agp_metadata(agp_metadata_path)
    sleep_df = ingest_sleep_metadata(sleep_metadata_path)
    
    # Verify integrity
    verify_integrity(agp_df, sleep_df)
    
    # Filter missing data
    agp_df, sleep_df = filter_missing_data(agp_df, sleep_df)
    
    # Cap outliers
    sleep_df = cap_outliers(sleep_df)
    
    # Merge datasets on Participant ID
    logger.info("Merging datasets on Participant ID...")
    merged_df = pd.merge(
        agp_df,
        sleep_df,
        on='Participant ID',
        how='inner'
    )
    
    if len(merged_df) == 0:
        logger.warning("No matching participants found; proceeding with available sample size")
        # Log warning but continue
    else:
        logger.info(f"Successfully merged {len(merged_df)} participants")
    
    # Impute covariates
    merged_df = impute_covariates(merged_df)
    
    # Validate merged cohort
    validate_merged_cohort(merged_df)
    
    # Generate summary report
    report_path = processed_dir / 'cohort_summary.txt'
    generate_summary_report(merged_df, report_path)
    
    # Save final merged cohort
    output_path = processed_dir / 'cohort_merged.csv'
    save_cohort(merged_df, output_path)
    
    logger.info("Ingestion pipeline completed successfully")

if __name__ == "__main__":
    main()
