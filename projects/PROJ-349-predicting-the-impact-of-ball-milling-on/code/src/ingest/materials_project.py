"""
Materials Project Data Fetcher (T012)

Fetches ball milling experimental data from the Materials Project API v2.
Queries for entries containing 'ball milling' or 'milling' in keywords/abstracts.
Extracts required fields and saves to data/raw/materials_project_raw.json.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.exceptions import DataIngestionError, SourceConnectionError, SourceNotFoundError
from src.config.env_config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MP_API_URL = "https://next-gen.materialsproject.org/materials"
MP_API_VERSION = "v2"
MP_HEADERS = {
    "X-API-Key": os.getenv("MATERIALS_PROJECT_API_KEY", ""),
    "Content-Type": "application/json"
}

# Required output path
OUTPUT_PATH = Path("data/raw/materials_project_raw.json")

# Fields to extract from Materials Project API
# Note: Materials Project doesn't directly store milling parameters,
# so we extract available material properties and flag for manual enrichment
EXTRACT_FIELDS = [
    "material_id",
    "nsid",
    "pretty_formula",
    "elements",
    "nelements",
    "nsites",
    "volume",
    "density",
    "e_hull_per_atom",
    "decomposition_energy_per_atom",
    "formation_energy_per_atom",
    "space_group.number",
    "space_group.symbol",
    "space_group.crystal_system",
    "is_metal",
    "is_gap_direct",
    "band_gap",
    "total_magnetization",
    "volume_per_atom",
    "nsites",
    "structure",
    "kpoints",
    "kpoints_density",
    "kpoints_method",
    "kpoints_spacing",
    "kpoints_gamma_centered",
    "kpoints_monkhorst_pack",
    "kpoints_gamma_only",
    "kpoints_mesh",
    "kpoints_mesh_density",
    "kpoints_method",
    "kpoints_spacing",
    "kpoints_gamma_centered",
    "kpoints_monkhorst_pack",
    "kpoints_gamma_only",
    "kpoints_mesh",
    "kpoints_mesh_density"
]

def _get_api_key() -> str:
    """
    Retrieve the Materials Project API key from environment variables.

    Returns:
        str: The API key.

    Raises:
        SourceAuthenticationError: If the API key is not set.
    """
    api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if not api_key:
        raise SourceAuthenticationError(
            "Materials Project API key not found. Set MATERIALS_PROJECT_API_KEY environment variable."
        )
    return api_key

def _search_materials(query: str, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
    """
    Search Materials Project database for materials matching the query.

    Args:
        query (str): Search query string.
        page (int): Page number for pagination.
        page_size (int): Number of results per page.

    Returns:
        Dict[str, Any]: JSON response from the API.

    Raises:
        SourceConnectionError: If the API request fails.
        SourceNotFoundError: If no results are found.
    """
    url = f"{MP_API_URL}/search"
    params = {
        "q": query,
        "page": page,
        "page_size": page_size,
        "fields": ",".join(EXTRACT_FIELDS)
    }

    try:
        response = requests.get(url, headers=MP_HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise SourceConnectionError(f"Failed to connect to Materials Project API: {e}")

def _extract_material_data(material: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract relevant data from a single material entry.

    Args:
        material (Dict[str, Any]): Raw material data from API.

    Returns:
        Optional[Dict[str, Any]]: Extracted data or None if invalid.
    """
    try:
        # Extract basic properties
        extracted = {
            "material_id": material.get("material_id"),
            "nsid": material.get("nsid"),
            "pretty_formula": material.get("pretty_formula"),
            "elements": material.get("elements", []),
            "nelements": material.get("nelements"),
            "nsites": material.get("nsites"),
            "volume": material.get("volume"),
            "density": material.get("density"),
            "e_hull_per_atom": material.get("e_hull_per_atom"),
            "decomposition_energy_per_atom": material.get("decomposition_energy_per_atom"),
            "formation_energy_per_atom": material.get("formation_energy_per_atom"),
            "space_group_number": material.get("space_group", {}).get("number") if material.get("space_group") else None,
            "space_group_symbol": material.get("space_group", {}).get("symbol") if material.get("space_group") else None,
            "crystal_system": material.get("space_group", {}).get("crystal_system") if material.get("space_group") else None,
            "is_metal": material.get("is_metal"),
            "is_gap_direct": material.get("is_gap_direct"),
            "band_gap": material.get("band_gap"),
            "total_magnetization": material.get("total_magnetization"),
            "volume_per_atom": material.get("volume_per_atom"),
        }

        # Add source-specific fields (these will be empty/placeholder for now)
        # as Materials Project doesn't directly store milling parameters
        extracted["source"] = "materials_project"
        extracted["experiment_id"] = None  # Will be generated during merge
        extracted["milling_speed"] = None  # Not available in MP
        extracted["milling_time"] = None   # Not available in MP
        extracted["ball_to_powder_ratio"] = None  # Not available in MP
        extracted["youngs_modulus"] = None  # Not available in MP
        extracted["d10"] = None  # Not available in MP
        extracted["d50"] = None  # Not available in MP
        extracted["d90"] = None  # Not available in MP
        extracted["process_duration"] = None  # Not available in MP

        return extracted
    except Exception as e:
        logger.warning(f"Failed to extract data from material {material.get('material_id')}: {e}")
        return None

