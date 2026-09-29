"""
Data Ingestion Pipeline for Election Data.

Handles downloading, parsing, and validating election data from verified sources.
Implements strict validation for required variables to ensure data integrity.
"""

import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Set
import pandas as pd
import requests

# Import local project utilities and exceptions
from exceptions import DataAcquisitionError, ValidationFailureError, MissingDataError
from logger import get_logger_for_module, setup_logging

# Configure module logger
logger = get_logger_for_module(__name__)

# Verified data sources (Hugging Face datasets or direct URLs)
VERIFIED_SOURCES = {
    "huggingface": "https://huggingface.co/datasets",
    # Add other verified sources as they are vetted
}

# Required columns for validation
REQUIRED_PRECINCT_COLUMNS = {'precinct_id', 'votes'}
REQUIRED_COUNTY_COLUMNS = {'county_id', 'total_votes'}

# Schema for processed output (defined in T007)
OUTPUT_SCHEMA = [
    'precinct_sum', 
    'county_reported', 
    'discrepancy_abs', 
    'discrepancy_pct', 
    'missing_data'
]

class DataIngestionPipeline:
    """
    Pipeline for ingesting election data from verified sources.
    
    Implements:
    - Verified source gate before download
    - Parsing and normalization
    - Strict validation of required variables (T016)
    - Error handling for missing fields (T014b)
    - Missing data handling (T014c)
    """
    
    def __init__(self, raw_data_dir: str = "data/raw", processed_data_dir: str = "data/processed"):
        """
        Initialize the ingestion pipeline.
        
        Args:
            raw_data_dir: Path to store raw downloaded data
            processed_data_dir: Path to store processed data
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directories ensured: {self.raw_data_dir}, {self.processed_data_dir}")
    
    def verify_source(self, source_url: str) -> bool:
        """
        Verify that a data source is on the verified list.
        
        Args:
            source_url: URL of the data source
            
        Returns:
            True if source is verified, False otherwise
          
        Raises:
            DataAcquisitionError: If source is not verified
        """
        for verified_prefix in VERIFIED_SOURCES.values():
            if source_url.startswith(verified_prefix):
                logger.info(f"Source verified: {source_url}")
                return True
        
        raise DataAcquisitionError(
            f"Data source is not verified: {source_url}. "
            f"Only verified sources are allowed: {list(VERIFIED_SOURCES.values())}"
        )
    
    def download_data(self, source_url: str, filename: str) -> Path:
        """
        Download data from a verified source.
        
        Args:
            source_url: Verified URL to download from
            filename: Local filename to save as
            
        Returns:
            Path to the downloaded file
            
        Raises:
            DataAcquisitionError: If download fails or source is not verified
        """
        self.verify_source(source_url)
        
        local_path = self.raw_data_dir / filename
        
        try:
            logger.info(f"Downloading data from: {source_url}")
            response = requests.get(source_url, timeout=60)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # Compute checksum
            checksum = self._compute_file_hash(local_path)
            logger.info(f"Downloaded {filename} (SHA256: {checksum})")
            
            return local_path
        
        except requests.RequestException as e:
            raise DataAcquisitionError(f"Failed to download data from {source_url}: {str(e)}")
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def load_and_parse_csv(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load and parse a CSV file, normalizing aggregation levels.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Parsed DataFrame
            
        Raises:
            ValidationFailureError: If file cannot be parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise DataAcquisitionError(f"File not found: {file_path}")
        
        try:
            # Auto-detect delimiter
            with open(file_path, 'r') as f:
                sample = f.read(1024)
                if ',' in sample and ';' not in sample:
                    delimiter = ','
                elif ';' in sample:
                    delimiter = ';'
                else:
                    delimiter = ','
            
            df = pd.read_csv(file_path, delimiter=delimiter)
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
            
            return df
        
        except Exception as e:
            raise ValidationFailureError(f"Failed to parse CSV {file_path}: {str(e)}")
    
    def validate_required_variables(self, df: pd.DataFrame, data_type: str = "precinct") -> pd.DataFrame:
        """
        Validate that required variables exist in the DataFrame.
        
        This is the core implementation of T016.
        
        Args:
            df: DataFrame to validate
            data_type: Type of data being validated ('precinct' or 'county')
            
        Returns:
            The validated DataFrame (unchanged)
            
        Raises:
            ValidationFailureError: If required columns are missing
            MissingDataError: If critical fields have no data
        """
        if data_type == "precinct":
            required_cols = REQUIRED_PRECINCT_COLUMNS
        elif data_type == "county":
            required_cols = REQUIRED_COUNTY_COLUMNS
        else:
            raise ValueError(f"Unknown data_type: {data_type}")
        
        logger.info(f"Validating required variables for {data_type} data: {required_cols}")
        
        # Check for missing columns
        missing_cols = required_cols - set(df.columns)
        
        if missing_cols:
            error_msg = (
                f"Required variables missing for {data_type} data: {missing_cols}. "
                f"Available columns: {list(df.columns)}. "
                f"Cannot proceed with analysis without these fields."
            )
            logger.error(error_msg)
            raise ValidationFailureError(error_msg)
        
        # Check for empty critical fields
        for col in required_cols:
            if df[col].isnull().all():
                error_msg = (
                    f"Critical field '{col}' is entirely null/empty in {data_type} data. "
                    f"Cannot proceed with analysis."
                )
                logger.error(error_msg)
                raise MissingDataError(error_msg)
        
        # Check for zero values in vote columns (handled in T014b, but we validate presence)
        vote_cols = [col for col in required_cols if 'vote' in col.lower()]
        for col in vote_cols:
            zero_count = (df[col] == 0).sum()
            if zero_count > 0:
                logger.warning(
                    f"Found {zero_count} records with zero votes in '{col}'. "
                    f"These will be skipped during analysis (T014b)."
                )
        
        logger.info(f"Validation passed for {data_type} data: {len(df)} records")
        return df
    
    def normalize_aggregation_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize aggregation levels across datasets.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Normalized DataFrame
        """
        # Standardize column names
        rename_map = {}
        
        # Map common variations to standard names
        if 'precinct' in df.columns or 'precinct_id' in df.columns:
            pass  # Already standard
        
        # Ensure consistent types
        for col in df.columns:
            if 'id' in col.lower():
                df[col] = df[col].astype(str)
            elif 'vote' in col.lower():
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logger.info(f"Normalized aggregation levels for {len(df)} records")
        return df
    
    def run_pipeline(self, source_url: str, filename: str, data_type: str = "precinct") -> pd.DataFrame:
        """
        Run the full ingestion pipeline.
        
        Args:
            source_url: Verified URL of the data source
            filename: Local filename for the downloaded data
            data_type: Type of data ('precinct' or 'county')
            
        Returns:
            Processed and validated DataFrame
        """
        # Step 1: Download
        local_path = self.download_data(source_url, filename)
        
        # Step 2: Parse
        df = self.load_and_parse_csv(local_path)
        
        # Step 3: Normalize
        df = self.normalize_aggregation_levels(df)
        
        # Step 4: Validate required variables (T016)
        df = self.validate_required_variables(df, data_type)
        
        # Step 5: Save raw data
        raw_output_path = self.raw_data_dir / filename
        df.to_csv(raw_output_path, index=False)
        logger.info(f"Saved raw data to {raw_output_path}")
        
        return df


def main():
    """
    Main entry point for the ingestion pipeline.
    
    Usage:
        python code/ingestion.py --source <url> --filename <name> --type <precinct|county>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest election data from verified sources")
    parser.add_argument("--source", type=str, required=True, help="Verified URL of data source")
    parser.add_argument("--filename", type=str, required=True, help="Local filename to save")
    parser.add_argument("--type", type=str, default="precinct", choices=["precinct", "county"],
                      help="Type of data being ingested")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Raw data directory")
    parser.add_argument("--processed-dir", type=str, default="data/processed", help="Processed data directory")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        pipeline = DataIngestionPipeline(
            raw_data_dir=args.raw_dir,
            processed_data_dir=args.processed_dir
        )
        
        df = pipeline.run_pipeline(
            source_url=args.source,
            filename=args.filename,
            data_type=args.type
        )
        
        logger.info(f"Pipeline completed successfully. Processed {len(df)} records.")
        
    except (DataAcquisitionError, ValidationFailureError, MissingDataError) as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()