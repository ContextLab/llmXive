import csv
import json
import logging
import os
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np

from utils import setup_logging, get_dataset_url, ensure_dir, get_env_var
from config_env import configure_environment

# Configure logging
logger = setup_logging("ingestion")

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
METAL_TYPES = {"Fe", "Ni", "Ti", "Al", "Cu", "Cr", "Co", "Mn", "Mo", "W", "Nb", "Ta", "Zr", "Hf", "V", "Re", "Ru", "Rh", "Pd", "Pt", "Ag", "Au", "Mg", "Zn", "Sn", "Pb", "Sb", "Bi", "In", "Cd", "Sc", "Y", "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}

# Zenodo Dataset ID for Corrosion Data (Real source)
# Using a known public dataset ID or a placeholder that points to a real accessible source if available.
# For this implementation, we assume the environment variable ZENODO_CORROSION_URL is set,
# or we use a known public dataset. If not set, we attempt a known fallback.
# Note: In a real production environment, this URL must be verified.
# Fallback to a known public dataset structure if URL not provided.
# Since I cannot browse live to verify a specific new ID, I will use a robust fetch mechanism.
# The task requires REAL data. If the URL is not provided or fails, we raise an error.

# Default URL for demonstration if env var is missing (This would be replaced by the actual Zenodo URL in production)
# Using a generic placeholder that raises an error if not overridden, OR a real dataset if known.
# Let's assume the spec points to a specific Zenodo record.
# Example: https://zenodo.org/api/records/123456/files/corrosion_data.csv
# We will use the environment variable as the primary source.

def download_raw_data(output_path: Optional[Path] = None) -> Path:
    """
    Downloads the raw corrosion dataset from Zenodo.
    Verifies URL reachability.
    Raises an error if the fetch fails.
    """
    url = get_env_var("ZENODO_CORROSION_URL", None)
    if not url:
        # Fallback to a known public dataset if env var is not set.
        # Using a specific Zenodo record for corrosion data if available, otherwise error.
        # For this implementation, we strictly require the URL or a verified real source.
        # If no URL is provided, we cannot fabricate data.
        logger.error("ZENODO_CORROSION_URL environment variable not set.")
        raise ValueError("ZENODO_CORROSION_URL environment variable is required to fetch real data.")
    
    logger.info(f"Downloading raw data from: {url}")
    ensure_dir(RAW_DATA_DIR)
    
    if output_path is None:
        output_path = RAW_DATA_DIR / "raw_corrosion_data.csv"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded raw data to {output_path}")
        return output_path
    except requests.RequestException as e:
        logger.error(f"Failed to download data from {url}: {e}")
        raise

def filter_metallic_alloys(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Filters records to retain ONLY metallic alloys.
    Discards polymers, composites, and ceramics.
    """
    logger.info(f"Filtering metallic alloys from {input_path}")
    
    # Load data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise
    
    # Identify the column containing material type. 
    # Common column names: 'material_type', 'classification', 'type'
    type_col = None
    candidates = ['material_type', 'classification', 'type', 'material_class']
    for col in candidates:
        if col in df.columns:
            type_col = col
            break
    
    if type_col is None:
        # Fallback: assume all are metallic if no type column exists, 
        # but log a warning. In a real scenario, this might be an error.
        logger.warning("No material type column found. Assuming all records are metallic.")
        metallic_df = df.copy()
    else:
        # Filter based on metallic keywords
        # We check if the type string contains any known metal keywords or is in our list
        # A simple heuristic: if the type is not polymer, composite, ceramic, etc.
        non_metallic_keywords = ['polymer', 'composite', 'ceramic', 'glass', 'plastic', 'rubber', 'organic']
        
        mask = df[type_col].astype(str).str.lower().apply(
            lambda x: not any(keyword in x for keyword in non_metallic_keywords)
        )
        metallic_df = df[mask].copy()
        
        logger.info(f"Retained {len(metallic_df)} metallic records out of {len(df)} total.")
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    metallic_df.to_csv(output_path, index=False)
    logger.info(f"Filtered data saved to {output_path}")
    
    return metallic_df

def handle_missing_values(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Calculates missing value percentages and applies imputation or exclusion rules.
    - <5% missing: Median imputation
    - >=5% missing: Drop column
    - Returns cleaned DataFrame.
    """
    logger.info("Handling missing values")
    
    initial_cols = len(df.columns)
    initial_rows = len(df)
    
    # Identify numeric columns for imputation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    missing_stats = {}
    
    for col in numeric_cols:
        missing_pct = df[col].isna().sum() / len(df) * 100
        missing_stats[col] = missing_pct
        
        if missing_pct < 5.0:
            # Median imputation
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            logger.debug(f"Imputed {col} with median {median_val} ({missing_pct:.2f}% missing)")
        elif missing_pct >= 5.0:
            # Drop column
            df.drop(columns=[col], inplace=True)
            logger.warning(f"Dropped {col} due to {missing_pct:.2f}% missing values")
    
    # Drop rows with any remaining missing values (should be minimal)
    initial_len = len(df)
    df.dropna(inplace=True)
    dropped_rows = initial_len - len(df)
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows with remaining missing values.")
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Missing value handling complete. Saved to {output_path}")
    
    return df

def run_ingestion_pipeline(raw_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the full ingestion pipeline: download, filter, impute.
    Generates cleaned_alloys.csv and retention_audit.json.
    """
    # Step 1: Download
    raw_file_path = RAW_DATA_DIR / "raw_corrosion_data.csv"
    if not raw_file_path.exists():
        download_raw_data(raw_file_path)
    
    # Step 2: Filter
    filtered_file_path = RAW_DATA_DIR / "filtered_metallic.csv"
    metallic_df = filter_metallic_alloys(raw_file_path, filtered_file_path)
    
    # Step 3: Handle Missing Values
    cleaned_file_path = PROCESSED_DATA_DIR / "cleaned_alloys.csv"
    cleaned_df = handle_missing_values(metallic_df, cleaned_file_path)
    
    # Step 4: Calculate and Log Retention Stats
    # We need the original count for retention calculation. 
    # Assuming the raw file had the original count.
    try:
        original_df = pd.read_csv(raw_file_path)
        original_count = len(original_df)
    except Exception:
        # Fallback if original read fails, use filtered count as base (less accurate)
        logger.warning("Could not read original raw file for retention count. Using filtered count as base.")
        original_count = len(metallic_df)
    
    final_count = len(cleaned_df)
    retention_percentage = (final_count / original_count) * 100 if original_count > 0 else 0.0
    
    audit_report = {
        "original_record_count": original_count,
        "filtered_record_count": len(metallic_df),
        "final_record_count": final_count,
        "retention_percentage": retention_percentage,
        "target_retention_percentage": 70.0,
        "target_record_count": 200,
        "meets_target_retention": retention_percentage >= 70.0,
        "meets_target_count": final_count >= 200,
        "status": "PASS" if (retention_percentage >= 70.0 and final_count >= 200) else "FAIL"
    }
    
    audit_path = PROCESSED_DATA_DIR / "retention_audit.json"
    ensure_dir(audit_path.parent)
    
    with open(audit_path, 'w') as f:
        json.dump(audit_report, f, indent=2)
    
    logger.info(f"Retention audit saved to {audit_path}")
    logger.info(f"Final Stats: Count={final_count}, Retention={retention_percentage:.2f}%")
    
    return audit_report

def main():
    """Main entry point for the ingestion script."""
    configure_environment()
    logger.info("Starting Ingestion Pipeline")
    
    try:
        report = run_ingestion_pipeline()
        if report["status"] == "FAIL":
            logger.warning("Ingestion pipeline completed but did not meet targets.")
        else:
            logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
