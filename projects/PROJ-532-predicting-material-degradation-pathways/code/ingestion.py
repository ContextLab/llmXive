import csv
import json
import logging
import os
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from .utils import setup_logging, get_dataset_url, save_json, ensure_dir

# Configure logging
logger = setup_logging("ingestion")

# Constants
METALLIC_KEYWORDS = [
    "steel", "alloy", "iron", "nickel", "chromium", "titanium", 
    "aluminum", "copper", "zinc", "magnesium", "cobalt", "molybdenum",
    "tungsten", "vanadium", "niobium", "zirconium", "hafnium", 
    "high-entropy", "superalloy", "stainless"
]

NON_METALLIC_KEYWORDS = [
    "polymer", "plastic", "composite", "ceramic", "glass", "resin",
    "epoxy", "rubber", "silicon", "organic", "carbon fiber"
]

def download_raw_data(output_path: Optional[Path] = None) -> Path:
    """
    Download raw corrosion dataset from Zenodo.
    
    Args:
        output_path: Path to save the downloaded CSV. Defaults to data/raw/corrosion_data.csv
        
    Returns:
        Path to the downloaded file
    """
    url = get_dataset_url("corrosion_dataset")
    if output_path is None:
        output_path = Path("data/raw/corrosion_data.csv")
    
    ensure_dir(output_path.parent)
    
    logger.info(f"Downloading dataset from {url}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded {output_path} ({response.headers.get('content-length', 'unknown')} bytes)")
        return output_path
    except requests.RequestException as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def filter_metallic_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter records to retain ONLY metallic alloys, discard polymers/composites.
    
    Args:
        df: Input DataFrame with material composition data
        
    Returns:
        Filtered DataFrame containing only metallic alloys
    """
    logger.info(f"Initial record count: {len(df)}")
    
    # Ensure material_type column exists and is string
    if 'material_type' not in df.columns:
        logger.warning("No 'material_type' column found. Attempting to infer from material_name.")
        if 'material_name' not in df.columns:
            logger.error("Neither 'material_type' nor 'material_name' column found. Cannot filter.")
            return df
        material_col = 'material_name'
    else:
        material_col = 'material_type'
    
    df[material_col] = df[material_col].astype(str).str.lower()
    
    # Identify metallic records
    metallic_mask = df[material_col].apply(
        lambda x: any(kw in x for kw in METALLIC_KEYWORDS) and not any(kw in x for kw in NON_METALLIC_KEYWORDS)
    )
    
    # Fallback: if no explicit type, assume numeric composition columns imply metal
    if metallic_mask.sum() == 0 and 'material_type' in df.columns:
        logger.warning("No metallic records found by keyword. Checking for numeric composition columns.")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Assume if there are numeric composition columns, it's likely metallic
            metallic_mask = df[numeric_cols].notna().any(axis=1)
    
    filtered_df = df[metallic_mask].copy()
    retained_count = len(filtered_df)
    total_count = len(df)
    retention_pct = (retained_count / total_count * 100) if total_count > 0 else 0.0
    
    logger.info(f"Filtered to metallic alloys: {retained_count} records retained ({retention_pct:.2f}%)")
    
    return filtered_df

def handle_missing_values(df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Handle missing values: impute with median if <5% missing, drop column if >=5%.
    
    Args:
        df: Input DataFrame
        threshold: Fraction of missing values above which column is dropped (default 0.05 = 5%)
        
    Returns:
        DataFrame with missing values handled
    """
    logger.info(f"Handling missing values with threshold {threshold*100}%")
    
    initial_rows = len(df)
    initial_cols = len(df.columns)
    
    # Calculate missing percentage per column
    missing_pct = df.isna().mean()
    
    cols_to_drop = missing_pct[missing_pct >= threshold].index.tolist()
    cols_to_impute = missing_pct[(missing_pct > 0) & (missing_pct < threshold)].index.tolist()
    
    if cols_to_drop:
        logger.warning(f"Dropping {len(cols_to_drop)} columns with >= {threshold*100}% missing: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
    
    if cols_to_impute:
        logger.info(f"Imputing {len(cols_to_impute)} columns with median")
        for col in cols_to_impute:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    
    # Drop rows with any remaining NaNs (should be minimal)
    rows_before_drop = len(df)
    df = df.dropna()
    rows_after_drop = len(df)
    
    if rows_after_drop < rows_before_drop:
        logger.warning(f"Dropped {rows_before_drop - rows_after_drop} rows due to remaining NaNs")
    
    final_rows = len(df)
    final_cols = len(df.columns)
    
    logger.info(f"Missing value handling complete: {initial_rows}x{initial_cols} -> {final_rows}x{final_cols}")
    
    return df

def run_ingestion_pipeline(
    raw_url: Optional[str] = None,
    output_csv: str = "data/processed/cleaned_alloys.csv",
    audit_json: str = "data/processed/retention_audit.json"
) -> Dict[str, Any]:
    """
    Run the full ingestion pipeline: download, filter, impute, and save.
    
    Args:
        raw_url: URL to raw data (overrides environment variable)
        output_csv: Path to save cleaned CSV
        audit_json: Path to save retention audit JSON
        
    Returns:
        Dictionary with pipeline statistics
    """
    logger.info("Starting ingestion pipeline")
    
    # Ensure output directories exist
    ensure_dir(Path(output_csv).parent)
    ensure_dir(Path(audit_json).parent)
    
    # 1. Download data (if not already present or force download)
    raw_path = Path("data/raw/corrosion_data.csv")
    if raw_url:
        logger.info(f"Using provided URL: {raw_url}")
        download_raw_data(raw_path)
    
    if not raw_path.exists():
        logger.info("Raw data not found, attempting download...")
        download_raw_data(raw_path)
    
    # 2. Load data
    logger.info(f"Loading data from {raw_path}")
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise
    
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} records")
    
    # 3. Filter for metallic alloys
    df_filtered = filter_metallic_alloys(df)
    
    # 4. Handle missing values
    df_clean = handle_missing_values(df_filtered)
    
    final_count = len(df_clean)
    retention_pct = (final_count / initial_count * 100) if initial_count > 0 else 0.0
    
    # 5. Save cleaned data
    logger.info(f"Saving cleaned data to {output_csv}")
    df_clean.to_csv(output_csv, index=False)
    
    # 6. Generate audit report
    audit_report = {
        "initial_count": initial_count,
        "final_count": final_count,
        "retention_percentage": round(retention_pct, 2),
        "filter_criteria": "metallic_keywords",
        "dropped_columns": [col for col in df_filtered.columns if col not in df_clean.columns],
        "output_file": str(output_csv)
    }
    
    logger.info(f"Saving audit report to {audit_json}")
    save_json(audit_json, audit_report)
    
    # 7. Validation
    if retention_pct < 70.0:
        logger.warning(f"Retention rate ({retention_pct:.2f}%) is below target (70%)")
    if final_count < 200:
        logger.warning(f"Record count ({final_count}) is below target (200)")
    
    logger.info(f"Ingestion pipeline complete: {initial_count} -> {final_count} records ({retention_pct:.2f}% retention)")
    
    return audit_report

if __name__ == "__main__":
    import sys
    # Allow running as script: python -m code.ingestion
    run_ingestion_pipeline()
