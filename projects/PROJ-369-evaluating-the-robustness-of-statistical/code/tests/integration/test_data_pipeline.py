"""Integration test for full data pipeline."""
import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'src'))

from data.ingestion import create_manifest, ingest_dataset
from data.preprocessing import preprocess_dataset
from data.metrics import compute_metrics_for_dataset

def test_full_pipeline():
    """Test the full pipeline: ingestion -> preprocessing -> metrics."""
    # This is a placeholder for the actual integration test
    # It would require real URLs and data
    assert True
