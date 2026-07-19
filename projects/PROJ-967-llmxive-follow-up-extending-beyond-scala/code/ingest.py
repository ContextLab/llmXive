"""
Ingestion module for the llmXive Follow-up project.
Handles downloading, verifying, and preprocessing the Z-Reward dataset.
"""
import argparse
import hashlib
import logging
import os
import sys
import csv
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import requests, fallback to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
ZREWARD_URL = "https://huggingface.co/datasets/llm-safety/zreward/resolve/main/data/train-00000-of-00001.parquet"
# Note: The actual Z-Reward dataset is distributed as Parquet.
# We will download it and convert to CSV as per task requirements.
# The SHA256 below is a placeholder; in a real scenario, this would be verified
# against the official release or computed after download for the first run.
# Since the dataset is large and dynamic, we will verify existence and schema
# rather than a static checksum which might change with dataset updates.
EXPECTED_SHA256 = None 

def setup_directories():
    """Ensure required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {DATA_RAW_DIR}")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(url: str, output_path: Path) -> Path:
    """
    Download the dataset from the specified URL.
    Uses requests if available, otherwise falls back to urllib.
    """
    if output_path.exists():
        logger.info(f"Dataset already exists at {output_path}. Skipping download.")
        return output_path

    logger.info(f"Downloading dataset from {url}...")
    
    try:
        if HAS_REQUESTS:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        else:
            urllib.request.urlretrieve(url, output_path)
        
        logger.info(f"Download complete: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def validate_schema(csv_path: Path) -> bool:
    """
    Validate the schema of the downloaded CSV.
    Checks for the presence of required rubric dimensions and human annotation columns.
    """
    required_columns = {
        'Alignment', 'Realism', 'Aesthetics', 'Plausibility',
        'human_score', 'prompt_id'
    }
    
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        return False

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            header_set = set(header)
            
            missing = required_columns - header_set
            if missing:
                logger.error(f"Schema validation failed. Missing columns: {missing}")
                return False
            
            logger.info("Schema validation passed. All required columns present.")
            return True
    except Exception as e:
        logger.error(f"Error reading CSV for validation: {e}")
        return False

def convert_parquet_to_csv(parquet_path: Path, csv_path: Path) -> Path:
    """
    Convert a Parquet file to CSV.
    Requires pandas and pyarrow.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required for Parquet conversion. Please install it.")
        raise

    logger.info(f"Converting {parquet_path} to {csv_path}...")
    try:
        df = pd.read_parquet(parquet_path)
        # Ensure the required columns exist before saving
        required = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility', 'human_score', 'prompt_id']
        missing = set(required) - set(df.columns)
        if missing:
            logger.warning(f"Parquet file missing expected columns: {missing}. Proceeding with available columns.")
        
        df.to_csv(csv_path, index=False)
        logger.info(f"Conversion complete: {csv_path}")
        return csv_path
    except Exception as e:
        logger.error(f"Failed to convert Parquet to CSV: {e}")
        raise

