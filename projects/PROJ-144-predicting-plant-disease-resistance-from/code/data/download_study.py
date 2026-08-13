import os
import sys
import json
import hashlib
import requests
import zipfile
import io
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from utils.exceptions import TemporalVerificationError, DataUnavailableError
from utils.io import compute_file_hash, log_artifact
from utils.constants import DATA_RAW_DIR, PROJECT_ROOT

# Ensure the raw data directory exists
DATA_RAW_DIR = Path(PROJECT_ROOT) / "data" / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

def get_study_download_url(study_id: str) -> str:
    """
    Constructs the download URL for a study's raw intensity and phenotype data.
    Based on Metabolomics Workbench standard pattern.
    """
    # The standard pattern for downloading study data (intensity + phenotype)
    # is typically: https://www.metabolomicsworkbench.org/data/REST2/MetabolomicsWorkbench/REST2/download_study.php?STUDY_ID=STXXXXXX
    # However, direct links to intensity tables often follow:
    # https://www.metabolomicsworkbench.org/data/download.php?STUDY_ID=STXXXXXX&FILE_TYPE=INTENSITY
    # We will attempt the generic download endpoint which usually returns a zip or directs to files.
    # For this implementation, we assume the manifest provides a direct link or we construct the base.
    # The task says: "Construct download_url ... using the standard Metabolomics Workbench pattern"
    # Pattern: https://www.metabolomicsworkbench.org/data/download.php?STUDY_ID={study_id}
    base_url = "https://www.metabolomicsworkbench.org/data/download.php"
    return f"{base_url}?STUDY_ID={study_id}"

