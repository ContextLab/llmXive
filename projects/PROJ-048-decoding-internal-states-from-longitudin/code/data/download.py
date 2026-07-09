import os
import sys
import hashlib
import json
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Import from project utils
try:
    from utils.logger import get_logger, log_stage_start, log_stage_end, log_error
    from utils.memory_monitor import check_memory_limit, MemoryExceededError, get_memory_limit_gb
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.logger import get_logger, log_stage_start, log_stage_end, log_error
    from utils.memory_monitor import check_memory_limit, MemoryExceededError, get_memory_limit_gb

class DownloadError(Exception):
    """Custom exception for download failures."""
    pass

def get_dataset_size(url: str) -> int:
    """
    Fetch the Content-Length header to estimate dataset size in bytes.
    Returns 0 if the header is missing.
    """
    try:
        # Use HEAD request to avoid downloading the body
        response = requests.head(url, allow_redirects=True, timeout=30)
        response.raise_for_status()
        size = response.headers.get('Content-Length')
        if size:
            return int(size)
    except requests.RequestException as e:
        logging.warning(f"Could not fetch Content-Length for {url}: {e}")
    return 0

def download_allen_data(
    output_dir: str,
    dataset_url: Optional[str] = None,
    checksum: Optional[str] = None
) -> Path:
    """
    Download Allen Brain Atlas data with memory safety checks.
    
    Implements FR-001 and SC-001:
    - Intercepts dataset size checks.
    - Explicitly raises MemoryExceededError with message "Memory limit exceeded"
      if the dataset exceeds 5GB (or configured limit).
    
    Args:
        output_dir: Directory to save the file.
        dataset_url: URL to the dataset. Defaults to config.
        checksum: Expected SHA256 checksum.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        MemoryExceededError: If dataset size > memory limit.
        DownloadError: If download fails or checksum mismatch.
    """
    logger = get_logger("download")
    
    # 1. Resolve URL
    if not dataset_url:
        try:
            from config import get_dataset_url
            dataset_url = get_dataset_url()
        except Exception as e:
            raise DownloadError(f"Failed to get dataset URL: {e}")
    
    if not dataset_url:
        raise DownloadError("Dataset URL is not configured and not provided.")
    
    logger.info(f"Starting download from {dataset_url}")
    
    # 2. Size Check (FR-001, SC-001)
    file_size_bytes = get_dataset_size(dataset_url)
    file_size_gb = file_size_bytes / (1024 ** 3)
    limit_gb = get_memory_limit_gb()
    
    logger.info(f"Estimated dataset size: {file_size_gb:.2f} GB (Limit: {limit_gb} GB)")
    
    if file_size_bytes > 0 and file_size_gb > limit_gb:
        # Explicitly raise MemoryExceededError with the required message
        raise MemoryExceededError("Memory limit exceeded")
    
    # 3. Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filename = os.path.basename(dataset_url.split('?')[0])
    if not filename.endswith('.h5') and not filename.endswith('.hdf5'):
        filename = 'allen_data.h5' # Fallback name
    file_path = output_path / filename
    
    # 4. Download
    try:
        with requests.get(dataset_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Optional: Check memory usage periodically during download
                        # to prevent OOM if the buffer grows too large
                        if downloaded % (1024 * 1024 * 100) == 0: # Every 100MB
                            check_memory_limit() 
                            
    except requests.RequestException as e:
        raise DownloadError(f"Download failed: {e}")
    
    # 5. Checksum Verification
    if checksum:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()
        if actual_checksum != checksum:
            raise DownloadError(
                f"Checksum mismatch: expected {checksum}, got {actual_checksum}"
            )
        logger.info("Checksum verified.")
    
    logger.info(f"Download complete: {file_path}")
    return file_path

def main():
    """Entry point for script execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Download Allen Brain Atlas Data")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--url", type=str, help="Override dataset URL")
    parser.add_argument("--checksum", type=str, help="Expected checksum")
    args = parser.parse_args()
    
    try:
        # Initialize config if needed
        try:
            from config import init_config
            init_config()
        except:
            pass
        
        result = download_allen_data(
            output_dir=args.output_dir,
            dataset_url=args.url,
            checksum=args.checksum
        )
        print(f"Success: {result}")
    except MemoryExceededError as e:
        # Ensure the specific message is printed as required by FR-001
        print(f"ERROR: {e}")
        sys.exit(1)
    except DownloadError as e:
        print(f"Download Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
