"""
Integration test for Zenodo DOI reachability and data retention.

This test verifies:
1. The primary Zenodo DOI (10.5281/zenodo.10043838) is reachable.
2. The fallback DOI (10.5281/zenodo.11023456) is reachable if primary fails.
3. The data loading pipeline successfully retrieves records with non-null Tg and composition.
4. The retention rate is calculated and logged.
5. The cleaned data is written to disk.

This test MUST fail loudly if the real data source is unreachable.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import pytest
import pandas as pd

# Import the actual implementation from the project code
from code.ingest import fetch_from_zenodo, load_and_validate_data, clean_data
from code.config.config import get_config

# Configure logging for the test run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants from tasks.md
PRIMARY_DOI = "10.5281/zenodo.10043838"
FALLBACK_DOI = "10.5281/zenodo.11023456"
OUTPUT_PATH = Path("data/processed/cleaned_mg.csv")
STATS_PATH = Path("data/ingestion_stats.json")

# Ensure data directories exist
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
STATS_PATH.parent.mkdir(parents=True, exist_ok=True)


class TestZenodoIngestion:
    """Integration tests for Zenodo data ingestion."""

    def test_primary_doi_reachability(self):
        """Test that the primary Zenodo DOI is reachable and returns a record."""
        logger.info(f"Testing reachability of primary DOI: {PRIMARY_DOI}")
        
        try:
            record = fetch_from_zenodo(PRIMARY_DOI)
            assert record is not None, "Primary DOI fetch returned None"
            assert "files" in record, "Primary DOI record missing 'files' key"
            assert len(record["files"]) > 0, "Primary DOI record has no files"
            logger.info(f"Primary DOI reachable. Found {len(record['files'])} files.")
        except Exception as e:
            pytest.fail(f"Primary DOI {PRIMARY_DOI} is unreachable: {str(e)}")

    def test_fallback_doi_reachability_if_primary_fails(self):
        """Test fallback DOI if primary fails (skipped if primary succeeds)."""
        try:
            fetch_from_zenodo(PRIMARY_DOI)
            logger.info("Primary DOI succeeded, skipping fallback test.")
            return
        except Exception:
            logger.info("Primary DOI failed, testing fallback DOI.")
            try:
                record = fetch_from_zenodo(FALLBACK_DOI)
                assert record is not None, "Fallback DOI fetch returned None"
                assert "files" in record, "Fallback DOI record missing 'files' key"
                logger.info(f"Fallback DOI reachable. Found {len(record['files'])} files.")
            except Exception as e:
                pytest.fail(f"Both primary and fallback DOIs are unreachable: {str(e)}")

    def test_data_loading_and_validation(self):
        """Test that data can be loaded and validated from the real Zenodo source."""
        logger.info("Testing data loading and validation from Zenodo.")
        
        # Determine which DOI works
        doi_to_use = None
        for doi in [PRIMARY_DOI, FALLBACK_DOI]:
            try:
                fetch_from_zenodo(doi)
                doi_to_use = doi
                break
            except Exception:
                continue

        if not doi_to_use:
            pytest.fail("No reachable DOI found for data loading test.")

        logger.info(f"Using DOI: {doi_to_use} for data loading.")
        record = fetch_from_zenodo(doi_to_use)
        
        # The ingest module expects a specific file name or structure.
        # We assume the first file in the record is the dataset.
        file_info = record["files"][0]
        file_url = file_info["links"]["self"]
        
        # Load and validate
        df = load_and_validate_data(file_url)
        
        assert df is not None, "Data loading returned None"
        assert isinstance(df, pd.DataFrame), "Loaded data is not a DataFrame"
        assert df.shape[0] > 0, "Loaded DataFrame is empty"
        
        # Check for required columns (Tg and composition)
        # The schema might vary, but Tg is critical.
        # Assuming 'Tg' or 'T_g' exists based on domain context.
        tg_cols = [c for c in df.columns if 'Tg' in c or 'T_g' in c]
        if not tg_cols:
            # Fallback check for common variations
            tg_cols = [c for c in df.columns if 'temperature' in c.lower()]
        
        assert len(tg_cols) > 0, f"Could not find Tg column in {df.columns}"
        
        logger.info(f"Data loaded successfully: {df.shape}")
        return df

    def test_data_cleaning_and_retention(self):
        """Test the cleaning logic and retention rate calculation."""
        logger.info("Testing data cleaning and retention.")
        
        # Re-load data for this test
        doi_to_use = None
        for doi in [PRIMARY_DOI, FALLBACK_DOI]:
            try:
                fetch_from_zenodo(doi)
                doi_to_use = doi
                break
            except Exception:
                continue

        if not doi_to_use:
            pytest.fail("No reachable DOI found for cleaning test.")

        record = fetch_from_zenodo(doi_to_use)
        file_url = record["files"][0]["links"]["self"]
        
        raw_df = load_and_validate_data(file_url)
        initial_count = len(raw_df)
        assert initial_count > 0, "Raw data is empty"
        
        # Clean data
        cleaned_df = clean_data(raw_df)
        final_count = len(cleaned_df)
        
        assert final_count > 0, "Cleaned data is empty - all records dropped?"
        assert final_count <= initial_count, "Cleaned data count exceeds raw data count"
        
        retention_rate = final_count / initial_count
        logger.info(f"Retention rate: {retention_rate:.2%} ({final_count}/{initial_count})")
        
        assert retention_rate > 0.0, "Retention rate is zero"
        
        # Verify no null Tg in cleaned data
        tg_cols = [c for c in cleaned_df.columns if 'Tg' in c or 'T_g' in c]
        if tg_cols:
            tg_col = tg_cols[0]
            assert cleaned_df[tg_col].isnull().sum() == 0, "Cleaned data contains null Tg values"
        
        # Verify composition columns (assuming 'Composition' or similar)
        comp_cols = [c for c in cleaned_df.columns if 'Composition' in c or 'composition' in c]
        if comp_cols:
            comp_col = comp_cols[0]
            # Check for empty strings or nulls
            null_comp = cleaned_df[comp_col].isnull().sum()
            empty_comp = (cleaned_df[comp_col].astype(str) == "").sum()
            assert null_comp == 0 and empty_comp == 0, "Cleaned data contains missing composition"

    def test_end_to_end_ingestion_and_output(self):
        """Full integration test: fetch, clean, save, and verify stats."""
        logger.info("Running end-to-end ingestion test.")
        
        # Determine working DOI
        doi_to_use = None
        for doi in [PRIMARY_DOI, FALLBACK_DOI]:
            try:
                fetch_from_zenodo(doi)
                doi_to_use = doi
                break
            except Exception:
                continue

        if not doi_to_use:
            pytest.fail("No reachable DOI found for end-to-end test.")

        record = fetch_from_zenodo(doi_to_use)
        file_url = record["files"][0]["links"]["self"]
        
        raw_df = load_and_validate_data(file_url)
        cleaned_df = clean_data(raw_df)
        
        # Save cleaned data
        cleaned_df.to_csv(OUTPUT_PATH, index=False)
        assert OUTPUT_PATH.exists(), "Cleaned data file was not created"
        
        # Calculate and save stats
        stats = {
            "primary_doi": PRIMARY_DOI,
            "fallback_doi": FALLBACK_DOI,
            "used_doi": doi_to_use,
            "initial_count": len(raw_df),
            "final_count": len(cleaned_df),
            "retention_rate": len(cleaned_df) / len(raw_df),
            "output_file": str(OUTPUT_PATH)
        }
        
        with open(STATS_PATH, "w") as f:
            json.dump(stats, f, indent=2)
        
        assert STATS_PATH.exists(), "Stats file was not created"
        
        # Verify stats content
        with open(STATS_PATH, "r") as f:
            loaded_stats = json.load(f)
        
        assert loaded_stats["final_count"] > 0, "Final count in stats is zero"
        assert loaded_stats["retention_rate"] > 0.0, "Retention rate in stats is zero"
        
        logger.info(f"End-to-end test passed. Output: {OUTPUT_PATH}, Stats: {STATS_PATH}")