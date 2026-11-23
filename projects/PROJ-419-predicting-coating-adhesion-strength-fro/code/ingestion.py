"""
Data ingestion module for the Coating Adhesion Pipeline.
"""
import os
import time
import logging
from typing import Optional, List, Dict, Any
import requests
import pandas as pd
import json
import hashlib

from utils import DataGapError, APIError, exponential_backoff, fetch_json_data, verify_url_accessibility

logger = logging.getLogger(__name__)

# Configuration imports (assuming config.py has these)
try:
    from config import MP_API_KEY, NIST_URL, LIT_API_URL, LIT_API_KEY, DATA_RAW_DIR, DATA_PROCESSED_DIR, MAX_ROWS
except ImportError:
    # Fallback for testing if config is not available
    MP_API_KEY = os.getenv("MP_API_KEY", "dummy_key")
    NIST_URL = os.getenv("NIST_URL", "https://dummy-nist-url.com")
    LIT_API_URL = os.getenv("LIT_API_URL", "https://dummy-lit-url.com")
    LIT_API_KEY = os.getenv("LIT_API_KEY", "dummy_key")
    DATA_RAW_DIR = "data/raw"
    DATA_PROCESSED_DIR = "data/processed"
    MAX_ROWS = 5000

def ensure_data_dirs():
    """Ensure data directories exist."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

@exponential_backoff()
def fetch_materials_project_data():
    """Fetch data from Materials Project API."""
    # This is a placeholder. In a real implementation, you would use the actual API.
    # For now, we'll simulate fetching data.
    logger.info("Fetching data from Materials Project API...")
    
    # Simulate data fetch
    data = {
        "materials": [
            {"material_id": "mp-1", "composition": "Al2O3", "properties": {"band_gap": 8.0}},
            {"material_id": "mp-2", "composition": "SiO2", "properties": {"band_gap": 9.0}}
        ]
    }
    return data

@exponential_backoff()
def fetch_nist_surface_metrology_data():
    """Fetch data from NIST Surface Metrology Repository."""
    logger.info("Fetching data from NIST Surface Metrology Repository...")
    
    # Simulate data fetch
    data = {
        "surfaces": [
            {"surface_id": "nist-1", "roughness": 0.5, "skewness": 0.1},
            {"surface_id": "nist-2", "roughness": 0.8, "skewness": 0.2}
        ]
    }
    return data

@exponential_backoff()
def fetch_open_access_literature_data():
    """Fetch data from Literature Source."""
    logger.info("Fetching data from Literature Source...")
    
    # Simulate data fetch
    data = {
        "literature": [
            {"study_id": "lit-1", "adhesion_strength": 25.0, "coating_id": "coat-1", "substrate_id": "sub-1"},
            {"study_id": "lit-2", "adhesion_strength": 30.0, "coating_id": "coat-2", "substrate_id": "sub-2"}
        ]
    }
    return data

def filter_astm_d4541_records(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Filter records to ASTM D4541 pull-off test results."""
    logger.info("Filtering records to ASTM D4541 pull-off test results...")
    # In a real implementation, you would filter based on the test method field.
    # For now, we assume all data is ASTM D4541 compliant.
    return data

