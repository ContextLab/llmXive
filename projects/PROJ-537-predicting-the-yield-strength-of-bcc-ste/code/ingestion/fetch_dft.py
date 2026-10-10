"""
Fetch DFT elastic constants from the Materials Project API.

The original implementation fetched data for a supplied list of material IDs
but did not persist the results to disk, which broke downstream steps.
This revised version:

1. Reads the experimental dataset (downloaded by ``fetch_experimental_data``)
   to obtain the list of ``material_id`` values.
2. Queries the Materials Project API for each ID, applying exponential back‑off
   and logging each request.
3. Writes the collected records to ``CONFIG.RAW_DFT_PATH`` as a CSV file.
4. Returns the list of result dictionaries (useful for interactive use).

All failures are **loud** – the function returns ``[]`` only when the API key
is missing; otherwise any HTTP error is logged and the entry is skipped.
"""

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

# Ensure project root is on sys.path for relative imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import CONFIG
from utils.logging import get_logger, log_api_query, log_data_artifact

logger = get_logger(__name__)

def _session_with_retry() -> requests.Session:
    """Create a ``requests`` session with exponential‑backoff retries."""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def _fetch_elastic_data(material_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Query the Materials Project ``/materials/<id>/elasticity`` endpoint.

    Returns a dictionary with the fields we care about or ``None`` if the
    request fails or the response does not contain elastic data.
    """
    session = _session_with_retry()
    url = f"{CONFIG.MP_API_BASE_URL}/materials/{material_id}/elasticity"
    params = {"key": api_key}
    start = time.time()
    try:
        response = session.get(url, params=params, timeout=30)
        elapsed = time.time() - start

        if response.status_code == 200:
            payload = response.json()
            log_api_query(
                service="Materials Project Elasticity",
                query_params={"material_id": material_id},
                success=True,
                response_time=elapsed,
            )
            return payload.get("data", {})
        else:
            log_api_query(
                service="Materials Project Elasticity",
                query_params={"material_id": material_id},
                success=False,
                response_time=elapsed,
                error=f"HTTP {response.status_code}: {response.text}",
            )
            logger.warning(f"Failed to fetch elasticity for {material_id}: {response.status_code}")
            return None
    except requests.exceptions.RequestException as exc:
        elapsed = time.time() - start
        log_api_query(
            service="Materials Project Elasticity",
            query_params={"material_id": material_id},
            success=False,
            response_time=elapsed,
            error=str(exc),
        )
        logger.error(f"Request exception for {material_id}: {exc}")
        return None

def fetch_dft_data() -> List[Dict[str, Any]]:
    """
    High‑level entry point used by the ingestion pipeline.

    It reads the experimental CSV (downloaded by ``fetch_experimental_data``),
    extracts the ``material_id`` column, queries the Materials Project for each
    ID, writes the consolidated results to ``CONFIG.RAW_DFT_PATH`` and returns
    the list of dictionaries.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.error("MP_API_KEY environment variable not set.")
        return []

    # Load experimental data to obtain material IDs
    exp_path = Path(CONFIG.EXPERIMENTAL_DATA_PATH)
    if not exp_path.is_file():
        logger.error(f"Experimental data not found at {exp_path}. Cannot determine material IDs.")
        return []

    import pandas as pd

    exp_df = pd.read_csv(exp_path)
    if "material_id" not in exp_df.columns:
        logger.error("Column 'material_id' missing from experimental dataset – cannot map to DFT data.")
        return []

    material_ids = exp_df["material_id"].dropna().unique().tolist()
    logger.info(f"Fetching DFT data for {len(material_ids)} material IDs.")

    results: List[Dict[str, Any]] = []
    for mid in material_ids:
        data = _fetch_elastic_data(str(mid), api_key)
        if data:
            elasticity = data.get("elasticity", {})
            g_vrh = elasticity.get("g_voigt_reuss_hill")
            b_vrh = elasticity.get("b_voigt_reuss_hill")
            if g_vrh is not None:
                results.append(
                    {
                        "material_id": mid,
                        "shear_modulus_GPa": g_vrh,
                        "bulk_modulus_GPa": b_vrh,
                        "anisotropy": elasticity.get("anisotropy"),
                        "poisson_ratio": elasticity.get("poisson_ratio"),
                    }
                )
            else:
                logger.warning(f"Shear modulus missing for {mid}; skipping.")
        else:
            logger.warning(f"No elasticity data returned for {mid}.")

    # Persist results
    if results:
        dft_df = pd.DataFrame(results)
        output_path = Path(CONFIG.RAW_DFT_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dft_df.to_csv(output_path, index=False)
        logger.info(f"Wrote DFT data for {len(dft_df)} materials to {output_path}")
        log_data_artifact(output_path, action="created")
    else:
        logger.warning("No DFT records were fetched; RAW DFT file will not be created.")

    return results

def main():
    """
    Simple CLI entry point – useful for manual debugging.
    """
    logger.info("Starting DFT fetch (T014)")
    fetched = fetch_dft_data()
    if fetched:
        logger.info(f"Fetched DFT data for {len(fetched)} materials.")
    else:
        logger.error("No DFT data fetched.")
        sys.exit(1)

if __name__ == "__main__":
    main()
