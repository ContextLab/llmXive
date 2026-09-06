"""
Download the latest eBird Basic Dataset (EBD) release from S3.

This script implements Constitution Principle VI by fetching exclusively from the
canonical S3 bucket. It will fail loudly (raise FileNotFoundError) if the download
fails, ensuring no synthetic fallback is used.
"""
import os
import sys
import hashlib
import yaml
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports from utils
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_raw_data_dir, get_metadata_file
from utils.provenance import save_provenance_record, compute_file_hash


S3_BUCKET = "s3://ebird-data/ebd_release/"
# Note: Since we cannot use boto3 without credentials in this environment,
# we will simulate the listing by checking a known public mirror or a specific
# URL pattern if available. However, the task explicitly requires listing S3.
# To make this runnable in a restricted environment without AWS credentials,
# we will attempt to fetch the index if available, or raise a clear error
# if the canonical source is unreachable.

# For the purpose of this implementation, we assume the S3 bucket is public 
# or we have a way to list it. Since direct S3 listing without boto3/credentials 
# is difficult, we will use a known public HTTP mirror of the index if available,
# or construct the download URL directly if we know the naming convention.
# The eBird data is often available via a public URL pattern.
# The latest release usually follows a pattern like:
# https://ebird.org/data/download/ebd_release_YYYYMMDD.zip or parquet

# However, the task specifies S3. We will attempt to use the `requests` library
# to access the public S3 endpoint if it's open, or fall back to the known
# public URL for the latest release if the S3 listing is not directly accessible
# via HTTP GET (which is common for private buckets).
# Given the constraints, we will implement the logic to fetch the latest file
# by attempting to access a known public index or the specific file URL.

# REAL SOURCE: eBird EBD is available at https://ebird.org/data
# The S3 bucket is the internal source. We will use the public download URL
# which points to the same S3 object.

# The latest EBD is typically available as a Parquet file in a public bucket
# or via a direct download link. We will use the direct download link for the
# latest version if we can determine it, or list the bucket if public.

# Since we cannot list a private S3 bucket without credentials, we will use
# the public download URL for the latest release. The URL pattern is:
# https://data.ebird.org/ebd_release/ebd_rel_YYYYMMDD.zip (or .parquet)
# We will attempt to find the latest by checking a known index or using a
# hardcoded latest version if necessary, but the task requires listing.

# To satisfy the "list S3" requirement in a real environment, one would use boto3.
# Here, we simulate the listing by checking a public index file if it exists,
# or by using a known public endpoint that lists the files.
# If that fails, we raise an error as per the "fail loudly" requirement.

# For this implementation, we will try to access the public S3 bucket listing
# via HTTP (if configured as public) or use the known public download URL.
# The eBird data is publicly available. The S3 bucket `ebird-data` is public.
# We can list it via: https://ebird-data.s3.amazonaws.com/ebird_release/

BASE_URL = "https://ebird-data.s3.amazonaws.com/ebd_release/"
LISTING_URL = BASE_URL


def list_s3_bucket(bucket_url: str) -> List[Dict[str, Any]]:
    """
    List objects in the S3 bucket.
    Returns a list of dicts with 'Key' and 'LastModified'.
    """
    import urllib.request
    import xml.etree.ElementTree as ET
    
    try:
        # Attempt to fetch the bucket listing (S3 ListObjectsV2 via HTTP)
        # This works if the bucket is public or signed URLs are used.
        # eBird bucket is public.
        response = urllib.request.urlopen(f"{bucket_url}?list-type=2")
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        ns = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
        contents = []
        for obj in root.findall('s3:Contents', ns):
            key_elem = obj.find('s3:Key', ns)
            last_mod_elem = obj.find('s3:LastModified', ns)
            if key_elem is not None and last_mod_elem is not None:
                contents.append({
                    'Key': key_elem.text,
                    'LastModified': last_mod_elem.text
                })
        return contents
    except Exception as e:
        raise RuntimeError(f"Failed to list S3 bucket {bucket_url}: {e}")


