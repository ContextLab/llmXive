import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import requests
import json
import pandas as pd

# Import from existing project modules
from utils.config import get_env_var
from utils.io import setup_logging, fail_loud_loader, compute_sha256
from features.dataset_models import validate_entry_to_model, DataSource, AlloyFamily

# Ensure logging is configured
logger = setup_logging()

# Constants
MP_API_KEY = get_env_var("MP_API_KEY")
AFLOW_API_KEY = get_env_var("AFLOW_API_KEY")
ZENODO_ID = get_env_var("ZENODO_ID", default="1234567")

def fetch_materials_project_data() -> pd.DataFrame:
    """Fetch data from Materials Project API."""
    if not MP_API_KEY:
        logger.warning("MP_API_KEY not set, skipping Materials Project fetch.")
        return pd.DataFrame()
    
    # Placeholder for actual API implementation
    # In a real scenario, this would query the MP API
    # For now, we return an empty DataFrame to simulate the "no data" scenario
    return pd.DataFrame()

def fetch_aflow_data() -> pd.DataFrame:
    """Fetch data from AFLOWlib API."""
    if not AFLOW_API_KEY:
        logger.warning("AFLOW_API_KEY not set, skipping AFLOWlib fetch.")
        return pd.DataFrame()
    
    # Placeholder for actual API implementation
    return pd.DataFrame()

def fetch_zenodo_fallback() -> pd.DataFrame:
    """Fetch fallback data from Zenodo."""
    logger.info(f"Attempting to fetch fallback data from Zenodo ID: {ZENODO_ID}")
    # Placeholder for actual Zenodo fetch
    return pd.DataFrame()

def fetch_data() -> Tuple[pd.DataFrame, str]:
    """
    Main data fetching function.
    Returns a tuple of (DataFrame, source_name).
    """
    sources = [
        ("Materials Project", fetch_materials_project_data),
        ("AFLOWlib", fetch_aflow_data),
        ("Zenodo Fallback", fetch_zenodo_fallback)
    ]
    
    for source_name, fetch_func in sources:
        try:
            logger.info(f"Fetching data from {source_name}...")
            df = fetch_func()
            if not df.empty:
                logger.info(f"Successfully fetched {len(df)} entries from {source_name}.")
                return df, source_name
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {str(e)}")
            continue
    
    # If all sources fail
    raise RuntimeError("All data sources failed to return valid data.")

def main():
    """
    Main entry point for the data ingestion pipeline.
    Implements 'Phase 0.5: No Data Termination' logic.
    """
    logger.info("Starting data ingestion pipeline (T020: Phase 0.5 No Data Termination)")
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    metrics_path = results_dir / "metrics.json"
    
    try:
        # Attempt to fetch data
        df, source = fetch_data()
        
        # Check if we have any data
        n = len(df)
        logger.info(f"Total entries fetched: {n}")
        
        if n == 0:
            # Phase 0.5: No Data Termination
            logger.error("No valid metallic glass entries found.")
            
            # Generate metrics.json with no_data status
            metrics = {
                "status": "no_data",
                "source": "none",
                "count": 0
            }
            
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            logger.info(f"Metrics written to {metrics_path}")
            logger.info("Exiting cleanly with code 0 (Phase 0.5 termination)")
            sys.exit(0)
        
        # If we have data, continue with normal flow
        logger.info(f"Data fetched successfully from {source}. Proceeding with pipeline.")
        # Note: In a full implementation, we would save this data here
        # For T020, we just ensure the no-data path works correctly
        
    except RuntimeError as e:
        # All sources failed
        logger.error(f"Data fetch failed: {str(e)}")
        
        # Generate metrics.json with no_data status
        metrics = {
            "status": "no_data",
            "source": "all_failed",
            "count": 0,
            "error": str(e)
        }
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics written to {metrics_path}")
        logger.info("Exiting cleanly with code 0 (Phase 0.5 termination)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error during data ingestion: {str(e)}")
        raise

if __name__ == "__main__":
    main()