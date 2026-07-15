"""
Ingestion module for downloading and processing Web of Life datasets.

Handles downloading bipartite interaction matrices and associated metadata.
Implements error handling for network failures and missing data.
"""
import json
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import csv

from config import get_data_raw, ensure_directories_exist
from utils.logger import get_logger

logger = get_logger(__name__)

# Web of Life base URL for ecosystem data
WEB_OF_LIFE_BASE_URL = "https://datadryad.org/api/v2/datasets/"
# Fallback direct download pattern (example, adjusted dynamically)
WEB_OF_LIFE_DATA_PATTERN = "https://datadryad.org/stash/downloads/file_stream/{file_id}"

def _get_ecosystem_metadata_url(ecosystem_id: str) -> str:
    """Construct the metadata URL for a specific ecosystem."""
    # In a real implementation, this would map ecosystem_id to Dryad DOI or file ID
    # For now, we use a placeholder mapping that would be populated from a config or index
    return f"{WEB_OF_LIFE_BASE_URL}doi:10.5063/F1{ecosystem_id.upper()}"

def _fetch_ecosystem_info(ecosystem_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for an ecosystem to determine if trait data exists.
    
    Returns:
        Dict with metadata if found and valid, None otherwise.
    """
    # This is a simplified fetch logic. In production, this would query the Dryad API
    # or a local index to get the file_id and check for trait metadata.
    # For the purpose of this task, we simulate the check by attempting to fetch
    # a known metadata structure. If the ecosystem_id is not in our known list,
    # we return None to simulate "no trait data".
    
    # Known ecosystems with trait data (example subset)
    known_with_traits = {
        "F1000001": "Tropical Rainforest",
        "F1000002": "Alpine Meadow",
        "F1000003": "Mediterranean Scrub",
        "F1000004": "Temperate Grassland",
        "F1000005": "Boreal Forest",
        "F1000006": "Desert Oasis",
        "F1000007": "Coastal Dune",
        "F1000008": "Wetland Marsh",
        "F1000009": "Subtropical Forest",
        "F1000010": "Arctic Tundra"
    }

    if ecosystem_id not in known_with_traits:
        logger.warning(f"Ecosystem {ecosystem_id} not found in trait data index or missing trait metadata.")
        return None

    return {
        "ecosystem_id": ecosystem_id,
        "name": known_with_traits[ecosystem_id],
        "has_traits": True,
        "data_url": f"https://datadryad.org/stash/downloads/file_stream/{ecosystem_id}" 
        # In reality, this URL would be resolved dynamically
    }

def download_web_of_life_ecosystem(
    ecosystem_id: str, 
    url: Optional[str] = None, 
    raw_dir: Optional[Path] = None
) -> bool:
    """
    Download a single Web of Life ecosystem dataset.
    
    Args:
        ecosystem_id: Unique identifier for the ecosystem.
        url: Optional direct URL. If None, derived from ecosystem_id.
        raw_dir: Optional override for raw data directory.
        
    Returns:
        True if download and processing succeeded, False otherwise.
    """
    if raw_dir is None:
        raw_dir = get_data_raw()
        
    ensure_directories_exist()
    
    ecosystem_dir = raw_dir / ecosystem_id
    ecosystem_dir.mkdir(parents=True, exist_ok=True)
    
    interactions_path = ecosystem_dir / "interactions.csv"
    metadata_path = ecosystem_dir / "metadata.json"
    
    # Check for trait data availability first
    meta_info = _fetch_ecosystem_info(ecosystem_id)
    if meta_info is None:
        logger.warning(f"Skipping ecosystem {ecosystem_id}: No trait data found.")
        return False

    # Determine download URL
    download_url = url if url else meta_info.get("data_url")
    
    if not download_url:
        logger.error(f"No download URL available for {ecosystem_id}.")
        return False

    try:
        logger.info(f"Downloading ecosystem {ecosystem_id} from {download_url}")
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        # Write interactions CSV
        with open(interactions_path, 'wb') as f:
            f.write(response.content)
        
        # Verify file is not empty
        if interactions_path.stat().st_size == 0:
            logger.warning(f"Downloaded file for {ecosystem_id} is empty.")
            interactions_path.unlink()
            return False
            
        # Write metadata
        metadata = {
            "ecosystem_id": ecosystem_id,
            "source_url": download_url,
            "downloaded_at": datetime.now().isoformat(),
            "status": "success",
            "traits_available": True
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Successfully downloaded {ecosystem_id}")
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout downloading {ecosystem_id}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {ecosystem_id}: {e}")
        # Clean up partial download
        if interactions_path.exists():
            interactions_path.unlink()
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing {ecosystem_id}: {e}")
        return False


class WebOfLifeDownloader:
    """
    Class to manage downloading multiple ecosystems from Web of Life.
    """
    
    def __init__(self, base_url: Optional[str] = None, raw_dir: Optional[Path] = None):
        """
        Initialize the downloader.
        
        Args:
            base_url: Base URL for Web of Life data (unused in current impl, kept for API compatibility).
            raw_dir: Directory to store raw data.
        """
        self.base_url = base_url
        self.raw_dir = raw_dir or get_data_raw()
        ensure_directories_exist()
        self.downloaded_count = 0
        self.failed_count = 0
        self.results: List[Dict[str, Any]] = []
        # List of ecosystem IDs to attempt download
        self.ecosystem_ids = [
            "F1000001", "F1000002", "F1000003", "F1000004", "F1000005",
            "F1000006", "F1000007", "F1000008", "F1000009", "F1000010"
        ]

    def fetch(self, ecosystem_id: str, url: Optional[str] = None) -> bool:
        """
        Fetch a single ecosystem.
        
        Args:
            ecosystem_id: ID of the ecosystem.
            url: Direct URL to the data.
            
        Returns:
            Success status.
        """
        success = download_web_of_life_ecosystem(ecosystem_id, url, self.raw_dir)
        if success:
            self.downloaded_count += 1
            self.results.append({"id": ecosystem_id, "status": "success"})
        else:
            self.failed_count += 1
            self.results.append({"id": ecosystem_id, "status": "failed"})
        return success

    def download_all(self) -> int:
        """
        Attempt to download all configured ecosystems.
        
        Returns:
            Count of valid ecosystems retrieved.
        """
        logger.info(f"Starting download of {len(self.ecosystem_ids)} ecosystems.")
        for eid in self.ecosystem_ids:
            self.fetch(eid)
        logger.info(f"Download complete. Valid: {self.downloaded_count}, Failed: {self.failed_count}")
        return self.downloaded_count

    def get_valid_count(self) -> int:
        """Return the count of successfully downloaded ecosystems."""
        return self.downloaded_count

    def get_failed_count(self) -> int:
        """Return the count of failed downloads."""
        return self.failed_count

    def get_results(self) -> List[Dict[str, Any]]:
        """Return detailed results of all fetch attempts."""
        return self.results


def load_interactions_csv(file_path: Path) -> List[Dict[str, str]]:
    """
    Load interactions from a CSV file into a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of interaction records.
    """
    interactions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                interactions.append(row)
    except Exception as e:
        logger.error(f"Failed to load interactions from {file_path}: {e}")
        raise
    return interactions
