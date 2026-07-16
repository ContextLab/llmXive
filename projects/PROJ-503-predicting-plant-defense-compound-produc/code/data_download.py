import logging
import json
import time
import sys
import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "logs" / "data_download.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create a requests session with standard headers and retry logic."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "llmXive-PlantDefense-Pipeline/1.0 (contact: research@llmxive.org)",
        "Accept": "application/json"
    })
    return session


def search_metabolomics_workbench(
    keywords: List[str],
    organism: str,
    study_type: str = "targeted"
) -> List[Dict[str, Any]]:
    """
    Search Metabolomics Workbench for defense-related metabolite experiments.
    
    Uses the public REST API to find studies matching herbivore stress,
    terpenoids, alkaloids, or phenylpropanoids in the specified organism.
    
    Args:
        keywords: List of search terms (e.g., "herbivore", "jasmonate")
        organism: Target organism (e.g., "Arabidopsis thaliana", "Solanum lycopersicum")
        study_type: Type of study ("targeted", "untargeted", "both")
        
    Returns:
        List of study metadata dictionaries containing 'study_id', 'title', 
        'organisms', 'study_type', and download URLs if available.
        
    Raises:
        RuntimeError: If the API is unreachable or returns an error.
    """
    session = create_session()
    base_url = "https://www.metabolomicsworkbench.org/rest/study/study_search"
    
    # Construct query parameters
    params = {
        "keyword": " OR ".join(keywords),
        "organism": organism,
        "study_type": study_type,
        "format": "json"
    }
    
    logger.info(f"Searching MW for {organism} with keywords: {keywords}")
    
    try:
        response = session.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "STUDIES" not in data:
            logger.warning("No studies found in response.")
            return []
        
        studies = data["STUDIES"]
        logger.info(f"Found {len(studies)} candidate studies.")
        
        # Filter for relevant studies (defense compounds)
        relevant_studies = []
        defense_terms = ["defense", "herbivore", "jasmonate", "salicylate", 
                       "terpenoid", "alkaloid", "phenylpropanoid", "secondary metabolite"]
        
        for study in studies:
            title = study.get("STUDY_TITLE", "").lower()
            abstract = study.get("ABSTRACT", "").lower() if study.get("ABSTRACT") else ""
            combined_text = f"{title} {abstract}"
            
            if any(term in combined_text for term in defense_terms):
                relevant_studies.append({
                    "study_id": study.get("STUDY_ID"),
                    "title": study.get("STUDY_TITLE"),
                    "organisms": study.get("ORGANISMS", []),
                    "study_type": study.get("STUDY_TYPE"),
                    "download_url": study.get("DOWNLOAD_URL")
                })
        
        return relevant_studies
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to search Metabolomics Workbench: {e}")
        raise RuntimeError(f"API request failed: {e}")


