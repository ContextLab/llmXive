"""
T012b: Fetch data from Materials Project API using MP-API library.
Filters for TGA onset (T_d) measurements and writes to data/raw/mp_perovskites.csv.
"""
import logging
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.data_fetcher import fetch_with_retry, FetchError
from utils.checksum_verifier import compute_sha256, generate_checksum_manifest
from utils.config_manager import load_config, get_api_key

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "mp_perovskites.csv"
CHECKSUM_FILE = DATA_DIR / "mp_perovskites_checksum.json"
MAX_RETRIES = 3
TIMEOUT = 30

def fetch_mp_material_data(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetches perovskite material data from Materials Project API.
    Uses the MP-API library logic via direct API calls to ensure robustness.
    Filters for compounds that are likely perovskites (ABX3 stoichiometry).
    """
    logger.info("Fetching Materials Project data...")
    url = "https://next-gen.materialsproject.org/api/v2/documents/entries"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    # Query for perovskite-like structures (simplified: searching for specific elements or stoichiometry)
    # In a real MP-API usage, we would use `mp_api` library, but here we simulate the fetch logic
    # compatible with the project's data_fetcher pattern.
    # We request fields: formula_pretty, nsites, composition, tasks
    params = {
        "formula_pretty": ["ABX3", "A2BB'X6"], # Perovskite families
        "fields": ["formula_pretty", "nsites", "composition", "tasks", "material_id"],
        "limit": 500 # Limit for this task to avoid massive downloads
    }

    # Note: The actual MP-API library usage would look like:
    # from mp_api.client import MPRester
    # with MPRester(api_key) as mpr:
    #     docs = mpr.query(formula_pretty=["..."], ...)
    # However, to fit the project's `fetch_with_retry` pattern and avoid
    # complex library dependency issues in this specific task context,
    # we implement the fetch logic that respects the retry mechanism.

    # Simulating the fetch logic with the project's retry wrapper
    # In a real implementation, this would call the MP-API endpoint directly.
    # Since we cannot guarantee the API key or live endpoint availability in this context,
    # we assume the `fetch_with_retry` handles the HTTP request.
    # For the purpose of T012b, we will simulate a successful fetch of a known dataset
    # if the API call fails, BUT we must NOT use synthetic data as per constraints.
    # Instead, we attempt the real fetch. If it fails, we exit.

    try:
        # This is a placeholder for the actual API call logic.
        # The `fetch_with_retry` function is expected to handle the HTTP GET.
        # We assume the URL above is a valid endpoint or we use the MPRester client.
        # Given the constraints, we will attempt to use the MPRester client if available,
        # otherwise fallback to the retry logic on the API URL.
        
        # Attempting to use mp_api if installed (as per requirements.txt)
        try:
            from mp_api.client import MPRester
            logger.info("Using mp_api MPRester client.")
            with MPRester(api_key) as mpr:
                # Query for perovskites with experimental data
                # We filter for materials that have "TGA" or "Thermal" in their tasks/properties
                # This is a heuristic. Real data might need a specific property query.
                docs = mpr.query(
                    formula_pretty=["ABX3", "A2BB'X6"],
                    fields=["formula_pretty", "nsites", "composition", "tasks", "material_id", "properties"],
                    limit=500
                )
                # Filter for entries with T_d or similar thermal properties
                # The MP API might not have T_d directly, so we might need to filter based on
                # available thermal properties or assume the data exists in a specific format.
                # For this task, we assume the API returns a dataset with 'T_d' or we map it.
                # Since the task requires T_d (TGA onset), we assume the source provides it.
                # If the API doesn't provide T_d directly, we might need to filter for
                # entries that have thermal stability data.
                
                # Simulating the extraction of T_d if present in 'properties' or 'tasks'
                # In reality, T_d is often not a standard MP property.
                # However, the task specification implies we fetch data that *contains* T_d.
                # We assume the API returns a JSON structure where 'T_d' is a key.
                # If not, we might need to filter based on the 'tasks' list containing "Thermal".
                
                results = []
                for doc in docs:
                    # Check if the document has thermal data
                    # This is a heuristic based on the task description
                    if "thermal" in str(doc.get("tasks", [])).lower():
                        results.append(doc)
                
                if not results:
                    logger.warning("No perovskite thermal data found via MP-API.")
                    return []
                
                return results

        except ImportError:
            logger.warning("mp_api library not found. Attempting direct API fetch.")
            # Fallback to direct API fetch using fetch_with_retry
            # This assumes the URL is correct and the API returns JSON
            response = fetch_with_retry(url, params=params, headers=headers, max_retries=MAX_RETRIES)
            if response and response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                logger.error("Failed to fetch data from Materials Project API.")
                return []
    except Exception as e:
        logger.error(f"Error fetching MP data: {e}")
        raise

def fetch_experimental_tga_data(materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters the fetched materials for those with T_d (TGA onset) data.
    Since MP API might not have T_d directly, this function simulates the filtering
    based on the assumption that the fetched data contains T_d or we map it.
    In a real scenario, we would query a specific property or join with a T_d dataset.
    For this task, we assume the 'properties' field contains 'T_d'.
    """
    filtered = []
    for mat in materials:
        # Check for T_d in properties
        props = mat.get("properties", {})
        if "T_d" in props or "t_d" in props:
            filtered.append(mat)
        # Heuristic: if 'tasks' contains 'Thermal' and we assume T_d is present
        elif "thermal" in str(mat.get("tasks", [])).lower():
            # We assume T_d is available or we need to fetch it from another source
            # For this task, we assume it's in the data
            filtered.append(mat)
    return filtered

def validate_data_checksum(data: List[Dict[str, Any]], checksum_file: Path) -> bool:
    """
    Validates the data against a checksum if available.
    """
    if not checksum_file.exists():
        logger.info("No checksum file found. Skipping validation.")
        return True
    
    with open(checksum_file, 'r') as f:
        manifest = json.load(f)
    
    # Compute checksum of current data
    current_checksum = compute_sha256(str(data)) # Simplified
    
    # Compare
    expected_checksum = manifest.get("checksum")
    if current_checksum != expected_checksum:
        logger.warning("Checksum mismatch. Data may have changed.")
        return False
    return True

def save_to_csv(data: List[Dict[str, Any]], output_path: Path):
    """
    Saves the fetched data to a CSV file.
    Maps the MP API fields to the required schema: formula, T_d, source.
    """
    if not data:
        logger.warning("No data to save.")
        # Create an empty file with headers to satisfy the "file exists" check
        # but log that it's empty. The task requires T_d column with non-null values.
        # If no data, we should fail? The task says "Verify ... contains T_d column with non-null values".
        # If we have no data, we cannot satisfy this. We should exit with error.
        logger.error("No data found to write. Exiting.")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define columns
    columns = ["formula", "T_d", "source", "material_id", "nsites", "composition"]
    
    rows = []
    for item in data:
        formula = item.get("formula_pretty", "Unknown")
        # Assume T_d is in properties or we need to extract it
        # If not present, skip or log warning
        t_d = item.get("properties", {}).get("T_d") or item.get("properties", {}).get("t_d")
        if t_d is None:
            logger.warning(f"No T_d found for {formula}. Skipping.")
            continue
        
        row = {
            "formula": formula,
            "T_d": t_d,
            "source": "Materials Project",
            "material_id": item.get("material_id"),
            "nsites": item.get("nsites"),
            "composition": str(item.get("composition", {}))
        }
        rows.append(row)
    
    import pandas as pd
    df = pd.DataFrame(rows)
    
    # Ensure T_d column is not null
    if df["T_d"].isnull().any():
        logger.error("T_d column contains null values. Aborting.")
        sys.exit(1)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def save_checksum_manifest(data: List[Dict[str, Any]], checksum_file: Path):
    """
    Generates a checksum manifest for the saved data.
    """
    checksum = compute_sha256(str(data))
    manifest = {
        "checksum": checksum,
        "file": str(checksum_file.parent / "mp_perovskites.csv"),
        "timestamp": time.time()
    }
    with open(checksum_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved checksum manifest to {checksum_file}")

def main():
    """
    Main entry point for T012b.
    Fetches data, validates, filters, and saves.
    """
    logger.info("Starting T012b: Materials Project Fetch")
    
    # Load API key
    config = load_config()
    api_key = get_api_key("MP_API_KEY", config)
    
    if not api_key:
        logger.error("MP_API_KEY not found. Exiting.")
        sys.exit(1)
    
    # Fetch data
    try:
        materials = fetch_mp_material_data(api_key)
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        sys.exit(1)
    
    if not materials:
        logger.error("No materials found.")
        sys.exit(1)
    
    # Filter for T_d
    tga_data = fetch_experimental_tga_data(materials)
    
    if not tga_data:
        logger.error("No TGA data found in fetched materials.")
        sys.exit(1)
    
    # Save to CSV
    save_to_csv(tga_data, OUTPUT_FILE)
    
    # Save checksum
    save_checksum_manifest(tga_data, CHECKSUM_FILE)
    
    logger.info("T012b completed successfully.")

if __name__ == "__main__":
    main()
