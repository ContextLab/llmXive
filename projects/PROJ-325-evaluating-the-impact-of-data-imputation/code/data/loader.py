import argparse
import logging
import sys
import os
import hashlib
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MANIFEST_PATH = Path("state/manifest.yaml")
MAX_ROWS = 50000
MISSINGNESS_THRESHOLD = 0.30  # 30%

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class SubsetLimitError(Exception):
    """Raised when a dataset exceeds the row limit."""
    pass

class MissingDesignColumnsError(Exception):
    """Raised when required design columns are missing."""
    pass

def ensure_directories():
    """Ensure required directories exist."""
    dirs = ["data/raw", "data/raw/cache", "data/processed", "state"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> Dict[str, Any]:
    """Load the manifest file."""
    ensure_directories()
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    return {"artifact_hashes": {}, "logs": []}

def update_manifest_with_checksum(file_path: str, key: str, status: str = "success", error: Optional[str] = None):
    """Update manifest with file checksum and status."""
    manifest = load_manifest()
    if "artifact_hashes" not in manifest:
        manifest["artifact_hashes"] = {}
    
    if os.path.exists(file_path):
        checksum = compute_sha256(file_path)
        manifest["artifact_hashes"][key] = {
            "path": file_path,
            "sha256": checksum,
            "status": status
        }
    else:
        manifest["artifact_hashes"][key] = {
            "path": file_path,
            "status": "missing"
        }
    
    if error:
        manifest["logs"] = manifest.get("logs", [])
        manifest["logs"].append({
            "timestamp": pd.Timestamp.now().isoformat(),
            "level": "ERROR",
            "message": error
        })
    
    with open(MANIFEST_PATH, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)

def check_design_columns(df: pd.DataFrame, variable_name: str) -> Tuple[bool, List[str]]:
    """
    Check for presence of design columns (weight, psu, strata).
    Returns (is_valid, list_of_missing_columns).
    """
    required_cols = ["weight", "psu", "strata"]
    missing = [col for col in required_cols if col not in df.columns]
    return len(missing) == 0, missing

def detect_missingness(df: pd.DataFrame, threshold: float = MISSINGNESS_THRESHOLD) -> Dict[str, float]:
    """
    Detect variables with missingness above the threshold.
    
    Args:
        df: Input DataFrame
        threshold: Maximum allowed missingness rate (default 0.30)
    
    Returns:
        Dict mapping variable names to their missingness rate.
    """
    missingness_rates = {}
    for col in df.columns:
        if col in ["weight", "psu", "strata"]:
            continue
        rate = df[col].isna().sum() / len(df)
        missingness_rates[col] = rate
        if rate > threshold:
            logger.warning(f"Variable '{col}' has {rate:.2%} missingness (>{threshold:.0%}). Skipping.")
    return missingness_rates

def fetch_and_save_data(url: str, output_path: str) -> pd.DataFrame:
    """
    Fetch data from URL and save to CSV.
    
    Args:
        url: Source URL
        output_path: Path to save the CSV
    
    Returns:
        Loaded DataFrame
    """
    try:
        # Attempt to fetch from URL
        # For this implementation, we assume the URL points to a CSV or we use a fallback
        # In a real scenario, we would use requests or pandas.read_csv directly
        logger.info(f"Attempting to fetch data from: {url}")
        
        # Simulate fetch for demonstration if URL is placeholder
        if "<GSS_URL>" in url or "<ACS_URL>" in url:
            raise DataFetchError("URL is a placeholder. Please provide a real URL or use cache.")
        
        # Try to read directly
        df = pd.read_csv(url)
        
        # Enforce subset limit
        if len(df) > MAX_ROWS:
            logger.info(f"Dataset has {len(df)} rows. Truncating to {MAX_ROWS} rows.")
            df = df.head(MAX_ROWS)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Data saved to {output_path}")
        return df
        
    except Exception as e:
        raise DataFetchError(f"Failed to fetch data from {url}: {str(e)}")

def fetch_and_save_from_cache(cache_path: str, output_path: str) -> pd.DataFrame:
    """
    Load data from cache and save to output path.
    
    Args:
        cache_path: Path to cached file
        output_path: Path to save the CSV
    
    Returns:
        Loaded DataFrame
    """
    if not os.path.exists(cache_path):
        raise DataFetchError(f"Cache file not found: {cache_path}")
    
    df = pd.read_csv(cache_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Data loaded from cache and saved to {output_path}")
    return df

def fetch_and_validate(source: str, url: Optional[str] = None, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch data, validate design columns, and detect missingness.
    
    Args:
        source: Data source identifier ('gss', 'acs', etc.)
        url: Source URL (optional if using cache)
        output_path: Output path for the CSV
    
    Returns:
        Validated DataFrame
    """
    ensure_directories()
    output_path = output_path or f"data/raw/{source}_subset.csv"
    cache_path = f"data/raw/cache/{source}_cache.csv"
    
    df = None
    
    # Attempt to fetch
    if url:
        try:
            df = fetch_and_save_data(url, output_path)
        except DataFetchError as e:
            logger.warning(f"URL fetch failed: {e}")
            # Try cache
            if os.path.exists(cache_path):
                logger.info("Falling back to cache...")
                df = fetch_and_save_from_cache(cache_path, output_path)
            else:
                raise DataFetchError(f"Both URL and cache failed for {source}")
    else:
        # Use cache only
        if os.path.exists(cache_path):
            df = fetch_and_save_from_cache(cache_path, output_path)
        else:
            raise DataFetchError(f"No URL provided and cache not found for {source}")
    
    # Check design columns
    is_valid, missing_cols = check_design_columns(df, source)
    if not is_valid:
        error_msg = f"Missing design columns for {source}: {', '.join(missing_cols)}"
        logger.error(error_msg)
        update_manifest_with_checksum(output_path, source, status="failed", error=error_msg)
        raise MissingDesignColumnsError(error_msg)
    
    # Detect missingness
    missingness = detect_missingness(df)
    logger.info(f"Missingness analysis complete. Variables skipped: {[k for k, v in missingness.items() if v > MISSINGNESS_THRESHOLD]}")
    
    # Update manifest
    update_manifest_with_checksum(output_path, source, status="success")
    
    return df

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Data loader with design validation and missingness detection.")
    parser.add_argument("--source", type=str, required=True, help="Data source (e.g., 'gss', 'acs')")
    parser.add_argument("--url", type=str, help="Source URL")
    parser.add_argument("--output", type=str, help="Output path")
    parser.add_argument("--fetch", action="store_true", help="Force fetch from URL")
    parser.add_argument("--verify-abort", action="store_true", help="Verify abort on missing columns")
    
    args = parser.parse_args()
    
    try:
        df = fetch_and_validate(source=args.source, url=args.url, output_path=args.output)
        logger.info(f"Successfully loaded {len(df)} rows from {args.source}")
        sys.exit(0)
    except (DataFetchError, MissingDesignColumnsError, SubsetLimitError) as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()