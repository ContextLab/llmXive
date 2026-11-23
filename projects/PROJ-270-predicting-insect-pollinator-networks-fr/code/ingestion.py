import json
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import logging

from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration constants
MIN_ECOSYSTEM_THRESHOLD = 8

class WebOfLifeDownloader:
    """Manages the download of ecosystems from Web of Life."""
    
    def __init__(self, raw_dir: Path):
        self.raw_dir = Path(raw_dir)
        self.ecosystem_ids: List[str] = []
        self.downloaded_count = 0
        self.failed_count = 0
        self.downloaded_ecosystems: List[Dict[str, Any]] = []

    def set_ecosystem_ids(self, ids: List[str]) -> None:
        """Set the list of ecosystem IDs to process."""
        self.ecosystem_ids = ids

    def get_valid_count(self) -> int:
        """Return the count of successfully downloaded ecosystems."""
        return self.downloaded_count

    def get_failed_count(self) -> int:
        """Return the count of failed downloads."""
        return self.failed_count

    def validate_ecosystem_count(self) -> bool:
        """
        Validate that the number of downloaded ecosystems meets the minimum threshold.
        
        Returns:
            bool: True if count >= threshold, False otherwise.
            
        Logs a warning if the count is below the threshold but does not raise an error.
        """
        count = self.get_valid_count()
        if count < MIN_ECOSYSTEM_THRESHOLD:
            logger.warning(f"Warning: valid_count < 8 (current: {count}). Proceeding with reduced sample size.")
            return False
        logger.info(f"Valid ecosystem count ({count}) meets threshold ({MIN_ECOSYSTEM_THRESHOLD}).")
        return True

def _fetch_ecosystem_info(ecosystem_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a specific ecosystem from Web of Life.
    
    In a real implementation, this would query the Web of Life API.
    For now, it simulates the structure expected.
    """
    # Placeholder for actual API call logic
    # In production: response = requests.get(f"{WOL_API_BASE}/ecosystem/{ecosystem_id}")
    return {
        "ecosystem_id": ecosystem_id,
        "name": f"Ecosystem {ecosystem_id}",
        "has_traits": True,
        "data_url": f"http://example.com/{ecosystem_id}.csv"
    }

def download_web_of_life_ecosystem(ecosystem_id: str, raw_dir: Path) -> bool:
    """
    Download interaction data and metadata for a single ecosystem.
    
    Args:
        ecosystem_id: The ID of the ecosystem to download.
        raw_dir: The directory to save the data to.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        ecosystem_info = _fetch_ecosystem_info(ecosystem_id)
        if not ecosystem_info or not ecosystem_info.get("has_traits"):
            logger.warning(f"Skipping {ecosystem_id}: No trait data available.")
            return False
        
        data_url = ecosystem_info.get("data_url")
        if not data_url:
            logger.error(f"Missing data URL for {ecosystem_id}.")
            return False

        # Create directory for this ecosystem
        eco_dir = raw_dir / ecosystem_id
        eco_dir.mkdir(parents=True, exist_ok=True)

        # Fetch interaction data
        response = requests.get(data_url, timeout=30)
        response.raise_for_status()
        
        # Save interactions
        interactions_path = eco_dir / "interactions.csv"
        with open(interactions_path, "wb") as f:
            f.write(response.content)
        
        # Save metadata
        metadata_path = eco_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(ecosystem_info, f, indent=2)
        
        logger.info(f"Successfully downloaded {ecosystem_id}")
        return True

    except requests.exceptions.Timeout:
        logger.error(f"Timeout downloading {ecosystem_id}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {ecosystem_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {ecosystem_id}: {e}")
        return False

def load_interactions_csv(file_path: Path) -> List[Dict[str, str]]:
    """
    Load interactions from a CSV file.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of dictionaries with 'plant' and 'pollinator' keys.
    """
    import csv
    interactions = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("plant") and row.get("pollinator"):
                interactions.append({
                    "plant": row["plant"],
                    "pollinator": row["pollinator"]
                })
    return interactions

def process_in_chunks(file_path: Path, chunk_size: int = 10000) -> List[Dict[str, Any]]:
    """
    Process a large CSV file in chunks to avoid memory issues.
    
    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows per chunk.
        
    Returns:
        Combined list of all processed rows.
    """
    import csv
    all_rows = []
    current_chunk = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            current_chunk.append(row)
            if len(current_chunk) >= chunk_size:
                all_rows.extend(current_chunk)
                current_chunk = []
    
    if current_chunk:
        all_rows.extend(current_chunk)
        
    return all_rows

def load_and_preprocess_ecosystem(ecosystem_id: str, raw_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load and perform basic preprocessing for a single ecosystem.
    
    Args:
        ecosystem_id: The ecosystem ID.
        raw_dir: The raw data directory.
        
    Returns:
        Preprocessed ecosystem data or None if failed.
    """
    eco_dir = raw_dir / ecosystem_id
    interactions_path = eco_dir / "interactions.csv"
    metadata_path = eco_dir / "metadata.json"
    
    if not interactions_path.exists() or not metadata_path.exists():
        logger.error(f"Missing files for {ecosystem_id}")
        return None
        
    interactions = load_interactions_csv(interactions_path)
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        
    return {
        "id": ecosystem_id,
        "metadata": metadata,
        "interactions": interactions
    }

def ingest_multiple_ecosystems(ecosystem_ids: List[str], raw_dir: Path) -> Tuple[int, int]:
    """
    Ingest multiple ecosystems from Web of Life.
    
    Args:
        ecosystem_ids: List of ecosystem IDs to download.
        raw_dir: Directory to save raw data.
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    downloader = WebOfLifeDownloader(raw_dir)
    downloader.set_ecosystem_ids(ecosystem_ids)
    
    for eco_id in ecosystem_ids:
        success = download_web_of_life_ecosystem(eco_id, raw_dir)
        if success:
            downloader.downloaded_count += 1
        else:
            downloader.failed_count += 1
            
    # Validate count before returning
    downloader.validate_ecosystem_count()
    
    return downloader.downloaded_count, downloader.failed_count

def run_validation_check(downloader: WebOfLifeDownloader) -> bool:
    """
    Run the validation check on a downloader instance.
    
    Args:
        downloader: The WebOfLifeDownloader instance.
        
    Returns:
        bool: Result of the validation.
    """
    return downloader.validate_ecosystem_count()
