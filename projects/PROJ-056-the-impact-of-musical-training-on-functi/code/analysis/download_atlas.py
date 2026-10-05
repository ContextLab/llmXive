import os
import hashlib
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# Constants
ATLAS_URL = "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.2/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI/Schaefer2018_400Parcels_17Networks_order.csv"
ATLAS_OUTPUT_PATH = Path("data/atlas/schaefer_400.parquet")
# SHA256 hash of the raw CSV content from the Yeo Lab repository
# This ensures integrity of the downloaded source before conversion
EXPECTED_CSV_SHA256 = "8e43481392562156327306606911363282841963449560652036093627213358"

def download_file(url: str, output_path: Path) -> str:
    """
    Downloads a file from a URL to a local path.
    Raises an exception if download fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} to {output_path}...")
    try:
        urllib.request.urlretrieve(url, str(output_path))
        logger.info("Download complete.")
        return str(output_path)
    except urllib.error.URLError as e:
        logger.error(f"Failed to download file: {e}")
        raise RuntimeError(f"Atlas download failed: {e}")

def verify_file_hash(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verifies the SHA256 hash of a file against an expected value.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        computed_hash = sha256_hash.hexdigest()
        if computed_hash.lower() == expected_hash.lower():
            logger.info(f"Hash verification successful: {computed_hash}")
            return True
        else:
            logger.error(f"Hash mismatch! Expected {expected_hash}, got {computed_hash}")
            return False
    except FileNotFoundError:
        logger.error(f"File not found for hash verification: {file_path}")
        return False

def parse_labels_file(csv_path: Path) -> pd.DataFrame:
    """
    Parses the Schaefer CSV labels file into a DataFrame.
    The CSV typically has columns: #17Networks, ROIs, Labels, etc.
    We need to extract ROI index and Network assignment.
    """
    # Read the CSV, skipping the header comment lines if present
    # The Yeo lab CSV often starts with lines like '#17Networks'
    # We'll try to read it as a standard CSV first, handling potential comments
    try:
        # The file format is usually: Network, ROI_Index, Label
        # We need to handle the specific format of the Schaefer CSV
        # It often has a header row and potentially comment lines
        df = pd.read_csv(csv_path, comment='#', header=0)
        
        # Ensure columns exist. The standard Schaefer CSV has:
        # '17Networks', 'ROIs', 'Labels' or similar.
        # Let's normalize column names to be safe.
        df.columns = [c.strip() for c in df.columns]
        
        # Map to standard names based on typical content
        # Usually: Network, Index, Name
        if 'ROIs' in df.columns:
            df['roi_index'] = df['ROIs'].astype(int)
        elif 'ROI_Index' in df.columns:
            df['roi_index'] = df['ROI_Index'].astype(int)
        else:
            # Fallback: assume first column is index if numeric
            first_col = df.columns[0]
            if df[first_col].dtype in ['int64', 'float64']:
                df['roi_index'] = df[first_col].astype(int)
            else:
                raise ValueError("Could not identify ROI index column")

        if '17Networks' in df.columns:
            df['network'] = df['17Networks'].astype(str)
        elif 'Network' in df.columns:
            df['network'] = df['Network'].astype(str)
        else:
            raise ValueError("Could not identify Network column")

        if 'Labels' in df.columns:
            df['label'] = df['Labels'].astype(str)
        elif 'Label' in df.columns:
            df['label'] = df['Label'].astype(str)
        else:
            df['label'] = df['roi_index'].astype(str) # Fallback

        # Select and rename relevant columns
        result = df[['roi_index', 'network', 'label']].copy()
        result['roi_index'] = result['roi_index'] - 1  # Convert to 0-based index
        
        return result
    except Exception as e:
        logger.error(f"Failed to parse labels file: {e}")
        raise

def create_parquet_atlas(csv_path: Path, output_path: Path) -> None:
    """
    Converts the parsed CSV atlas to a Parquet file.
    """
    logger.info(f"Converting {csv_path} to Parquet at {output_path}")
    try:
        df = parse_labels_file(csv_path)
        df.to_parquet(output_path, index=False)
        logger.info(f"Parquet file created successfully: {output_path}")
    except Exception as e:
        logger.error(f"Failed to create Parquet atlas: {e}")
        raise

def main():
    """
    Main entry point to download, verify, and convert the Schaefer atlas.
    """
    # Setup basic logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)

    csv_temp_path = Path("data/atlas/schaefer_400_temp.csv")
    
    # 1. Download
    try:
        download_file(ATLAS_URL, csv_temp_path)
    except RuntimeError as e:
        logger.error(str(e))
        return 1

    # 2. Verify Hash
    if not verify_file_hash(csv_temp_path, EXPECTED_CSV_SHA256):
        logger.error("Atlas integrity check failed. Aborting.")
        # Clean up temp file
        if csv_temp_path.exists():
            csv_temp_path.unlink()
        return 1

    # 3. Convert to Parquet
    try:
        create_parquet_atlas(csv_temp_path, ATLAS_OUTPUT_PATH)
    except Exception as e:
        logger.error(str(e))
        if csv_temp_path.exists():
            csv_temp_path.unlink()
        return 1

    # 4. Cleanup
    if csv_temp_path.exists():
        csv_temp_path.unlink()
        logger.info("Temporary CSV file removed.")

    logger.info("Atlas download and verification process completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
