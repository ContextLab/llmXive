import os
import sys
import json
import hashlib
import requests
import zipfile
import csv
import io
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import custom exceptions
try:
    from utils.exceptions import TemporalVerificationError, DataUnavailableError
except ImportError:
    # Fallback for direct execution or different import context
    class TemporalVerificationError(Exception):
        """Raised when temporal separation cannot be verified."""
        pass
    class DataUnavailableError(Exception):
        """Raised when prerequisite data is missing."""
        pass


def get_study_download_url(study_id: str) -> str:
    """
    Constructs the download URL for a study's data files from Metabolomics Workbench.
    Note: The actual study data is often distributed as a zip file containing the CSVs.
    We assume the manifest provides a direct link to the study data zip or the API
    structure is predictable. If the manifest URL points to a study page, we might
    need to parse it, but T012a is expected to provide the direct download URL.
    """
    # If the manifest already has a download_url, we might just use that.
    # However, standard MW URLs for data download often follow a pattern.
    # We will trust the manifest's download_url if it looks like a data link,
    # otherwise we construct a standard one.
    # For this implementation, we assume the manifest provides the base data URL.
    # If it's a study page URL, we'd need to fetch the study info first.
    # Given T012a's output requirement, we assume 'download_url' is the direct link.
    return f"https://www.metabolomicsworkbench.org/data/study_download.php?STUDY_ID={study_id}"


def download_study_data(url: str, output_dir: Path) -> str:
    """
    Downloads the study data zip file from the provided URL.
    Returns the path to the downloaded zip file.
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Determine filename from URL or Content-Disposition
    filename = url.split('/')[-1]
    if not filename.endswith('.zip'):
        filename = "study_data.zip"

    zip_path = output_dir / filename
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(zip_path)


def extract_and_save_csvs(zip_path: str, output_dir: Path, study_id: str):
    """
    Extracts the raw intensity and phenotype CSVs from the zip file
    and saves them with the expected naming convention.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # List files to find the correct ones
        file_list = zip_ref.namelist()
        
        intensity_file = None
        phenotype_file = None

        # Heuristic to find the files
        for name in file_list:
            if 'intensity' in name.lower() or 'data' in name.lower():
                if not intensity_file:
                    intensity_file = name
            elif 'phenotype' in name.lower() or 'sample' in name.lower():
                if not phenotype_file:
                    phenotype_file = name

        # If heuristics fail, try to find any CSV
        if not intensity_file:
            csv_files = [f for f in file_list if f.endswith('.csv')]
            if csv_files:
                # Assume the first one is intensity, second is phenotype if available
                intensity_file = csv_files[0]
                if len(csv_files) > 1:
                    phenotype_file = csv_files[1]

        if not intensity_file:
            raise FileNotFoundError(f"Could not find intensity data in {zip_path}")

        # Extract intensity
        intensity_content = zip_ref.read(intensity_file)
        intensity_path = output_dir / f"{study_id}_raw_intensity.csv"
        with open(intensity_path, 'wb') as f:
            f.write(intensity_content)

        # Extract phenotype if found
        if phenotype_file:
            phenotype_content = zip_ref.read(phenotype_file)
            phenotype_path = output_dir / f"{study_id}_phenotype.csv"
            with open(phenotype_path, 'wb') as f:
                f.write(phenotype_content)
        else:
            # If no phenotype file found, we might need to generate one or fail
            # For now, we'll create a placeholder if the study ID implies a standard structure
            # But strict requirement says download phenotype metadata.
            # If the zip doesn't have it, we might have to look for a separate file or fail.
            # Let's assume the zip contains it or the study ID allows us to find it.
            # If not found, we raise an error.
            raise FileNotFoundError(f"Could not find phenotype metadata in {zip_path}")


