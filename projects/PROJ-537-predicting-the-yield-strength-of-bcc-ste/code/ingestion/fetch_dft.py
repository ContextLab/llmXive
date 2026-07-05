import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CONFIG
from utils.logging import get_logger, log_api_query

logger = get_logger(__name__)

def get_session_with_retry() -> requests.Session:
    """
    Create a requests session with exponential backoff retry logic.
    """
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_elastic_data(material_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch elastic constants for a specific material from Materials Project API.
    """
    session = get_session_with_retry()
    url = f"{CONFIG.MP_API_BASE_URL}/materials/{material_id}/elasticity"
    params = {"key": api_key}

    start_time = time.time()
    try:
        response = session.get(url, params=params, timeout=30)
        response_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            # Log success
            log_api_query(
                service="Materials Project Elasticity",
                query_params={"material_id": material_id},
                success=True,
                response_time=response_time
            )
            return data.get("data", {})
        else:
            # Log failure
            log_api_query(
                service="Materials Project Elasticity",
                query_params={"material_id": material_id},
                success=False,
                response_time=response_time,
                error=f"HTTP {response.status_code}: {response.text}"
            )
            logger.warning(f"Failed to fetch elasticity for {material_id}: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        response_time = time.time() - start_time
        log_api_query(
            service="Materials Project Elasticity",
            query_params={"material_id": material_id},
            success=False,
            response_time=response_time,
            error=str(e)
        )
        logger.error(f"Request exception for {material_id}: {e}")
        return None

def fetch_dft_data(material_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch DFT elastic data for a list of material IDs.
    Returns a list of dictionaries containing material_id, shear_modulus, bulk_modulus, etc.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.error("MP_API_KEY environment variable not set.")
        return []

    results = []
    logger.info(f"Fetching DFT data for {len(material_ids)} materials.")

    for mid in material_ids:
        data = fetch_elastic_data(mid, api_key)
        if data:
            # Extract relevant fields
            # Assuming the API returns 'elasticity' object with 'g_voigt_reuss_hill' etc.
            # Adjust based on actual API response structure if needed
            elasticity = data.get("elasticity", {})
            g_vrh = elasticity.get("g_voigt_reuss_hill")
            b_vrh = elasticity.get("b_voigt_reuss_hill")

            if g_vrh is not None:
                results.append({
                    "material_id": mid,
                    "shear_modulus_GPa": g_vrh,
                    "bulk_modulus_GPa": b_vrh,
                    "anisotropy": elasticity.get("anisotropy"),
                    "poisson_ratio": elasticity.get("poisson_ratio")
                })
            else:
                logger.warning(f"Shear modulus missing for {mid}. Skipping.")
        else:
            logger.warning(f"No data retrieved for {mid}. Skipping.")

    return results

def main():
    """
    Main entry point for testing the DFT fetcher.
    In a real pipeline, this would be called by merge_and_filter.py.
    """
    # Example: Fetch a few known BCC materials (Fe, Cr, W, etc.)
    # In reality, this list comes from the experimental dataset matching
    test_ids = ["mp-13", "mp-19138", "mp-2248"] # Fe, Cr, W example IDs
    data = fetch_dft_data(test_ids)
    if data:
        print(json.dumps(data, indent=2))
    else:
        print("No data fetched.")

if __name__ == "__main__":
    main()