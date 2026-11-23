"""
Download Mg-B entries from the Materials Project API.

This module fetches magnesium diboride (MgB2) related entries,
handles rate limiting, verifies cached files via checksums,
and attaches provenance metadata.

Constraints:
- Must raise RuntimeError if no MgB2 entries are found.
- Must NOT generate synthetic fallback data.
- Must handle caching and checksum verification.
"""
import os
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.utils.config import get_materials_project_api_key, get_project_root
from code.src.utils.logging import get_ingestion_logger
from code.src.utils.data_provenance import generate_provenance_header

logger = get_ingestion_logger(__name__)

# Configuration
MATERIALS_PROJECT_API_URL = "https://api.materialsproject.org/v2/materials"
RATE_LIMIT_DELAY = 1.0  # seconds between requests
CACHE_DIR = Path("data/raw")
CACHE_FILENAME = "materials_project_mgb2_raw.json"
OUTPUT_FILENAME = "materials_project_mgb2_processed.json"
TIMEOUT_SECONDS = 30

def _calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _verify_cache(cache_path: Path) -> bool:
    """
    Verify if cached file exists and is valid.
    Returns True if cache is valid and provenance can be attached.
    Returns False if cache is missing or invalid (checksum mismatch).
    """
    if not cache_path.exists():
        logger.info(f"Cache file not found: {cache_path}")
        return False

    # Check for corresponding checksum file
    checksum_file = cache_path.with_suffix(cache_path.suffix + ".sha256")
    if not checksum_file.exists():
        logger.warning(f"Checksum file missing for {cache_path}, treating as invalid")
        return False

    try:
        with open(checksum_file, "r") as f:
            stored_checksum = f.read().strip()
        
        current_checksum = _calculate_file_checksum(cache_path)
        
        if stored_checksum != current_checksum:
            logger.error(f"Checksum mismatch for {cache_path}: stored={stored_checksum}, current={current_checksum}")
            return False
        
        logger.info(f"Cache verified successfully: {cache_path}")
        return True
    except Exception as e:
        logger.error(f"Error verifying cache: {e}")
        return False

def _save_with_checksum(data: List[Dict], cache_path: Path) -> None:
    """Save data to JSON and create checksum file."""
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    checksum = _calculate_file_checksum(cache_path)
    checksum_file = cache_path.with_suffix(cache_path.suffix + ".sha256")
    with open(checksum_file, "w") as f:
        f.write(checksum)
    
    logger.info(f"Saved {len(data)} entries to {cache_path} with checksum {checksum[:16]}...")

def _attach_provenance(cache_path: Path) -> None:
    """Attach provenance header to the processed output file."""
    processed_path = cache_path.parent / OUTPUT_FILENAME
    
    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    provenance_info = {
        "source": "materials_project",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0",
        "file": str(cache_path.name),
        "checksum": _calculate_file_checksum(cache_path)
    }
    
    provenance_header = generate_provenance_header(
        source="materials_project",
        timestamp=provenance_info["timestamp"],
        version=provenance_info["version"]
    )
    
    # Prepend provenance header to JSON
    with open(processed_path, "w", encoding="utf-8") as f:
        f.write(provenance_header + "\n")
        json.dump(data, f, indent=2)
    
    logger.info(f"Attached provenance header to {processed_path}")