def load_phenotype_metadata(phenotype_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the phenotype metadata from a CSV file.
    Returns a list of dictionaries representing rows.
    """
    if not phenotype_path.exists():
        raise FileNotFoundError(f"Phenotype file not found: {phenotype_path}")

    data = []
    with open(phenotype_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def verify_temporal_separation(phenotype_data: List[Dict[str, Any]], study_id: str) -> bool:
    """
    Verifies that the metadata contains 'pre-challenge', 'baseline', or timestamps
    prior to pathogen inoculation.
    Raises TemporalVerificationError if not found.
    """
    temporal_keywords = ['pre-challenge', 'baseline', 'pre_challenge', 'before_inoculation', 't0', 'time_0']
    found_temporal = False

    # Check column names for temporal indicators
    if phenotype_data:
        columns = phenotype_data[0].keys()
        temporal_columns = [col for col in columns if any(kw in col.lower() for kw in temporal_keywords)]
        
        # Check values in relevant columns
        for row in phenotype_data:
            for col in columns:
                val = str(row.get(col, '')).lower()
                if any(kw in val for kw in temporal_keywords):
                    found_temporal = True
                    break
            if found_temporal:
                break

    if not found_temporal:
        # Check if there is a 'time' column that could indicate pre-challenge
        time_columns = [col for col in (phenotype_data[0].keys() if phenotype_data else []) if 'time' in col.lower()]
        if time_columns:
            for row in phenotype_data:
                for col in time_columns:
                    try:
                        val = float(row.get(col, ''))
                        if val <= 0: # Assuming 0 is baseline/pre-challenge
                            found_temporal = True
                            break
                    except (ValueError, TypeError):
                        continue
                if found_temporal:
                    break

    if not found_temporal:
        raise TemporalVerificationError(
            f"Temporal separation verification failed for study {study_id}. "
            "No 'pre-challenge', 'baseline', or pre-inoculation timestamps found in metadata."
        )
    
    return True


def compute_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """
    Computes SHA256 checksums for the given files.
    Returns a dictionary mapping filename to hash.
    """
    checksums = {}
    for path in file_paths:
        if path.exists():
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksums[path.name] = sha256_hash.hexdigest()
        else:
            checksums[path.name] = "MISSING"
    return checksums


def download_study(manifest_entry: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    """
    Downloads a single study based on the manifest entry.
    Returns a result dictionary with status and file paths.
    """
    study_id = manifest_entry.get('study_id')
    download_url = manifest_entry.get('download_url')
    
    if not study_id or not download_url:
        raise ValueError(f"Invalid manifest entry: {manifest_entry}")

    result = {
        'study_id': study_id,
        'status': 'success',
        'intensity_path': None,
        'phenotype_path': None,
        'checksums': {}
    }

    try:
        # Download zip
        zip_path = download_study_data(download_url, output_dir)
        
        # Extract and save CSVs
        extract_and_save_csvs(zip_path, output_dir, study_id)
        
        intensity_path = output_dir / f"{study_id}_raw_intensity.csv"
        phenotype_path = output_dir / f"{study_id}_phenotype.csv"
        
        if not intensity_path.exists():
            raise FileNotFoundError(f"Intensity file not created: {intensity_path}")
        
        result['intensity_path'] = str(intensity_path)
        result['phenotype_path'] = str(phenotype_path)
        
        # Verify temporal separation
        phenotype_data = load_phenotype_metadata(phenotype_path)
        verify_temporal_separation(phenotype_data, study_id)
        
        # Compute checksums
        result['checksums'] = compute_checksums([intensity_path, phenotype_path])
        
        # Clean up zip
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        raise

    return result


def main():
    """
    Main entry point for T012b.
    Reads data/raw/study_manifest.json, downloads studies, and verifies temporal data.
    """
    manifest_path = Path("data/raw/study_manifest.json")
    output_dir = Path("data/raw")
    
    if not manifest_path.exists():
        raise DataUnavailableError("Pre-requisite manifest missing. Run T012a first.")

    with open(manifest_path, 'r') as f:
        studies = json.load(f)

    if not studies:
        print("No studies found in manifest.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for study in studies:
        print(f"Processing study: {study.get('study_id')}")
        try:
            result = download_study(study, output_dir)
            results.append(result)
            print(f"  Success: {result['intensity_path']}")
        except TemporalVerificationError as e:
            print(f"  Temporal Verification Failed: {e}")
            results.append({'study_id': study.get('study_id'), 'status': 'failed', 'error': str(e)})
        except DataUnavailableError as e:
            print(f"  Data Unavailable: {e}")
            raise
        except Exception as e:
            print(f"  Failed: {e}")
            results.append({'study_id': study.get('study_id'), 'status': 'failed', 'error': str(e)})

    # Save results
    results_path = output_dir / "download_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Download results saved to {results_path}")


if __name__ == "__main__":
    main()
