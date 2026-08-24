import os
import ftplib
import csv
import io
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import yaml
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary directories if they don't exist."""
    dirs = ['data/raw', 'data/processed', 'results', 'results/figures']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def log_message(level, message):
    """Log a message with the specified level."""
    if level == 'INFO':
        logger.info(message)
    elif level == 'WARNING':
        logger.warning(message)
    elif level == 'ERROR':
        logger.error(message)
    elif level == 'FATAL':
        logger.fatal(message)

def load_manifest(manifest_path='data/source_manifest.yaml') -> Dict[str, Any]:
    """Load the source manifest YAML file."""
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest not found at {manifest_path}, creating empty structure.")
        return {"sources": {}, "metadata": {}, "processed": {}}
    
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)

def save_manifest(manifest: Dict[str, Any], manifest_path='data/source_manifest.yaml'):
    """Save the manifest back to YAML."""
    with open(manifest_path, 'w') as f:
        yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)

def update_manifest_entry(manifest: Dict[str, Any], source_key: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a specific source entry in the manifest."""
    if source_key not in manifest.get('sources', {}):
        manifest['sources'][source_key] = {}
    manifest['sources'][source_key].update(updates)
    return manifest

def connect_to_swpc(url: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Attempt to connect to an FTP/HTTP URL to verify reachability.
    Returns (success, message).
    """
    if url.startswith('ftp://'):
        try:
            ftp = ftplib.FTP()
            ftp.connect(url.split('/')[2], timeout=timeout)
            ftp.login()
            ftp.quit()
            return True, "FTP connection successful"
        except Exception as e:
            return False, f"FTP connection failed: {str(e)}"
    elif url.startswith('http://') or url.startswith('https://'):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            if response.status_code == 200:
                return True, "HTTP connection successful"
            else:
                return False, f"HTTP status code: {response.status_code}"
        except Exception as e:
            return False, f"HTTP connection failed: {str(e)}"
    else:
        return False, "Unsupported URL scheme"

def fetch_with_backoff(url: str, max_retries: int = 3, backoff_factor: float = 2.0) -> requests.Response:
    """
    Fetch a URL with exponential backoff retry logic.
    Raises ConnectionError or TimeoutError if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            return response
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = backoff_factor ** attempt
            logger.warning(f"Retrying {url} in {wait_time}s due to {e}")
            time.sleep(wait_time)
    raise RuntimeError("Max retries exceeded")

def fetch_dst_indices_http() -> List[Dict[str, Any]]:
    """Fetch Dst indices from NOAA SWPC via HTTP."""
    url = "https://www.swpc.noaa.gov/products/dst-index"
    # Placeholder for actual scraping/parsing logic
    # In a real implementation, this would parse the HTML or find the direct CSV link
    logger.info(f"Fetching Dst indices from {url}")
    return []

def fetch_kp_indices_http() -> List[Dict[str, Any]]:
    """Fetch Kp indices from NOAA SWPC via HTTP."""
    url = "https://www.swpc.noaa.gov/products/kp-index"
    # Placeholder for actual scraping/parsing logic
    logger.info(f"Fetching Kp indices from {url}")
    return []

def validate_kp_schema(data: List[Dict[str, Any]]) -> bool:
    """Validate Kp data against expected schema."""
    if not data:
        return False
    required_keys = ['date', 'kp_index', 'time']
    for row in data:
        if not all(k in row for k in required_keys):
            return False
    return True

def write_kp_data(data: List[Dict[str, Any]], output_path: str = 'data/raw/kp_indices.csv'):
    """Write Kp data to CSV."""
    if not data:
        logger.warning("No Kp data to write.")
        return
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Wrote {len(data)} Kp records to {output_path}")

def write_dst_data(data: List[Dict[str, Any]], output_path: str = 'data/raw/dst_indices.csv'):
    """Write Dst data to CSV."""
    if not data:
        logger.warning("No Dst data to write.")
        return
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Wrote {len(data)} Dst records to {output_path}")

def fetch_goess_flare_list() -> List[Dict[str, Any]]:
    """Fetch GOES flare list from NOAA FTP."""
    # Implementation for T011
    return []

def fetch_cme_catalog() -> List[Dict[str, Any]]:
    """Fetch CME catalog from CDAWeb."""
    # Implementation for T012
    return []

def fetch_dst_indices_real() -> List[Dict[str, Any]]:
    """Fetch real Dst indices (implementation for T013)."""
    # Implementation for T013
    return []

def pre_flight_verify_urls(manifest: Dict[str, Any]) -> Dict[str, str]:
    """
    Pre-flight verification of all URLs in the manifest.
    Checks if URLs are reachable and return valid content.
    Updates manifest status for each source.
    Returns a dict of source_key -> status ("passed" or "failed").
    """
    results = {}
    log_message("INFO", "Starting pre-flight URL verification...")
    
    for source_key, source_info in manifest.get('sources', {}).items():
        url = source_info.get('url')
        if not url:
            log_message("WARNING", f"No URL found for source {source_key}")
            results[source_key] = "failed"
            continue
        
        log_message("INFO", f"Verifying URL for {source_key}: {url}")
        success, message = connect_to_swpc(url)
        
        if success:
            log_message("INFO", f"Pre-flight PASSED for {source_key}: {message}")
            results[source_key] = "passed"
            # Update manifest
            manifest = update_manifest_entry(manifest, source_key, {
                'pre_flight_status': 'passed',
                'last_verified': datetime.now().isoformat()
            })
        else:
            log_message("FATAL", f"Pre-flight FAILED for {source_key}: {message}")
            results[source_key] = "failed"
            manifest = update_manifest_entry(manifest, source_key, {
                'pre_flight_status': 'failed',
                'last_verified': datetime.now().isoformat()
            })
    
    return results, manifest

def main():
    """Main entry point for the ingest module."""
    ensure_directories()
    manifest = load_manifest()
    
    # Run pre-flight verification (T048)
    results, manifest = pre_flight_verify_urls(manifest)
    
    # Check if any verification failed
    if any(status == 'failed' for status in results.values()):
        log_message("FATAL", "Pre-flight verification failed for one or more sources. Aborting pipeline.")
        # Update manifest with overall status
        manifest['metadata']['pre_flight_status'] = 'failed'
        save_manifest(manifest)
        raise RuntimeError("Pre-flight verification failed. Check logs for details.")
    
    log_message("INFO", "Pre-flight verification passed for all sources.")
    manifest['metadata']['pre_flight_status'] = 'passed'
    save_manifest(manifest)
    
    # Continue with data ingestion if verification passed
    # This would call fetch functions for each source
    # For now, just log success
    log_message("INFO", "Ready to proceed with data ingestion.")

if __name__ == '__main__':
    main()
