"""
Main data ingestion script for the Glass Forming Region prediction project.

This script:
1. Attempts to fetch data from the primary Zenodo DOI source (Science Advances)
2. Falls back to Materials Project API if Zenodo is unavailable
3. Falls back to synthetic data generator if both external sources fail
4. Merges records, deduplicates, and outputs the engineered dataset

Usage:
    python code/main.py
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# Project imports
from utils.io import load_csv, save_csv, load_json, save_json
from utils.dedup import deduplicate_compositions, get_deduplication_stats
from features.descriptors import apply_descriptors_to_dataframe
from utils.synthetic import generate_synthetic_dataset
from config import get_materials_project_api_key, get_data_path, ensure_data_directories, get_custom_dataset_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ZENODO_DOI = "10.1126/sciadv.aaq1566"
ZENODO_API_URL = f"https://zenodo.org/api/records?qdoi:{ZENODO_DOI}"
MP_API_BASE = "https://api.materialsproject.org"
MP_VERSION = "v3"

# Output paths
DATA_PATH = get_data_path()
RAW_PATH = DATA_PATH / "raw"
PROCESSED_PATH = DATA_PATH / "processed"
PROVENANCE_PATH = DATA_PATH / "provenance.json"

def fetch_zenodo_data() -> Optional[pd.DataFrame]:
    """
    Fetch data from Zenodo using the DOI.
    
    Returns:
        DataFrame with alloy compositions or None if fetch fails
    """
    logger.info(f"Attempting to fetch data from Zenodo DOI: {ZENODO_DOI}")
    
    try:
        # Zenodo API search by DOI
        response = requests.get(
            ZENODO_API_URL,
            timeout=30,
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'hits' in data and len(data['hits']['hits']) > 0:
                # Extract record data
                record = data['hits']['hits'][0]
                files = record.get('files', [])
                
                # Look for CSV files
                for file_info in files:
                    if file_info.get('key', '').endswith('.csv'):
                        file_url = file_info.get('links', {}).get('self')
                        if file_url:
                            csv_response = requests.get(file_url, timeout=60)
                            if csv_response.status_code == 200:
                                # Parse CSV from content
                                import io
                                df = pd.read_csv(io.StringIO(csv_response.text))
                                logger.info(f"Successfully loaded {len(df)} records from Zenodo")
                                return df
                
                logger.warning("No CSV files found in Zenodo record")
                return None
            else:
                logger.warning("No records found for DOI")
                return None
        else:
            logger.warning(f"Zenodo API returned status {response.status_code}")
            return None
            
    except (RequestException, Timeout, ConnectionError) as e:
        logger.warning(f"Failed to fetch from Zenodo: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from Zenodo: {e}")
        return None

def fetch_materials_project_data() -> Optional[pd.DataFrame]:
    """
    Fetch alloy composition data from Materials Project API.
    
    Returns:
        DataFrame with compositions or None if fetch fails
    """
    api_key = get_materials_project_api_key()
    if not api_key:
        logger.warning("Materials Project API key not set. Skipping MP fetch.")
        return None
    
    logger.info("Fetching data from Materials Project API...")
    
    try:
        # Query for amorphous/crystalline phases (using materials API)
        # Note: This is a simplified query; real implementation might need more complex filtering
        url = f"{MP_API_BASE}/{MP_VERSION}/materials"
        params = {
            "api_key": api_key,
            "format": "json",
            "criteria": '{"phase": {"$in": ["amorphous", "crystalline"]}}'
        }
        
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                records = data['data']
                # Transform to our format
                rows = []
                for record in records:
                    comp = record.get('composition', '')
                    phase = record.get('phase', 'unknown')
                    if phase in ['amorphous', 'crystalline']:
                        rows.append({
                            'composition': comp,
                            'phase': phase,
                            'source': 'materials_project',
                            'url': f"https://materialsproject.org/materials/{record.get('material_id', '')}"
                        })
                
                if rows:
                    df = pd.DataFrame(rows)
                    logger.info(f"Successfully loaded {len(df)} records from Materials Project")
                    return df
                else:
                    logger.warning("No matching records found in Materials Project")
                    return None
            else:
                logger.warning("No data in Materials Project response")
                return None
        else:
            logger.warning(f"Materials Project API returned status {response.status_code}")
            return None
            
    except (RequestException, Timeout, ConnectionError) as e:
        logger.warning(f"Failed to fetch from Materials Project: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from Materials Project: {e}")
        return None

def fetch_synthetic_data() -> pd.DataFrame:
    """
    Generate synthetic data as a fallback.
    
    Returns:
        DataFrame with synthetic alloy compositions
    """
    logger.info("Generating synthetic data as fallback...")
    df = generate_synthetic_dataset(n_samples=1000)
    logger.info(f"Generated {len(df)} synthetic samples")
    return df

def load_and_merge_datasets() -> pd.DataFrame:
    """
    Attempt to load data from primary and secondary sources, merge, and deduplicate.
    
    Returns:
        Combined DataFrame with all sources
    """
    sources = []
    
    # 1. Try Zenodo (Primary)
    zenodo_df = fetch_zenodo_data()
    if zenodo_df is not None:
        sources.append(zenodo_df)
        logger.info("Zenodo data loaded successfully")
    else:
        logger.warning("Zenodo data unavailable, trying fallbacks...")
    
    # 2. Try Materials Project (Secondary)
    mp_df = fetch_materials_project_data()
    if mp_df is not None:
        sources.append(mp_df)
        logger.info("Materials Project data loaded successfully")
    else:
        logger.warning("Materials Project data unavailable, trying fallbacks...")
    
    # 3. Fallback to synthetic if both external sources failed
    if not sources:
        logger.warning("All external sources unavailable. Using synthetic data.")
        return fetch_synthetic_data()
    
    # Merge all sources
    combined_df = pd.concat(sources, ignore_index=True)
    logger.info(f"Combined dataset has {len(combined_df)} records before deduplication")
    
    return combined_df

def run_ingestion_pipeline():
    """
    Execute the full data ingestion pipeline:
    1. Load and merge data
    2. Deduplicate
    3. Compute descriptors
    4. Save outputs
    """
    logger.info("Starting data ingestion pipeline...")
    
    # Ensure directories exist
    ensure_data_directories()
    
    # Step 1: Load and merge
    raw_df = load_and_merge_datasets()
    
    # Step 2: Deduplicate
    logger.info("Deduplicating compositions...")
    deduped_df, stats = deduplicate_compositions(raw_df)
    logger.info(f"Deduplication stats: {stats}")
    
    # Save raw data
    raw_output_path = RAW_PATH / "raw_compositions.csv"
    save_csv(deduped_df, raw_output_path)
    logger.info(f"Saved raw data to {raw_output_path}")
    
    # Step 3: Compute descriptors
    logger.info("Computing atomic descriptors...")
    engineered_df = apply_descriptors_to_dataframe(deduped_df)
    
    # Validate descriptor completeness
    total_descriptors = len([c for c in engineered_df.columns if c not in 
                            ['composition', 'phase', 'source', 'url', 'normalized_formula']])
    missing_count = engineered_df[engineered_df[engineered_df.columns[10:]].isnull().any(axis=1)].shape[0]
    completeness = 100.0 * (len(engineered_df) - missing_count) / len(engineered_df)
    logger.info(f"Descriptor completeness: {completeness:.2f}% ({total_descriptors} descriptors)")
    
    if completeness < 95:
        logger.warning(f"Descriptor completeness ({completeness:.2f}%) is below 95% threshold. Dropping incomplete rows.")
        # Drop rows with missing descriptors (columns starting after metadata)
        metadata_cols = ['composition', 'phase', 'source', 'url', 'normalized_formula']
        desc_cols = [c for c in engineered_df.columns if c not in metadata_cols]
        engineered_df = engineered_df.dropna(subset=desc_cols)
    
    # Step 4: Save processed dataset
    processed_output_path = PROCESSED_PATH / "engineered_dataset.csv"
    save_csv(engineered_df, processed_output_path)
    logger.info(f"Saved processed dataset to {processed_output_path}")
    
    # Step 5: Update provenance
    provenance = {
        "sources": [
            {
                "name": "Zenodo DOI",
                "doi": ZENODO_DOI,
                "url": ZENODO_API_URL,
                "status": "loaded" if "Zenodo" in stats.get('source_counts', {}) else "unavailable"
            },
            {
                "name": "Materials Project API",
                "url": f"{MP_API_BASE}/{MP_VERSION}",
                "status": "loaded" if "materials_project" in stats.get('source_counts', {}) else "unavailable"
            },
            {
                "name": "Synthetic Fallback",
                "url": "synthetic://fallback",
                "status": "used" if "synthetic_fallback" in stats.get('source_counts', {}) else "not_used"
            }
        ],
        "record_counts": {
            "raw": len(raw_df),
            "deduplicated": len(deduped_df),
            "processed": len(engineered_df)
        },
        "descriptor_completeness": completeness,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    save_json(provenance, PROVENANCE_PATH)
    logger.info(f"Updated provenance at {PROVENANCE_PATH}")
    
    logger.info("Data ingestion pipeline completed successfully.")
    return engineered_df

if __name__ == "__main__":
    run_ingestion_pipeline()
