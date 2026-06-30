import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout

# Constants for retry logic
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 30.0  # seconds
TIMEOUT_SECONDS = 30

def setup_download_logging() -> logging.Logger:
    """Configure and return a logger for download operations."""
    logger = logging.getLogger("download")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def fetch_mp_structure(mp_id: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Fetch a crystal structure from Materials Project by MP-ID.
    
    Args:
        mp_id: Materials Project ID (e.g., 'mp-12345')
        logger: Logger instance
        
    Returns:
        Structure data dict or None if failed
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.warning("MP_API_KEY not set, skipping Materials Project fetch")
        return None

    url = f"https://materialsproject.org/rest/v2/materials/{mp_id}/structure"
    headers = {"X-API-Key": api_key}
    params = {"pretty": "true"}

    attempt = 0
    last_exception = None
    
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Fetching MP structure {mp_id} (attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            if "response" in data and "structures" in data["response"]:
                return data["response"]["structures"][0]
            else:
                logger.warning(f"No structure found in MP response for {mp_id}")
                return None
        except (Timeout, RequestException) as e:
            last_exception = e
            attempt += 1
            if attempt < MAX_RETRIES:
                delay = min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)
                logger.warning(f"MP fetch failed for {mp_id}: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(f"MP fetch failed for {mp_id} after {MAX_RETRIES} attempts: {e}")
    
    return None

def fetch_obelix_structure(composition: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Fetch defect data from OBELiX by composition.
    
    Args:
        composition: Chemical composition string (e.g., 'LiLaO2')
        logger: Logger instance
        
    Returns:
        Defect data dict or None if failed
    """
    # Simulated OBELiX endpoint (replace with actual URL when available)
    # Using a mock implementation that returns None to indicate missing data
    # as per T013 requirements for handling missing OBELiX data
    url = f"https://obelix.example.com/api/v1/defects?composition={composition}"
    
    attempt = 0
    last_exception = None
    
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Fetching OBELiX data for {composition} (attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            return data
        except (Timeout, RequestException) as e:
            last_exception = e
            attempt += 1
            if attempt < MAX_RETRIES:
                delay = min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)
                logger.warning(f"OBELiX fetch failed for {composition}: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(f"OBELiX fetch failed for {composition} after {MAX_RETRIES} attempts: {e}")
                logger.info(f"Proceeding with DFT-computed values as per T013")
    
    return None

def save_structure(structure_data: Dict[str, Any], output_path: Path, logger: logging.Logger) -> bool:
    """
    Save structure data to a JSON file.
    
    Args:
        structure_data: Structure data dictionary
        output_path: Path to save the file
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(structure_data, f, indent=2)
        logger.info(f"Saved structure to {output_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to save structure to {output_path}: {e}")
        return False

def download_all_structures(
    mp_ids: List[str],
    compositions: List[str],
    output_dir: Path,
    logger: logging.Logger
) -> Dict[str, bool]:
    """
    Download structures for all given MP-IDs and compositions.
    
    Args:
        mp_ids: List of Materials Project IDs
        compositions: List of chemical compositions for OBELiX
        output_dir: Directory to save downloaded files
        logger: Logger instance
        
    Returns:
        Dict mapping identifier to success status
    """
    results = {}
    
    # Download MP structures
    for mp_id in mp_ids:
        structure = fetch_mp_structure(mp_id, logger)
        if structure:
            output_path = output_dir / f"{mp_id}.json"
            results[mp_id] = save_structure(structure, output_path, logger)
        else:
            results[mp_id] = False
            logger.warning(f"Failed to download MP structure {mp_id}")
    
    # Download OBELiX data
    for comp in compositions:
        data = fetch_obelix_structure(comp, logger)
        if data:
            output_path = output_dir / f"{comp}_obelix.json"
            results[comp] = save_structure(data, output_path, logger)
        else:
            results[comp] = False
            logger.warning(f"Failed to download OBELiX data for {comp}")
    
    return results

def main():
    """Main entry point for download script."""
    logger = setup_download_logging()
    logger.info("Starting structure download process")
    
    # Example configuration - in real usage, load from config.yaml
    mp_ids = ["mp-12345", "mp-67890"]
    compositions = ["LiLaO2", "LiNbO3"]
    output_dir = Path("data/raw/structures")
    
    results = download_all_structures(mp_ids, compositions, output_dir, logger)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    logger.info(f"Download complete: {success_count}/{total_count} successful")
    
    if success_count < total_count:
        logger.warning("Some downloads failed. Check logs for details.")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())