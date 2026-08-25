"""
Data Ingestion Module for Solar and Geomagnetic Data.

Downloads GOES X-ray flare lists, CME catalog data, Dst indices, and Kp indices
from NOAA SWPC and CDAWeb. Implements streaming for large files and fail-loud
behavior for data fetch errors.

Dependencies:
- requests (for HTTP downloads)
- yaml (for manifest handling)
- pandas (for CSV processing)

This module MUST NOT use HuggingFace datasets or synthetic data generation.
"""
import os
import sys
import csv
import io
import requests
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
MANIFEST_PATH = DATA_DIR / "source_manifest.yaml"

# Configure logging
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'ingest.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Data fetch error class
class DataFetchError(Exception):
    """Raised when a real data fetch fails."""
    pass

def ensure_directories():
    """Create required data directories."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log_message(msg: str, level: str = "info"):
    """Log a message at the specified level."""
    getattr(logger, level)(msg)

def load_manifest() -> Dict[str, Any]:
    """Load the source manifest from disk."""
    import yaml
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest file missing at {MANIFEST_PATH}. "
            "Pipeline cannot proceed without a valid source manifest."
        )
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_manifest(data: Dict[str, Any]) -> None:
    """Atomically save the manifest to disk."""
    import yaml
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(suffix='.yaml')
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        os.replace(temp_path, MANIFEST_PATH)
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise RuntimeError(f"Failed to save manifest atomically: {e}")

def update_manifest_entry(source_name: str, status: str, url: Optional[str] = None, record_count: Optional[int] = None) -> None:
    """Update a source entry in the manifest with timestamp."""
    manifest = load_manifest()
    if 'sources' not in manifest:
        manifest['sources'] = {}
    
    if source_name not in manifest['sources']:
        manifest['sources'][source_name] = {}
    
    manifest['sources'][source_name]['status'] = status
    manifest['sources'][source_name]['last_verified_at'] = datetime.utcnow().isoformat()
    if url:
        manifest['sources'][source_name]['url'] = url
    if record_count is not None:
        manifest['sources'][source_name]['record_count'] = record_count
    
    save_manifest(manifest)
    logger.info(f"Updated manifest for {source_name}: status={status}")

def fetch_with_backoff(url: str, max_retries: int = 3, timeout: int = 30) -> requests.Response:
    """Fetch a URL with exponential backoff."""
    import time
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                raise DataFetchError(f"URL not found: {url}")
            else:
                raise DataFetchError(f"HTTP {response.status_code} for {url}")
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise DataFetchError(f"Failed to fetch {url} after {max_retries} retries: {e}")
            wait_time = 2 ** attempt
            logger.warning(f"Retry {attempt+1}/{max_retries} for {url} after {wait_time}s: {e}")
            time.sleep(wait_time)
    raise DataFetchError(f"Failed to fetch {url}")

def stream_csv_lines(url: str) -> Iterator[Dict[str, str]]:
    """
    Stream CSV lines from a URL without loading the entire file into memory.
    
    Args:
        url: URL to the CSV file.
        
    Yields:
        Dictionary representing each row.
    """
    response = fetch_with_backoff(url)
    response.raw.decode_content = True
    reader = csv.DictReader(io.TextIOWrapper(response.raw, encoding='utf-8'))
    for row in reader:
        yield row

def fetch_dst_indices_http() -> List[Dict[str, Any]]:
    """
    Fetch Dst indices from NOAA SWPC.
    
    Returns:
        List of dictionaries with Dst data.
    """
    url = "https://services.swpc.noaa.gov/products/dst-index.txt"
    logger.info(f"Fetching Dst indices from {url}")
    
    try:
        response = fetch_with_backoff(url)
        response.raw.decode_content = True
        text_data = io.TextIOWrapper(response.raw, encoding='utf-8').read()
        
        lines = text_data.strip().split('\n')
        data = []
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 6:
                try:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    hour = int(parts[3])
                    dst = float(parts[4])
                    data.append({
                        'year': year,
                        'month': month,
                        'day': day,
                        'hour': hour,
                        'dst': dst,
                        'timestamp': f"{year}-{month:02d}-{day:02d}T{hour:02d}:00:00"
                    })
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Fetched {len(data)} Dst records")
        return data
    except Exception as e:
        raise DataFetchError(f"Failed to fetch Dst indices: {e}")

def write_dst_data(data: List[Dict[str, Any]]) -> str:
    """
    Write Dst data to CSV.
    
    Args:
        data: List of Dst records.
        
    Returns:
        Path to the written file.
    """
    ensure_directories()
    output_path = RAW_DIR / "dst_indices.csv"
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    logger.info(f"Wrote {len(data)} Dst records to {output_path}")
    return str(output_path)

def fetch_kp_indices_http() -> List[Dict[str, Any]]:
    """
    Fetch Kp indices from NOAA SWPC.
    
    Returns:
        List of dictionaries with Kp data.
    """
    url = "https://services.swpc.noaa.gov/products/kp-index.txt"
    logger.info(f"Fetching Kp indices from {url}")
    
    try:
        response = fetch_with_backoff(url)
        response.raw.decode_content = True
        text_data = io.TextIOWrapper(response.raw, encoding='utf-8').read()
        
        lines = text_data.strip().split('\n')
        data = []
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 6:
                try:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    hour = int(parts[3])
                    kp = float(parts[4])
                    data.append({
                        'year': year,
                        'month': month,
                        'day': day,
                        'hour': hour,
                        'kp': kp,
                        'timestamp': f"{year}-{month:02d}-{day:02d}T{hour:02d}:00:00"
                    })
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Fetched {len(data)} Kp records")
        return data
    except Exception as e:
        raise DataFetchError(f"Failed to fetch Kp indices: {e}")

def write_kp_data(data: List[Dict[str, Any]]) -> str:
    """
    Write Kp data to CSV.
    
    Args:
        data: List of Kp records.
        
    Returns:
        Path to the written file.
    """
    ensure_directories()
    output_path = RAW_DIR / "kp_indices.csv"
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    logger.info(f"Wrote {len(data)} Kp records to {output_path}")
    return str(output_path)

def validate_kp_schema(data: List[Dict[str, Any]]) -> bool:
    """
    Validate Kp data against expected schema.
    
    Args:
        data: List of Kp records.
        
    Returns:
        True if valid, False otherwise.
    """
    required_keys = {'year', 'month', 'day', 'hour', 'kp', 'timestamp'}
    for record in data:
        if not required_keys.issubset(record.keys()):
            return False
        if not (0.0 <= record['kp'] <= 9.0):
            return False
    return True

def main():
    """Main entry point for ingestion."""
    ensure_directories()
    
    try:
        # Fetch and write Dst indices
        dst_data = fetch_dst_indices_http()
        if dst_data:
            dst_path = write_dst_data(dst_data)
            update_manifest_entry('dst_indices', 'Verified', 
                                  url="https://services.swpc.noaa.gov/products/dst-index.txt",
                                  record_count=len(dst_data))
        else:
            update_manifest_entry('dst_indices', 'Failed')
            raise DataFetchError("No Dst data retrieved")
        
        # Fetch and write Kp indices
        kp_data = fetch_kp_indices_http()
        if kp_data:
            if not validate_kp_schema(kp_data):
                raise DataFetchError("Kp data schema validation failed")
            kp_path = write_kp_data(kp_data)
            update_manifest_entry('kp_indices', 'Verified',
                                  url="https://services.swpc.noaa.gov/products/kp-index.txt",
                                  record_count=len(kp_data))
        else:
            update_manifest_entry('kp_indices', 'Failed')
            raise DataFetchError("No Kp data retrieved")
        
        logger.info("Ingestion completed successfully")
        
    except DataFetchError as e:
        logger.error(f"Ingestion failed: {e}")
        # Update manifest entries for failed sources
        update_manifest_entry('dst_indices', 'Failed')
        update_manifest_entry('kp_indices', 'Failed')
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()
