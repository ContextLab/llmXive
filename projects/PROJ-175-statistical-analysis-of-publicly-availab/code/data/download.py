"""
Data download module for T012a.
Implements streaming download of Recipe1M and other datasets.
"""
import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Exception raised when data is unavailable."""
    pass

def ensure_directories():
    """Ensure required directories exist."""
    data_dir = project_root / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def verify_url_status(url: str) -> bool:
    """Verify that a URL is accessible."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"URL verification failed for {url}: {e}")
        return False

def load_verification_report():
    """Load the verification report from T012b."""
    report_path = project_root / "data" / "download_status.json"
    if not report_path.exists():
        raise FileNotFoundError("Verification report not found. Run T012 first.")
    with open(report_path, 'r') as f:
        return json.load(f)

def save_manifest(manifest: Dict[str, Any]):
    """Save the download manifest."""
    manifest_path = project_root / "data" / "download_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def download_recipe1m_streaming(output_path: Path):
    """
    Stream the Recipe1M dataset from HuggingFace.
    Uses the datasets library for streaming.
    """
    try:
        from datasets import load_dataset
        import pyarrow.parquet as pq
        import io
        
        logger.info("Starting Recipe1M download with streaming...")
        
        # Load dataset in streaming mode
        # Note: Recipe1M is large, so we stream and process in chunks
        dataset = load_dataset("recipe1m", split="train", streaming=True)
        
        # Convert to parquet
        # We'll collect a subset for now to avoid memory issues
        # In a real scenario, we might stream directly to parquet
        records = []
        count = 0
        max_records = 100000  # Limit for testing purposes
        
        for item in dataset:
            records.append(item)
            count += 1
            if count >= max_records:
                break
        
        # Create DataFrame and save
        df = pd.DataFrame(records)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved {count} records to {output_path}")
        
    except ImportError:
        logger.error("datasets library not installed. Install with: pip install datasets")
        raise
    except Exception as e:
        logger.error(f"Failed to download Recipe1M: {e}")
        raise

def download_datasets():
    """Main function to download all datasets."""
    output_dir = ensure_directories()
    
    # Load verification report to check status
    try:
        report = load_verification_report()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Check if Recipe1M is marked as successful
    if report.get('recipe1m') != 'SUCCESS':
        logger.warning("Recipe1M not marked as SUCCESS in verification report.")
        # Proceed anyway if we have the file, or fail if not
    
    # Download Recipe1M
    recipe1m_path = output_dir / "recipe1m_raw.parquet"
    if not recipe1m_path.exists():
        try:
            download_recipe1m_streaming(recipe1m_path)
            # Update report
            report['recipe1m'] = 'SUCCESS'
            with open(output_dir.parent / "download_status.json", 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            logger.error(f"Recipe1M download failed: {e}")
            report['recipe1m'] = 'FAILED'
            with open(output_dir.parent / "download_status.json", 'w') as f:
                json.dump(report, f, indent=2)
            raise DataUnavailableError("Recipe1M download failed.")
    else:
        logger.info("Recipe1M already exists.")

def main():
    """Entry point for the download script."""
    logging.basicConfig(level=logging.INFO)
    try:
        download_datasets()
        logger.info("Download completed successfully.")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
