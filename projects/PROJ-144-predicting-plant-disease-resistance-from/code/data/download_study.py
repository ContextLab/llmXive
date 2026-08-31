import os
import sys
import json
import hashlib
import requests
import zipfile
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Ensure we can import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.exceptions import DataUnavailableError
from utils.io import compute_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")

def get_study_download_url(manifest_path: Path) -> List[Dict[str, Any]]:
    """
    Load the study manifest and return download URLs.
    """
    if not manifest_path.exists():
        raise DataUnavailableError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        studies = json.load(f)
    
    if not isinstance(studies, list) or len(studies) == 0:
        raise DataUnavailableError("Manifest is empty or invalid format.")
    
    return studies

def download_study_data(url: str, output_dir: Path, study_id: str) -> Tuple[str, str]:
    """
    Download raw intensity and phenotype data from the provided URL.
    The URL is expected to point to a zip file or a direct CSV.
    Returns the paths to the saved intensity and phenotype files.
    """
    logger.info(f"Downloading study data from: {url}")
    
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to download data from {url}: {e}")
        raise RuntimeError(f"Download failed: {e}")

    # Determine if it's a zip or direct CSV
    content_type = response.headers.get('Content-Type', '')
    is_zip = 'application/zip' in content_type or url.endswith('.zip')
    
    intensity_path = output_dir / f"{study_id}_raw_intensity.csv"
    phenotype_path = output_dir / f"{study_id}_phenotype.csv"

    if is_zip:
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Try to find CSV files inside
                csv_files = [f for f in z.namelist() if f.endswith('.csv')]
                
                if not csv_files:
                    raise ValueError(f"No CSV files found in zip archive for {study_id}")
                
                # Heuristic: usually one file is intensity, one is phenotype
                # or we might need to inspect filenames. 
                # For now, assume the first two distinct CSVs or specific names.
                # If there's only one, we might need to split or it's an error.
                
                # Let's try to identify based on common naming conventions if possible,
                # otherwise just take the first two.
                # If the zip contains a single large CSV with both, we can't separate without schema.
                # Assuming the manifest logic (T012a) ensures we get a link to a zip containing distinct files.
                
                if len(csv_files) < 2:
                    # Fallback: if only 1 file, assume it contains both or we need to check content
                    # For this implementation, we raise an error if we can't separate them clearly
                    # unless the filename indicates otherwise.
                    raise ValueError(f"Expected at least 2 CSV files in zip, found {len(csv_files)}")
                
                # Simple heuristic: sort names, assume first is intensity, second is phenotype
                # or look for keywords
                sorted_files = sorted(csv_files)
                intensity_file = None
                phenotype_file = None
                
                for f in sorted_files:
                    fname_lower = f.lower()
                    if 'intensity' in fname_lower or 'matrix' in fname_lower:
                        intensity_file = f
                    elif 'phenotype' in fname_lower or 'label' in fname_lower or 'meta' in fname_lower:
                        phenotype_file = f
                
                if not intensity_file:
                    intensity_file = sorted_files[0]
                if not phenotype_file:
                    phenotype_file = sorted_files[1] if len(sorted_files) > 1 else sorted_files[0]
                
                if intensity_file == phenotype_file and len(sorted_files) > 1:
                    phenotype_file = sorted_files[1]

                with z.open(intensity_file) as src:
                    with open(intensity_path, 'wb') as dst:
                        dst.write(src.read())
                
                with z.open(phenotype_file) as src:
                    with open(phenotype_path, 'wb') as dst:
                        dst.write(src.read())
                        
        except zipfile.BadZipFile:
            raise ValueError("Downloaded file is not a valid ZIP archive.")
    else:
        # Assume direct CSV download - this is rare for bulk data but possible
        # We might need to split or assume the manifest provides separate URLs.
        # If the manifest provides one URL for a single CSV, we can't split it here.
        # Assuming the task context implies a zip or a specific endpoint structure.
        # If it's a single CSV, we'll save it as intensity and raise an error for missing phenotype.
        with open(intensity_path, 'wb') as f:
            f.write(response.content)
        
        # If it's not a zip, we can't reliably extract a separate phenotype file
        # without knowing the structure. We'll raise a specific error if phenotype is missing.
        # However, for the sake of the pipeline, we assume the manifest logic (T012a) 
        # ensures we have a valid source. If T012a returns a zip, this block handles it.
        # If T012a returns a direct CSV, this is a limitation.
        # Let's assume for T012b that the URL is a zip as per typical Metabolomics Workbench.
        raise ValueError("Direct CSV download not supported for bulk data extraction. Expected ZIP.")

    return str(intensity_path), str(phenotype_path)

