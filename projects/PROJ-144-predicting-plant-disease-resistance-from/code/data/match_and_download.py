"""
T012c: Match resistance metadata and filter studies.
Implements filtering for studies containing pre-challenge/baseline profiles
and disease resistance/phenotype metadata.
"""
import os
import sys
import json
import glob
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import custom exceptions from the project's exceptions module
from utils.exceptions import DataAvailabilityError, DataFetchError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RESISTANCE_COLUMNS = [
    'phenotype', 'resistance_score', 'disease_status', 'challenge_outcome',
    'resistance', 'disease_severity', 'infection_status'
]
TEMPORAL_COLUMNS = [
    'timepoint', 'sample_date', 'collection_date', 'inoculation_date',
    'days_post_inoculation', 'dpi', 'pre_challenge', 'baseline'
]
RAW_DATA_DIR = Path('data/raw')
FILTERED_MANIFEST_PATH = RAW_DATA_DIR / 'filtered_study_manifest.json'
STUDY_MANIFEST_PATH = RAW_DATA_DIR / 'study_manifest.json'

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the study manifest from JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def fetch_phenotype_preview(study_id: str, download_url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a preview of the phenotype data to check for required columns.
    Returns the first row as a dictionary or None if fetch fails.
    """
    try:
        # Attempt to fetch the phenotype file directly if URL is provided
        # If download_url is a zip, we might need to handle it differently
        # For now, assume direct CSV access or handle zip extraction
        logger.info(f"Fetching phenotype preview for study {study_id} from {download_url}")
        
        # Try to get the phenotype file URL (often provided in study metadata)
        # If download_url points to a zip, we need to extract it first
        # This is a simplified approach - in production, we'd handle zip extraction
        
        # Attempt to construct phenotype URL if download_url is a study page
        if 'download_url' in download_url or 'study.php' in download_url:
            # Try to access the phenotype file directly
            # This assumes the API provides direct links
            response = requests.get(download_url, timeout=30)
            if response.status_code == 200:
                # Parse CSV from response content
                import io
                import pandas as pd
                df = pd.read_csv(io.StringIO(response.text))
                return df.head(1).to_dict(orient='records')[0] if not df.empty else None
        else:
            # Try direct access
            response = requests.get(download_url, timeout=30)
            if response.status_code == 200:
                import io
                import pandas as pd
                df = pd.read_csv(io.StringIO(response.text))
                return df.head(1).to_dict(orient='records')[0] if not df.empty else None
                
        return None
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch phenotype preview for {study_id}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error processing phenotype data for {study_id}: {e}")
        return None

def check_metadata_in_preview(phenotype_preview: Dict[str, Any], required_columns: List[str]) -> bool:
    """Check if any of the required columns exist in the phenotype preview."""
    if not phenotype_preview:
        return False
    return any(col.lower() in [k.lower() for k in phenotype_preview.keys()] for col in required_columns)

def has_resistance_metadata(phenotype_preview: Dict[str, Any]) -> bool:
    """Check if the phenotype data contains resistance-related columns."""
    return check_metadata_in_preview(phenotype_preview, RESISTANCE_COLUMNS)

def has_temporal_metadata(phenotype_preview: Dict[str, Any]) -> bool:
    """Check if the phenotype data contains temporal/baseline columns."""
    return check_metadata_in_preview(phenotype_preview, TEMPORAL_COLUMNS)

def download_study_files(study_id: str, download_url: str, output_dir: Path) -> bool:
    """
    Download study files (intensity and phenotype) from the provided URL.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info(f"Downloading study {study_id} from {download_url}")
        
        # Attempt to download the study data
        response = requests.get(download_url, timeout=60)
        if response.status_code != 200:
            logger.error(f"Failed to download {study_id}: HTTP {response.status_code}")
            return False
        
        # Save the raw data
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle different file formats (CSV, ZIP, etc.)
        if 'text/csv' in response.headers.get('Content-Type', ''):
            # Direct CSV download
            file_path = output_dir / f"{study_id}_raw_intensity.csv"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Saved intensity data to {file_path}")
            
            # Try to get phenotype data (often in a separate file or same file)
            # This is a simplified approach
            phenotype_path = output_dir / f"{study_id}_phenotype.csv"
            # In a real implementation, we'd extract phenotype from the response
            # or download it separately
            return True
        elif 'application/zip' in response.headers.get('Content-Type', ''):
            # ZIP download - extract files
            import zipfile
            import io
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(output_dir)
                logger.info(f"Extracted study {study_id} files to {output_dir}")
            
            # Check if phenotype file was extracted
            phenotype_files = list(output_dir.glob(f"{study_id}_phenotype*.csv"))
            if not phenotype_files:
                logger.warning(f"No phenotype file found for {study_id} after extraction")
                return False
            
            return True
        else:
            # Unknown format - save as-is
            file_path = output_dir / f"{study_id}_raw_data.bin"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.warning(f"Saved unknown format data to {file_path}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Network error downloading {study_id}: {e}")
        raise DataFetchError(f"Failed to download study {study_id}: {e}")
    except Exception as e:
        logger.error(f"Error processing download for {study_id}: {e}")
        raise DataFetchError(f"Error processing download for {study_id}: {e}")

def compute_checksums(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def filter_studies_by_metadata(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter studies that have both resistance metadata and temporal/baseline metadata.
    """
    valid_studies = []
    missing_resistance = []
    missing_temporal = []
    
    for study in studies:
        study_id = study.get('study_id', study.get('STUDY_ID', ''))
        download_url = study.get('download_url', study.get('DOWNLOAD_URL', ''))
        
        if not study_id or not download_url:
            logger.warning(f"Skipping study with missing ID or URL: {study}")
            continue
        
        # Check if phenotype file already exists locally (from T012b)
        phenotype_path = RAW_DATA_DIR / f"{study_id}_phenotype.csv"
        intensity_path = RAW_DATA_DIR / f"{study_id}_raw_intensity.csv"
        
        if phenotype_path.exists():
            # Load and check local phenotype file
            import pandas as pd
            try:
                df = pd.read_csv(phenotype_path)
                columns = [col.lower() for col in df.columns]
                
                has_resistance = any(col in columns for col in [c.lower() for c in RESISTANCE_COLUMNS])
                has_temporal = any(col in columns for col in [c.lower() for c in TEMPORAL_COLUMNS])
                
                if has_resistance and has_temporal:
                    valid_studies.append(study)
                    logger.info(f"Study {study_id} has both resistance and temporal metadata (local)")
                else:
                    if not has_resistance:
                        missing_resistance.append(study_id)
                    if not has_temporal:
                        missing_temporal.append(study_id)
                    logger.info(f"Study {study_id} missing required metadata: resistance={has_resistance}, temporal={has_temporal}")
            except Exception as e:
                logger.error(f"Error reading phenotype file for {study_id}: {e}")
                continue
        else:
            # Fetch phenotype preview from API
            phenotype_preview = fetch_phenotype_preview(study_id, download_url)
            
            if not phenotype_preview:
                logger.warning(f"Could not fetch phenotype preview for {study_id}, skipping")
                continue
            
            has_resistance = has_resistance_metadata(phenotype_preview)
            has_temporal = has_temporal_metadata(phenotype_preview)
            
            if has_resistance and has_temporal:
                valid_studies.append(study)
                logger.info(f"Study {study_id} has both resistance and temporal metadata (API)")
            else:
                if not has_resistance:
                    missing_resistance.append(study_id)
                if not has_temporal:
                    missing_temporal.append(study_id)
                logger.info(f"Study {study_id} missing required metadata: resistance={has_resistance}, temporal={has_temporal}")
    
    logger.info(f"Filtered studies: {len(valid_studies)} valid, {len(missing_resistance)} missing resistance, {len(missing_temporal)} missing temporal")
    
    if not valid_studies:
        raise DataAvailabilityError(
            "No studies found with both resistance metadata and temporal/baseline metadata. "
            "Pipeline cannot proceed without resistance data."
        )
    
    return valid_studies

def main():
    """Main entry point for T012c: Match resistance metadata and filter studies."""
    logger.info("Starting T012c: Match resistance metadata and filter studies")
    
    # Ensure raw data directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load study manifest
    try:
        studies = load_manifest(STUDY_MANIFEST_PATH)
        logger.info(f"Loaded {len(studies)} studies from manifest")
    except FileNotFoundError as e:
        logger.error(f"Study manifest not found: {e}")
        logger.info("Please run T012a and T012a-ser first to generate the study manifest.")
        sys.exit(1)
    
    # Filter studies by metadata requirements
    try:
        valid_studies = filter_studies_by_metadata(studies)
        logger.info(f"Found {len(valid_studies)} studies with required metadata")
    except DataAvailabilityError as e:
        logger.error(f"Data availability error: {e}")
        raise
    
    # Create filtered manifest
    filtered_manifest = {
        'filtered_studies': valid_studies,
        'filter_criteria': {
            'resistance_columns': RESISTANCE_COLUMNS,
            'temporal_columns': TEMPORAL_COLUMNS
        },
        'timestamp': str(pd.Timestamp.now()) if 'pd' in dir() else str(__import__('datetime').datetime.now())
    }
    
    # Save filtered manifest
    with open(FILTERED_MANIFEST_PATH, 'w') as f:
        json.dump(filtered_manifest, f, indent=2)
    
    logger.info(f"Saved filtered manifest to {FILTERED_MANIFEST_PATH}")
    logger.info("T012c completed successfully")
    
    return filtered_manifest

if __name__ == '__main__':
    main()
