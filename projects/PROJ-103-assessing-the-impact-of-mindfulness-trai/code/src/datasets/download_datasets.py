"""
Dataset download script with URL validation and checksum verification.

This module handles the downloading of OpenNeuro datasets, validating URLs,
verifying checksums, and organizing downloaded files into the data/raw/ directory.
"""
import os
import re
import json
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from src.config.env import get_data_dir, get_openneuro_api_key
from src.datasets.openneuro_client import OpenNeuroClient, DatasetNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Base exception for download-related errors."""
    pass


class URLValidationError(DownloadError):
    """Raised when URL format validation fails."""
    pass


class ChecksumError(DownloadError):
    """Raised when checksum verification fails."""
    pass


def validate_url_format(url: str) -> bool:
    """
    Validate that a URL has the correct format for OpenNeuro.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if the URL format is valid
        
    Raises:
        URLValidationError: If the URL format is invalid
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL must be a non-empty string")
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Check scheme
    if parsed.scheme not in ('http', 'https'):
        raise URLValidationError(f"URL must use http or https scheme, got: {parsed.scheme}")
    
    # Check domain (must be openneuro.org or a known mirror)
    if 'openneuro.org' not in parsed.netloc and 'openneuro-production.s3.amazonaws.com' not in parsed.netloc:
        raise URLValidationError(f"URL domain must be openneuro.org, got: {parsed.netloc}")
    
    # Check path contains dataset identifier
    if '/datasets/' not in parsed.path:
        raise URLValidationError(f"URL must contain '/datasets/' path component")
    
    return True


def get_dataset_id_from_url(url: str) -> str:
    """
    Extract the dataset ID from an OpenNeuro URL.
    
    Args:
        url: The OpenNeuro URL
        
    Returns:
        The dataset ID (e.g., 'ds000001')
        
    Raises:
        URLValidationError: If the URL is invalid or doesn't contain a dataset ID
    """
    validate_url_format(url)
    
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    
    # Find the dataset ID in the path
    for i, part in enumerate(path_parts):
        if part == 'datasets' and i + 1 < len(path_parts):
            dataset_id = path_parts[i + 1]
            # Validate dataset ID format
            if re.match(r'^ds\d{6}$', dataset_id):
                return dataset_id
    
    raise URLValidationError(f"Could not extract valid dataset ID from URL: {url}")


def compute_file_checksum(file_path: str, algorithm: str = 'sha256', chunk_size: int = 8192) -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        chunk_size: Size of chunks to read
        
    Returns:
        Hexadecimal checksum string
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use
        
    Returns:
        True if checksums match
        
    Raises:
        ChecksumError: If checksums don't match
    """
    if not os.path.exists(file_path):
        raise ChecksumError(f"File does not exist: {file_path}")
    
    actual_checksum = compute_file_checksum(file_path, algorithm)
    
    if actual_checksum.lower() != expected_checksum.lower():
        raise ChecksumError(
            f"Checksum mismatch for {file_path}\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}"
        )
    
    return True


def download_file(url: str, output_path: str, chunk_size: int = 8192) -> None:
    """
    Download a file from a URL to the specified output path.
    
    Args:
        url: Source URL
        output_path: Destination file path
        chunk_size: Size of chunks to download
        
    Raises:
        DownloadError: If download fails
    """
    import requests
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Create parent directories if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
        
        logger.info(f"Downloaded: {url} -> {output_path}")
        
    except requests.exceptions.RequestException as e:
        raise DownloadError(f"Failed to download {url}: {str(e)}")
    except IOError as e:
        raise DownloadError(f"Failed to write file {output_path}: {str(e)}")


def download_dataset(dataset_id: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Download a dataset from OpenNeuro using the dataset ID.
    
    This function uses the OpenNeuro API to get download URLs and then
    downloads the files using git-annex or direct download.
    
    Args:
        dataset_id: The dataset ID (e.g., 'ds000001')
        output_dir: Directory to download to (defaults to data/raw/datasets/{dataset_id})
        
    Returns:
        Dictionary containing download results and metadata
        
    Raises:
        DownloadError: If download fails
    """
    if not re.match(r'^ds\d{6}$', dataset_id):
        raise URLValidationError(f"Invalid dataset ID format: {dataset_id}")
    
    data_dir = Path(output_dir) if output_dir else get_data_dir() / 'raw' / 'datasets' / dataset_id
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading dataset {dataset_id} to {data_dir}")
    
    # Try to use git-annex if available, otherwise fall back to direct download
    try:
        # Check if git-annex is available
        subprocess.run(['git-annex', 'version'], capture_output=True, check=True)
        
        # Initialize git repository
        subprocess.run(['git', 'init'], cwd=data_dir, check=True)
        
        # Configure git for large files
        subprocess.run(['git', 'annex', 'init'], cwd=data_dir, check=True)
        
        # Add the remote
        remote_url = f"https://openneuro.org/datasets/{dataset_id}/files"
        subprocess.run(['git', 'annex', 'initremote', 'openneuro', f'type=directory', f'directory={data_dir}'], 
                     cwd=data_dir, check=True)
        
        # Get the dataset files
        subprocess.run(['git', 'annex', 'get', '.'], cwd=data_dir, check=True)
        
        logger.info(f"Dataset {dataset_id} downloaded via git-annex")
        
        return {
            'dataset_id': dataset_id,
            'output_dir': str(data_dir),
            'status': 'success',
            'method': 'git-annex'
        }
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to direct download via API
        logger.info(f"Git-annex not available, attempting direct download for {dataset_id}")
        
        try:
            client = OpenNeuroClient()
            dataset_info = client.get_dataset_info(dataset_id)
            
            # Get download URLs
            if 'files' in dataset_info:
                files_info = dataset_info['files']
                downloaded_files = []
                
                for file_info in files_info:
                    if 'url' in file_info and 'filename' in file_info:
                        url = file_info['url']
                        filename = file_info['filename']
                        file_path = data_dir / filename
                        
                        try:
                            download_file(url, str(file_path))
                            downloaded_files.append({
                                'filename': filename,
                                'url': url,
                                'status': 'success'
                            })
                            
                            # Verify checksum if available
                            if 'checksum' in file_info:
                                verify_checksum(str(file_path), file_info['checksum'])
                                
                        except Exception as e:
                            logger.warning(f"Failed to download {filename}: {str(e)}")
                            downloaded_files.append({
                                'filename': filename,
                                'url': url,
                                'status': 'failed',
                                'error': str(e)
                            })
                
                return {
                    'dataset_id': dataset_id,
                    'output_dir': str(data_dir),
                    'status': 'success',
                    'method': 'direct',
                    'files': downloaded_files
                }
            else:
                raise DownloadError(f"No file information found for dataset {dataset_id}")
                
        except DatasetNotFoundError as e:
            raise DownloadError(f"Dataset not found: {str(e)}")
        except Exception as e:
            raise DownloadError(f"Failed to download dataset {dataset_id}: {str(e)}")