def extract_and_save_csvs(zip_path: Path, output_dir: Path, study_id: str) -> Tuple[str, str]:
    """
    Extracts CSVs from a local zip file.
    """
    with zipfile.ZipFile(zip_path, 'r') as z:
        csv_files = [f for f in z.namelist() if f.endswith('.csv')]
        # Logic similar to download_study_data
        # ... (implementation omitted for brevity as download_study_data handles in-memory)
        pass
    return "", ""

def load_phenotype_metadata(phenotype_path: Path) -> pd.DataFrame:
    import pandas as pd
    if not phenotype_path.exists():
        raise FileNotFoundError(f"Phenotype file not found: {phenotype_path}")
    return pd.read_csv(phenotype_path)

def verify_temporal_separation(df: pd.DataFrame) -> bool:
    """
    Check if the dataframe has temporal information (baseline, pre-challenge).
    Returns True if valid, False otherwise.
    """
    # Placeholder for T013 logic
    return True

def compute_checksums(file_paths: List[str]) -> Dict[str, str]:
    """
    Compute SHA256 checksums for a list of files.
    """
    checksums = {}
    for path in file_paths:
        if os.path.exists(path):
            checksums[path] = compute_file_hash(path)
        else:
            logger.warning(f"File not found for checksum: {path}")
    return checksums

def download_study(study_entry: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    """
    Downloads data for a single study entry from the manifest.
    Returns a dictionary with the result status and file paths.
    """
    study_id = study_entry.get('study_id')
    download_url = study_entry.get('download_url')
    
    if not study_id or not download_url:
        logger.error(f"Invalid study entry: {study_entry}")
        return {"status": "error", "reason": "Missing study_id or download_url"}

    logger.info(f"Processing study: {study_id}")
    
    try:
        intensity_path, phenotype_path = download_study_data(download_url, output_dir, study_id)
        
        # Verify files are non-empty
        if os.path.getsize(intensity_path) == 0:
            raise ValueError(f"Intensity file is empty: {intensity_path}")
        if os.path.getsize(phenotype_path) == 0:
            raise ValueError(f"Phenotype file is empty: {phenotype_path}")

        checksums = compute_checksums([intensity_path, phenotype_path])
        
        return {
            "status": "success",
            "study_id": study_id,
            "intensity_path": intensity_path,
            "phenotype_path": phenotype_path,
            "checksums": checksums
        }
    except Exception as e:
        logger.error(f"Failed to download study {study_id}: {e}")
        return {"status": "error", "reason": str(e)}

def main():
    """
    Main entry point for T012b.
    Reads data/raw/study_manifest.json, downloads files, and saves checksums.
    """
    manifest_path = Path("data/raw/study_manifest.json")
    output_dir = Path("data/raw")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Pre-check
    if not manifest_path.exists():
        raise DataUnavailableError("Pre-requisite manifest missing. Run T012a first.")

    studies = get_study_download_url(manifest_path)
    results = []

    for study in studies:
        result = download_study(study, output_dir)
        results.append(result)
        
        if result["status"] == "error":
            logger.warning(f"Skipping further processing for {study.get('study_id', 'unknown')} due to error.")

    # Save a summary log of the download step
    log_path = output_dir / "download_log.json"
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Download process complete. Log saved to {log_path}")

    # Verify outputs
    success_count = sum(1 for r in results if r["status"] == "success")
    if success_count == 0:
        raise RuntimeError("No studies were successfully downloaded.")
    
    print(f"Successfully downloaded {success_count} studies.")

if __name__ == "__main__":
    main()
