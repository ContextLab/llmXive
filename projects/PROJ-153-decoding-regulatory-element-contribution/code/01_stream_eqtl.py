"""
T045: Download eQTL dataset and stream it for processing.

This script implements a two-phase approach:
1. Download the eQTL dataset from a verified real source (GEO/SRA or HuggingFace) 
   to `data/raw/` as a static, checksummed file.
2. Stream the dataset using `datasets.load_dataset(..., streaming=True)` to process
   in chunks without loading the entire dataset into memory.

This ensures reproducibility on fresh runners while preserving statistical power.

Requirements:
- datasets (HuggingFace)
- pandas
- pyarrow
"""

import os
import sys
import hashlib
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from datasets import load_dataset
except ImportError:
    logging.error("The 'datasets' package is required. Install with: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
EQTL_OUTPUT_FILE = DATA_RAW_DIR / "yeast_eqtl_full.tsv"
CHECKSUM_FILE = DATA_RAW_DIR / "yeast_eqtl_full.tsv.sha256"

# Real data source configuration
# Using HuggingFace datasets library to access the yeast eQTL dataset
# If a specific dataset is not available, we use a verified public source
# For this implementation, we assume the dataset is available via a HuggingFace hub
# or a direct URL. The manifest.yaml (from T052) should contain the actual accession.
# Since T052 populated manifest.yaml with verified accessions, we read from there.

def load_manifest() -> Dict[str, Any]:
    """Load the manifest.yaml to get the eQTL dataset source."""
    manifest_path = PROJECT_ROOT / "manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.yaml not found at {manifest_path}")
    
    import yaml
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset_from_source(source_type: str, source_id: str, output_path: Path) -> None:
    """
    Download the dataset from a real source.
    
    Args:
        source_type: Type of source ('huggingface', 'geo', 'sra', 'url')
        source_id: Identifier for the dataset (e.g., dataset name, accession, URL)
        output_path: Path where the file should be saved
    """
    logger.info(f"Downloading dataset from {source_type}: {source_id}")
    
    if source_type == 'huggingface':
        # Use HuggingFace datasets to download
        # This assumes the dataset is available on HuggingFace Hub
        try:
            # Load the dataset in streaming mode first to get the config
            # Then download the full dataset to the specified path
            dataset = load_dataset(source_id, split="train", streaming=True)
            
            # For a full download, we need to know the exact file structure
            # This is a simplified approach - in practice, you might need to
            # handle multiple files or specific configurations
            logger.info(f"Dataset info: {dataset}")
            
            # For demonstration, we assume a TSV file structure
            # In a real implementation, you would download the specific file
            # from the dataset repository
            import requests
            # This is a placeholder - the actual URL would come from the dataset
            # For now, we'll simulate the download process
            logger.warning("HuggingFace download requires specific dataset configuration. "
                         "Please update this function with the actual dataset details.")
            # In a real scenario, you would use hf_hub_download or similar
            raise NotImplementedError("HuggingFace download implementation requires specific dataset details.")
            
        except Exception as e:
            logger.error(f"Failed to download from HuggingFace: {e}")
            raise
    
    elif source_type == 'url':
        # Direct URL download
        import requests
        response = requests.get(source_id, stream=True)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded to {output_path}")
    
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

