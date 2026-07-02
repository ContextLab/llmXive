"""
Integration test for the full preprocessing and matching pipeline (User Story 1).

This test verifies:
1. Existence of processed data files (microbiome_features.csv, eeg_features.csv).
2. Minimum row counts for processed data (Microbiome >= 100, EEG >= 50).
3. Successful path selection logic:
   - If matched_pairs.csv exists, verify it has >= 10 rows.
   - If distribution_groups.csv exists, verify it has valid group assignments.
4. Schema compliance for the output files using the project's SchemaValidator.
"""

import os
import sys
import logging
import pytest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_project_root
from schema_validator import SchemaValidator, validate_artifacts
from logging_config import get_logger, initialize_logging

# Initialize logger for test output
initialize_logging()
logger = get_logger("integration_test_preprocessing")

# Constants for thresholds defined in tasks.md
MIN_MICROBIOME_ROWS = 100
MIN_EEG_ROWS = 50
MIN_MATCHED_PAIRS = 10

class TestPreprocessingPipeline:
    """Integration tests for the US1 preprocessing and matching pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.project_root = get_project_root()
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.contracts_dir = self.project_root / "contracts"
        
        # Ensure directories exist (they should from T001)
        assert self.data_processed_dir.exists(), f"Directory {self.data_processed_dir} does not exist. Run T001a/T001c."
        assert self.contracts_dir.exists(), f"Contracts directory {self.contracts_dir} does not exist. Run T004b."

    def test_01_microbiome_file_exists_and_has_rows(self):
        """Verify microbiome_features.csv exists and has >= 100 rows."""
        file_path = self.data_processed_dir / "microbiome_features.csv"
        
        assert file_path.exists(), f"File not found: {file_path}. Run code/preprocess_microbiome.py"
        
        import pandas as pd
        df = pd.read_csv(file_path)
        
        logger.info(f"Microbiome file found with {len(df)} rows.")
        assert len(df) >= MIN_MICROBIOME_ROWS, (
            f"Microbiome data has {len(df)} rows, but requires at least {MIN_MICROBIOME_ROWS}."
        )

    def test_02_eeg_file_exists_and_has_rows(self):
        """Verify eeg_features.csv exists and has >= 50 rows."""
        file_path = self.data_processed_dir / "eeg_features.csv"
        
        assert file_path.exists(), f"File not found: {file_path}. Run code/preprocess_eeg.py"
        
        import pandas as pd
        df = pd.read_csv(file_path)
        
        logger.info(f"EEG file found with {len(df)} rows.")
        assert len(df) >= MIN_EEG_ROWS, (
            f"EEG data has {len(df)} rows, but requires at least {MIN_EEG_ROWS}."
        )

    def test_03_path_selection_logic(self):
        """
        Verify that the pipeline successfully selected a path (A or B).
        - Path A: matched_pairs.csv exists with >= 10 rows.
        - Path B: distribution_groups.csv exists with valid groups.
        """
        matched_pairs_path = self.data_processed_dir / "matched_pairs.csv"
        distribution_groups_path = self.data_processed_dir / "distribution_groups.csv"

        path_a_valid = False
        path_b_valid = False

        # Check Path A
        if matched_pairs_path.exists():
            import pandas as pd
            df = pd.read_csv(matched_pairs_path)
            logger.info(f"Path A selected: matched_pairs.csv found with {len(df)} rows.")
            if len(df) >= MIN_MATCHED_PAIRS:
                path_a_valid = True
            else:
                logger.warning(f"Path A file exists but has insufficient rows: {len(df)} < {MIN_MATCHED_PAIRS}")
        else:
            logger.info("Path A file (matched_pairs.csv) not found.")

        # Check Path B
        if distribution_groups_path.exists():
            import pandas as pd
            df = pd.read_csv(distribution_groups_path)
            logger.info(f"Path B selected: distribution_groups.csv found with {len(df)} rows.")
            # Basic validation: must have a group column and non-zero rows
            if len(df) > 0 and "group" in df.columns:
                path_b_valid = True
            elif len(df) > 0 and "Group" in df.columns:
                path_b_valid = True
            else:
                logger.warning("Path B file exists but lacks expected 'group' column or is empty.")
        else:
            logger.info("Path B file (distribution_groups.csv) not found.")

        # Assert that at least one path was successfully executed
        assert path_a_valid or path_b_valid, (
            "Pipeline failed to produce valid output for either Path A (matched_pairs.csv >= 10 rows) "
            "or Path B (distribution_groups.csv with valid groups)."
        )

    def test_04_schema_compliance(self):
        """
        Verify that the generated output files comply with the defined schemas.
        This acts as a contract test for the data model.
        """
        matched_pairs_path = self.data_processed_dir / "matched_pairs.csv"
        distribution_groups_path = self.data_processed_dir / "distribution_groups.csv"
        
        # Load schema if available
        output_schema_path = self.contracts_dir / "output.schema.yaml"
        
        if not output_schema_path.exists():
            logger.warning(f"Schema file {output_schema_path} not found. Skipping schema validation.")
            # If schema is missing, we rely on the row count tests above
            return

        validator = SchemaValidator(schema_path=str(output_schema_path))
        
        # Validate matched pairs if it exists
        if matched_pairs_path.exists():
            try:
                validator.validate_file(str(matched_pairs_path), schema_key="matched_pairs")
                logger.info("Schema validation passed for matched_pairs.csv")
            except AssertionError as e:
                pytest.fail(f"Schema validation failed for matched_pairs.csv: {e}")

        # Validate distribution groups if it exists
        if distribution_groups_path.exists():
            try:
                validator.validate_file(str(distribution_groups_path), schema_key="distribution_groups")
                logger.info("Schema validation passed for distribution_groups.csv")
            except AssertionError as e:
                pytest.fail(f"Schema validation failed for distribution_groups.csv: {e}")

    def test_05_artifacts_checksum_protocol(self):
        """
        Verify that the checksum protocol is enforced if checksums.txt exists.
        This ensures data integrity as per T006.
        """
        checksums_path = self.project_root / "artifacts" / "checksums.txt"
        
        if not checksums_path.exists():
            # If checksums file doesn't exist yet, this is not a failure of the pipeline itself,
            # but rather that the checksum generation step hasn't run.
            logger.info("artifacts/checksums.txt not found. Skipping checksum verification.")
            return

        from checksum_utils import verify_checksums
        
        # Verify the processed files against the checksums
        processed_files = [
            self.data_processed_dir / "microbiome_features.csv",
            self.data_processed_dir / "eeg_features.csv"
        ]
        
        # Add path-specific files if they exist
        if (self.data_processed_dir / "matched_pairs.csv").exists():
            processed_files.append(self.data_processed_dir / "matched_pairs.csv")
        if (self.data_processed_dir / "distribution_groups.csv").exists():
            processed_files.append(self.data_processed_dir / "distribution_groups.csv")

        try:
            success, failed = verify_checksums(str(checksums_path))
            if not success:
                logger.error(f"Checksum verification failed for: {failed}")
                pytest.fail(f"Checksum verification failed for files: {failed}")
            else:
                logger.info("Checksum verification passed for all processed files.")
        except Exception as e:
            pytest.fail(f"Error during checksum verification: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])