def download_datasets_from_list(dataset_ids: List[str], output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Download multiple datasets from a list of IDs.
    
    Args:
        dataset_ids: List of dataset IDs to download
        output_dir: Base directory for downloads
        
    Returns:
        Dictionary containing results for all datasets
    """
    results = {
        'total': len(dataset_ids),
        'successful': 0,
        'failed': 0,
        'datasets': []
    }
    
    for dataset_id in dataset_ids:
        try:
            result = download_dataset(dataset_id, output_dir)
            if result['status'] == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
            results['datasets'].append(result)
        except Exception as e:
            results['failed'] += 1
            results['datasets'].append({
                'dataset_id': dataset_id,
                'status': 'failed',
                'error': str(e)
            })
            logger.error(f"Failed to download {dataset_id}: {str(e)}")
    
    return results


def main():
    """
    Main entry point for downloading datasets.
    
    This function can be run from the command line to download specific
    datasets or all datasets that match certain criteria.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Download OpenNeuro datasets')
    parser.add_argument('--dataset-id', '-d', type=str, help='Single dataset ID to download')
    parser.add_argument('--dataset-ids', '-i', type=str, nargs='+', help='Multiple dataset IDs to download')
    parser.add_argument('--output-dir', '-o', type=str, help='Output directory for downloads')
    parser.add_argument('--validate-only', action='store_true', help='Only validate URLs, do not download')
    
    args = parser.parse_args()
    
    if not args.dataset_id and not args.dataset_ids:
        parser.error("Must specify either --dataset-id or --dataset-ids")
    
    dataset_ids = []
    if args.dataset_id:
        dataset_ids.append(args.dataset_id)
    if args.dataset_ids:
        dataset_ids.extend(args.dataset_ids)
    
    # Validate all dataset IDs
    for dataset_id in dataset_ids:
        try:
            validate_url_format(f"https://openneuro.org/datasets/{dataset_id}")
            logger.info(f"Validated dataset ID: {dataset_id}")
        except URLValidationError as e:
            logger.error(f"Invalid dataset ID {dataset_id}: {str(e)}")
            return 1
    
    if args.validate_only:
        logger.info("Validation complete, not downloading")
        return 0
    
    # Download datasets
    logger.info(f"Starting download of {len(dataset_ids)} dataset(s)")
    results = download_datasets_from_list(dataset_ids, args.output_dir)
    
    # Log results
    logger.info(f"Download complete: {results['successful']} successful, {results['failed']} failed")
    
    # Save results to JSON
    results_path = Path(args.output_dir or get_data_dir()) / 'raw' / 'download_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    
    return 0 if results['failed'] == 0 else 1


if __name__ == '__main__':
    exit(main())