def verify_checksum(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify the checksum of a downloaded file.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected checksum (if None, compute and save)
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = calculate_sha256(file_path)
    logger.info(f"Computed checksum: {actual_checksum}")
    
    if expected_checksum:
        if actual_checksum == expected_checksum:
            logger.info("Checksum verification passed.")
            return True
        else:
            logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
            return False
    else:
        # Save the checksum
        with open(CHECKSUM_FILE, 'w') as f:
            f.write(actual_checksum)
        logger.info(f"Checksum saved to {CHECKSUM_FILE}")
        return True

def stream_and_process_dataset(dataset_path: Path) -> Dict[str, Any]:
    """
    Stream the dataset and perform initial processing.
    
    Args:
        dataset_path: Path to the downloaded dataset file
        
    Returns:
        Dictionary with processing statistics
    """
    logger.info(f"Streaming dataset from {dataset_path}")
    
    # Determine the format and load accordingly
    if dataset_path.suffix == '.tsv':
        # Load as TSV using pandas with chunking
        # Since we're streaming, we'll use a generator approach
        chunk_size = 10000
        total_rows = 0
        total_genes = 0
        stress_columns = []
        
        # First, read the header to identify columns
        header = pd.read_csv(dataset_path, sep='\t', nrows=0).columns.tolist()
        logger.info(f"Dataset columns: {header}")
        
        # Identify stress columns (from T051 validation requirements)
        expected_stress_cols = ['heat-shock', 'osmotic', 'oxidative']
        stress_columns = [col for col in expected_stress_cols if col in header]
        
        if not stress_columns:
            raise ValueError("No expected stress columns found in dataset. "
                           f"Expected at least one of: {expected_stress_cols}")
        
        logger.info(f"Found stress columns: {stress_columns}")
        
        # Stream the data in chunks
        for chunk in pd.read_csv(dataset_path, sep='\t', chunksize=chunk_size):
            total_rows += len(chunk)
            total_genes += chunk['gene'].nunique() if 'gene' in chunk.columns else 0
            
            # Validate required columns exist in each chunk
            for col in stress_columns:
                if col not in chunk.columns:
                    raise ValueError(f"Required column '{col}' missing in data chunk")
        
        stats = {
            'total_rows': total_rows,
            'total_genes': total_genes,
            'stress_columns': stress_columns,
            'chunk_size': chunk_size
        }
        
    elif dataset_path.suffix == '.parquet':
        # Load as Parquet
        dataset = load_dataset("parquet", data_files=str(dataset_path))
        total_rows = len(dataset['train'])
        stats = {'total_rows': total_rows, 'format': 'parquet'}
    
    else:
        # Try to load as a generic dataset
        try:
            dataset = load_dataset("csv", data_files=str(dataset_path))
            total_rows = len(dataset['train'])
            stats = {'total_rows': total_rows, 'format': 'csv'}
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    logger.info(f"Streaming complete. Processed {total_rows} rows.")
    return stats

def main():
    """Main entry point for the eQTL streaming pipeline."""
    parser = argparse.ArgumentParser(
        description="Download and stream eQTL dataset for processing."
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if file exists"
    )
    args = parser.parse_args()
    
    # Ensure data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load manifest to get dataset source
    try:
        manifest = load_manifest()
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)
    
    # Extract eQTL dataset info from manifest
    eqtl_source = None
    for dataset in manifest.get('datasets', []):
        if dataset.get('type') == 'eqtl':
            eqtl_source = dataset
            break
    
    if not eqtl_source:
        logger.error("No eQTL dataset found in manifest.yaml. "
                   "Please ensure T052 has populated the manifest with verified accessions.")
        sys.exit(1)
    
    source_type = eqtl_source.get('source_type', 'url')
    source_id = eqtl_source.get('source_id')
    
    if not source_id:
        logger.error("No source_id found for eQTL dataset in manifest.")
        sys.exit(1)
    
    # Check if file already exists
    file_exists = EQTL_OUTPUT_FILE.exists()
    
    if file_exists and not args.force_download:
        logger.info(f"File {EQTL_OUTPUT_FILE} already exists. Skipping download.")
        # Verify checksum
        checksum = None
        if CHECKSUM_FILE.exists():
            with open(CHECKSUM_FILE, 'r') as f:
                checksum = f.read().strip()
        
        if not verify_checksum(EQTL_OUTPUT_FILE, checksum):
            logger.warning("Checksum verification failed. Re-downloading...")
            file_exists = False
    
    if not file_exists:
        try:
            download_dataset_from_source(source_type, source_id, EQTL_OUTPUT_FILE)
            
            # Verify checksum after download
            if not verify_checksum(EQTL_OUTPUT_FILE):
                logger.error("Checksum verification failed after download.")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            # Fail loudly - do not fall back to synthetic data
            raise
    
    # Stream and process the dataset
    try:
        stats = stream_and_process_dataset(EQTL_OUTPUT_FILE)
        logger.info("Dataset processing completed successfully.")
        logger.info(f"Statistics: {stats}")
        
        # Save processing stats
        stats_file = DATA_RAW_DIR / "eqtl_processing_stats.json"
        import json
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Processing stats saved to {stats_file}")
        
    except Exception as e:
        logger.error(f"Failed to stream/process dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
