"""
Integration test for User Story 1: Data Ingestion and Resistance Score Extraction.

This test verifies that the full download pipeline (T010-T014) executes successfully
and produces a valid CSV output file with the expected schema and minimum row count.

Prerequisites:
- T014 must have been run to generate data/raw/raw_dataset.csv
- The HuggingFace dataset 'plant-metabolomics/herbivore-resistance-v1' must be accessible
"""

import os
import sys
import csv
import hashlib
import json
import logging
from pathlib import Path

# Add project root to path to allow imports from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_ROOT
from ingest import (
    load_raw_dataset,
    extract_resistance_column,
    convert_categorical_to_ordinal,
    check_herbivore_density_normalization,
    save_harmonized_dataset,
    compute_sha256
)

# Configure logging for the test run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'data' / 'interim' / 'integration_test_run.log')
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'sample_id',
    'genotype_id',
    'resistance',
    'herbivore_density'
]

MIN_ROWS = 10

class DataIngestionIntegrationTest:
    """Integration test suite for data ingestion pipeline."""

    def __init__(self):
        self.data_root = Path(DATA_ROOT)
        self.raw_dir = self.data_root / 'raw'
        self.interim_dir = self.data_root / 'interim'
        self.raw_csv_path = self.raw_dir / 'raw_dataset.csv'
        self.checksum_path = self.raw_dir / 'raw_dataset.csv.sha256'
        self.harmonized_path = self.interim_dir / 'harmonized.csv'
        self.verified = False

    def run_full_pipeline(self):
        """Execute the full ingestion pipeline from scratch."""
        logger.info("Starting full data ingestion pipeline...")

        # Step 1: Load raw dataset (T010)
        logger.info("Step 1: Loading raw dataset from HuggingFace...")
        try:
            raw_dataset = load_raw_dataset()
            logger.info(f"Successfully loaded dataset with {len(raw_dataset)} rows.")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

        # Step 2: Extract resistance column (T011)
        logger.info("Step 2: Extracting resistance column...")
        try:
            resistance_data = extract_resistance_column(raw_dataset)
            logger.info("Resistance column extracted successfully.")
        except Exception as e:
            logger.error(f"Failed to extract resistance column: {e}")
            raise

        # Step 3: Convert categorical to ordinal (T012)
        logger.info("Step 3: Converting categorical resistance to ordinal...")
        try:
            ordinal_dataset = convert_categorical_to_ordinal(resistance_data)
            logger.info("Categorical conversion completed.")
        except Exception as e:
            logger.error(f"Failed to convert categorical data: {e}")
            raise

        # Step 4: Check herbivore density (T013)
        logger.info("Step 4: Checking herbivore density normalization...")
        try:
            density_status = check_herbivore_density_normalization(ordinal_dataset)
            logger.info(f"H herbivore density status: {density_status}")
        except Exception as e:
            logger.error(f"Failed to check herbivore density: {e}")
            raise

        # Step 5: Save raw data with checksum (T014)
        logger.info("Step 5: Saving raw dataset and generating checksum...")
        try:
            # Ensure directories exist
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            self.interim_dir.mkdir(parents=True, exist_ok=True)

            # Save raw dataset to CSV
            with open(self.raw_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=ordinal_dataset.column_names)
                writer.writeheader()
                for row in ordinal_dataset:
                    writer.writerow(row)

            # Compute and save checksum
            checksum = compute_sha256(self.raw_csv_path)
            with open(self.checksum_path, 'w', encoding='utf-8') as f:
                f.write(checksum)

            logger.info(f"Raw dataset saved to {self.raw_csv_path}")
            logger.info(f"Checksum saved to {self.checksum_path}")
        except Exception as e:
            logger.error(f"Failed to save raw dataset: {e}")
            raise

        # Step 6: Save harmonized dataset (T015)
        logger.info("Step 6: Saving harmonized dataset...")
        try:
            save_harmonized_dataset(ordinal_dataset, self.harmonized_path)
            logger.info(f"Harmonized dataset saved to {self.harmonized_path}")
        except Exception as e:
            logger.error(f"Failed to save harmonized dataset: {e}")
            raise

        self.verified = True
        logger.info("Pipeline execution completed successfully.")

    def verify_output_structure(self):
        """Verify the output CSV structure meets requirements."""
        logger.info("Verifying output CSV structure...")

        if not self.raw_csv_path.exists():
            raise FileNotFoundError(f"Raw dataset file not found: {self.raw_csv_path}")

        if not self.checksum_path.exists():
            raise FileNotFoundError(f"Checksum file not found: {self.checksum_path}")

        # Verify row count
        with open(self.raw_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            row_count = len(rows)

        if row_count < MIN_ROWS:
            raise AssertionError(
                f"Dataset has only {row_count} rows, but minimum required is {MIN_ROWS}"
            )

        logger.info(f"Row count verification passed: {row_count} rows >= {MIN_ROWS}")

        # Verify required columns
        with open(self.raw_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            actual_columns = reader.fieldnames

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in actual_columns]
        if missing_columns:
            raise AssertionError(
                f"Missing required columns: {missing_columns}. "
                f"Found: {actual_columns}"
            )

        logger.info("Column verification passed. All required columns present.")

        # Verify checksum
        with open(self.checksum_path, 'r', encoding='utf-8') as f:
          stored_checksum = f.read().strip()

        computed_checksum = compute_sha256(self.raw_csv_path)
        if stored_checksum != computed_checksum:
            raise AssertionError(
                f"Checksum mismatch. Stored: {stored_checksum}, Computed: {computed_checksum}"
            )

        logger.info("Checksum verification passed.")

        # Verify harmonized dataset exists
        if not self.harmonized_path.exists():
            raise FileNotFoundError(f"Harmonized dataset not found: {self.harmonized_path}")

        with open(self.harmonized_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            harmonized_rows = list(reader)

        if len(harmonized_rows) != row_count:
            raise AssertionError(
                f"Harmonized dataset row count ({len(harmonized_rows)}) "
                f"does not match raw dataset ({row_count})"
            )

        logger.info("Harmonized dataset verification passed.")

    def run(self):
        """Execute the full integration test."""
        try:
            self.run_full_pipeline()
            self.verify_output_structure()
            logger.info("✅ ALL INTEGRATION TESTS PASSED")
            return True
        except Exception as e:
            logger.error(f"❌ INTEGRATION TEST FAILED: {e}")
            return False


def main():
    """Entry point for the integration test."""
    test_runner = DataIngestionIntegrationTest()
    success = test_runner.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()