def find_latest_parquet(files: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Sort files by LastModified descending and return the first .parquet file.
    """
    parquet_files = [f for f in files if f['Key'].endswith('.parquet')]
    if not parquet_files:
        return None
    
    # Sort by LastModified descending
    # Note: ISO 8601 strings sort correctly lexicographically
    sorted_files = sorted(parquet_files, key=lambda x: x['LastModified'], reverse=True)
    return sorted_files[0]


def download_file(url: str, dest_path: Path) -> None:
    """
    Download a file from a URL to a local path.
    """
    print(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded successfully to {dest_path}")
    except requests.exceptions.RequestException as e:
        raise FileNotFoundError(f"Failed to download file from {url}: {e}")


def convert_parquet_to_csv(parquet_path: Path, csv_path: Path) -> None:
    """
    Convert a Parquet file to CSV.
    Note: This requires pandas and pyarrow.
    """
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        # Save as CSV to match the task requirement of outputting a CSV
        # The task says: "download it to data/raw/ebd_train.csv (or parquet)"
        # We will save as CSV as requested by the path in the task.
        df.to_csv(csv_path, index=False)
        print(f"Converted {parquet_path} to {csv_path}")
    except ImportError:
        raise RuntimeError("pandas is required to convert Parquet to CSV. Install it via requirements.txt.")
    except Exception as e:
        raise RuntimeError(f"Failed to convert Parquet to CSV: {e}")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_metadata(metadata_path: Path, record: Dict[str, Any]) -> None:
    """Append or update provenance record in metadata.yaml."""
    if not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w') as f:
            yaml.dump({"datasets": {}, "artifacts": {}, "pipeline_runs": []}, f)
    
    with open(metadata_path, 'r') as f:
        metadata = yaml.safe_load(f)
    
    # Update datasets section
    dataset_name = "ebd_train"
    metadata["datasets"][dataset_name] = {
        "source_url": record["source_url"],
        "version": record["version"],
        "download_date": record["download_date"],
        "checksum": record["checksum"],
        "local_path": str(record["local_path"])
    }
    
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)


def main():
    """Main entry point for downloading EBD data."""
    print("Starting EBD download process...")
    
    # Ensure directories exist
    raw_data_dir = get_raw_data_dir()
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_path = get_metadata_file()
    
    # 1. List S3 bucket
    print(f"Listing S3 bucket: {S3_BUCKET}")
    try:
        files = list_s3_bucket(LISTING_URL)
    except Exception as e:
        # Fail loudly as per Constitution Principle VI
        raise FileNotFoundError(f"Cannot access canonical S3 source {S3_BUCKET}. Error: {e}")
    
    if not files:
        raise FileNotFoundError(f"No files found in S3 bucket {S3_BUCKET}")
    
    # 2. Find latest .parquet file
    latest_file = find_latest_parquet(files)
    if not latest_file:
        raise FileNotFoundError(f"No .parquet files found in S3 bucket {S3_BUCKET}")
    
    print(f"Selected latest file: {latest_file['Key']} (Modified: {latest_file['LastModified']})")
    
    # 3. Construct download URL
    file_key = latest_file['Key']
    download_url = f"{BASE_URL}{file_key}"
    
    # 4. Download to raw data directory
    parquet_filename = Path(file_key).name
    parquet_path = raw_data_dir / parquet_filename
    csv_path = raw_data_dir / "ebd_train.csv"
    
    try:
        download_file(download_url, parquet_path)
    except FileNotFoundError as e:
        raise e  # Re-raise to fail loudly
    
    # 5. Convert to CSV
    try:
        convert_parquet_to_csv(parquet_path, csv_path)
    except Exception as e:
        raise RuntimeError(f"Conversion to CSV failed: {e}")
    
    # 6. Compute checksum
    checksum = compute_sha256(csv_path)
    
    # 7. Save provenance to metadata.yaml
    record = {
        "source_url": download_url,
        "version": file_key, # Use the file key as version identifier
        "download_date": datetime.now().isoformat(),
        "checksum": checksum,
        "local_path": str(csv_path)
    }
    save_metadata(metadata_path, record)
    
    print(f"EBD download complete. Output: {csv_path}")
    print(f"Checksum: {checksum}")
    print(f"Metadata updated: {metadata_path}")


if __name__ == "__main__":
    from datetime import datetime
    main()
