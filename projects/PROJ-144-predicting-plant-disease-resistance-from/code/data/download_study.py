"""
Download Phenotype and Intensity data for discovered studies.
Implements Task T012b.
"""
import os
import sys
import json
import hashlib
import requests
import zipfile
import io
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MW_BASE_URL = "https://www.metabolomicsworkbench.org"
STUDY_URL_TEMPLATE = f"{MW_BASE_URL}/data/study.php?STUDY_ID={study_id}"
DOWNLOAD_URL_TEMPLATE = f"{MW_BASE_URL}/data/study_files.php?STUDY_ID={study_id}"

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class BatchCorrectionFailureError(Exception):
    """Raised when ComBat fails to converge."""
    pass

class TemporalVerificationError(Exception):
    """Raised when no studies are verified for temporal metadata."""
    pass

class DataUnavailableError(Exception):
    """Raised when required data files are missing."""
    pass

def get_study_download_url(study_id: str) -> Optional[str]:
    """
    Fetch the download URL for a specific study from Metabolomics Workbench.
    """
    url = f"{MW_BASE_URL}/data/study_files.php?STUDY_ID={study_id}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # The response might be HTML or JSON depending on the endpoint behavior
            # We look for the actual download link in the response text
            # Typically, the study_files.php page lists files. We need to find the direct download link.
            # For robustness, we assume the API returns a JSON or we parse the HTML for the link.
            # However, MW often requires a specific request or returns a page with links.
            # Let's try to parse the response for a direct download link pattern.
            if "application/json" in response.headers.get("Content-Type", ""):
                data = response.json()
                if isinstance(data, dict) and "download_url" in data:
                    return data["download_url"]
            else:
                # Fallback: try to find a link in HTML if JSON fails
                # This is a heuristic; MW API structure might vary
                if "download.php" in response.text:
                    # Extract the first download.php link
                    import re
                    match = re.search(r'href="([^"]*download\.php[^"]*)"', response.text)
                    if match:
                        return match.group(1)
        else:
            logger.warning(f"Failed to fetch download URL for {study_id}: HTTP {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Network error fetching download URL for {study_id}: {e}")
    
    # If we can't get a direct URL from the API, we might need to construct it
    # MW typically has a pattern: https://www.metabolomicsworkbench.org/data/STUDYID_XXX.zip
    # But we should rely on the API first.
    return None

def download_study_data(download_url: str, study_id: str, output_dir: Path) -> Dict[str, str]:
    """
    Download the study data (zip file) from the provided URL.
    Returns a dictionary of downloaded file paths.
    """
    if not download_url.startswith("http"):
        download_url = f"{MW_BASE_URL}/{download_url}" if download_url.startswith("/") else download_url

    logger.info(f"Downloading data for {study_id} from {download_url}")
    try:
        response = requests.get(download_url, timeout=300, stream=True)
        response.raise_for_status()
        
        # Save the zip file
        zip_filename = f"{study_id}_data.zip"
        zip_path = output_dir / zip_filename
        
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded zip file to {zip_path}")
        return {"zip": str(zip_path)}
    except requests.RequestException as e:
        raise DataFetchError(f"Failed to download data for {study_id}: {e}")

def compute_checksums(file_paths: Dict[str, str]) -> Dict[str, str]:
    """
    Compute SHA256 checksums for downloaded files.
    """
    checksums = {}
    for key, path in file_paths.items():
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        checksums[key] = sha256_hash.hexdigest()
    return checksums

def extract_and_save_files(study_id: str, zip_path: str, output_dir: Path) -> List[str]:
    """
    Extract the zip file and save phenotype and intensity CSVs to the output directory.
    Returns a list of saved file paths.
    """
    saved_files = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in the zip
            file_list = zip_ref.namelist()
            logger.info(f"Found {len(file_list)} files in {zip_path}")
            
            for file_name in file_list:
                # Determine if it's phenotype or intensity data
                # MW naming conventions vary, but often contain 'phenotype' or 'data'
                # We'll look for CSVs and try to classify them
                if file_name.endswith('.csv'):
                    # Extract to a temporary location first
                    with zip_ref.open(file_name) as source, open(output_dir / file_name, "wb") as target:
                        target.write(source.read())
                    
                    saved_files.append(str(output_dir / file_name))
                    logger.info(f"Extracted {file_name} to {output_dir / file_name}")
                    
            # If no CSVs were found, log a warning
            if not saved_files:
                logger.warning(f"No CSV files found in {zip_path} for study {study_id}")
                
    except zipfile.BadZipFile:
        raise DataFetchError(f"Corrupted zip file for {study_id}: {zip_path}")
    except Exception as e:
        raise DataFetchError(f"Failed to extract zip for {study_id}: {e}")
        
    return saved_files

