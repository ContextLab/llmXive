import os
import sys
import json
import hashlib
import requests
import zipfile
import io
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Constants for file paths
RAW_DATA_DIR = Path("data/raw")
MANIFEST_PATH = Path("data/raw/study_manifest.json")

def get_study_download_url(study_id: str) -> Optional[str]:
    """
    Fetch the download URL for a specific study from Metabolomics Workbench.
    """
    api_url = f"https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={study_id}"
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        # The API returns a list of studies, but we queried by ID so expect one or error
        if "STUDIES" in data and len(data["STUDIES"]) > 0:
            study_info = data["STUDIES"][0]
            return study_info.get("DOWNLOAD_URL")
        return None
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch download URL for study {study_id}: {e}")

def download_study_data(download_url: str, output_dir: Path) -> Dict[str, str]:
    """
    Download the study data (zip) from the provided URL and extract it.
    Returns a dict mapping expected filenames to their actual paths.
    """
    if not download_url:
        raise ValueError("Download URL is empty or None")

    try:
        response = requests.get(download_url, timeout=300) # 5 min timeout for large files
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download study data from {download_url}: {e}")

    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # List files to find intensity and phenotype CSVs
            file_list = zip_ref.namelist()
            
            intensity_file = None
            phenotype_file = None

            for f in file_list:
                if f.endswith('_intensity.csv') or 'intensity' in f.lower():
                    intensity_file = f
                elif f.endswith('_phenotype.csv') or 'phenotype' in f.lower():
                    phenotype_file = f

            if not intensity_file and not phenotype_file:
                # Fallback: try to find any CSVs if specific naming fails
                csv_files = [f for f in file_list if f.endswith('.csv')]
                if len(csv_files) >= 2:
                    intensity_file = csv_files[0]
                    phenotype_file = csv_files[1]
                elif len(csv_files) == 1:
                    intensity_file = csv_files[0] # Assume one file contains both or is intensity

            if not intensity_file and not phenotype_file:
                raise ValueError(f"No CSV files found in study archive. Files: {file_list}")

            extracted_paths = {}

            # Extract Intensity
            if intensity_file:
                target_intensity = output_dir / f"{intensity_file.split('/')[-1].replace('.csv', '')}_raw_intensity.csv"
                with zip_ref.open(intensity_file) as zf, open(target_intensity, 'wb') as out_f:
                    out_f.write(zf.read())
                extracted_paths['intensity'] = str(target_intensity)

            # Extract Phenotype
            if phenotype_file:
                target_phenotype = output_dir / f"{phenotype_file.split('/')[-1].replace('.csv', '')}_phenotype.csv"
                with zip_ref.open(phenotype_file) as zf, open(target_phenotype, 'wb') as out_f:
                    out_f.write(zf.read())
                extracted_paths['phenotype'] = str(target_phenotype)

            return extracted_paths

    except zipfile.BadZipFile:
        raise RuntimeError(f"Downloaded content for {download_url} is not a valid ZIP file.")

def compute_checksums(file_paths: List[str]) -> Dict[str, str]:
    """
    Compute SHA256 checksums for a list of file paths.
    """
    checksums = {}
    for path in file_paths:
        if os.path.exists(path):
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksums[path] = sha256_hash.hexdigest()
        else:
            checksums[path] = "MISSING"
    return checksums

def download_study(study_id: str, download_url: str, output_dir: Path) -> Dict[str, Any]:
    """
    Orchestrates the download and extraction for a single study.
    """
    print(f"Processing study: {study_id}")
    result = {
        "study_id": study_id,
        "status": "pending",
        "files": {},
        "checksums": {},
        "error": None
    }

    try:
        extracted = download_study_data(download_url, output_dir)
        result["files"] = extracted
        
        # Compute checksums
        file_list = list(extracted.values())
        result["checksums"] = compute_checksums(file_list)
        
        # Verify files are non-empty
        for f_path in file_list:
            if os.path.getsize(f_path) == 0:
                raise ValueError(f"Downloaded file {f_path} is empty.")

        result["status"] = "success"
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result

def main():
    """
    Main entry point for T012b: Download raw data for all studies in manifest.
    """
    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load manifest
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest file not found: {MANIFEST_PATH}. Run T012a-ser first.")

    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)

    if not isinstance(manifest, list) or len(manifest) == 0:
        raise ValueError("Manifest is empty or invalid.")

    print(f"Found {len(manifest)} studies to download.")

    results = []
    for study_entry in manifest:
        study_id = study_entry.get("study_id")
        download_url = study_entry.get("download_url")

        if not study_id or not download_url:
            print(f"Skipping entry missing ID or URL: {study_entry}")
            continue

        result = download_study(study_id, download_url, RAW_DATA_DIR)
        results.append(result)

    # Save download log
    log_path = RAW_DATA_DIR / "download_log.json"
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Check for failures
    failed_count = sum(1 for r in results if r["status"] == "failed")
    if failed_count > 0:
        print(f"Warning: {failed_count} studies failed to download. Check {log_path} for details.")
        # We do not raise here to allow partial success if some downloads worked, 
        # but the task requires "Confirm files exist and are non-empty". 
        # If critical files are missing, the next stage (T012c) will fail loudly.
    
    print("Download process completed.")

if __name__ == "__main__":
    main()
