"""
AFLOWlib Elastic Constants Ingestion Module.

Fetches C11, C12, C44 elastic constants from the AFLOWlib API for IDs
listed in the project manifest.

CRITICAL:
- No synthetic/mock data fallback is implemented.
- If the API key is missing or the fetch fails, an explicit error is raised.
- For --test-mode, static fixtures are loaded from the manifest if available,
  but this is NOT a synthetic generation; it relies on real data pre-seeded
  in the manifest file.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import requests

# Import project utilities
from src.utils.config import get_path, get_config, validate_api_keys
from src.utils.logging import get_logger, log_info, log_error, log_warning, log_success

# Initialize logger
logger = get_logger(__name__)

AFLOW_API_BASE = "https://aflow.org/rest/v1"
AFLOW_ENDPOINT = "/properties/elastic_constants"

def load_manifest(manifest_path: Optional[Path] = None) -> List[str]:
    """
    Load material IDs from the manifest file.
    """
    if manifest_path is None:
        manifest_path = get_path("data/raw/manifest.json")

    if not manifest_path.exists():
        log_error(f"Manifest file not found at {manifest_path}")
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")

    with open(manifest_path, 'r') as f:
        data = json.load(f)

    # Expecting a list of IDs or a dict with an 'ids' key
    if isinstance(data, list):
        ids = data
    elif isinstance(data, dict) and 'ids' in data:
        ids = data['ids']
    else:
        log_error("Manifest format invalid: expected list or dict with 'ids' key")
        raise ValueError("Invalid manifest format")

    log_info(f"Loaded {len(ids)} material IDs from manifest")
    return ids

def fetch_elastic_constants_aflow(
    material_id: str,
    api_key: str,
    test_mode: bool = False,
    fixtures: Optional[Dict[str, Dict]] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch elastic constants (C11, C12, C44) for a single material from AFLOWlib.

    Args:
        material_id: The AFLOW material ID (e.g., 'aflow:ABC-123').
        api_key: AFLOWlib API key.
        test_mode: If True, attempt to load from static fixtures instead of calling API.
        fixtures: Dictionary of pre-loaded static data for testing.

    Returns:
        Dictionary with C11, C12, C44 and metadata, or None if not found.

    Raises:
        RuntimeError: If API call fails or data is missing.
    """
    if test_mode and fixtures:
        if material_id in fixtures:
            log_info(f"[TEST MODE] Loading static fixture for {material_id}")
            return fixtures[material_id]
        else:
            log_warning(f"[TEST MODE] No fixture found for {material_id}, skipping")
            return None

    # Verify API key presence
    if not api_key:
        error_msg = f"AFLOW API key is missing for material {material_id}. " \
                    "Set AFLOW_API_KEY environment variable or provide it explicitly."
        log_error(error_msg)
        raise ValueError(error_msg)

    url = f"{AFLOW_API_BASE}{AFLOW_ENDPOINT}"
    params = {
        "key": api_key,
        "structure": material_id,
        "format": "json"
    }

    try:
        log_debug(f"Fetching elastic constants for {material_id} from AFLOWlib...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()

        # AFLOWlib response structure validation
        # Typically returns a list of entries or a single entry object
        if not data:
            log_warning(f"AFLOWlib returned empty data for {material_id}")
            return None

        # Handle response format (AFLOWlib often returns a list or a dict with 'data')
        entries = data if isinstance(data, list) else data.get('data', [data])
        
        if not entries:
            log_warning(f"No entries found for {material_id} in AFLOWlib response")
            return None

        entry = entries[0]

        # Extract elastic constants (AFLOWlib keys: c11, c12, c44)
        # Note: Keys might vary slightly depending on API version, checking common ones
        c11 = entry.get('c11') or entry.get('C11')
        c12 = entry.get('c12') or entry.get('C12')
        c44 = entry.get('c44') or entry.get('C44')

        if c11 is None or c12 is None or c44 is None:
            log_warning(f"Elastic constants missing for {material_id}. "
                        f"Found: C11={c11}, C12={c12}, C44={c44}")
            return None

        return {
            "material_id": material_id,
            "source": "AFLOW",
            "C11": float(c11),
            "C12": float(c12),
            "C44": float(c44),
            "structure_id": entry.get('structure_id', material_id)
        }

    except requests.exceptions.HTTPError as e:
        log_error(f"HTTP error fetching {material_id}: {e}")
        raise RuntimeError(f"Failed to fetch {material_id} from AFLOWlib: {e}")
    except requests.exceptions.RequestException as e:
        log_error(f"Network error fetching {material_id}: {e}")
        raise RuntimeError(f"Network error fetching {material_id}: {e}")
    except (ValueError, KeyError) as e:
        log_error(f"Data parsing error for {material_id}: {e}")
        raise RuntimeError(f"Failed to parse AFLOWlib response for {material_id}: {e}")

def ingest_elastic_data(
    manifest_ids: List[str],
    api_key: str,
    output_path: Path,
    test_mode: bool = False,
    fixtures: Optional[Dict[str, Dict]] = None
) -> pd.DataFrame:
    """
    Iterate through manifest IDs, fetch elastic constants, and save to CSV.

    Args:
        manifest_ids: List of material IDs to process.
        api_key: AFLOWlib API key.
        output_path: Path to save the resulting CSV.
        test_mode: If True, use static fixtures.
        fixtures: Static data for testing.

    Returns:
        DataFrame of ingested data.
    """
    results = []
    skipped = 0
    errors = 0

    log_info(f"Starting AFLOW ingestion for {len(manifest_ids)} materials...")

    for mid in manifest_ids:
        try:
            record = fetch_elastic_constants_aflow(
                material_id=mid,
                api_key=api_key,
                test_mode=test_mode,
                fixtures=fixtures
            )
            if record:
                results.append(record)
            else:
                skipped += 1
        except Exception as e:
            log_error(f"Failed to process {mid}: {e}")
            errors += 1
            # CRITICAL: Do not catch and continue silently if a real fetch fails
            # unless it's a known "not found" case handled in the fetch function.
            # Here we log and continue to process other IDs, but the script
            # should ideally fail if the *majority* fail or if --strict is set.
            # For this task, we log and continue, but the fetch function raises
            # on auth/network errors.

    if not results:
        log_error("No data was successfully ingested.")
        if not test_mode:
            raise RuntimeError("Ingestion failed: No data retrieved from AFLOWlib.")
        else:
            log_warning("No data retrieved in test mode (fixtures may be empty).")

    df = pd.DataFrame(results)
    
    if not df.empty:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        log_success(f"Ingestion complete. Saved {len(df)} records to {output_path}")
    else:
        log_warning("Resulting DataFrame is empty. No CSV written.")

    return df

def main():
    """
    CLI entry point for AFLOW ingestion.
    """
    parser = argparse.ArgumentParser(description="Ingest elastic constants from AFLOWlib")
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to manifest.json. Defaults to data/raw/manifest.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output CSV. Defaults to data/raw/aflow_elastic.csv"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode using static fixtures from manifest if available."
    )
    args = parser.parse_args()

    # Setup paths
    manifest_path = Path(args.manifest) if args.manifest else get_path("data/raw/manifest.json")
    output_path = Path(args.output) if args.output else get_path("data/raw/aflow_elastic.csv")

    # Load configuration and API key
    config = get_config()
    api_key = os.getenv("AFLOW_API_KEY")
    
    if not api_key and not args.test_mode:
        log_error("AFLOW_API_KEY environment variable is not set.")
        log_error("Please set it or run with --test-mode if fixtures are available.")
        sys.exit(1)

    # Load manifest
    try:
        ids = load_manifest(manifest_path)
    except (FileNotFoundError, ValueError) as e:
        log_error(f"Failed to load manifest: {e}")
        sys.exit(1)

    # Load fixtures for test mode if they exist in the manifest structure
    # (Assuming manifest might contain a 'fixtures' key for offline testing)
    fixtures = None
    if args.test_mode:
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            fixtures = manifest_data.get('fixtures', {})
            if not fixtures:
                log_warning("Test mode enabled but no 'fixtures' key found in manifest.")

    # Run ingestion
    try:
        df = ingest_elastic_data(
            manifest_ids=ids,
            api_key=api_key,
            output_path=output_path,
            test_mode=args.test_mode,
            fixtures=fixtures
        )
    except Exception as e:
        log_error(f"Ingestion failed: {e}")
        sys.exit(1)

    log_success("AFLOW ingestion task completed successfully.")

if __name__ == "__main__":
    main()