"""
Dataset download script with URL validation and checksum verification.

Downloads datasets from OpenNeuro using the OpenNeuro API client.
Validates URL format and verifies checksums of downloaded archives.
"""
import os
import sys
import hashlib
import json
import re
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.datasets.openneuro_client import OpenNeuroClient
from src.config.env import get_data_dir, get_openneuro_api_key


# Constants
VALID_URL_PATTERN = re.compile(
    r'^https://openneuro\.org/datasets/[a-zA-Z0-9-]+/versions/[0-9]+\.[0-9]+\.[0-9]+$'
)
SUPPORTED_EXTENSIONS = ('.tar.gz', '.zip')
CHECKSUM_ALGORITHM = 'md5'


class DownloadError(Exception):
    """Exception raised for download failures."""
    pass


class ValidationFailedError(Exception):
    """Exception raised when URL or checksum validation fails."""
    pass


def validate_url(url: str) -> bool:
    """
    Validate OpenNeuro dataset URL format.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if URL is valid
        
    Raises:
        ValidationFailedError: If URL format is invalid
    """
    if not VALID_URL_PATTERN.match(url):
        raise ValidationFailedError(
            f"Invalid OpenNeuro URL format: {url}. "
            f"Expected format: https://openneuro.org/datasets/<dataset-id>/versions/<version>"
        )
    return True


def compute_checksum(file_path: Path) -> str:
    """
    Compute MD5 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of MD5 checksum
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected MD5 checksum
        
    Returns:
        True if checksum matches
        
    Raises:
        ValidationFailedError: If checksum doesn't match
    """
    actual_checksum = compute_checksum(file_path)
    if actual_checksum.lower() != expected_checksum.lower():
        raise ValidationFailedError(
            f"Checksum mismatch for {file_path.name}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
    return True


def download_file(url: str, destination: Path, api_key: Optional[str] = None) -> Path:
    """
    Download a file with progress bar and optional authentication.
    
    Args:
        url: Download URL
        destination: Destination path
        api_key: Optional API key for authentication
        
    Returns:
        Path to downloaded file
        
    Raises:
        DownloadError: If download fails
    """
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
        
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(destination, 'wb') as f, tqdm(
            desc=destination.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
                    
        return destination
        
    except requests.RequestException as e:
        raise DownloadError(f"Failed to download {url}: {e}")


def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """
    Extract a compressed archive.
    
    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract to
        
    Raises:
        DownloadError: If extraction fails
    """
    extract_to.mkdir(parents=True, exist_ok=True)
    
    try:
        if archive_path.suffix == '.gz' and archive_path.name.endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=extract_to)
        elif archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(path=extract_to)
        else:
            raise DownloadError(f"Unsupported archive format: {archive_path}")
            
    except (tarfile.TarError, zipfile.BadZipFile) as e:
        raise DownloadError(f"Failed to extract {archive_path}: {e}")


def download_dataset(
    dataset_id: str,
    version: str,
    output_dir: Optional[Path] = None,
    api_key: Optional[str] = None,
    verify_checksum: bool = True
) -> Tuple[Path, Dict]:
    """
    Download a complete dataset from OpenNeuro.
    
    Args:
        dataset_id: OpenNeuro dataset identifier (e.g., 'ds000001')
        version: Dataset version (e.g., '1.0.0')
        output_dir: Base output directory (defaults to data/raw/)
        api_key: Optional API key
        verify_checksum: Whether to verify checksum after download
        
    Returns:
        Tuple of (extracted_path, metadata_dict)
        
    Raises:
        DownloadError: If download or extraction fails
        ValidationFailedError: If validation fails
    """
    if output_dir is None:
        output_dir = Path(get_data_dir()) / 'raw'
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize client and get download URL
    client = OpenNeuroClient(api_key=api_key)
    dataset_info = client.get_dataset_info(dataset_id, version)
    
    if not dataset_info:
        raise DownloadError(f"Could not retrieve information for dataset {dataset_id}")
    
    # Construct download URL (OpenNeuro provides snapshot download endpoint)
    download_url = f"https://openneuro.org/datasets/{dataset_id}/versions/{version}/download"
    
    # Validate URL format
    validate_url(download_url)
    
    # Prepare file paths
    archive_name = f"{dataset_id}_{version}.tar.gz"
    archive_path = output_dir / archive_name
    extract_dir = output_dir / dataset_id / version
    
    # Download archive
    print(f"Downloading {dataset_id} version {version}...")
    download_file(download_url, archive_path, api_key)
    
    # Verify checksum if requested
    if verify_checksum and 'checksum' in dataset_info:
        print("Verifying checksum...")
        verify_checksum(archive_path, dataset_info['checksum'])
    
    # Extract archive
    print(f"Extracting to {extract_dir}...")
    extract_archive(archive_path, extract_dir)
    
    # Clean up archive
    archive_path.unlink()
    
    metadata = {
        'dataset_id': dataset_id,
        'version': version,
        'download_url': download_url,
        'extract_path': str(extract_dir),
        'checksum': compute_checksum(extract_dir / 'dataset_description.json') 
                   if (extract_dir / 'dataset_description.json').exists() else None,
        'download_timestamp': str(Path(output_dir).stat().st_mtime)
    }
    
    return extract_dir, metadata


def main():
    """Main entry point for dataset download."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download datasets from OpenNeuro with URL validation and checksum verification.'
    )
    parser.add_argument(
        'dataset_id',
        type=str,
        help='OpenNeuro dataset ID (e.g., ds000001)'
    )
    parser.add_argument(
        'version',
        type=str,
        help='Dataset version (e.g., 1.0.0)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (defaults to data/raw/)'
    )
    parser.add_argument(
        '--no-checksum',
        action='store_true',
        help='Skip checksum verification'
    )
    
    args = parser.parse_args()
    
    try:
        api_key = get_openneuro_api_key()
        output_dir = Path(args.output_dir) if args.output_dir else None
        
        extract_path, metadata = download_dataset(
            dataset_id=args.dataset_id,
            version=args.version,
            output_dir=output_dir,
            api_key=api_key,
            verify_checksum=not args.no_checksum
        )
        
        print(f"\nDownload complete!")
        print(f"Dataset: {args.dataset_id} version {args.version}")
        print(f"Extracted to: {extract_path}")
        print(f"Metadata saved to: {output_dir / 'download_metadata.json' if output_dir else Path(get_data_dir()) / 'raw' / 'download_metadata.json'}")
        
        # Save metadata
        metadata_path = (output_dir or Path(get_data_dir()) / 'raw') / 'download_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    except (DownloadError, ValidationFailedError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
