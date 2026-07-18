"""
Unified dataset loader for 2D material elastic moduli prediction.

WARNING: This model is a surrogate interpolating pre-computed DFT results. It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""

import os
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

import pandas as pd
from matminer.datasets import load_dataset

from utils.config import Config
from ingest.loader_base import DataLoader
from ingest.validator import enforce_single_source

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DownloadManifest:
    """Data class to hold download metadata."""
    def __init__(self, source: str, records: int, checksum: str, output_path: str):
        self.source = source
        self.records = records
        self.checksum = checksum
        self.output_path = output_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "records": self.records,
            "checksum": self.checksum,
            "output_path": self.output_path
        }

class UnifiedDatasetLoader(DataLoader):
    """
    Concrete implementation of the DataLoader base class.
    Fetches data from a single canonical source (Materials Project via matminer).
    """

    def __init__(self, source: str = 'materials_project', output_dir: Optional[Path] = None):
        """
        Initialize the loader.

        Args:
            source: The data source identifier ('materials_project', 'aflow', 'oqmd').
                    Only 'materials_project' is currently implemented with matminer.
            output_dir: Directory to save raw data. Defaults to 'data/raw'.
        """
        self.source = source
        self.output_dir = output_dir or Path('data/raw')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Verify source is allowed
        allowed_sources = ['materials_project', 'aflow', 'oqmd']
        if source not in allowed_sources:
            raise ValueError(f"Source '{source}' not in allowed sources: {allowed_sources}")

        # Enforce single source constraint
        enforce_single_source(source)

    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch data from the configured source.

        Returns:
            DataFrame with material_id, composition, cif, elastic_tensor, etc.
        """
        logger.info(f"Fetching data from source: {self.source}")

        if self.source == 'materials_project':
            # Use the verified real data source recipe
            # This loads the 2015 elasticity dataset bundled with matminer
            try:
                df = load_dataset('elastic_tensor_2015')
            except Exception as e:
                logger.error(f"Failed to load dataset from matminer: {e}")
                raise

            # Verify required fields exist
            required_fields = ['material_id', 'composition', 'cif', 'elastic_tensor', 'elastic_tensor_units']
            missing = [f for f in required_fields if f not in df.columns]
            if missing:
                raise ValueError(f"Missing required fields in dataset: {missing}")

            # Rename columns to match our canonical schema
            df = df.rename(columns={
                'elastic_tensor': 'elastic_tensor_6c',
                'elastic_tensor_units': 'elastic_tensor_units'
            })

            logger.info(f"Successfully loaded {len(df)} records from Materials Project (via matminer)")
            return df

        elif self.source == 'aflow':
            # TODO: Implement AFLOW loader when API is available
            raise NotImplementedError(f"Source '{self.source}' not yet implemented")

        elif self.source == 'oqmd':
            # TODO: Implement OQMD loader when API is available
            raise NotImplementedError(f"Source '{self.source}' not yet implemented")

        else:
            raise ValueError(f"Unknown source: {self.source}")

    def validate_source(self) -> bool:
        """
        Validate that the source is accessible and returns valid data.

        Returns:
            True if validation passes, False otherwise.
        """
        try:
            df = self.fetch_data()
            if df is None or len(df) == 0:
                logger.error("Dataset is empty or None")
                return False
            return True
        except Exception as e:
            logger.error(f"Source validation failed: {e}")
            return False

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the loaded dataset.

        Returns:
            Dictionary with source info, record count, and column names.
        """
        df = self.fetch_data()
        return {
            "source": self.source,
            "record_count": len(df),
            "columns": list(df.columns),
            "output_dir": str(self.output_dir)
        }

    def save_raw_data(self, df: pd.DataFrame) -> str:
        """
        Save the raw DataFrame to disk as Parquet.

        Args:
            df: The DataFrame to save.

        Returns:
            Path to the saved file.
        """
        output_path = self.output_dir / "raw_elastic_data.parquet"
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved raw data to {output_path}")
        return str(output_path)

    def compute_checksum(self, file_path: str) -> str:
        """
        Compute SHA256 checksum of a file.

        Args:
            file_path: Path to the file.

        Returns:
            Hex digest of the SHA256 hash.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def run(self) -> DownloadManifest:
        """
        Execute the full download and save process.

        Returns:
            DownloadManifest with metadata about the download.
        """
        # Fetch data
        df = self.fetch_data()

        # Save raw data
        output_path = self.save_raw_data(df)

        # Compute checksum
        checksum = self.compute_checksum(output_path)

        # Create manifest
        manifest = DownloadManifest(
            source=self.source,
            records=len(df),
            checksum=checksum,
            output_path=output_path
        )

        # Save manifest
        manifest_path = self.output_dir / "download_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        logger.info(f"Saved download manifest to {manifest_path}")

        return manifest

def main():
    """Main entry point for the download script."""
    parser = argparse.ArgumentParser(description="Download raw elastic data from canonical source")
    parser.add_argument(
        '--source',
        type=str,
        default=None,
        choices=['materials_project', 'aflow', 'oqmd'],
        help="Data source to use (default: from DATA_SOURCE env var or 'materials_project')"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Output directory for raw data (default: data/raw)"
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help="Sample N records from the dataset (for testing)"
    )

    args = parser.parse_args()

    # Determine source from args or environment
    source = args.source or os.getenv('DATA_SOURCE', 'materials_project')

    # Determine output directory
    output_dir = Path(args.output) if args.output else Path('data/raw')

    logger.info(f"Starting download from source: {source}")
    logger.info(f"Output directory: {output_dir}")

    # Initialize loader
    loader = UnifiedDatasetLoader(source=source, output_dir=output_dir)

    # Validate source
    if not loader.validate_source():
        logger.error("Source validation failed. Exiting.")
        exit(1)

    # Run download
    manifest = loader.run()

    logger.info(f"Download complete. Records: {manifest.records}, Checksum: {manifest.checksum}")

    # If sampling requested, log the sample size
    if args.sample:
        logger.info(f"Note: Full dataset has {manifest.records} records. Sample size: {args.sample}")

if __name__ == '__main__':
    main()
