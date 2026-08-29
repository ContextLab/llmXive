"""
Unit tests for T018: Data Quality Reporting in ingest.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Mock the config to use temp directories
@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_raw = Path(tmpdir) / "data" / "raw"
        data_processed = Path(tmpdir) / "data" / "processed"
        data_results = Path(tmpdir) / "data" / "results"
        data_raw.mkdir(parents=True)
        data_processed.mkdir(parents=True)
        data_results.mkdir(parents=True)
        yield {
            "raw": data_raw,
            "processed": data_processed,
            "results": data_results
        }

@pytest.fixture
def mock_raw_data(temp_dirs):
    """Create a mock raw parquet file."""
    data = {
        "smiles": ["CCO", "invalid_smiles", "CC(=O)O", None, "C1=CC=CC=C1"],
        "yield": [80.0, "50-60", 95.5, None, 105.0],
        "reaction_class": ["A", "B", "A", "C", "D"]
    }
    df = pd.DataFrame(data)
    path = temp_dirs["raw"] / "uspto_raw.parquet"
    df.to_parquet(path)
    return path

def test_ingest_generates_quality_report(temp_dirs, mock_raw_data):
    """Test that ingest.py generates the data quality report JSON."""
    # Patch the config paths
    with patch("preprocessing.ingest.DATA_RAW_DIR", temp_dirs["raw"]), \
         patch("preprocessing.ingest.DATA_PROCESSED_DIR", temp_dirs["processed"]), \
         patch("preprocessing.ingest.DATA_RESULTS_DIR", temp_dirs["results"]):
         
         # Import after patching
         from preprocessing.ingest import run_ingestion_pipeline
         
         # Run pipeline
         df, metrics = run_ingestion_pipeline()
         
         # Check report file exists
         report_path = temp_dirs["results"] / "data_quality_report.json"
         assert report_path.exists(), "Data quality report JSON not generated"
         
         # Check content
         with open(report_path) as f:
             report = json.load(f)
         
         assert "exclusion_reasons" in report
         assert "data_quality" in report
         assert "counts" in report
         
         # Check specific exclusion reasons
         assert "null_smiles" in report["exclusion_reasons"] or "salt_removal_failed" in report["exclusion_reasons"]
         
         # Check data quality metrics
         assert "yield" in report["data_quality"]
         assert "min" in report["data_quality"]["yield"]
         assert "max" in report["data_quality"]["yield"]

def test_ingest_handles_empty_dataset(temp_dirs, mock_raw_data):
    """Test that ingest.py handles empty dataset after sanitization."""
    # Create a dataset that will be fully excluded
    data = {
        "smiles": [None, None, None],
        "yield": [None, None, None],
        "reaction_class": ["A", "B", "C"]
    }
    df = pd.DataFrame(data)
    path = temp_dirs["raw"] / "uspto_raw.parquet"
    df.to_parquet(path)
    
    with patch("preprocessing.ingest.DATA_RAW_DIR", temp_dirs["raw"]), \
         patch("preprocessing.ingest.DATA_PROCESSED_DIR", temp_dirs["processed"]), \
         patch("preprocessing.ingest.DATA_RESULTS_DIR", temp_dirs["results"]):
         
         from preprocessing.ingest import run_ingestion_pipeline
         
         with pytest.raises(ValueError, match="Sanitization resulted in an empty dataset"):
             run_ingestion_pipeline()

def test_ingest_validates_fingerprint_dimensions(temp_dirs, mock_raw_data):
    """Test that fingerprint dimensions are validated in the report."""
    # This test relies on the fingerprints being generated correctly
    # We assume the fingerprint generation step is working (T016)
    with patch("preprocessing.ingest.DATA_RAW_DIR", temp_dirs["raw"]), \
         patch("preprocessing.ingest.DATA_PROCESSED_DIR", temp_dirs["processed"]), \
         patch("preprocessing.ingest.DATA_RESULTS_DIR", temp_dirs["results"]):
         
         from preprocessing.ingest import run_ingestion_pipeline
         
         df, metrics = run_ingestion_pipeline()
         
         report_path = temp_dirs["results"] / "data_quality_report.json"
         with open(report_path) as f:
             report = json.load(f)
         
         # Check that fingerprint dimensions are reported
         assert "fingerprint_ecfp" in report["data_quality"]
         assert "expected_length" in report["data_quality"]["fingerprint_ecfp"]
         assert report["data_quality"]["fingerprint_ecfp"]["expected_length"] == 2048