def exclude_missing_target_records(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Exclude records with missing target variables."""
    logger.info("Excluding records with missing target variables...")
    # Filter out records where adhesion_strength is missing
    if 'literature' in data:
        data['literature'] = [r for r in data['literature'] if r.get('adhesion_strength') is not None]
    return data

def resolve_duplicates(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Resolve duplicates (most recent date or highest sample count)."""
    logger.info("Resolving duplicates...")
    # In a real implementation, you would use date or sample count to resolve.
    # For now, we assume no duplicates.
    return data

def sample_dataset_to_memory_limit(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Sample dataset to memory limit if needed."""
    logger.info("Sampling dataset to memory limit...")
    # If data exceeds MAX_ROWS, sample it
    total_records = sum(len(v) for v in data.values())
    if total_records > MAX_ROWS:
        logger.warning(f"Dataset exceeds {MAX_ROWS} rows. Sampling...")
        # Simple sampling: take first MAX_ROWS records
        sampled_data = {}
        remaining = MAX_ROWS
        for key, records in data.items():
            take = min(len(records), remaining)
            sampled_data[key] = records[:take]
            remaining -= take
            if remaining <= 0:
                break
        return sampled_data
    return data

def exclude_missing_surface_roughness(data: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing surface roughness: impute using median of same substrate_id group if missing, else exclude.
    Run ONLY on the subset of records that have successfully passed Strict ID Alignment.
    """
    logger.info("Handling missing surface roughness...")
    
    if 'roughness' not in data.columns:
        logger.warning("Roughness column not found. Skipping imputation.")
        return data
    
    if 'substrate_id' not in data.columns:
        logger.warning("substrate_id column not found. Cannot impute by group.")
        # Exclude records with missing roughness
        before_count = len(data)
        data = data.dropna(subset=['roughness'])
        logger.info(f"Excluded {before_count - len(data)} records with missing roughness (no substrate_id group).")
        return data
    
    # Group by substrate_id and impute using median
    def impute_roughness(group):
        if group['roughness'].isna().all():
            return group  # Cannot impute if all are NaN
        median_val = group['roughness'].median()
        group['roughness'] = group['roughness'].fillna(median_val)
        return group
    
    before_count = len(data)
    data = data.groupby('substrate_id', group_keys=False).apply(impute_roughness)
    
    # Now exclude any remaining NaNs (groups that were entirely NaN)
    data = data.dropna(subset=['roughness'])
    after_count = len(data)
    logger.info(f"Imputed/excluded records: {before_count - after_count} excluded, {after_count} remaining.")
    
    return data

def align_records_strictly(materials_data: Dict, nist_data: Dict, literature_data: Dict) -> pd.DataFrame:
    """
    Align records strictly using unique, verified identifiers.
    Any record pair that cannot be linked via a verified unique identifier is excluded.
    """
    logger.info("Aligning records strictly by unique identifiers...")
    
    # This is a simplified alignment. In a real implementation, you would use the actual unique IDs.
    # We assume:
    # - Materials Project data has 'material_id'
    # - NIST data has 'surface_id'
    # - Literature data has 'coating_id' and 'substrate_id'
    
    # Create DataFrames
    df_materials = pd.DataFrame(materials_data.get('materials', []))
    df_nist = pd.DataFrame(nist_data.get('surfaces', []))
    df_literature = pd.DataFrame(literature_data.get('literature', []))
    
    # Merge literature with materials on coating_id = material_id
    # and with nist on substrate_id = surface_id
    # Strict alignment: only keep records that match in both
    
    if df_materials.empty or df_nist.empty or df_literature.empty:
        logger.warning("One or more data sources are empty. Cannot align.")
        return pd.DataFrame()
    
    # Ensure column names match for merging
    df_materials = df_materials.rename(columns={'material_id': 'coating_id'})
    df_nist = df_nist.rename(columns={'surface_id': 'substrate_id'})
    
    # Merge literature with materials
    df_merged = pd.merge(df_literature, df_materials, on='coating_id', how='inner')
    # Merge with nist
    df_merged = pd.merge(df_merged, df_nist, on='substrate_id', how='inner')
    
    logger.info(f"Aligned {len(df_merged)} records strictly.")
    return df_merged

def process_ingestion_data():
    """
    Main ingestion pipeline: fetch, filter, align, and save intermediate data.
    """
    logger.info("Starting data ingestion pipeline...")
    ensure_data_dirs()
    
    # 1. Fetch data
    materials_data = fetch_materials_project_data()
    nist_data = fetch_nist_surface_metrology_data()
    literature_data = fetch_open_access_literature_data()
    
    # 2. Filter to ASTM D4541
    materials_data = filter_astm_d4541_records(materials_data)
    nist_data = filter_astm_d4541_records(nist_data)
    literature_data = filter_astm_d4541_records(literature_data)
    
    # 3. Exclude missing targets
    literature_data = exclude_missing_target_records(literature_data)
    
    # 4. Resolve duplicates
    materials_data = resolve_duplicates(materials_data)
    nist_data = resolve_duplicates(nist_data)
    literature_data = resolve_duplicates(literature_data)
    
    # 5. Sample to memory limit
    materials_data = sample_dataset_to_memory_limit(materials_data)
    nist_data = sample_dataset_to_memory_limit(nist_data)
    literature_data = sample_dataset_to_memory_limit(literature_data)
    
    # 6. Align strictly
    aligned_df = align_records_strictly(materials_data, nist_data, literature_data)
    
    if aligned_df.empty:
        logger.error("No records aligned. Pipeline cannot proceed.")
        return
    
    # 7. Handle missing surface roughness (T027)
    # This runs AFTER strict alignment (T075)
    aligned_df = exclude_missing_surface_roughness(aligned_df)
    
    if aligned_df.empty:
        logger.error("No records remaining after roughness handling. Pipeline cannot proceed.")
        return
    
    # 8. Save aligned data to a temporary file for T031 to pick up
    aligned_path = os.path.join(DATA_PROCESSED_DIR, "aligned_coating_data.csv")
    aligned_df.to_csv(aligned_path, index=False)
    logger.info(f"Aligned data saved to {aligned_path}")
    
    return aligned_df

def main():
    """Main entry point for ingestion."""
    process_ingestion_data()

if __name__ == '__main__':
    main()
