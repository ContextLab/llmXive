import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Local imports based on provided API surface
from logger import get_logger
from error_handling import handle_errors, validate_required_fields
from exceptions import DiscrepancyError, DataAcquisitionError, MissingDataError, ValidationFailureError
from models import validate_output_schema

# Configure logger
logger = get_logger(__name__)

class DataIngestionPipeline:
    """
    Handles the ingestion of raw election data, validation of required fields,
    and initial preprocessing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ingestion pipeline.

        Args:
            config: Optional configuration dictionary containing data sources,
                    validation rules, and output paths.
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.required_fields = self._load_required_fields()
        self.raw_data_dir = Path(self.config.get('paths', {}).get('raw', 'data/raw'))
        self.processed_data_dir = Path(self.config.get('paths', {}).get('processed', 'data/processed'))

        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def _load_required_fields(self) -> List[str]:
        """
        Load the list of required fields from configuration or defaults.
        These fields are critical for discrepancy calculation.
        """
        default_fields = ['precinct_votes', 'county_total_votes']
        return self.config.get('validation', {}).get('required_fields', default_fields)

    def _validate_file_exists(self, file_path: Path) -> None:
        """
        Validate that a specific file exists before attempting to read it.

        Args:
            file_path: Path to the file to check.

        Raises:
            DataAcquisitionError: If the file does not exist.
        """
        if not file_path.exists():
            raise DataAcquisitionError(f"Required data file not found: {file_path}")

    def _validate_dataframe_schema(self, df: pd.DataFrame, source_file: str) -> None:
        """
        Validate that the loaded DataFrame contains all required fields.
        This is the core validation logic for T016.

        Args:
            df: The DataFrame to validate.
            source_file: The name of the source file for error reporting.

        Raises:
            ValidationFailureError: If required fields are missing or empty.
        """
        if df.empty:
            raise ValidationFailureError(f"Loaded data from {source_file} is empty.")

        # Check for missing columns
        missing_cols = [col for col in self.required_fields if col not in df.columns]
        
        if missing_cols:
            error_msg = (
                f"Validation failed in {source_file}: "
                f"Missing required columns: {missing_cols}. "
                f"Required columns are: {self.required_fields}."
            )
            logger.error(error_msg)
            raise ValidationFailureError(error_msg)

        # Check for nulls in critical fields
        for col in self.required_fields:
            null_count = df[col].isna().sum()
            if null_count > 0:
                logger.warning(
                    f"Found {null_count} null values in column '{col}' for {source_file}. "
                    f"These rows will be flagged or imputed downstream, but strict validation "
                    f"of non-nullity for calculation will happen in discrepancy module."
                )
                # We log but do not raise here for nulls, as imputation might be allowed.
                # However, if the spec requires immediate rejection of nulls, we would raise.
                # Based on T016 description: "raising clear errors if missing [columns]".
                # Nulls in existing columns are handled by T020 (missing data handling).
                # So we only strictly error on missing *columns* here.

        logger.info(f"Schema validation passed for {source_file}.")

    def load_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Load a CSV file and perform schema validation.

        Args:
            file_path: Path to the CSV file.

        Returns:
            pd.DataFrame: The loaded and validated DataFrame.

        Raises:
            DataAcquisitionError: If file cannot be read.
            ValidationFailureError: If schema validation fails.
        """
        self._validate_file_exists(file_path)
        self.logger.info(f"Loading CSV: {file_path}")
        
        try:
            # Auto-detect delimiter
            with open(file_path, 'r') as f:
                first_line = f.readline()
                if ';' in first_line:
                    delimiter = ';'
                elif '\t' in first_line:
                    delimiter = '\t'
                else:
                    delimiter = ','
            
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            # Validate schema (T016 logic)
            self._validate_dataframe_schema(df, str(file_path.name))
            
            return df

        except pd.errors.EmptyDataError:
            raise DataAcquisitionError(f"File {file_path} is empty or invalid.")
        except Exception as e:
            raise DataAcquisitionError(f"Failed to load CSV {file_path}: {str(e)}")

    def process_batch(self, file_paths: List[Path]) -> pd.DataFrame:
        """
        Process a batch of files, validating each and concatenating results.

        Args:
            file_paths: List of paths to CSV files.

        Returns:
            pd.DataFrame: Concatenated DataFrame of all valid files.

        Raises:
            ValidationFailureError: If any file fails validation.
        """
        dfs = []
        for path in file_paths:
            try:
                df = self.load_csv(path)
                df['source_file'] = path.name
                dfs.append(df)
            except (DataAcquisitionError, ValidationFailureError) as e:
                # Depending on strategy, we might skip or fail fast.
                # T016 implies strict validation: "raising clear errors".
                # We re-raise to stop the pipeline on critical schema errors.
                raise e

        if not dfs:
            raise DataAcquisitionError("No valid files were processed.")

        combined_df = pd.concat(dfs, ignore_index=True)
        self.logger.info(f"Combined {len(dfs)} files into {len(combined_df)} rows.")
        
        # Final schema check on combined data
        self._validate_dataframe_schema(combined_df, "combined_batch")
        
        return combined_df

    def run(self) -> pd.DataFrame:
        """
        Execute the ingestion pipeline based on configuration.

        Returns:
            pd.DataFrame: The final processed DataFrame.

        Raises:
            DataAcquisitionError: If ingestion fails.
        """
        source_files = self.config.get('sources', {}).get('files', [])
        if not source_files:
            # Fallback to scanning data/raw if no files specified in config
            source_files = list(self.raw_data_dir.glob("*.csv"))
            if not source_files:
                raise DataAcquisitionError("No source files found in data/raw or config.")

        paths = [Path(f) if isinstance(f, str) else f for f in source_files]
        return self.process_batch(paths)


@handle_errors
def main():
    """
    Entry point for the ingestion script.
    Loads configuration, runs the pipeline, and saves raw/processed data.
    """
    # Default config if none provided
    config = {
        'paths': {
            'raw': 'data/raw',
            'processed': 'data/processed'
        },
        'validation': {
            'required_fields': ['precinct_votes', 'county_total_votes']
        },
        'sources': {
            'files': []  # Will auto-discover from data/raw if empty
        }
    }

    # Try to load from a config file if it exists
    config_path = Path('config/ingestion_config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            config.update(user_config)

    pipeline = DataIngestionPipeline(config)
    
    try:
        logger.info("Starting Data Ingestion Pipeline (T016 Validation)")
        df = pipeline.run()
        
        # Save processed data
        output_path = pipeline.processed_data_dir / 'ingested_data.csv'
        df.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")
        
        # Save raw checksums if needed (T021 dependency)
        # For now, just log success
        logger.info("Ingestion pipeline completed successfully.")
        return df

    except (DataAcquisitionError, ValidationFailureError) as e:
        logger.critical(f"Ingestion failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()