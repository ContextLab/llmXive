import json
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import config utilities to ensure paths are set up correctly
# We assume the project root is the parent of the 'code' directory
# so we add the parent to sys.path if not already present
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.config.config_loader import load_env_config, validate_manifest_exists, get_data_paths

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configures logging for the ingestion process.
    Logs to both console and a file if provided.
    """
    logger = logging.getLogger("ctcf_ingest")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the data manifest JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'entries' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'entries' in data:
        return data['entries']
    else:
        raise ValueError("Manifest must be a list or a dict with 'entries' key")

def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, logger: logging.Logger) -> bool:
    """
    Downloads a file from a URL to a destination path.
    Returns True on success, False on failure.
    """
    import requests
    from requests.exceptions import RequestException

    try:
        logger.info(f"Downloading {url} to {dest_path}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded {dest_path.name}")
        return True
    except RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False

def process_manifest_entry(entry: Dict[str, Any], base_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Processes a single manifest entry: downloads file, calculates checksum,
    and logs cell type and exclusion reasons.
    """
    accession_id = entry.get('accession_id', 'unknown')
    cell_type = entry.get('cell_type', 'unknown')
    file_type = entry.get('file_type', 'unknown')
    url = entry.get('url', '')
    status = entry.get('status', 'pending')

    log_prefix = f"[{cell_type} - {accession_id}]"

    if status == 'excluded':
        reason = entry.get('exclusion_reason', 'Unknown reason')
        logger.warning(f"{log_prefix} EXCLUDED: {reason}")
        return {
            'accession_id': accession_id,
            'cell_type': cell_type,
            'status': 'excluded',
            'reason': reason
        }

    if not url:
        reason = "No download URL provided in manifest"
        logger.error(f"{log_prefix} EXCLUDED: {reason}")
        return {
            'accession_id': accession_id,
            'cell_type': cell_type,
            'status': 'excluded',
            'reason': reason
        }

    # Determine file extension and target path
    ext = '.bam' if file_type == 'bam' else '.bigwig' if file_type == 'bigwig' else '.gz'
    filename = f"{accession_id}{ext}"
    dest_path = base_dir / filename

    if dest_path.exists():
        logger.info(f"{log_prefix} File already exists, skipping download: {filename}")
        # Verify checksum if local file exists
        local_checksum = calculate_sha256(dest_path)
        expected_checksum = entry.get('checksum', '')
        if expected_checksum and local_checksum != expected_checksum:
            logger.warning(f"{log_prefix} Checksum mismatch. Re-downloading.")
            # Re-download logic could go here, for now we just log
        else:
            return {
                'accession_id': accession_id,
                'cell_type': cell_type,
                'status': 'downloaded',
                'path': str(dest_path),
                'checksum': local_checksum
            }

    # Attempt download
    if download_file(url, dest_path, logger):
        checksum = calculate_sha256(dest_path)
        logger.info(f"{log_prefix} Download complete. Checksum: {checksum}")
        return {
            'accession_id': accession_id,
            'cell_type': cell_type,
            'status': 'downloaded',
            'path': str(dest_path),
            'checksum': checksum
        }
    else:
        reason = "Download failed"
        logger.error(f"{log_prefix} EXCLUDED: {reason}")
        return {
            'accession_id': accession_id,
            'cell_type': cell_type,
            'status': 'excluded',
            'reason': reason
        }

def main():
    """
    Main entry point for data ingestion with logging.
    """
    # Setup logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "ingest_run.log"
    logger = setup_logging(log_file)

    logger.info("="*50)
    logger.info("Starting CTCF Data Ingestion Pipeline")
    logger.info("="*50)

    try:
        # Load configuration
        config = load_env_config()
        data_paths = get_data_paths()
        raw_data_dir = data_paths.get('raw', Path("data/raw"))
        raw_data_dir.mkdir(parents=True, exist_ok=True)

        # Validate manifest
        manifest_path = Path("data/manifest.json")
        validate_manifest_exists(manifest_path)
        
        entries = load_manifest(manifest_path)
        logger.info(f"Loaded {len(entries)} entries from manifest.")

        # Counters for logging summary
        total_count = len(entries)
        processed_count = 0
        excluded_count = 0
        downloaded_count = 0
        exclusion_reasons: Dict[str, int] = {}

        results = []

        for entry in entries:
            processed_count += 1
            result = process_manifest_entry(entry, raw_data_dir, logger)
            results.append(result)

            if result['status'] == 'excluded':
                excluded_count += 1
                reason = result.get('reason', 'Unknown')
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            elif result['status'] == 'downloaded':
                downloaded_count += 1

        # Final Summary Log
        logger.info("="*50)
        logger.info("Ingestion Summary")
        logger.info("="*50)
        logger.info(f"Total entries processed: {total_count}")
        logger.info(f"Successfully downloaded: {downloaded_count}")
        logger.info(f"Excluded: {excluded_count}")
        
        if exclusion_reasons:
            logger.info("Exclusion Reasons Breakdown:")
            for reason, count in exclusion_reasons.items():
                logger.info(f"  - {reason}: {count}")
        
        logger.info(f"Logs saved to: {log_file}")
        logger.info("Ingestion complete.")

    except FileNotFoundError as e:
        logger.error(f"Configuration or Manifest error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()