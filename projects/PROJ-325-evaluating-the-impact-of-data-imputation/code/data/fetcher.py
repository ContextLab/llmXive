import os
import sys
import logging
import hashlib
import yaml
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def ensure_directories(path: str) -> None:
    """Ensure the directory for the given path exists."""
    dir_path = Path(path).parent
    dir_path.mkdir(parents=True, exist_ok=True)

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: str = "state/manifest.yaml") -> Dict[str, Any]:
    """Load the manifest file."""
    if not os.path.exists(manifest_path):
        return {"artifact_hashes": {}}
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)

def update_manifest_with_checksum(
    artifact_path: str,
    checksum: str,
    manifest_path: str = "state/manifest.yaml"
) -> None:
    """Update the manifest with the artifact's checksum."""
    manifest = load_manifest(manifest_path)
    if "artifact_hashes" not in manifest:
        manifest["artifact_hashes"] = {}
    manifest["artifact_hashes"][os.path.basename(artifact_path)] = {
        "path": artifact_path,
        "checksum": checksum
    }
    ensure_directories(manifest_path)
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)

def fetch_and_save_data(
    url: str,
    output_path: str,
    source_name: str = "unknown"
) -> None:
    """
    Fetch data from a URL and save it to a local file.
    
    Args:
        url: The URL to fetch data from.
        output_path: The local path to save the data.
        source_name: Name of the data source for logging.
    
    Raises:
        DataFetchError: If the fetch fails and no cache is available.
    """
    logger.info(f"Attempting to fetch data from: {url}")
    try:
        # Attempt direct download
        df = pd.read_csv(url)
        
        # Ensure output directory exists
        ensure_directories(output_path)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Data saved to: {output_path}")
        
        # Compute and record checksum
        checksum = compute_checksum(output_path)
        update_manifest_with_checksum(output_path, checksum)
        logger.info(f"Checksum recorded: {checksum}")
        
    except Exception as e:
        logger.error(f"Direct fetch failed: {e}")
        # Check cache
        cache_dir = "data/raw/cache"
        cache_file = os.path.join(cache_dir, f"{source_name}_cached.csv")
        
        if os.path.exists(cache_file):
            logger.info(f"Using cached file: {cache_file}")
            # Copy cache to output
            import shutil
            shutil.copy(cache_file, output_path)
            checksum = compute_checksum(output_path)
            update_manifest_with_checksum(output_path, checksum)
            logger.info(f"Cache copied and checksum recorded: {checksum}")
        else:
            raise DataFetchError(f"Failed to fetch data from {url} and no cache available.")

def fetch_and_save_from_cache(
    source_name: str,
    output_path: str,
    manifest_path: str = "state/manifest.yaml"
) -> None:
    """
    Fetch data from cache if available.
    
    Args:
        source_name: Name of the data source.
        output_path: The local path to save the data.
        manifest_path: Path to the manifest file.
    
    Raises:
        DataFetchError: If no cache is available.
    """
    cache_dir = "data/raw/cache"
    cache_file = os.path.join(cache_dir, f"{source_name}_cached.csv")
    
    if not os.path.exists(cache_file):
        raise DataFetchError(f"No cache found for {source_name} at {cache_file}")
    
    ensure_directories(output_path)
    import shutil
    shutil.copy(cache_file, output_path)
    
    checksum = compute_checksum(output_path)
    update_manifest_with_checksum(output_path, checksum, manifest_path)
    logger.info(f"Data copied from cache to: {output_path}, checksum: {checksum}")

def main():
    """Main entry point for the fetcher script."""
    import argparse
    parser = argparse.ArgumentParser(description="Fetch and save data from a URL or cache.")
    parser.add_argument("--url", type=str, help="URL to fetch data from")
    parser.add_argument("--output", type=str, required=True, help="Output file path")
    parser.add_argument("--source", type=str, default="unknown", help="Source name for cache")
    parser.add_argument("--use-cache", action="store_true", help="Use cache only")
    
    args = parser.parse_args()
    
    if args.use_cache:
        try:
            fetch_and_save_from_cache(args.source, args.output)
        except DataFetchError as e:
            logger.error(str(e))
            sys.exit(1)
    elif args.url:
        try:
            fetch_and_save_data(args.url, args.output, args.source)
        except DataFetchError as e:
            logger.error(str(e))
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()