def identify_phenotype_and_intensity_files(saved_files: List[str]) -> Dict[str, Optional[str]]:
    """
    Identify which files are phenotype and which are intensity data.
    Returns a dict with keys 'phenotype' and 'intensity'.
    """
    phenotype_file = None
    intensity_file = None
    
    for file_path in saved_files:
        file_name = os.path.basename(file_path).lower()
        
        # Heuristics for identifying file types
        if 'phenotype' in file_name or 'meta' in file_name:
            phenotype_file = file_path
        elif 'data' in file_name or 'intensity' in file_name or 'abundance' in file_name:
            # Avoid double-counting if it's also a phenotype file
            if 'phenotype' not in file_name:
                intensity_file = file_path
        else:
            # Fallback: if we have only two CSVs, assume first is phenotype, second is intensity
            # This is a last resort
            if phenotype_file is None:
                phenotype_file = file_path
            elif intensity_file is None:
                intensity_file = file_path
                
    return {
        'phenotype': phenotype_file,
        'intensity': intensity_file
    }

def download_study(study_id: str, output_dir: Path) -> Dict[str, str]:
    """
    Main function to download and extract study data.
    Returns a dict with paths to phenotype and intensity files.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Get download URL
    download_url = get_study_download_url(study_id)
    if not download_url:
        # Fallback: Try to construct a likely URL
        # MW often has a pattern: https://www.metabolomicsworkbench.org/data/STUDYID_XXX.zip
        # But we should try the API first.
        # If API fails, we might need to manually specify or skip.
        raise DataFetchError(f"Could not determine download URL for study {study_id}")
    
    # Step 2: Download the zip file
    file_paths = download_study_data(download_url, study_id, output_dir)
    
    # Step 3: Extract files
    saved_files = extract_and_save_files(study_id, file_paths['zip'], output_dir)
    
    # Step 4: Identify phenotype and intensity files
    identified_files = identify_phenotype_and_intensity_files(saved_files)
    
    # Step 5: Rename files to standard naming convention
    final_paths = {}
    if identified_files['phenotype']:
        old_path = identified_files['phenotype']
        new_name = f"{study_id}_phenotype.csv"
        new_path = output_dir / new_name
        os.rename(old_path, new_path)
        final_paths['phenotype'] = str(new_path)
        logger.info(f"Renamed phenotype file to {new_name}")
        
    if identified_files['intensity']:
        old_path = identified_files['intensity']
        new_name = f"{study_id}_raw_intensity.csv"
        new_path = output_dir / new_name
        os.rename(old_path, new_path)
        final_paths['intensity'] = str(new_path)
        logger.info(f"Renamed intensity file to {new_name}")
        
    return final_paths

def main():
    """
    Main entry point for T012b: Download Phenotype and Intensity data.
    """
    # Load the study manifest
    manifest_path = Path("data/raw/study_manifest.json")
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        logger.error("Please run T012a and T012a-ser first to generate the study manifest.")
        sys.exit(1)
        
    with open(manifest_path, 'r') as f:
        studies = json.load(f)
        
    logger.info(f"Found {len(studies)} studies in manifest")
    
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_studies = []
    failed_studies = []
    
    for study in studies:
        study_id = study.get('study_id')
        if not study_id:
            logger.warning(f"Skipping study with missing ID: {study}")
            continue
            
        logger.info(f"Processing study: {study_id}")
        try:
            final_paths = download_study(study_id, output_dir)
            
            if 'phenotype' in final_paths and 'intensity' in final_paths:
                # Verify files are non-empty
                if os.path.getsize(final_paths['phenotype']) == 0:
                    raise DataFetchError(f"Phenotype file is empty for {study_id}")
                if os.path.getsize(final_paths['intensity']) == 0:
                    raise DataFetchError(f"Intensity file is empty for {study_id}")
                
                downloaded_studies.append({
                    'study_id': study_id,
                    'phenotype_file': final_paths['phenotype'],
                    'intensity_file': final_paths['intensity']
                })
                logger.info(f"Successfully downloaded {study_id}")
            else:
                logger.warning(f"Failed to identify both phenotype and intensity files for {study_id}")
                failed_studies.append(study_id)
                
        except DataFetchError as e:
            logger.error(f"Failed to download {study_id}: {e}")
            failed_studies.append(study_id)
        except Exception as e:
            logger.error(f"Unexpected error downloading {study_id}: {e}")
            failed_studies.append(study_id)
    
    # Log summary
    logger.info(f"Downloaded {len(downloaded_studies)} studies successfully")
    logger.info(f"Failed to download {len(failed_studies)} studies: {failed_studies}")
    
    # Write a summary log
    log_path = output_dir / "download_log.json"
    with open(log_path, 'w') as f:
        json.dump({
            'downloaded': downloaded_studies,
            'failed': failed_studies,
            'total_attempted': len(studies)
        }, f, indent=2)
        
    if failed_studies:
        logger.warning(f"Some studies failed to download. Check {log_path} for details.")
        # Do not exit with error code to allow partial progress
    else:
        logger.info("All studies downloaded successfully")

if __name__ == "__main__":
    main()
