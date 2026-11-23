"""
Integration test for the full data pipeline (NOAA, Yahoo Finance, UK Grid).
Verifies ingestion, preprocessing, and metrics computation for real public datasets.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Add src to path if not already present
if "src" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

from src.data.ingestion import (
    IngestionError,
    validate_url,
    download_file,
    load_csv_robust,
    DatasetManifest,
    create_manifest,
    ingest_dataset,
)
from src.data.preprocessing import (
    PreprocessingError,
    interpolate_missing,
    check_stationarity,
    detrend_series,
    difference_series,
    preprocess_series,
    preprocess_dataset,
)
from src.data.metrics import (
    MetricsError,
    compute_acf_lag,
    compute_dfa_hurst,
    compute_spectral_peak_ratio,
    compute_all_metrics,
    compute_metrics_for_dataset,
)
from src.utils.logging import setup_logger, get_logger

# Setup logger for integration tests
logger = setup_logger("integration_test", level="INFO")


@pytest.fixture(scope="module")
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    tmp_dir = tempfile.mkdtemp(prefix="pipeline_test_")
    yield tmp_dir
    # Cleanup after test
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def sample_manifest(temp_output_dir):
    """Create a minimal manifest for the integration test."""
    # Define real public URLs for the test
    datasets = [
        {
            "id": "noaa_temp",
            "name": "NOAA Temperature",
            "url": "https://www.ncei.noaa.gov/data/noaa-ghcn-pds/csv/ghcn_daily_all.csv",
            "expected_checksum": None,  # Skip checksum for this test as URLs change
            "description": "NOAA GHCN Daily Temperature",
        },
        {
            "id": "yahoo_aapl",
            "name": "Yahoo Finance AAPL",
            "url": "https://query1.finance.yahoo.com/v7/finance/download/AAPL?period1=1577836800&period2=1609459200&interval=1d&events=history",
            "expected_checksum": None,
            "description": "Apple Inc. Stock Prices",
        },
        {
            "id": "uk_grid_load",
            "name": "UK National Grid Load",
            "url": "https://www.nationalgrideso.com/document/164661/download",
            "expected_checksum": None,
            "description": "UK National Grid Electricity Load",
        },
    ]

    manifest_path = os.path.join(temp_output_dir, "test_manifest.json")
    manifest = create_manifest(datasets, manifest_path)
    return manifest


def test_full_pipeline_ingestion(temp_output_dir, sample_manifest):
    """Test ingestion of all datasets in the manifest."""
    logger.info("Starting ingestion test...")
    processed_files = {}

    for dataset in sample_manifest["datasets"]:
        dataset_id = dataset["id"]
        logger.info(f"Ingesting dataset: {dataset_id}")

        try:
            # Attempt to download and load
            # Note: In a real CI environment, we might need to handle rate limits or specific access
            # For this test, we attempt to load the URL directly
            url = dataset["url"]
            validate_url(url)

            # Create a temporary file for download
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Download the file
                download_file(url, tmp_path)
                logger.info(f"Downloaded {dataset_id} to {tmp_path}")

                # Load the CSV
                df = load_csv_robust(tmp_path)
                logger.info(f"Loaded {len(df)} rows for {dataset_id}")

                # Save to processed directory
                processed_path = os.path.join(temp_output_dir, f"{dataset_id}_raw.csv")
                df.to_csv(processed_path, index=False)
                processed_files[dataset_id] = processed_path

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            # Log the error but continue with other datasets
            # In a real scenario, we might want to fail the test if a critical dataset fails
            logger.warning(f"Failed to ingest {dataset_id}: {str(e)}")
            # For this integration test, we expect at least one dataset to succeed
            # If all fail, the test will fail at the end

    # Assert that at least one dataset was successfully ingested
    assert len(processed_files) > 0, "No datasets were successfully ingested"
    logger.info(f"Successfully ingested {len(processed_files)} datasets")
    return processed_files


def test_full_pipeline_preprocessing(processed_files, temp_output_dir):
    """Test preprocessing (missing value interpolation, stationarity check, differencing/detrending) for all datasets."""
    logger.info("Starting preprocessing test...")
    processed_paths = {}

    for dataset_id, raw_path in processed_files.items():
        logger.info(f"Preprocessing dataset: {dataset_id}")

        try:
            # Load the raw data
            df = pd.read_csv(raw_path)

            # Identify the time series column
            # This is a simplification - in reality, we'd need to detect the column
            # For this test, we'll assume the first numeric column is the time series
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                logger.warning(f"No numeric columns found in {dataset_id}, skipping")
                continue

            ts_col = numeric_cols[0]
            ts_data = df[ts_col].dropna().values

            # Skip if too short
            if len(ts_data) < 25:
                logger.warning(f"Dataset {dataset_id} has less than 25 points, skipping")
                continue

            # Preprocess the series
            preprocessed_data, status = preprocess_series(ts_data)

            if status != "success":
                logger.warning(f"Preprocessing failed for {dataset_id}: {status}")
                continue

            # Save preprocessed data
            preprocessed_path = os.path.join(temp_output_dir, f"{dataset_id}_preprocessed.csv")
            pd.Series(preprocessed_data).to_csv(preprocessed_path, index=False, header=[ts_col])
            processed_paths[dataset_id] = preprocessed_path

        except Exception as e:
            logger.error(f"Preprocessing error for {dataset_id}: {str(e)}")
            # Continue with other datasets

    assert len(processed_paths) > 0, "No datasets were successfully preprocessed"
    logger.info(f"Successfully preprocessed {len(processed_paths)} datasets")
    return processed_paths


def test_full_pipeline_metrics(processed_paths, temp_output_dir):
    """Test metrics computation (ACF, Hurst, Spectral Density) for all preprocessed datasets."""
    logger.info("Starting metrics computation test...")
    metrics_results = {}

    for dataset_id, preprocessed_path in processed_paths.items():
        logger.info(f"Computing metrics for {dataset_id}")

        try:
            # Load preprocessed data
            df = pd.read_csv(preprocessed_path)
            ts_data = df.iloc[:, 0].values

            # Compute metrics
            metrics = compute_all_metrics(ts_data)

            # Save metrics
            metrics_path = os.path.join(temp_output_dir, f"{dataset_id}_metrics.json")
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)

            metrics_results[dataset_id] = metrics

        except Exception as e:
            logger.error(f"Metrics computation error for {dataset_id}: {str(e)}")
            # Continue with other datasets

    assert len(metrics_results) > 0, "No datasets had metrics computed"
    logger.info(f"Successfully computed metrics for {len(metrics_results)} datasets")

    # Verify metrics structure
    for dataset_id, metrics in metrics_results.items():
        assert "ACF_Lag20" in metrics, f"ACF_Lag20 missing for {dataset_id}"
        assert "Hurst_Exponent" in metrics, f"Hurst_Exponent missing for {dataset_id}"
        assert "Spectral_Peak_Ratio" in metrics, f"Spectral_Peak_Ratio missing for {dataset_id}"
        logger.info(f"Metrics for {dataset_id}: {metrics}")

    return metrics_results


def test_end_to_end_pipeline(temp_output_dir):
    """Run the full pipeline: ingestion -> preprocessing -> metrics."""
    logger.info("Starting end-to-end pipeline test...")

    # Step 1: Create manifest
    sample_manifest = None
    try:
        datasets = [
            {
                "id": "yahoo_aapl",
                "name": "Yahoo Finance AAPL",
                "url": "https://query1.finance.yahoo.com/v7/finance/download/AAPL?period1=1577836800&period2=1609459200&interval=1d&events=history",
                "expected_checksum": None,
                "description": "Apple Inc. Stock Prices",
            },
        ]
        manifest_path = os.path.join(temp_output_dir, "test_manifest.json")
        sample_manifest = create_manifest(datasets, manifest_path)
    except Exception as e:
        logger.warning(f"Could not create manifest: {str(e)}")
        # If manifest creation fails, skip the rest of the test
        pytest.skip("Manifest creation failed, skipping end-to-end test")

    # Step 2: Ingestion
    processed_files = test_full_pipeline_ingestion(temp_output_dir, sample_manifest)

    # Step 3: Preprocessing
    processed_paths = test_full_pipeline_preprocessing(processed_files, temp_output_dir)

    # Step 4: Metrics
    metrics_results = test_full_pipeline_metrics(processed_paths, temp_output_dir)

    # Final assertion: ensure the pipeline produced valid results
    assert len(metrics_results) > 0, "End-to-end pipeline failed to produce any results"
    logger.info("End-to-end pipeline test completed successfully")