def fetch_materials_project_entries(
    api_key: str,
    elements: List[str] = None,
    bandgap: Optional[float] = None,
    num_entries: Optional[int] = 1000
) -> List[Dict[str, Any]]:
    """
    Fetch entries from Materials Project API.
    
    Args:
        api_key: Materials Project API key
        elements: List of chemical elements to filter (e.g., ['Mg', 'B'])
        bandgap: Optional bandgap filter
        num_entries: Maximum number of entries to fetch
        
    Returns:
        List of material entries
        
    Raises:
        RuntimeError: If API returns empty results for Mg-B system
        requests.RequestException: If API request fails
    """
    if elements is None:
        elements = ['Mg', 'B']
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "elements": ",".join(elements),
        "fields": "materials_id,formula,pretty_formula,structure,nsites,band_gap,e_final,e_hull,decomposition_energy,thermodynamic_stability,is_stable,space_group.number,space_group.symbol,structure.formula_pretty",
        "limit": num_entries or 1000,
        "all_keywords": "true"
    }
    
    logger.info(f"Fetching Mg-B entries from Materials Project API...")
    logger.debug(f"API URL: {MATERIALS_PROJECT_API_URL}/search")
    
    try:
        # Use the search endpoint for element filtering
        search_url = f"{MATERIALS_PROJECT_API_URL}/search"
        response = requests.get(search_url, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 401:
            logger.error("API key invalid or expired. Check your Materials Project API key.")
            raise RuntimeError("Invalid Materials Project API key")
        elif response.status_code == 429:
            logger.error("Rate limit exceeded. Please wait and retry.")
            raise RuntimeError("Rate limit exceeded")
        elif response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            raise RuntimeError(f"API request failed: {response.status_code}")
        
        data = response.json()
        
        if "data" not in data or len(data["data"]) == 0:
            logger.error("No Mg-B entries found in Materials Project API response")
            raise RuntimeError("No MgB2 entries found in Materials Project API")
        
        entries = data["data"]
        logger.info(f"Retrieved {len(entries)} entries from Materials Project")
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        
        return entries
        
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        raise RuntimeError("API request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise RuntimeError(f"API request failed: {e}")

def filter_mgb2_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter entries to keep only MgB2-related compounds.
    
    Args:
        entries: List of material entries from API
        
    Returns:
        Filtered list of MgB2 entries
    """
    mgb2_entries = []
    
    for entry in entries:
        formula = entry.get("formula", "").lower()
        pretty_formula = entry.get("pretty_formula", "").lower()
        
        # Check for MgB2 or Mg-B compounds with stoichiometry close to 1:2
        if "mgb2" in formula or "mgb2" in pretty_formula:
            mgb2_entries.append(entry)
        elif "mg" in formula and "b" in formula:
            # Additional check for stoichiometry
            try:
                # Parse formula to check Mg:B ratio
                import re
                mg_match = re.search(r'Mg(\d*)', formula)
                b_match = re.search(r'B(\d*)', formula)
                
                if mg_match and b_match:
                    mg_count = int(mg_match.group(1)) if mg_match.group(1) else 1
                    b_count = int(b_match.group(1)) if b_match.group(1) else 1
                    
                    # Accept if ratio is close to 1:2 (within 20%)
                    if mg_count > 0 and b_count > 0:
                        ratio = b_count / mg_count
                        if 1.6 <= ratio <= 2.4:  # Allow some tolerance
                            mgb2_entries.append(entry)
            except Exception as e:
                logger.debug(f"Could not parse formula {formula}: {e}")
                # Keep entry if it contains Mg and B but parsing fails
                mgb2_entries.append(entry)
    
    logger.info(f"Filtered to {len(mgb2_entries)} MgB2-related entries")
    return mgb2_entries

def save_entries_to_json(entries: List[Dict[str, Any]], output_path: Path) -> None:
    """Save entries to JSON file with provenance."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    
    logger.info(f"Saved {len(entries)} entries to {output_path}")

def main():
    """Main entry point for downloading Materials Project data."""
    project_root = get_project_root()
    cache_path = project_root / CACHE_DIR / CACHE_FILENAME
    processed_path = project_root / CACHE_DIR / OUTPUT_FILENAME
    
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for API key
    try:
        api_key = get_materials_project_api_key()
        if not api_key:
            logger.error("Materials Project API key not found. Set MP_API_KEY environment variable.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error retrieving API key: {e}")
        sys.exit(1)
    
    # Check cache first
    if _verify_cache(cache_path):
        logger.info("Using cached data, attaching provenance...")
        _attach_provenance(cache_path)
        sys.exit(0)
    
    # Fetch fresh data
    try:
        entries = fetch_materials_project_entries(api_key)
        
        if not entries:
            logger.error("No entries retrieved from Materials Project API")
            sys.exit(1)
        
        # Filter for MgB2
        mgb2_entries = filter_mgb2_entries(entries)
        
        if not mgb2_entries:
            logger.error("No MgB2 entries found after filtering")
            sys.exit(1)
        
        # Save to cache
        _save_with_checksum(mgb2_entries, cache_path)
        
        # Attach provenance
        _attach_provenance(cache_path)
        
        logger.info(f"Successfully downloaded and processed {len(mgb2_entries)} MgB2 entries")
        sys.exit(0)
        
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()