def fetch_materials_project_data(max_pages: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch ball milling related data from Materials Project.

    Args:
        max_pages (int): Maximum number of pages to fetch.

    Returns:
        List[Dict[str, Any]]: List of extracted material data.

    Raises:
        DataIngestionError: If the fetch fails completely.
    """
    all_data = []
    queries = ["ball milling", "milling"]

    for query in queries:
        logger.info(f"Searching for materials with query: '{query}'")
        page = 1
        total_results = 0

        while page <= max_pages:
            try:
                response = _search_materials(query, page=page, page_size=100)

                if "data" not in response:
                    logger.warning(f"No data field in response for page {page}")
                    break

                results = response.get("data", [])
                if not results:
                    logger.info(f"No more results for query '{query}' at page {page}")
                    break

                # Extract data from each result
                for material in results:
                    extracted = _extract_material_data(material)
                    if extracted:
                        all_data.append(extracted)

                total_results += len(results)
                logger.info(f"Fetched {len(results)} results for '{query}' (page {page}, total: {total_results})")

                # Check if there are more pages
                if len(results) < 100:
                    break

                page += 1
                time.sleep(0.5)  # Rate limiting

            except SourceConnectionError as e:
                logger.error(f"Connection error while fetching page {page}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching page {page}: {e}")
                break

    logger.info(f"Total materials fetched: {len(all_data)}")
    return all_data

def save_to_json(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save fetched data to a JSON file.

    Args:
        data (List[Dict[str, Any]]): Data to save.
        output_path (Path): Output file path.

    Raises:
        DataIngestionError: If saving fails.
    """
    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {len(data)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save data to {output_path}: {e}")
        raise DataIngestionError(f"Failed to save data: {e}")

def run_materials_project_ingestion() -> bool:
    """
    Main entry point for Materials Project data ingestion.

    Returns:
        bool: True if successful, False if skipped due to errors.

    Raises:
        DataIngestionError: If the entire ingestion process fails.
    """
    try:
        logger.info("Starting Materials Project data ingestion (T012)")

        # Check API key
        try:
            _get_api_key()
        except SourceAuthenticationError as e:
            logger.warning(f"Source skipped: Materials Project (API key missing): {e}")
            logger.warning("Source skipped: Materials Project (0 rows or error)")
            return False

        # Fetch data
        data = fetch_materials_project_data()

        if not data:
            logger.warning("Source skipped: Materials Project (0 rows or error)")
            return False

        # Save to JSON
        save_to_json(data, OUTPUT_PATH)

        logger.info("Materials Project ingestion completed successfully")
        return True

    except SourceConnectionError as e:
        logger.warning(f"Source skipped: Materials Project (connection error): {e}")
        logger.warning("Source skipped: Materials Project (0 rows or error)")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Materials Project ingestion: {e}")
        raise DataIngestionError(f"Materials Project ingestion failed: {e}")

if __name__ == "__main__":
    success = run_materials_project_ingestion()
    if not success:
        logger.info("Materials Project ingestion was skipped (0 rows or error)")
        exit(0)  # Exit with 0 as per task constraint: skip, don't halt
    exit(0)