def validate_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate that studies have required metadata and download URLs.
    
    Args:
        studies: List of study metadata dictionaries.
        
    Returns:
        Filtered list of valid studies.
    """
    valid_studies = []
    for study in studies:
        if not study.get("study_id"):
            logger.warning(f"Skipping study with missing ID: {study}")
            continue
        if not study.get("download_url"):
            logger.warning(f"Skipping study {study.get('study_id')} without download URL")
            continue
        valid_studies.append(study)
    
    logger.info(f"Validated {len(valid_studies)} studies for download.")
    return valid_studies


def download_study_data(
    study_id: str,
    download_url: str,
    output_dir: Path
) -> Path:
    """
    Download metabolite data for a specific study.
    
    Args:
        study_id: Unique identifier for the study.
        download_url: URL to download the data.
        output_dir: Directory to save the downloaded file.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        RuntimeError: If download fails or file is empty.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"MW_{study_id}.zip"
    output_path = output_dir / filename
    
    logger.info(f"Downloading {download_url} to {output_path}")
    
    session = create_session()
    try:
        response = session.get(download_url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if output_path.stat().st_size == 0:
            raise RuntimeError(f"Downloaded file {output_path} is empty")
            
        logger.info(f"Successfully downloaded {output_path} ({output_path.stat().st_size} bytes)")
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed for {study_id}: {e}")
        raise RuntimeError(f"Download failed: {e}")


def save_search_results(
    studies: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save search results to a JSON file for downstream processing.
    
    Args:
        studies: List of study metadata dictionaries.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(studies, f, indent=2)
    logger.info(f"Saved search results to {output_path}")


def extract_metabolite_samples(study_path: Path) -> List[Dict[str, Any]]:
    """
    Extract sample-level metabolite data from a downloaded study archive.
    
    Note: This is a simplified implementation. Real Metabolomics Workbench
    archives often contain multiple CSV/TSV files with specific structures.
    This function assumes a standard 'METABOLITES.csv' or similar file exists.
    
    Args:
        study_path: Path to the downloaded study archive.
        
    Returns:
        List of sample dictionaries with metabolite concentrations.
        
    Raises:
        RuntimeError: If the archive cannot be processed or no data is found.
    """
    import zipfile
    import csv
    import pandas as pd
    
    if not study_path.exists():
        raise FileNotFoundError(f"Study file not found: {study_path}")
    
    samples = []
    
    try:
        with zipfile.ZipFile(study_path, 'r') as zip_ref:
            # Look for common data files
            possible_files = [f for f in zip_ref.namelist() 
                            if f.endswith('.csv') or f.endswith('.tsv')]
            
            if not possible_files:
                raise RuntimeError(f"No CSV/TSV files found in {study_path}")
            
            # Try to find the metabolite data file
            data_file = None
            for f in possible_files:
                if 'metabolite' in f.lower() or 'conc' in f.lower() or 'sample' in f.lower():
                    data_file = f
                    break
            
            if not data_file:
                # Fallback to first CSV
                data_file = possible_files[0]
                logger.warning(f"Using fallback data file: {data_file}")
            
            with zip_ref.open(data_file) as file:
                # Read as text
                import io
                content = file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(content))
                
                for row in reader:
                    # Normalize row keys (strip whitespace)
                    normalized_row = {k.strip(): v for k, v in row.items()}
                    samples.append(normalized_row)
                    
    except zipfile.BadZipFile:
        logger.error(f"Corrupted zip file: {study_path}")
        raise RuntimeError(f"Corrupted archive: {study_path}")
    except Exception as e:
        logger.error(f"Failed to extract samples from {study_path}: {e}")
        raise RuntimeError(f"Extraction failed: {e}")
    
    if not samples:
        raise RuntimeError(f"No metabolite samples found in {study_path}")
        
    logger.info(f"Extracted {len(samples)} samples from {study_path}")
    return samples


def main():
    """
    Main entry point for Metabolomics Workbench data retrieval.
    
    This function:
    1. Searches for relevant studies for Arabidopsis and Solanum
    2. Validates and downloads the studies
    3. Extracts sample-level metabolite data
    4. Saves the raw data to data/raw/
    """
    logger.info("Starting Metabolomics Workbench data retrieval...")
    
    # Define search parameters
    search_configs = [
        {
            "organism": "Arabidopsis thaliana",
            "keywords": ["herbivore", "jasmonate", "defense", "terpenoid"]
        },
        {
            "organism": "Solanum lycopersicum",
            "keywords": ["herbivore", "defense", "alkaloid", "phenylpropanoid"]
        },
        {
            "organism": "Solanum tuberosum",
            "keywords": ["herbivore", "defense", "glycoalkaloid"]
        }
    ]
    
    all_studies = []
    
    for config in search_configs:
        logger.info(f"Searching for {config['organism']}...")
        try:
            studies = search_metabolomics_workbench(
                keywords=config["keywords"],
                organism=config["organism"]
            )
            valid_studies = validate_studies(studies)
            all_studies.extend(valid_studies)
            
            # Download each study
            for study in valid_studies:
                try:
                    logger.info(f"Downloading study {study['study_id']}...")
                    study_path = download_study_data(
                        study_id=study["study_id"],
                        download_url=study["download_url"],
                        output_dir=DATA_RAW_DIR
                    )
                    
                    # Extract samples
                    samples = extract_metabolite_samples(study_path)
                    
                    # Save extracted samples as JSON for pairing step
                    samples_path = DATA_RAW_DIR / f"samples_{study['study_id']}.json"
                    with open(samples_path, "w") as f:
                        json.dump(samples, f, indent=2)
                    logger.info(f"Saved samples to {samples_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to process study {study['study_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Search failed for {config['organism']}: {e}")
    
    # Save all search results metadata
    search_results_path = DATA_RAW_DIR / "metabolomics_search_results.json"
    save_search_results(all_studies, search_results_path)
    
    logger.info(f"Completed. Found {len(all_studies)} valid studies.")
    return all_studies


if __name__ == "__main__":
    main()