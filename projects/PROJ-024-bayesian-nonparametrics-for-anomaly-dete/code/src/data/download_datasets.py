import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    dataset_name: str
    status: str  # 'success', 'failed', 'skipped'
    file_path: Optional[str]
    checksum: Optional[str]
    expected_checksum: Optional[str]
    message: Optional[str]
    verified: Optional[bool] = None

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksum(file_path: str, expected_checksum: str) -> bool:
    """Validate file checksum against expected value."""
    if not os.path.exists(file_path):
        return False
    
    computed_checksum = compute_file_checksum(file_path)
    return computed_checksum == expected_checksum

def load_checksum_cache(cache_path: str) -> Dict[str, str]:
    """Load checksum cache from JSON file."""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load checksum cache: {e}")
    return {}

def save_checksum_cache(cache_path: str, checksums: Dict[str, str]) -> None:
    """Save checksum cache to JSON file."""
    try:
        with open(cache_path, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Saved checksum cache to {cache_path}")
    except IOError as e:
        logger.error(f"Failed to save checksum cache: {e}")

def download_from_url(url: str, destination: str, timeout: int = 30) -> bool:
    """Download file from URL with SSL verification."""
    try:
        # Create SSL context that verifies certificates
        context = ssl.create_default_context()
        
        logger.info(f"Downloading from {url} to {destination}")
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Download file
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, context=context, timeout=timeout) as response:
            with open(destination, 'wb') as out_file:
                out_file.write(response.read())
        
        logger.info(f"Download successful: {destination}")
        return True
        
    except urllib.error.HTTPError as e:
        logger.error(f"Download failed: HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"Download failed: URL Error: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Download failed: {type(e).__name__}: {e}")
        return False

def download_electricity_dataset(data_dir: str, cache_path: str) -> DownloadResult:
    """Download UCI Electricity Load Diagrams dataset."""
    dataset_name = "electricity"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip"
    filename = "electricity.csv"
    destination = os.path.join(data_dir, filename)
    
    # Expected checksum (this would be populated from a verified source)
    # For now, we'll use None and update when we have the actual checksum
    expected_checksum = None
    
    result = DownloadResult(
        dataset_name=dataset_name,
        status="skipped",
        file_path=None,
        checksum=None,
        expected_checksum=expected_checksum,
        message="No verified checksum available"
    )
    
    if expected_checksum is None:
        logger.warning(f"{dataset_name}: No expected checksum available. Download skipped for verification.")
        return result
    
    # Check if file already exists and verify checksum
    if os.path.exists(destination):
        if validate_checksum(destination, expected_checksum):
            result.status = "success"
            result.file_path = destination
            result.checksum = compute_file_checksum(destination)
            result.verified = True
            result.message = "Existing file verified successfully"
            logger.info(f"{dataset_name}: ✓ Existing file verified")
            return result
        else:
            logger.warning(f"{dataset_name}: Existing file checksum mismatch. Re-downloading...")
    
    # Download the dataset
    if download_from_url(url, destination):
        # Verify checksum after download
        computed_checksum = compute_file_checksum(destination)
        if computed_checksum == expected_checksum:
            result.status = "success"
            result.file_path = destination
            result.checksum = computed_checksum
            result.verified = True
            result.message = "Download and verification successful"
            logger.info(f"{dataset_name}: ✓ Download and verification successful")
        else:
            result.status = "failed"
            result.message = f"Checksum mismatch: expected {expected_checksum}, got {computed_checksum}"
            logger.error(f"{dataset_name}: ✗ Checksum mismatch")
    else:
        result.status = "failed"
        result.message = "Download failed"
        logger.error(f"{dataset_name}: ✗ Download failed")
    
    return result

def download_traffic_dataset(data_dir: str, cache_path: str) -> DownloadResult:
    """Download UCI Traffic dataset."""
    dataset_name = "traffic"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00360/traffic.txt.zip"
    filename = "traffic.csv"
    destination = os.path.join(data_dir, filename)
    
    # Expected checksum (this would be populated from a verified source)
    expected_checksum = None
    
    result = DownloadResult(
        dataset_name=dataset_name,
        status="skipped",
        file_path=None,
        checksum=None,
        expected_checksum=expected_checksum,
        message="No verified checksum available"
    )
    
    if expected_checksum is None:
        logger.warning(f"{dataset_name}: No expected checksum available. Download skipped for verification.")
        return result
    
    # Check if file already exists and verify checksum
    if os.path.exists(destination):
        if validate_checksum(destination, expected_checksum):
            result.status = "success"
            result.file_path = destination
            result.checksum = compute_file_checksum(destination)
            result.verified = True
            result.message = "Existing file verified successfully"
            logger.info(f"{dataset_name}: ✓ Existing file verified")
            return result
        else:
            logger.warning(f"{dataset_name}: Existing file checksum mismatch. Re-downloading...")
    
    # Download the dataset
    if download_from_url(url, destination):
        # Verify checksum after download
        computed_checksum = compute_file_checksum(destination)
        if computed_checksum == expected_checksum:
            result.status = "success"
            result.file_path = destination
            result.checksum = computed_checksum
            result.verified = True
            result.message = "Download and verification successful"
            logger.info(f"{dataset_name}: ✓ Download and verification successful")
        else:
            result.status = "failed"
            result.message = f"Checksum mismatch: expected {expected_checksum}, got {computed_checksum}"
            logger.error(f"{dataset_name}: ✗ Checksum mismatch")
    else:
        result.status = "failed"
        result.message = "Download failed"
        logger.error(f"{dataset_name}: ✗ Download failed")
    
    return result

def download_synthetic_control_chart_dataset(data_dir: str, cache_path: str) -> DownloadResult:
    """Download Synthetic Control Chart Time Series dataset."""
    dataset_name = "synthetic_control_chart"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control.data"
    filename = "synthetic_control_chart.csv"
    destination = os.path.join(data_dir, filename)
    
    # Expected checksum (this would be populated from a verified source)
    expected_checksum = None
    
    result = DownloadResult(
        dataset_name=dataset_name,
        status="skipped",
        file_path=None,
        checksum=None,
        expected_checksum=expected_checksum,
        message="No verified checksum available"
    )
    
    if expected_checksum is None:
        logger.warning(f"{dataset_name}: No expected checksum available. Download skipped for verification.")
        return result
    
    # Check if file already exists and verify checksum
    if os.path.exists(destination):
        if validate_checksum(destination, expected_checksum):
            result.status = "success"
            result.file_path = destination
            result.checksum = compute_file_checksum(destination)
            result.verified = True
            result.message = "Existing file verified successfully"
            logger.info(f"{dataset_name}: ✓ Existing file verified")
            return result
        else:
            logger.warning(f"{dataset_name}: Existing file checksum mismatch. Re-downloading...")
    
    # Download the dataset
    if download_from_url(url, destination):
        # Verify checksum after download
        computed_checksum = compute_file_checksum(destination)
        if computed_checksum == expected_checksum:
            result.status = "success"
            result.file_path = destination
            result.checksum = computed_checksum
            result.verified = True
            result.message = "Download and verification successful"
            logger.info(f"{dataset_name}: ✓ Download and verification successful")
        else:
            result.status = "failed"
            result.message = f"Checksum mismatch: expected {expected_checksum}, got {computed_checksum}"
            logger.error(f"{dataset_name}: ✗ Checksum mismatch")
    else:
        result.status = "failed"
        result.message = "Download failed"
        logger.error(f"{dataset_name}: ✗ Download failed")
    
    return result

def download_pems_sf_dataset(data_dir: str, cache_path: str) -> DownloadResult:
    """Download PEMS-SF dataset (deprecated, will be skipped)."""
    dataset_name = "pems_sf"
    logger.warning(f"{dataset_name}: PEMS-SF dataset is deprecated and will be skipped")
    
    return DownloadResult(
        dataset_name=dataset_name,
        status="skipped",
        file_path=None,
        checksum=None,
        expected_checksum=None,
        message="PEMS-SF dataset is deprecated"
    )

def generate_synthetic_dataset(data_dir: str, cache_path: str) -> DownloadResult:
    """Generate synthetic dataset for testing."""
    dataset_name = "synthetic_test"
    filename = "synthetic_test.csv"
    destination = os.path.join(data_dir, filename)
    
    # Generate a simple synthetic dataset
    try:
        import numpy as np
        np.random.seed(42)
        
        # Generate 1000 data points with some anomalies
        n_points = 1000
        anomaly_indices = np.random.choice(n_points, size=int(n_points * 0.05), replace=False)
        
        data = np.random.randn(n_points)
        data[anomaly_indices] += np.random.randn(len(anomaly_indices)) * 3
        
        # Save to CSV
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        np.savetxt(destination, data, delimiter=',', header='value', comments='')
        
        # Compute checksum
        checksum = compute_file_checksum(destination)
        
        logger.info(f"{dataset_name}: Synthetic dataset generated at {destination}")
        
        return DownloadResult(
            dataset_name=dataset_name,
            status="success",
            file_path=destination,
            checksum=checksum,
            expected_checksum=None,
            message="Synthetic dataset generated",
            verified=True  # Synthetic data is inherently "verified"
        )
        
    except Exception as e:
        logger.error(f"{dataset_name}: Failed to generate synthetic dataset: {e}")
        return DownloadResult(
            dataset_name=dataset_name,
            status="failed",
            file_path=None,
            checksum=None,
            expected_checksum=None,
            message=f"Failed to generate: {e}"
        )

def download_all_datasets(data_dir: str, cache_path: Optional[str] = None) -> Tuple[bool, Dict[str, DownloadResult]]:
    """Download all datasets with checksum verification."""
    if cache_path is None:
        cache_path = os.path.join(os.path.dirname(data_dir), "state", "checksums.json")
    
    # Load existing checksum cache
    checksum_cache = load_checksum_cache(cache_path)
    
    results = {}
    
    # Define datasets to download
    downloaders = [
        ("electricity", download_electricity_dataset),
        ("traffic", download_traffic_dataset),
        ("synthetic_control_chart", download_synthetic_control_chart_dataset),
        ("pems_sf", download_pems_sf_dataset),
    ]
    
    for dataset_name, downloader in downloaders:
        # Skip if already in cache and verified
        if dataset_name in checksum_cache:
            cached_checksum = checksum_cache[dataset_name]
            # We would need to re-verify against the actual file
            # For now, we'll proceed with download/verification
        
        result = downloader(data_dir, cache_path)
        results[dataset_name] = result
        
        # Update cache if successful
        if result.status == "success" and result.checksum:
            checksum_cache[dataset_name] = result.checksum
    
    # Save updated cache
    save_checksum_cache(cache_path, checksum_cache)
    
    # Print summary
    logger.info("=" * 70)
    logger.info("Download Summary:")
    logger.info("=" * 70)
    
    all_success = True
    for dataset_name, result in results.items():
        status_icon = "✓" if result.status == "success" else "✗"
        logger.info(f"  {dataset_name}: {result.status.upper()} - {result.message}")
        if result.status != "success":
            all_success = False
    
    logger.info("=" * 70)
    
    if not all_success:
        logger.error("✗ Some downloads failed. Check error messages above.")
    else:
        logger.info("✓ All datasets downloaded and verified successfully.")
    
    return all_success, results

def main():
    """Main entry point for dataset download and verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and verify datasets with checksum validation")
    parser.add_argument("--data-dir", type=str, default="data/raw", help="Directory to store downloaded datasets")
    parser.add_argument("--cache-path", type=str, default=None, help="Path to checksum cache file")
    parser.add_argument("--datasets", type=str, nargs="+", default=None, 
                      help="Specific datasets to download (electricity, traffic, synthetic_control_chart, pems_sf)")
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Determine cache path
    cache_path = args.cache_path
    if cache_path is None:
        # Default to project state directory
        project_root = Path(__file__).parent.parent.parent.parent
        cache_path = os.path.join(project_root, "state", "checksums.json")
    
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Checksum cache: {cache_path}")
    
    # Download all datasets
    success, results = download_all_datasets(args.data_dir, cache_path)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()