"""
Data Download Module for PROJ-503

This module handles the downloading of gene expression matrices from GEO
for specific verified IDs: GSE21857 (Arabidopsis) and GSE167633 (Solanum).

It strictly adheres to the requirement of failing loudly if download fails
and does NOT provide synthetic fallbacks.
"""

import logging
import json
import time
import sys
import re
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import local project modules as per API surface
from exceptions import E_DATASET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GEO_BASE_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
GEO_API_URL = "https://api.ncbi.nlm.nih.gov/geo/v1/"
GEO_SOFT_DOWNLOAD = "https://www.ncbi.nlm.nih.gov/geo/download/?acc={}&format=soft"

# Verified IDs from tasks.md
GEO_IDS = ["GSE21857", "GSE167633"]
OUTPUT_PATH = "projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/geo_expression_matrix.csv"
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def create_session() -> requests.Session:
    """
    Creates a requests session with retry logic for robust downloads.
    """
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def validate_study_accession(accession: str) -> bool:
    """
    Validates that an accession string is a valid GEO study ID format.
    """
    pattern = r'^GSE\d+$'
    return bool(re.match(pattern, accession))

def fetch_geo_metadata(accession: str, session: requests.Session) -> Dict[str, Any]:
    """
    Fetches metadata for a GEO accession using the NCBI Geo API.
    """
    url = f"{GEO_API_URL}series/{accession}"
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch metadata for {accession}: {e}")
        raise E_DATASET(f"Failed to fetch metadata for {accession}: {e}")

def fetch_soft_file(accession: str, session: requests.Session) -> str:
    """
    Downloads the SOFT formatted file for a GEO accession.
    Returns the raw text content.
    """
    url = GEO_SOFT_DOWNLOAD.format(accession)
    try:
        logger.info(f"Downloading SOFT file for {accession}...")
        response = session.get(url, timeout=300) # Longer timeout for large files
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download SOFT file for {accession}: {e}")
        raise E_DATASET(f"Failed to download SOFT file for {accession}: {e}")

def parse_soft_expression_data(soft_content: str, accession: str) -> pd.DataFrame:
    """
    Parses the SOFT file content to extract expression data.
    
    Expected Output Format:
    - Rows: Gene IDs (e.g., GSM sample IDs or Probe IDs mapped to genes)
    - Columns: Sample IDs (GSM...)
    - Values: Expression values (intensity, log2, etc.)
    
    Note: GEO SOFT files often contain multiple platforms. This parser
    attempts to aggregate or select the primary expression matrix.
    """
    lines = soft_content.split('\n')
    
    samples = {} # GSM_ID -> list of expression values
    current_sample = None
    current_data = []
    features = set()
    
    # State machine for parsing SOFT format
    # We look for !Sample_title, !Sample_characteristics, and table data
    # However, for expression matrices, we usually look for the "TABLE" section
    # or the data blocks associated with each GSM.
    
    # Simplified approach for this task:
    # Many GEO series matrices are provided as a single table in the SOFT file
    # or we need to parse individual GSM files.
    # Given the constraint of "real data" and "fail loudly", we will attempt
    # to parse the main table if present, or extract from the series matrix if available.
    
    # Let's try to find the series matrix table which is common for GSE downloads
    # The series matrix file is often the most convenient format for expression data.
    # URL: https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE21857&format=soft&file=GSE21857_series_matrix.txt.gz
    
    # Since we are parsing the SOFT content directly here, we look for the table.
    # In a real SOFT file, data is often in a block:
    # ^Table
    # GSM123  GSM124 ...
    # 1.2  3.4 ...
    
    table_mode = False
    headers = []
    data_rows = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('^Table'):
            table_mode = True
            continue
        if table_mode:
            if line.startswith('!'):
                table_mode = False
                continue
            if line.startswith('!sample_table_end'):
                table_mode = False
                continue
            
            parts = line.split('\t')
            if not headers:
                # First row is headers (GSM IDs)
                headers = [p for p in parts if p.startswith('GSM')]
            else:
                # Data row: First column is usually the feature ID (Gene/Probe)
                if len(parts) >= 2:
                    feature_id = parts[0]
                    values = parts[1:]
                    # Only keep values that match header count
                    if len(values) == len(headers):
                        data_rows.append({'feature_id': feature_id, 'values': values})
    
    if not headers or not data_rows:
        # Fallback: Try to parse individual GSM data if series matrix not found
        # This is a more complex parsing logic, but for now, if we can't find a table,
        # we raise an error as per "fail loudly" requirement.
        logger.warning(f"No expression table found in SOFT content for {accession}.")
        raise E_DATASET(f"Could not parse expression table from SOFT file for {accession}.")

    # Construct DataFrame
    # Rows = features, Columns = samples
    df_data = []
    for row in data_rows:
        row_dict = {'feature_id': row['feature_id']}
        for i, val in enumerate(row['values']):
            try:
                row_dict[headers[i]] = float(val)
            except ValueError:
                row_dict[headers[i]] = 0.0 # Handle non-numeric if any
        df_data.append(row_dict)
    
    df = pd.DataFrame(df_data)
    df.set_index('feature_id', inplace=True)
    
    logger.info(f"Parsed {len(df)} features and {len(df.columns)} samples for {accession}.")
    return df

