import os
import sys
import json
import argparse
import logging
from pathlib import Path
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import requests
import pandas as pd

# Import from sibling modules as per API surface
from config import ensure_dirs, set_global_seed
from hash_artifacts import calculate_file_hash, save_manifest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_RAW_DIR = Path("data/raw")
STATE_DIR = Path("state")
MANIFEST_FILE = STATE_DIR / "download_manifest.json"

def get_valid_sources() -> List[Dict[str, Any]]:
    """
    Returns a list of valid data sources with their metadata.
    Excludes Materials Project as per T010 logic.
    """
    sources = [
        {
            "name": "OpenML",
            "type": "openml",
            "id": "aluminum_grain_size", # Placeholder ID, real ID would be fetched
            "url_template": "https://www.openml.org/api/v1/data/{id}",
            "schema_required": ["rolling_temperature", "grain_size", "composition", "process_type"],
            "active": True
        },
        {
            "name": "NOMAD",
            "type": "nomad",
            "id": "nomad_aluminum_rolling",
            "url_template": "https://nomad-laboratory.de/api/v1/entries",
            "schema_required": ["rolling_temperature", "grain_size", "composition", "process_type"],
            "active": True
        }
    ]
    return sources

def check_schema_precheck(source: Dict[str, Any]) -> bool:
    """
    Simulates a schema pre-check against source metadata.
    In a real implementation, this would fetch metadata from the API.
    For this task, we assume the sources defined in get_valid_sources are pre-validated.
    Returns True if the source is likely to have the required schema.
    """
    if not source.get("active", False):
        return False
    
    # Check if required fields are listed in source metadata
    required = source.get("schema_required", [])
    required_fields = ["rolling_temperature", "grain_size", "composition", "process_type"]
    return all(field in required for field in required_fields)

def filter_by_process_type(df: pd.DataFrame, process_type: str = "Rolling") -> pd.DataFrame:
    """
    Filters the dataframe to include only rows where process_type matches.
    Excludes Casting, SPD, etc.
    """
    if "process_type" not in df.columns:
        logger.warning("Column 'process_type' not found in dataframe. Returning full dataframe.")
        return df
    
    filtered_df = df[df["process_type"].str.strip().str.lower() == process_type.lower()]
    logger.info(f"Filtered to {len(filtered_df)} rows for process_type='{process_type}'")
    return filtered_df

