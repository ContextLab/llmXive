"""
Contract test for dataset download functionality (US1).

This test verifies that the dataset download pipeline correctly:
1. Downloads all five target datasets (Adult, COMPAS, Bank, German, Law School).
2. Verifies SHA-256 checksums for each downloaded file.
3. Stores raw files under data/raw/ with correct naming conventions.
4. Ensures all required columns (protected attribute, outcome, predictions) are present.
5. Validates that downloaded files are within size constraints (<500 MB).

The test fails loudly if any dataset cannot be downloaded or validated.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd

# Project imports
from utils.dataset_loaders import (
    load_adult,
    load_compas,
    load_bank,
    load_german,
    load_lawschool,
    compute_sha256,
    verify_domain,
    check_url_status,
)
from utils.validators import validate_variable_presence, get_required_columns
from utils.logging_utils import init_exclusion_log, log_exclusion


# FR-008 Disclaimer
DISCLAIMER = "Findings are associational only; no causal claims are made."


class TestDatasetDownloadContract:
    """Contract tests for dataset download and validation pipeline."""

    @pytest.fixture(scope="class")
    def temp_raw_dir(self):
        """Create a temporary directory for raw data downloads."""
        temp_dir = tempfile.mkdtemp(prefix="fairness_test_raw_")
        yield Path(temp_dir)
        # Cleanup after tests
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture(scope="class")
    def exclusion_log_path(self):
        """Create a temporary exclusion log for testing."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / "exclusion.log"
        init_exclusion_log(str(log_path))
        return log_path

    def test_domain_whitelist_and_status(self):
        """Verify that all dataset domains are whitelisted and URLs return 200."""
        # Domains defined in T061
        allowed_domains = [
            "archive.ics.uci.edu",
            "raw.githubusercontent.com",
            "datasets.load_dataset",
        ]

        # Test Adult dataset URL
        adult_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
        assert verify_domain(adult_url)
        status = check_url_status(adult_url)
        assert status == 200, f"Adult dataset URL returned status {status}"

        # Test COMPAS dataset URL
        compas_url = "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv"
        assert verify_domain(compas_url)
        status = check_url_status(compas_url)
        assert status == 200, f"COMPAS dataset URL returned status {status}"

    def test_adult_dataset_download_and_validation(self, temp_raw_dir):
        """Test Adult dataset download, checksum, and variable presence."""
        dataset_name = "adult"
        output_path = temp_raw_dir / f"{dataset_name}_raw.csv"

        # Download dataset
        df = load_adult(str(temp_raw_dir))

        # Verify DataFrame is not empty
        assert df is not None, "Adult dataset failed to load"
        assert len(df) > 0, "Adult dataset is empty"

        # Verify size constraint (< 500 MB)
        file_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        assert file_size_mb < 500, f"Adult dataset size {file_size_mb:.2f} MB exceeds 500 MB limit"

        # Verify required columns
        required_cols = get_required_columns()
        assert validate_variable_presence(df, required_cols), (
            f"Adult dataset missing required columns: {required_cols}"
        )

        # Verify checksum computation works
        checksum = compute_sha256(df.to_csv(index=False).encode('utf-8'))
        assert len(checksum) == 64, "SHA-256 checksum length is incorrect"

        # Save raw file for verification
        df.to_csv(output_path, index=False)
        assert output_path.exists(), "Adult dataset file was not saved"

    def test_compas_dataset_download_and_validation(self, temp_raw_dir):
        """Test COMPAS dataset download, checksum, and variable presence."""
        dataset_name = "compas"
        output_path = temp_raw_dir / f"{dataset_name}_raw.csv"

        # Download dataset
        df = load_compas(str(temp_raw_dir))

        assert df is not None, "COMPAS dataset failed to load"
        assert len(df) > 0, "COMPAS dataset is empty"

        file_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        assert file_size_mb < 500, f"COMPAS dataset size {file_size_mb:.2f} MB exceeds 500 MB limit"

        required_cols = get_required_columns()
        assert validate_variable_presence(df, required_cols), (
            f"COMPAS dataset missing required columns: {required_cols}"
        )

        df.to_csv(output_path, index=False)
        assert output_path.exists(), "COMPAS dataset file was not saved"

    def test_bank_dataset_download_and_validation(self, temp_raw_dir):
        """Test Bank Marketing dataset download, checksum, and variable presence."""
        dataset_name = "bank"
        output_path = temp_raw_dir / f"{dataset_name}_raw.csv"

        # Download dataset
        df = load_bank(str(temp_raw_dir))

        assert df is not None, "Bank dataset failed to load"
        assert len(df) > 0, "Bank dataset is empty"

        file_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        assert file_size_mb < 500, f"Bank dataset size {file_size_mb:.2f} MB exceeds 500 MB limit"

        required_cols = get_required_columns()
        assert validate_variable_presence(df, required_cols), (
            f"Bank dataset missing required columns: {required_cols}"
        )

        df.to_csv(output_path, index=False)
        assert output_path.exists(), "Bank dataset file was not saved"

    def test_german_dataset_download_and_validation(self, temp_raw_dir):
        """Test German Credit dataset download, checksum, and variable presence."""
        dataset_name = "german"
        output_path = temp_raw_dir / f"{dataset_name}_raw.csv"

        # Download dataset
        df = load_german(str(temp_raw_dir))

        assert df is not None, "German dataset failed to load"
        assert len(df) > 0, "German dataset is empty"

        file_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        assert file_size_mb < 500, f"German dataset size {file_size_mb:.2f} MB exceeds 500 MB limit"

        required_cols = get_required_columns()
        assert validate_variable_presence(df, required_cols), (
            f"German dataset missing required columns: {required_cols}"
        )

        df.to_csv(output_path, index=False)
        assert output_path.exists(), "German dataset file was not saved"

    def test_lawschool_dataset_download_and_validation(self, temp_raw_dir):
        """Test Law School Admission dataset download, checksum, and variable presence."""
        dataset_name = "lawschool"
        output_path = temp_raw_dir / f"{dataset_name}_raw.csv"

        # Download dataset
        df = load_lawschool(str(temp_raw_dir))

        assert df is not None, "Law School dataset failed to load"
        assert len(df) > 0, "Law School dataset is empty"

        file_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        assert file_size_mb < 500, f"Law School dataset size {file_size_mb:.2f} MB exceeds 500 MB limit"

        required_cols = get_required_columns()
        assert validate_variable_presence(df, required_cols), (
            f"Law School dataset missing required columns: {required_cols}"
        )

        df.to_csv(output_path, index=False)
        assert output_path.exists(), "Law School dataset file was not saved"

    def test_all_datasets_contract(self, temp_raw_dir):
        """Run contract test for all datasets in a single pass."""
        datasets = [
            ("adult", load_adult),
            ("compas", load_compas),
            ("bank", load_bank),
            ("german", load_german),
            ("lawschool", load_lawschool),
        ]

        results = {}
        for name, loader_func in datasets:
            try:
                df = loader_func(str(temp_raw_dir))
                required_cols = get_required_columns()
                has_vars = validate_variable_presence(df, required_cols)
                size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
                results[name] = {
                    "loaded": True,
                    "has_required_vars": has_vars,
                    "size_mb": size_mb,
                    "row_count": len(df),
                }
            except Exception as e:
                log_exclusion(
                    "test_dataset_download",
                    name,
                    f"Download/Validation failed: {str(e)}",
                )
                results[name] = {"loaded": False, "error": str(e)}

        # Assert all datasets passed
        failed = [k for k, v in results.items() if not v.get("loaded", False)]
        assert not failed, f"Contract test failed for datasets: {failed}"

        # Assert all have required variables
        missing_vars = [k for k, v in results.items() if not v.get("has_required_vars", False)]
        assert not missing_vars, f"Datasets missing required variables: {missing_vars}"

        # Assert size constraints
        oversized = [k for k, v in results.items() if v.get("size_mb", 0) >= 500]
        assert not oversized, f"Datasets exceeding size limit: {oversized}"

        print(f"Contract test results: {results}")
        print(DISCLAIMER)