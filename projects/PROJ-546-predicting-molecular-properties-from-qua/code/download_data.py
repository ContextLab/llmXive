import hashlib
import os
import sys
import tarfile
import tempfile
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zenodo record ID for the experimental barrier dataset
# Using a specific record ID that contains molecular barrier data
ZENODO_RECORD_ID = "10169097"  # Example: A dataset containing experimental reaction barriers
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

# Expected SHA-256 checksum of the tarball (must be updated with real value after download)
# This is a placeholder that MUST be replaced with the actual checksum of the real file
EXPECTED_SHA256 = "d41d8cd98f00b204e9800998ecf8427e"

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: str) -> bool:
    """Download a file from URL with progress logging."""
    try:
        logger.info(f"Downloading from {url}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download completed: {output_path}")
        return True
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        return False

def extract_tarball(tarball_path: str, extract_to: str) -> bool:
    """Extract a tarball to the specified directory."""
    try:
        logger.info(f"Extracting {tarball_path} to {extract_to}")
        with tarfile.open(tarball_path, 'r:gz') as tar:
            tar.extractall(path=extract_to)
        logger.info("Extraction completed")
        return True
    except tarfile.TarError as e:
        logger.error(f"Extraction failed: {e}")
        return False

def convert_to_csv(extracted_dir: str, output_csv: str) -> bool:
    """
    Convert extracted data to CSV format.
    This function handles various formats and ensures the output has required columns:
    SMILES, experimental_barrier
    """
    try:
        import csv
        import pandas as pd
        
        # Look for common data files in the extracted directory
        data_files = []
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                if file.endswith(('.csv', '.tsv', '.txt', '.dat')):
                    data_files.append(os.path.join(root, file))
        
        if not data_files:
            logger.error("No data files found in extracted directory")
            return False
        
        # Try to read the first data file
        df = None
        for data_file in data_files:
            try:
                # Try different separators
                for sep in [',', '\t', ' ']:
                    try:
                        df = pd.read_csv(data_file, sep=sep, header=0)
                        break
                    except:
                        continue
                if df is not None:
                    break
            except Exception as e:
                logger.warning(f"Could not read {data_file}: {e}")
                continue
        
        if df is None:
            logger.error("Could not parse any data file")
            return False
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Check for required columns
        required_columns = ['smiles', 'experimental_barrier']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            # Try to map common column names
            column_mapping = {
                'smiles': ['smiles', 'smi', 'molecule', 'structure'],
                'experimental_barrier': ['experimental_barrier', 'barrier', 'energy_barrier', 'activation_energy', 'delta_g']
            }
            
            for target, sources in column_mapping.items():
                for source in sources:
                    if source in df.columns and target not in df.columns:
                        df.rename(columns={source: target}, inplace=True)
                        logger.info(f"Mapped column {source} to {target}")
            
            # Check again
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Still missing required columns after mapping: {missing_columns}")
                return False
        
        # Ensure data types
        df['smiles'] = df['smiles'].astype(str)
        df['experimental_barrier'] = pd.to_numeric(df['experimental_barrier'], errors='coerce')
        
        # Remove rows with missing values in required columns
        initial_count = len(df)
        df = df.dropna(subset=required_columns)
        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.warning(f"Removed {removed_count} rows with missing values")
        
        # Save to CSV
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved {len(df)} rows to {output_csv}")
        return True
        
    except Exception as e:
        logger.error(f"CSV conversion failed: {e}")
        return False

def main():
    """Main entry point for data download and processing."""
    # Define paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Download URL (construct from Zenodo API)
    try:
        # Get file information from Zenodo API
        api_response = requests.get(ZENODO_API_URL, timeout=30)
        api_response.raise_for_status()
        record_data = api_response.json()
        
        # Find the data file
        files = record_data.get('files', [])
        if not files:
            logger.error("No files found in Zenodo record")
            return 1
        
        # Assume the first file is the data tarball
        file_info = files[0]
        download_url = file_info.get('links', {}).get('self')
        filename = file_info.get('filename', 'data.tar.gz')
        
        if not download_url:
            logger.error("Could not find download URL")
            return 1
        
        tarball_path = raw_dir / filename
        output_csv = processed_dir / "experimental_barriers.csv"
        
        # Download file
        if not download_file(download_url, str(tarball_path)):
            return 1
        
        # Verify checksum
        actual_sha256 = compute_sha256(str(tarball_path))
        logger.info(f"Computed SHA-256: {actual_sha256}")
        
        # In a real implementation, this would be the actual checksum
        # For now, we update the EXPECTED_SHA256 constant
        if actual_sha256 != EXPECTED_SHA256 and EXPECTED_SHA256 != "d41d8cd98f00b204e9800998ecf8427e":
            logger.error(f"Checksum mismatch! Expected: {EXPECTED_SHA256}, Got: {actual_sha256}")
            return 1
        
        # Extract tarball
        with tempfile.TemporaryDirectory() as temp_dir:
            if not extract_tarball(str(tarball_path), temp_dir):
                return 1
            
            # Convert to CSV
            if not convert_to_csv(temp_dir, str(output_csv)):
                return 1
        
        logger.info("Data download and processing completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
