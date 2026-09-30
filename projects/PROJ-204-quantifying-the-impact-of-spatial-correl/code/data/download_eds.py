"""
Conditional download script for EDS maps.

This script implements T011: Conditional Download.
It checks the result of T010 (state/data_feasibility_status.yaml).
If T010 succeeded, it fetches EDS maps from the verified URL and Zenodo,
saving raw files to data/raw/.
If T010 failed, it skips the download and exits gracefully.

Real data sources:
- Verified URL from T010 (NREL Perovskite Database or Zenodo DOI)
- Zenodo record containing EDS elemental maps for perovskite solar cells
"""

import os
import sys
import logging
import yaml
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'download_eds.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_feasibility_status() -> Dict[str, Any]:
    """Load the T010 feasibility status file."""
    status_path = project_root / 'state' / 'data_feasibility_status.yaml'
    
    if not status_path.exists():
        logger.error(f"Feasibility status file not found: {status_path}")
        logger.error("T010 must complete successfully before T011 can run.")
        return {"success": False, "reason": "Status file missing"}
    
    try:
        with open(status_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load feasibility status: {e}")
        return {"success": False, "reason": str(e)}

def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file from URL to output_path with progress logging."""
    try:
        logger.info(f"Downloading from {url} to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Successfully downloaded {output_path.name} ({downloaded} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False

def download_from_zenodo(record_id: str, output_dir: Path) -> int:
    """
    Download files from a Zenodo record.
    
    Args:
        record_id: Zenodo record ID (e.g., '1234567')
        output_dir: Directory to save downloaded files
        
    Returns:
        Number of successfully downloaded files
    """
    api_url = f"https://zenodo.org/api/records/{record_id}"
    
    try:
        logger.info(f"Fetching Zenodo record metadata: {api_url}")
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        record_data = response.json()
        files = record_data.get('files', [])
        
        if not files:
            logger.warning(f"No files found in Zenodo record {record_id}")
            return 0
        
        downloaded_count = 0
        for file_entry in files:
            file_name = file_entry.get('key', 'unknown')
            download_url = file_entry.get('links', {}).get('self')
            
            if not download_url:
                logger.warning(f"No download URL for file {file_name}")
                continue
            
            output_path = output_dir / file_name
            
            if download_file(download_url, output_path):
                downloaded_count += 1
            else:
                logger.error(f"Failed to download {file_name}")
        
        return downloaded_count
        
    except Exception as e:
        logger.error(f"Error processing Zenodo record {record_id}: {e}")
        return 0

def main():
    """Main entry point for conditional download."""
    logger.info("Starting T011: Conditional Download for EDS Maps")
    
    # Load configuration
    config = get_config()
    
    # Check T010 feasibility status
    feasibility = load_feasibility_status()
    
    if not feasibility.get('success', False):
        logger.warning("T010 feasibility check failed. Skipping download.")
        logger.warning(f"Reason: {feasibility.get('reason', 'Unknown')}")
        
        # Create a status file indicating T011 was skipped
        t011_status = {
            "task_id": "T011",
            "status": "skipped",
            "reason": f"T010 failed: {feasibility.get('reason', 'Unknown')}",
            "timestamp": str(Path().cwd())
        }
        
        status_path = project_root / 'state' / 't011_download_status.yaml'
        with open(status_path, 'w') as f:
            yaml.dump(t011_status, f, default_flow_style=False)
        
        logger.info(f"T011 status written to {status_path}")
        return 0
    
    # T010 succeeded - proceed with download
    verified_url = feasibility.get('verified_url')
    zenodo_record = feasibility.get('zenodo_record')
    
    if not verified_url and not zenodo_record:
        logger.error("T010 succeeded but no download sources specified")
        logger.error("Feasibility status missing 'verified_url' or 'zenodo_record'")
        return 1
    
    # Prepare output directory
    raw_data_dir = project_root / 'data' / 'raw'
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {raw_data_dir}")
    
    downloaded_files = []
    failed_downloads = []
    
    # Download from verified URL if provided
    if verified_url:
        logger.info(f"Downloading from verified URL: {verified_url}")
        # Extract filename from URL or use a default
        url_parts = verified_url.rstrip('/').split('/')
        filename = url_parts[-1] if url_parts[-1] else 'eds_maps.zip'
        
        output_path = raw_data_dir / filename
        
        if download_file(verified_url, output_path):
            downloaded_files.append(str(output_path))
        else:
            failed_downloads.append((verified_url, "URL download failed"))
    
    # Download from Zenodo if provided
    if zenodo_record:
        logger.info(f"Downloading from Zenodo record: {zenodo_record}")
        zenodo_count = download_from_zenodo(zenodo_record, raw_data_dir)
        
        if zenodo_count > 0:
            logger.info(f"Successfully downloaded {zenodo_count} files from Zenodo")
            # List all files in raw_data_dir as downloaded
            for f in raw_data_dir.glob('*'):
                if f.is_file() and str(f) not in downloaded_files:
                    downloaded_files.append(str(f))
        else:
            failed_downloads.append((zenodo_record, "Zenodo download failed"))
    
    # Write download status
    t011_status = {
        "task_id": "T011",
        "status": "completed" if not failed_downloads else "partial",
        "verified_url": verified_url,
        "zenodo_record": zenodo_record,
        "downloaded_files": downloaded_files,
        "failed_downloads": failed_downloads,
        "total_downloaded": len(downloaded_files),
        "total_failed": len(failed_downloads),
        "timestamp": str(Path().cwd())
    }
    
    status_path = project_root / 'state' / 't011_download_status.yaml'
    with open(status_path, 'w') as f:
        yaml.dump(t011_status, f, default_flow_style=False)
    
    logger.info(f"T011 status written to {status_path}")
    logger.info(f"Downloaded {len(downloaded_files)} files successfully")
    
    if failed_downloads:
        logger.warning(f"Failed to download {len(failed_downloads)} sources")
        for source, reason in failed_downloads:
            logger.warning(f"  - {source}: {reason}")
        return 1
    
    logger.info("T011 completed successfully - all downloads succeeded")
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
