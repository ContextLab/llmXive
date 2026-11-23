import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.config import get_path, validate_api_keys, get_config
from src.utils.logging import get_logger, setup_logger

logger = get_logger(__name__)

def load_manifest(manifest_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the list of material IDs from the manifest file."""
    if manifest_path is None:
        manifest_path = get_path("data_raw") / "manifest.json"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    return data.get("materials", [])

def fetch_elastic_constants(material_id: str, api_key: str) -> Dict[str, Any]:
    """
    Fetch elastic constants (C11, C12, C44) from Materials Project API.
    
    Endpoint: /materials/v1/elasticity
    
    Raises:
      ValueError: If API key is missing or invalid.
      RuntimeError: If fetch fails or data is missing.
    """
    # Validate API key explicitly
    if not api_key:
        raise ValueError(f"API Key is missing for Material ID {material_id}. "
                         "Set MP_API_KEY environment variable.")
    
    import requests
    
    url = f"https://api.materialsproject.org/v1/materials/{material_id}/elasticity"
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    logger.debug(f"Fetching elasticity data for {material_id} from MP API...")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP Error fetching {material_id}: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network Error fetching {material_id}: {e}")
    
    # Extract elastic constants
    # MP API structure: {'data': {'elasticity': {'eigenvalues': [...], 'tensor': [...]}}}
    # We need the Voigt notation tensor or specific components.
    # Standard MP elasticity response includes 'elastic_tensor_voigt' which is [C11, C12, C13, C14, C15, C16, C22, C23, C24, C25, C26, C33, C34, C35, C36, C44, C45, C46, C55, C56, C66]
    
    if 'data' not in data:
        raise RuntimeError(f"Unexpected response format for {material_id}: missing 'data' key")
    
    elasticity_data = data['data'].get('elasticity', {})
    tensor = elasticity_data.get('elastic_tensor_voigt')
    
    if not tensor or len(tensor) < 6:
        raise RuntimeError(f"Missing or incomplete elastic tensor for {material_id}")
    
    # Voigt notation mapping: 
    # 0: C11, 1: C12, 2: C13, ... 5: C16
    # 6: C22, 7: C23, ...
    # 15: C44
    
    # For cubic crystals: C11, C12, C44 are the independent components.
    # C11 = tensor[0], C12 = tensor[1], C44 = tensor[15]
    
    c11 = tensor[0]
    c12 = tensor[1]
    c44 = tensor[15]
    
    return {
        "material_id": material_id,
        "C11": c11,
        "C12": c12,
        "C44": c44,
        "source": "Materials Project"
    }

def ingest_elastic_data(
    manifest_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    test_mode: bool = False
) -> pd.DataFrame:
    """
    Ingest elastic data from Materials Project for all IDs in the manifest.
    
    Args:
        manifest_path: Path to manifest.json.
        output_path: Path to save the output CSV.
        test_mode: If True, load static fixtures from manifest (assuming manifest contains
                   pre-fetched data or a specific test structure). 
                   NOTE: Per T012a spec, test_mode loads static fixtures from manifest, 
                   NOT synthetic mocks. If manifest only has IDs, this function will still 
                   attempt fetch unless we assume a specific test fixture structure in manifest.
                   To support --test-mode robustly without API, we check if manifest has 
                   pre-filled 'elasticity' data. If not, we raise error in test mode if API fails,
                   or we assume the user provided a 'fixtures' key in manifest for offline testing.
    
    Returns:
        DataFrame with columns: material_id, C11, C12, C44, source
    """
    if output_path is None:
        output_path = get_path("data_processed") / "mp_elastic_raw.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    materials = load_manifest(manifest_path)
    
    if not materials:
        logger.warning("No materials found in manifest.")
        return pd.DataFrame(columns=["material_id", "C11", "C12", "C44", "source"])
    
    results = []
    api_key = os.getenv("MP_API_KEY")
    
    # If test_mode is True, we expect the manifest to contain the actual data 
    # or we skip API calls. However, the spec says "load static fixtures from manifest".
    # We will assume if 'elasticity' data is present in the manifest entry, we use it.
    # If not, and test_mode is True, we raise an error indicating API is needed or 
    # manifest needs fixtures.
    
    for mat in materials:
        mid = mat["material_id"]
        logger.info(f"Processing {mid}...")
        
        if test_mode:
            # Check if fixture data exists in manifest entry
            if "elasticity" in mat:
                el_data = mat["elasticity"]
                entry = {
                    "material_id": mid,
                    "C11": el_data.get("C11"),
                    "C12": el_data.get("C12"),
                    "C44": el_data.get("C44"),
                    "source": "Materials Project (Fixture)"
                }
                if entry["C11"] is None:
                    logger.warning(f"Fixture for {mid} missing C11, skipping.")
                    continue
                results.append(entry)
                continue
            else:
                # In test mode without fixture, we cannot fetch. 
                # Spec says "load static fixtures from manifest". If not present, 
                # and we can't fetch (no API), we must fail loudly or skip?
                # Spec: "If API key missing or fetch fails, raise explicit error."
                # But for test mode, we assume the manifest IS the fixture source.
                # If it's not there, it's a configuration error for test mode.
                logger.error(f"Test mode enabled but no fixture data found for {mid} in manifest.")
                raise RuntimeError(f"Test mode failed: No fixture data for {mid}. "
                                   "Add 'elasticity' key to manifest entry or disable test mode.")
        
        # Normal mode: Fetch from API
        if not api_key:
            raise ValueError(f"MP_API_KEY not set. Cannot fetch data for {mid}.")
        
        try:
            entry = fetch_elastic_constants(mid, api_key)
            results.append(entry)
        except (ValueError, RuntimeError) as e:
            logger.error(f"Failed to fetch {mid}: {e}")
            # Per spec: "If API key missing or fetch fails, raise explicit error."
            # We log and raise to stop the pipeline, ensuring no silent failure.
            raise e
    
    df = pd.DataFrame(results)
    if not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} entries to {output_path}")
    else:
        logger.warning("No data ingested. Output file may be empty.")
        # Still create empty file with headers? Or skip? 
        # Usually better to create empty file with headers for pipeline consistency.
        pd.DataFrame(columns=["material_id", "C11", "C12", "C44", "source"]).to_csv(output_path, index=False)
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Ingest elastic data from Materials Project")
    parser.add_argument("--manifest", type=str, help="Path to manifest.json")
    parser.add_argument("--output", type=str, help="Path to output CSV")
    parser.add_argument("--test-mode", action="store_true", help="Use static fixtures from manifest")
    
    args = parser.parse_args()
    
    manifest_path = Path(args.manifest) if args.manifest else None
    output_path = Path(args.output) if args.output else None
    
    setup_logger(level=logging.INFO)
    
    if args.test_mode:
        logger.info("Running in TEST MODE. Loading fixtures from manifest.")
    
    try:
        ingest_elastic_data(
            manifest_path=manifest_path,
            output_path=output_path,
            test_mode=args.test_mode
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()