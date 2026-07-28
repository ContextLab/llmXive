"""
Data Fetcher Module.
Handles downloading, converting, and validating survey data.
"""
import os
import sys
import logging
import hashlib
import yaml
import pandas as pd
from pathlib import Path
import requests
import pyreadstat

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DESIGN_COLUMNS = ['weight', 'psu', 'strata']

def ensure_directories(path: Path):
    """Ensure the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_manifest_with_checksum(artifact_path: str, checksum: str, status: str, error: str = None):
    """Update state/manifest.yaml with the artifact's checksum and status."""
    manifest_path = Path("state/manifest.yaml")
    ensure_directories(manifest_path)

    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {"artifact_hashes": {}, "status": {}}

    if "artifact_hashes" not in manifest:
        manifest["artifact_hashes"] = {}
    if "status" not in manifest:
        manifest["status"] = {}

    manifest["artifact_hashes"][artifact_path] = checksum
    manifest["status"][artifact_path] = {"status": status, "error": error}

    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)

    logger.info(f"Manifest updated for {artifact_path}: status={status}, checksum={checksum}")

def fetch_and_save_data(url: str, output_path: str, cache_dir: str, source_type: str):
    """
    Fetch data from URL, validate design columns, and save as CSV.
    Implements logic:
    1. Attempt URL download.
    2. If failed, check cache.
    3. If cache valid, use it.
    4. If both fail, raise DataFetchError.
    5. Validate design columns. Abort if missing.
    """
    cache_file = Path(cache_dir) / Path(url).name
    output_file = Path(output_path)

    # 1. Attempt URL download
    data_df = None
    source_used = "url"

    if not cache_file.exists() or source_type == "gss": # Always try URL for GSS if not cached or forced
        try:
            logger.info(f"Attempting to download from {url}...")
            if url.endswith('.dta'):
                # Download to temp, then read
                temp_path = cache_file.with_suffix('.tmp')
                response = requests.get(url, stream=True)
                response.raise_for_status()
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                data_df, _ = pyreadstat.read_dta(temp_path)
                temp_path.unlink()
            else:
                # Assume CSV or similar readable by pandas directly if URL is accessible
                data_df = pd.read_csv(url)
            
            # Save to cache if it's a local file we just downloaded
            if source_type == "gss":
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                # Save raw format to cache for potential reuse (dta)
                # But we need to convert to CSV for the output
                if url.endswith('.dta'):
                    # Re-read from temp or use data_df
                    pass 
                data_df.to_csv(cache_file.with_suffix('.csv'), index=False)
            
            logger.info("Download successful.")
        except Exception as e:
            logger.warning(f"URL download failed: {e}. Checking cache...")
            data_df = None
            source_used = "cache"

    # 2. Check cache if URL failed or data_df is None
    if data_df is None:
        cached_csv = Path(cache_dir) / (Path(url).stem + ".csv")
        if cached_csv.exists():
            logger.info(f"Loading from cache: {cached_csv}")
            try:
                data_df = pd.read_csv(cached_csv)
                source_used = "cache"
            except Exception as e:
                logger.error(f"Cache read failed: {e}")
                data_df = None
        else:
            raise RuntimeError(f"DataFetchError: Could not fetch from URL and no valid cache found at {cache_dir}")

    if data_df is None:
        raise RuntimeError("DataFetchError: Failed to load data from URL or cache.")

    # 3. Validate Design Columns
    missing_cols = [col for col in DESIGN_COLUMNS if col not in data_df.columns]
    if missing_cols:
        logger.error(f"ABORT: Missing required design columns: {missing_cols}")
        # Log to manifest as failure
        update_manifest_with_checksum(
            artifact_path=output_path,
            checksum="pending",
            status="failed",
            error=f"Missing design columns: {missing_cols}"
        )
        raise ValueError(f"Missing design columns: {missing_cols}. Analysis aborted for this variable.")

    # 4. Save to output
    logger.info(f"Saving processed data to {output_path}")
    data_df.to_csv(output_path, index=False)

    logger.info(f"Data fetch completed. Source: {source_used}")

def main():
    """CLI entry point for data fetcher."""
    parser = argparse.ArgumentParser(description="Fetch and save survey data.")
    parser.add_argument("--url", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--cache-dir", type=str, default="data/raw/cache")
    parser.add_argument("--source", type=str, required=True)
    
    args = parser.parse_args()
    fetch_and_save_data(args.url, args.output, args.cache_dir, args.source)

if __name__ == "__main__":
    main()
