"""
Dataset downloader for the transformation sensitivity study.
Fetches datasets from OpenML and UCI, verifies sources, 
saves as parquet, and records provisional metadata.
"""
import logging
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from sklearn.datasets import fetch_openml
from code.data.checksum_datasets import compute_sha256

log = logging.getLogger(__name__)

def is_source_verified(url: str) -> bool:
    """Verify that the dataset source URL belongs to a canonical public domain."""
    verified_domains = ["openml.org", "archive.ics.uci.edu"]
    return any(domain in url for domain in verified_domains)

def download_openml(dataset_id_str: str, raw_dir: Path) -> Optional[Dict[str, Any]]:
    """Download dataset from OpenML and save as parquet."""
    try:
        # Fix: Cast dataset_id to int to avoid the 'must be an int' error
        dataset_id = int(dataset_id_str)
        source_url = f"https://www.openml.org/d/{dataset_id}"
        
        if not is_source_verified(source_url):
            return None

        # Use fetch_openml to get the data
        oml = fetch_openml(data_id=dataset_id, as_frame=True, parser="auto")
        df = oml.frame
        
        filename = f"openml_{dataset_id}.parquet"
        file_path = raw_dir / filename
        df.to_parquet(file_path)
        
        return {
            "dataset_id": dataset_id_str,
            "source_url": source_url,
            "filename": str(file_path),
            "sample_size": len(df),
            "num_continuous_vars": len(df.select_dtypes(include="number").columns),
            "checksum_sha256": compute_sha256(file_path)
        }
    except Exception as e:
        log.warning(f"Failed to download OpenML dataset {dataset_id_str}: {e}")
        return None

def download_uci(url: str, raw_dir: Path) -> Optional[Dict[str, Any]]:
    """Download dataset from UCI URL and save as parquet."""
    try:
        if not is_source_verified(url):
            return None
        
        # Extract a simple ID from the URL
        dataset_id = url.split("/")[-1].split(".")[0]
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Attempt to read as CSV (UCI .data files are usually CSV-like)
        from io import StringIO
        df = pd.read_csv(StringIO(response.text), header=None)
        
        filename = f"uci_{dataset_id}.parquet"
        file_path = raw_dir / filename
        df.to_parquet(file_path)
        
        return {
            "dataset_id": dataset_id,
            "source_url": url,
            "filename": str(file_path),
            "sample_size": len(df),
            "num_continuous_vars": len(df.select_dtypes(include="number").columns),
            "checksum_sha256": compute_sha256(file_path)
        }
    except Exception as e:
        log.warning(f"Failed to download UCI dataset {url}: {e}")
        return None

def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    datasets_csv = Path("data/datasets.csv")
    checksums_csv = Path("data/checksums.csv")
    
    # Read source lists
    openml_ids_path = Path("data/openml_ids.txt")
    uci_urls_path = Path("data/uci_dataset_urls.txt")
    
    if not openml_ids_path.exists() or not uci_urls_path.exists():
        log.error("Source ID/URL files missing.")
        sys.exit(1)
        
    openml_ids = openml_ids_path.read_text().splitlines()
    uci_urls = uci_urls_path.read_text().splitlines()
    
    # Initialize CSVs
    # Columns per contracts/dataset.schema.yaml
    headers = [
        "dataset_id", "source_url", "filename", "checksum_sha256", 
        "sample_size", "num_continuous_vars", "shapiro_wilk_p", 
        "skewness", "kurtosis", "missing_pct", "status"
    ]
    
    # We will collect all and write at once to ensure consistency
    successful_datasets = []
    checksums_list = []
    
    # Process OpenML
    for oid in openml_ids:
        if len(successful_datasets) >= 60: # Cap to avoid excessive time
            break
        res = download_openml(oid, raw_dir)
        if res:
            successful_datasets.append(res)
            checksums_list.append({"dataset_id": res["dataset_id"], "checksum": res["checksum_sha256"]})
    
    # Process UCI
    for url in uci_urls:
        res = download_uci(url, raw_dir)
        if res:
            successful_datasets.append(res)
            checksums_list.append({"dataset_id": res["dataset_id"], "checksum": res["checksum_sha256"]})
    
    if len(successful_datasets) < 50:
        log.error(f"Only {len(successful_datasets)} datasets downloaded. Required >= 50.")
        raise ConnectionError(f"Insufficient datasets downloaded: {len(successful_datasets)}")

    # Write datasets.csv
    with datasets_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for ds in successful_datasets:
            # Map the internal dict to the schema
            row = {
                "dataset_id": ds["dataset_id"],
                "source_url": ds["source_url"],
                "filename": ds["filename"],
                "checksum_sha256": ds["checksum_sha256"],
                "sample_size": ds["sample_size"],
                "num_continuous_vars": ds["num_continuous_vars"],
                "shapiro_wilk_p": "", # computed in T003
                "skewness": "",       # computed in T003
                "kurtosis": "",       # computed in T003
                "missing_pct": "",    # computed in T003
                "status": "downloaded"
            }
            writer.writerow(row)
    
    # Write checksums.csv
    with checksums_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset_id", "checksum"])
        writer.writeheader()
        writer.writerows(checksums_list)
        
    log.info(f"Successfully downloaded {len(successful_datasets)} datasets.")

if __name__ == "__main__":
    main()