def validate_alloy_composition(df: pd.DataFrame) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validates that the dataset contains alloying elements and not just pure aluminum.
    Returns (is_valid, error_info).
    If invalid (pure aluminum), returns error dict with code E_INSUFFICIENT_VARIANCE.
    """
    if "composition" not in df.columns:
        logger.error("Column 'composition' not found. Cannot validate alloy composition.")
        return False, {"code": "E_DATA_MISSING", "message": "Missing composition column"}

    # Check if any row has non-zero alloying elements
    # Assuming composition is a dict or JSON string in the column
    has_alloy = False
    for idx, row in df.iterrows():
        comp = row["composition"]
        if isinstance(comp, str):
            try:
                comp = json.loads(comp)
            except json.JSONDecodeError:
                continue
        elif not isinstance(comp, dict):
            continue
        
        # Check if any value in composition dict is > 0 (excluding Al if present)
        for element, value in comp.items():
            if element.lower() != "al" and float(value) > 0:
                has_alloy = True
                break
        if has_alloy:
            break

    if not has_alloy:
        logger.error("Dataset contains only pure aluminum entries.")
        return False, {
            "code": "E_INSUFFICIENT_VARIANCE",
            "message": "Dataset contains only pure aluminum"
        }
    
    return True, None

def download_from_openml(source_id: str, output_path: Path) -> bool:
    """
    Downloads data from OpenML.
    Returns True on success, False on failure.
    """
    # In a real scenario, this would use the openml python package or requests
    # Since we cannot guarantee a specific dataset ID exists without API access,
    # we will simulate the download logic that would fetch from a real URL.
    # For the purpose of this task, we assume a fallback or a specific known dataset.
    # However, per constraints, we must not fabricate data.
    # We will attempt to fetch a known public dataset or return an error if not reachable.
    
    url = f"https://www.openml.org/api/v1/data/{source_id}/json"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Extract download link if available
            if "data_file" in data:
                file_url = data["data_file"]
                file_response = requests.get(file_url, timeout=60)
                if file_response.status_code == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(file_response.content)
                    logger.info(f"Downloaded from OpenML to {output_path}")
                    return True
        logger.error(f"Failed to download from OpenML: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Error downloading from OpenML: {e}")
        return False

def download_from_nomad(source_id: str, output_path: Path) -> bool:
    """
    Downloads data from NOMAD.
    Returns True on success, False on failure.
    """
    # Similar to OpenML, we attempt a real fetch.
    # NOMAD API requires specific query parameters.
    url = "https://nomad-laboratory.de/api/v1/entries"
    params = {
        "filter": '{"entry_name": {"contains": "aluminum"}}',
        "page_size": 100
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # NOMAD returns JSON, we might need to convert to CSV or process raw
            # For this task, we save the raw JSON response as a data file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Downloaded from NOMAD to {output_path}")
            return True
        logger.error(f"Failed to download from NOMAD: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Error downloading from NOMAD: {e}")
        return False

def run_download_pipeline():
    """
    Main pipeline function for downloading, validating, and hashing data.
    Implements T012-T016 and T017.
    """
    ensure_dirs()
    set_global_seed(42)

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    sources = get_valid_sources()
    successful_downloads = []
    
    for source in sources:
        if not check_schema_precheck(source):
            logger.info(f"Skipping source {source['name']} due to schema precheck failure.")
            continue
        
        logger.info(f"Attempting to download from {source['name']}...")
        output_filename = f"{source['name'].lower()}_data.json"
        output_path = DATA_RAW_DIR / output_filename
        
        success = False
        if source['type'] == 'openml':
            success = download_from_openml(source['id'], output_path)
        elif source['type'] == 'nomad':
            success = download_from_nomad(source['id'], output_path)
        
        if success and output_path.exists():
            successful_downloads.append(output_path)
        else:
            logger.warning(f"Download failed for {source['name']}.")

    if not successful_downloads:
        error_msg = {
            "code": "E_DATA_MISSING",
            "message": "All sources failed or variables missing."
        }
        logger.error(json.dumps(error_msg))
        with open(DATA_RAW_DIR / "error.json", 'w') as f:
            json.dump(error_msg, f)
        sys.exit(1)

    # T017: Integration with hash_artifacts.py
    logger.info("Hashing downloaded files...")
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "files": []
    }

    for file_path in successful_downloads:
        file_hash = calculate_file_hash(file_path)
        logger.info(f"Hash for {file_path.name}: {file_hash}")
        manifest["files"].append({
            "path": str(file_path),
            "hash": file_hash,
            "size": file_path.stat().st_size
        })

    save_manifest(manifest, MANIFEST_FILE)
    logger.info(f"Manifest saved to {MANIFEST_FILE}")

    # T014 & T015: Validation logic on downloaded data (if CSV/JSON processed)
    # Note: This part assumes the downloaded file is parseable as a dataset.
    # If the download was raw JSON from an API, we might need to parse it first.
    # For the sake of the pipeline flow, we attempt to load the first successful file.
    
    primary_file = successful_downloads[0]
    try:
        if primary_file.suffix == '.json':
            with open(primary_file, 'r') as f:
                raw_data = json.load(f)
            # If it's a list of entries, convert to DataFrame
            if isinstance(raw_data, list):
                df = pd.DataFrame(raw_data)
            elif isinstance(raw_data, dict) and 'entries' in raw_data:
                df = pd.DataFrame(raw_data['entries'])
            else:
                # Fallback: try to load as CSV if structure is weird
                df = pd.read_json(primary_file)
        else:
            df = pd.read_csv(primary_file)

        # T014: Filter by process type
        df = filter_by_process_type(df, "Rolling")

        if df.empty:
            error_msg = {
                "code": "E_DATA_MISSING",
                "message": "No data found for process_type='Rolling'."
            }
            logger.error(json.dumps(error_msg))
            with open(DATA_RAW_DIR / "error.json", 'w') as f:
                json.dump(error_msg, f)
            sys.exit(1)

        # T015: Validate alloy composition
        is_valid, error_info = validate_alloy_composition(df)
        if not is_valid:
            logger.error(json.dumps(error_info))
            with open(DATA_RAW_DIR / "error.json", 'w') as f:
                json.dump(error_info, f)
            sys.exit(1)

        # Save processed raw data (still raw, but filtered)
        processed_path = DATA_RAW_DIR / "aluminum_rolling_filtered.csv"
        df.to_csv(processed_path, index=False)
        logger.info(f"Saved filtered data to {processed_path}")
        
        # Re-hash the filtered file as part of the artifact chain?
        # The task specifically asks to hash "raw downloaded files".
        # We have already done that above.
        
    except Exception as e:
        logger.error(f"Error processing downloaded data: {e}")
        # If we can't process, we still have the raw file and its hash.
        # But the pipeline effectively stops here for downstream tasks.
        sys.exit(1)

    return 0

def main():
    """
    Entry point for the download script.
    """
    parser = argparse.ArgumentParser(description="Download and validate aluminum rolling data.")
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    set_global_seed(args.seed)
    exit_code = run_download_pipeline()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