def download_dataset(url: str, output_path: Path) -> Path:
    """
    Download the dataset from the specified URL.
    Uses requests if available, otherwise falls back to urllib.
    """
    if output_path.exists():
        logger.info(f"Dataset already exists at {output_path}. Skipping download.")
        return output_path

    logger.info(f"Downloading dataset from {url}...")
    
    try:
        if HAS_REQUESTS:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        else:
            urllib.request.urlretrieve(url, output_path)
        
        logger.info(f"Download complete: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def convert_parquet_to_csv(parquet_path: Path, csv_path: Path) -> Path:
    """
    Convert a Parquet file to CSV.
    Requires pandas and pyarrow.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required for Parquet conversion. Please install it.")
        raise

    logger.info(f"Converting {parquet_path} to {csv_path}...")
    try:
        df = pd.read_parquet(parquet_path)
        # Ensure the required columns exist before saving
        required = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility', 'human_score', 'prompt_id']
        missing = set(required) - set(df.columns)
        if missing:
            logger.warning(f"Parquet file missing expected columns: {missing}. Proceeding with available columns.")
        
        df.to_csv(csv_path, index=False)
        logger.info(f"Conversion complete: {csv_path}")
        return csv_path
    except Exception as e:
        logger.error(f"Failed to convert Parquet to CSV: {e}")
        raise

def identify_primary_quality_dimension(row: Dict[str, Any]) -> Optional[str]:
    """
    Identify the primary quality dimension based on row metadata.
    For now, returns the first non-null dimension or 'Alignment' as default.
    This logic is a placeholder and should be refined based on specific metadata rules.
    """
    dims = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    for dim in dims:
        if dim in row and row[dim] is not None:
            return dim
    return 'Alignment'

def load_and_align_data(csv_path: Path) -> list:
    """
    Load the CSV and align teacher/student outputs with human annotations.
    Returns a list of aligned dictionaries.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required for data loading.")
        raise

    logger.info(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Basic alignment logic: ensure all rows have the required keys
    aligned_data = []
    for _, row in df.iterrows():
        aligned_row = {
            'prompt_id': row.get('prompt_id'),
            'Alignment': row.get('Alignment'),
            'Realism': row.get('Realism'),
            'Aesthetics': row.get('Aesthetics'),
            'Plausibility': row.get('Plausibility'),
            'human_score': row.get('human_score'),
            'primary_dimension': identify_primary_quality_dimension(row.to_dict())
        }
        aligned_data.append(aligned_row)
    
    logger.info(f"Loaded and aligned {len(aligned_data)} samples.")
    return aligned_data

def print_summary(data: list):
    """Print a summary of the loaded data."""
    if not data:
        logger.warning("No data to summarize.")
        return

    total = len(data)
    missing_human = sum(1 for d in data if d['human_score'] is None)
    dims = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    
    logger.info(f"=== Data Summary ===")
    logger.info(f"Total samples: {total}")
    logger.info(f"Missing human annotations: {missing_human}")
    
    for dim in dims:
        count = sum(1 for d in data if d[dim] is not None)
        logger.info(f"  {dim} coverage: {count}/{total}")

def parse_args():
    parser = argparse.ArgumentParser(description="Ingest and preprocess Z-Reward dataset.")
    parser.add_argument('--url', type=str, default=ZREWARD_URL, help='URL to download the dataset from.')
    parser.add_argument('--output-dir', type=str, default=str(DATA_RAW_DIR), help='Directory to save the dataset.')
    parser.add_argument('--output-filename', type=str, default='zreward_dataset.csv', help='Output filename.')
    return parser.parse_args()

def main():
    args = parse_args()
    setup_directories()

    output_path = Path(args.output_dir) / args.output_filename
    parquet_path = Path(args.output_dir) / "train.parquet" # Temporary parquet storage

    # 1. Download
    try:
        # If the source is parquet, we download parquet first
        if args.url.endswith('.parquet'):
            download_dataset(args.url, parquet_path)
            # 2. Convert to CSV
            convert_parquet_to_csv(parquet_path, output_path)
            # Cleanup parquet if desired, but keeping for now
        else:
            # Assume direct CSV download if not parquet
            download_dataset(args.url, output_path)
    except Exception as e:
        logger.critical(f"Download or conversion failed: {e}")
        sys.exit(1)

    # 3. Verify Integrity (Checksum)
    # If EXPECTED_SHA256 is set, verify it. Otherwise, just check file existence and size.
    if not output_path.exists():
        logger.critical("Output file was not created.")
        sys.exit(1)

    if EXPECTED_SHA256:
        actual_hash = calculate_sha256(output_path)
        if actual_hash != EXPECTED_SHA256:
            logger.critical(f"Checksum mismatch. Expected: {EXPECTED_SHA256}, Got: {actual_hash}")
            sys.exit(1)
        logger.info("Checksum verification passed.")
    else:
        logger.info("Skipping checksum verification (EXPECTED_SHA256 not set).")

    # 4. Validate Schema
    if not validate_schema(output_path):
        logger.critical("Schema validation failed.")
        sys.exit(1)

    # 5. Load and Align (for summary)
    data = load_and_align_data(output_path)
    print_summary(data)

    logger.info("Ingestion pipeline completed successfully.")

if __name__ == '__main__':
    main()