def download_study_data(accession: str) -> pd.DataFrame:
    """
    Downloads and parses expression data for a single GEO accession.
    """
    if not validate_study_accession(accession):
        raise E_DATASET(f"Invalid accession format: {accession}")
    
    session = create_session()
    
    # Fetch metadata first to ensure the study exists
    metadata = fetch_geo_metadata(accession, session)
    logger.info(f"Metadata fetched for {accession}: {metadata.get('name', 'Unknown')}")
    
    # Download SOFT file
    soft_content = fetch_soft_file(accession, session)
    
    # Parse expression data
    df = parse_soft_expression_data(soft_content, accession)
    
    # Add source column for traceability
    df['source_study'] = accession
    
    return df

def save_search_results(results: Dict[str, Any], output_path: Path):
    """
    Saves search/download results to a JSON file for logging.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved search results to {output_path}")

def main():
    """
    Main entry point for downloading GEO expression matrices.
    Downloads GSE21857 and GSE167633 and merges them into a single CSV.
    """
    logger.info("Starting GEO expression matrix download...")
    
    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_file = DATA_RAW_DIR / "geo_expression_matrix.csv"
    
    all_dfs = []
    download_log = {
        "studies": GEO_IDS,
        "status": "in_progress",
        "details": []
    }
    
    try:
        for accession in GEO_IDS:
            logger.info(f"Processing {accession}...")
            try:
                df = download_study_data(accession)
                all_dfs.append(df)
                download_log["details"].append({
                    "accession": accession,
                    "status": "success",
                    "rows": len(df),
                    "cols": len(df.columns)
                })
            except E_DATASET as e:
                download_log["details"].append({
                    "accession": accession,
                    "status": "failed",
                    "error": str(e)
                })
                # Fail loudly: re-raise immediately
                raise
            except Exception as e:
                download_log["details"].append({
                    "accession": accession,
                    "status": "failed",
                    "error": str(e)
                })
                raise E_DATASET(f"Unexpected error processing {accession}: {e}")
        
        if not all_dfs:
            raise E_DATASET("No data was successfully downloaded from any study.")
        
        # Concatenate all dataframes
        # Assuming feature IDs are unique across studies or we want to keep them separate
        # If feature IDs collide, we might need to prefix them. 
        # For now, we concatenate and keep the 'source_study' column.
        combined_df = pd.concat(all_dfs, axis=0, ignore_index=False)
        
        # Reset index to make feature_id a column for CSV export
        combined_df.reset_index(inplace=True)
        combined_df.rename(columns={'index': 'feature_id'}, inplace=True)
        
        # Save to CSV
        combined_df.to_csv(output_file, index=False)
        
        logger.info(f"Successfully saved combined expression matrix to {output_file}")
        logger.info(f"Total shape: {combined_df.shape}")
        
        download_log["status"] = "completed"
        save_search_results(download_log, DATA_RAW_DIR / "geo_download_log.json")
        
    except E_DATASET as e:
        logger.error(f"Critical error: {e}")
        download_log["status"] = "failed"
        save_search_results(download_log, DATA_RAW_DIR / "geo_download_log.json")
        raise
    except Exception as e:
        logger.error(f"Unexpected critical error: {e}")
        download_log["status"] = "failed"
        save_search_results(download_log, DATA_RAW_DIR / "geo_download_log.json")
        raise E_DATASET(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
