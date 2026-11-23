"""
Download metabolite data from Metabolomics Workbench for specific verified ID: ST002565.
Output: data/raw/metabolite_matrix.csv.
MUST fail loudly if download fails; NO synthetic fallback.
"""
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import pandas as pd
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/metabolomics_download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
METABOLOMICS_WORKBENCH_API = "https://www.metabolomicsworkbench.org/rest"
STUDY_ID = "ST002565"
OUTPUT_PATH = Path("projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw/metabolite_matrix.csv")
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

class DownloadError(Exception):
    """Custom exception for download failures."""
    pass

def create_session() -> requests.Session:
    """Create a requests session with headers."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'llmXive-Research-Pipeline/1.0',
        'Accept': 'application/json'
    })
    return session

def fetch_study_metadata(session: requests.Session, study_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a specific study from Metabolomics Workbench.
    https://www.metabolomicsworkbench.org/rest/study/study_id/ST002565
    """
    url = f"{METABOLOMICS_WORKBENCH_API}/study/study_id/{study_id}"
    logger.info(f"Fetching metadata for study {study_id} from {url}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise DownloadError(f"Failed to fetch study metadata after {MAX_RETRIES} attempts: {e}")

def fetch_analysis_metadata(session: requests.Session, study_id: str) -> List[Dict[str, Any]]:
    """
    Fetch analysis metadata for a study.
    https://www.metabolomicsworkbench.org/rest/analysis/study_id/ST002565
    """
    url = f"{METABOLOMICS_WORKBENCH_API}/analysis/study_id/{study_id}"
    logger.info(f"Fetching analysis metadata for study {study_id}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise DownloadError(f"Failed to fetch analysis metadata after {MAX_RETRIES} attempts: {e}")

def fetch_sample_metadata(session: requests.Session, study_id: str) -> List[Dict[str, Any]]:
    """
    Fetch sample metadata for a study.
    https://www.metabolomicsworkbench.org/rest/sample/study_id/ST002565
    """
    url = f"{METABOLOMICS_WORKBENCH_API}/sample/study_id/{study_id}"
    logger.info(f"Fetching sample metadata for study {study_id}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise DownloadError(f"Failed to fetch sample metadata after {MAX_RETRIES} attempts: {e}")

def fetch_metabolite_data(session: requests.Session, study_id: str, analysis_id: str) -> Dict[str, Any]:
    """
    Fetch metabolite data for a specific analysis.
    https://www.metabolomicsworkbench.org/rest/analysis_data/analysis_id/{analysis_id}
    """
    url = f"{METABOLOMICS_WORKBENCH_API}/analysis_data/analysis_id/{analysis_id}"
    logger.info(f"Fetching metabolite data for analysis {analysis_id}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=60)  # Longer timeout for data download
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise DownloadError(f"Failed to fetch metabolite data after {MAX_RETRIES} attempts: {e}")

def build_metabolite_matrix(
    metabolite_data: Dict[str, Any],
    sample_metadata: List[Dict[str, Any]],
    analysis_metadata: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Build a wide-format metabolite matrix from the downloaded data.
    Rows = metabolites, Columns = samples (biosample_id), Values = concentrations.
    """
    logger.info("Building metabolite matrix from downloaded data")
    
    # Extract data from the API response
    # The structure is typically: { "data": { "metabolites": [...], "samples": [...], "values": [[...]] } }
    if "data" not in metabolite_data or "metabolites" not in metabolite_data["data"]:
        raise DownloadError("Invalid metabolite data structure: missing 'data.metabolites'")
    
    metabolites = metabolite_data["data"]["metabolites"]
    samples_in_data = metabolite_data["data"].get("samples", [])
    values = metabolite_data["data"].get("values", [])
    
    if not values:
        raise DownloadError("No metabolite values found in the downloaded data")
    
    # Create a mapping from sample_id to biosample_id using sample metadata
    # We need to match the sample IDs in the metabolite data with the biosample_ids
    sample_id_to_biosample_id = {}
    for sample in sample_metadata:
        sample_id = sample.get("sample_id") or sample.get("sample_name")
        biosample_id = sample.get("biosample_id") or sample.get("sample_name")
        if sample_id:
            sample_id_to_biosample_id[sample_id] = biosample_id
    
    # If sample metadata doesn't have biosample_id, try to use sample names directly
    if not sample_id_to_biosample_id:
        logger.warning("No biosample_id found in sample metadata, using sample names as identifiers")
        for sample in sample_metadata:
            sample_name = sample.get("sample_name") or sample.get("sample_id")
            if sample_name:
                sample_id_to_biosample_id[sample_name] = sample_name
    
    # Build the matrix
    # Rows: metabolites, Columns: biosample_ids
    matrix_data = {}
    
    # Get metabolite identifiers
    metabolite_ids = []
    for metab in metabolites:
        metab_id = metab.get("metabolite_id") or metab.get("metabolite_name") or metab.get("name")
        if metab_id:
            metabolite_ids.append(metab_id)
    
    # Map sample IDs from the data to biosample IDs
    biosample_ids = []
    for sample_id in samples_in_data:
        biosample_id = sample_id_to_biosample_id.get(sample_id, sample_id)
        biosample_ids.append(biosample_id)
    
    # Create the matrix
    for i, metab_id in enumerate(metabolite_ids):
        row_values = []
        if i < len(values):
            row_values = values[i]
        else:
            # Pad with NaN if values row is missing
            row_values = [float('nan')] * len(biosample_ids)
        
        matrix_data[metab_id] = dict(zip(biosample_ids, row_values))
    
    # Convert to DataFrame
    df = pd.DataFrame(matrix_data).T
    df.index.name = 'metabolite_id'
    df.columns.name = 'biosample_id'
    
    logger.info(f"Created metabolite matrix with {len(df)} metabolites and {len(df.columns)} samples")
    return df

def download_study_data(study_id: str, output_path: Path) -> None:
    """
    Main function to download metabolite data for a study and save to CSV.
    """
    logger.info(f"Starting download for study {study_id}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    session = create_session()
    
    try:
        # 1. Fetch study metadata
        study_metadata = fetch_study_metadata(session, study_id)
        logger.info(f"Study metadata fetched: {study_metadata.get('title', 'N/A')}")
        
        # 2. Fetch analysis metadata
        analysis_list = fetch_analysis_metadata(session, study_id)
        if not analysis_list:
            raise DownloadError(f"No analyses found for study {study_id}")
        
        # Use the first analysis (or filter for the one with metabolite data)
        # In practice, we might want to check which analysis has the data we need
        analysis_id = analysis_list[0].get("analysis_id")
        if not analysis_id:
            raise DownloadError("No valid analysis_id found in analysis metadata")
        
        logger.info(f"Using analysis {analysis_id}")
        
        # 3. Fetch sample metadata
        sample_metadata = fetch_sample_metadata(session, study_id)
        logger.info(f"Fetched {len(sample_metadata)} sample metadata entries")
        
        # 4. Fetch metabolite data
        metabolite_data = fetch_metabolite_data(session, study_id, analysis_id)
        logger.info("Metabolite data fetched successfully")
        
        # 5. Build and save the matrix
        matrix_df = build_metabolite_matrix(metabolite_data, sample_metadata, analysis_list)
        matrix_df.to_csv(output_path, index=True)
        
        logger.info(f"Successfully saved metabolite matrix to {output_path}")
        logger.info(f"Matrix shape: {matrix_df.shape}")
        
    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise DownloadError(f"Unexpected error: {e}")

def main():
    """Entry point for the script."""
    logger.info("Starting metabolite data download for T002")
    
    try:
        download_study_data(STUDY_ID, OUTPUT_PATH)
        logger.info("T002 completed successfully")
    except Exception as e:
        logger.error(f"T002 failed: {e}")
        # Re-raise to ensure the task is marked as failed
        raise

if __name__ == "__main__":
    main()