def download_study_data(download_url: str, output_dir: Path) -> Tuple[str, str]:
    """
    Downloads the study data from the provided URL.
    Returns the path to the downloaded intensity file and phenotype file.
    Raises an error if download fails.
    """
    session = requests.Session()
    session.headers.update({'User-Agent': 'llmXive-research-agent/1.0'})
    
    try:
        response = session.get(download_url, stream=True, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download study data from {download_url}: {e}")

    # The response might be a ZIP file or a redirect to specific files.
    # Metabolomics Workbench often serves a ZIP containing:
    # - STXXXXXX_intensity.csv
    # - STXXXXXX_phenotype.csv
    # We will check the content type or try to unzip.
    
    content_type = response.headers.get('Content-Type', '')
    if 'zip' in content_type or response.headers.get('Content-Disposition', '').endswith('.zip'):
        # It's a ZIP file
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # List files to find intensity and phenotype
            file_list = zip_ref.namelist()
            intensity_file = None
            phenotype_file = None
            
            for name in file_list:
                if 'intensity' in name.lower() and name.endswith('.csv'):
                    intensity_file = name
                elif 'phenotype' in name.lower() and name.endswith('.csv'):
                    phenotype_file = name
            
            if not intensity_file or not phenotype_file:
                # Fallback: try to find any csv if naming is weird
                if not intensity_file:
                    intensity_file = next((f for f in file_list if f.endswith('.csv')), None)
                if not phenotype_file:
                    phenotype_file = next((f for f in file_list if f.endswith('.csv') and f != intensity_file), None)

            if not intensity_file:
                raise FileNotFoundError("No intensity CSV found in downloaded study data.")

            # Extract to output_dir
            if intensity_file:
                with zip_ref.open(intensity_file) as f_in, open(output_dir / Path(intensity_file).name, 'wb') as f_out:
                    f_out.write(f_in.read())
            if phenotype_file:
                with zip_ref.open(phenotype_file) as f_in, open(output_dir / Path(phenotype_file).name, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            return str(output_dir / Path(intensity_file).name), str(output_dir / Path(phenotype_file).name) if phenotype_file else None
    else:
        # Assume it's a direct CSV or text stream? Unlikely for MW, but handle gracefully.
        # Or it might be an HTML page with links. We'll treat it as a single file for now if not zip.
        # For robustness, we'll assume the task expects the ZIP handling above.
        # If we get here, it's not a zip. Let's try to save as raw file.
        filename = "raw_data.txt"
        if 'filename=' in response.headers.get('Content-Disposition', ''):
            filename = response.headers['Content-Disposition'].split('filename=')[1].strip('"')
        
        file_path = output_dir / filename
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        # If it's not a zip and not a csv, we can't proceed with the expected logic.
        # We assume the MW API returns a zip for study IDs.
        if not file_path.suffix.lower() == '.csv':
            # Try to unzip if it's actually a zip but misidentified
             try:
                  with zipfile.ZipFile(file_path, 'r') as zip_ref:
                      zip_ref.extractall(output_dir)
                  # Re-scan for files
                  files = list(output_dir.glob("*.csv"))
                  if len(files) >= 2:
                      return str(files[0]), str(files[1])
                  elif len(files) == 1:
                       return str(files[0]), None
             except:
                  pass
        
        return str(file_path), None

def load_phenotype_metadata(phenotype_path: str) -> pd.DataFrame:
    """
    Loads the phenotype metadata from the downloaded file.
    """
    if not phenotype_path or not os.path.exists(phenotype_path):
        raise FileNotFoundError(f"Phenotype file not found: {phenotype_path}")
    
    try:
        df = pd.read_csv(phenotype_path)
        return df
    except Exception as e:
        raise ValueError(f"Failed to parse phenotype CSV: {e}")

def verify_temporal_separation(phenotype_df: pd.DataFrame, study_id: str) -> bool:
    """
    Verifies that the phenotype metadata contains temporal fields indicating
    'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation.
    Raises TemporalVerificationError if not found.
    """
    # Normalize column names
    cols_lower = {col.lower(): col for col in phenotype_df.columns}
    
    # Keywords to look for
    temporal_keywords = ['pre-challenge', 'prechallenge', 'baseline', 'pre_inoculation', 'pre_inoc', 'time_point', 'time', 'day', 'hour']
    found_temporal = False
    
    # Check for explicit temporal markers in column names or values
    for col in phenotype_df.columns:
        if any(kw in col.lower() for kw in ['time', 'day', 'hour', 'pre', 'baseline']):
            found_temporal = True
            break
    
    # Check values in likely columns if no temporal column found
    if not found_temporal:
        # Look for a column that might contain 'pre' or 'baseline' in its values
        for col in phenotype_df.columns:
            if phenotype_df[col].dtype == 'object':
                if phenotype_df[col].str.contains('pre|baseline|baseline', case=False, na=False).any():
                    found_temporal = True
                    break
    
    if not found_temporal:
        raise TemporalVerificationError(
            f"Study {study_id}: Temporal separation cannot be verified. "
            "No 'pre-challenge', 'baseline', or time-related fields found in phenotype metadata. "
            f"Columns found: {list(phenotype_df.columns)}"
        )
    
    return True

def compute_checksums(file_paths: List[str]) -> Dict[str, str]:
    """
    Computes SHA256 checksums for the downloaded files.
    """
    checksums = {}
    for path in file_paths:
        if os.path.exists(path):
            checksums[os.path.basename(path)] = compute_file_hash(path)
    return checksums

def download_study(study_id: str, download_url: str) -> Tuple[str, str, Dict[str, str]]:
    """
    Orchestrates the download, verification, and checksumming for a single study.
    Returns (intensity_path, phenotype_path, checksums)
    """
    output_dir = Path(DATA_RAW_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading study {study_id} from {download_url}...")
    intensity_path, phenotype_path = download_study_data(download_url, output_dir)
    
    # Verify temporal separation if phenotype exists
    if phenotype_path:
        phenotype_df = load_phenotype_metadata(phenotype_path)
        verify_temporal_separation(phenotype_df, study_id)
    else:
        # If no phenotype file, we can't verify. This might be a hard fail depending on strictness.
        # Task says: "Verify sample metadata ... Hard Fail: If temporal separation cannot be verified"
        raise TemporalVerificationError(f"Study {study_id}: Phenotype metadata missing, cannot verify temporal separation.")
    
    # Compute checksums
    files_to_hash = [f for f in [intensity_path, phenotype_path] if f and os.path.exists(f)]
    checksums = compute_checksums(files_to_hash)
    
    return intensity_path, phenotype_path, checksums

def main():
    """
    Main entry point to process the study manifest and download data.
    """
    manifest_path = Path(PROJECT_ROOT) / "data" / "raw" / "study_manifest.json"
    
    if not manifest_path.exists():
        raise DataUnavailableError(f"Manifest not found at {manifest_path}. Run T012a first.")
    
    with open(manifest_path, 'r') as f:
        studies = json.load(f)
    
    if not isinstance(studies, list) or len(studies) == 0:
        raise ValueError("Manifest is empty or invalid format.")
    
    results = []
    
    for study_entry in studies:
        study_id = study_entry.get('study_id')
        download_url = study_entry.get('download_url')
        
        if not study_id or not download_url:
            print(f"Skipping invalid entry: {study_entry}")
            continue
        
        try:
            intensity_path, phenotype_path, checksums = download_study(study_id, download_url)
            
            # Rename files to standard naming if they differ
            intensity_filename = f"{study_id}_raw_intensity.csv"
            phenotype_filename = f"{study_id}_phenotype.csv"
            
            # Move/Rename if necessary
            if intensity_path and not intensity_path.endswith(intensity_filename):
                new_intensity = Path(DATA_RAW_DIR) / intensity_filename
                if os.path.exists(intensity_path):
                    os.replace(intensity_path, new_intensity)
                    intensity_path = str(new_intensity)
            
            if phenotype_path and not phenotype_path.endswith(phenotype_filename):
                new_phenotype = Path(DATA_RAW_DIR) / phenotype_filename
                if os.path.exists(phenotype_path):
                    os.replace(phenotype_path, new_phenotype)
                    phenotype_path = str(new_phenotype)
            
            # Log results
            result = {
                "study_id": study_id,
                "intensity_file": intensity_path,
                "phenotype_file": phenotype_path,
                "checksums": checksums,
                "status": "success"
            }
            results.append(result)
            print(f"Successfully processed study {study_id}")
            
        except TemporalVerificationError as e:
            print(f"TEMPORAL VERIFICATION FAILED for {study_id}: {e}")
            # Hard fail as per task requirement
            raise e
        except Exception as e:
            print(f"Error processing study {study_id}: {e}")
            results.append({
                "study_id": study_id,
                "status": "failed",
                "error": str(e)
            })
    
    # Save a summary log
    log_path = Path(DATA_RAW_DIR) / "download_log.json"
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Download process complete. Log saved to {log_path}")

if __name__ == "__main__":
    main()
