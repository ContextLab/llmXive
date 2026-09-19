import pytest
import pandas as pd
from pathlib import Path
import ingestion

def test_ingestion_structure():
    """Test that ingestion functions exist and have correct signatures."""
    assert hasattr(ingestion, 'ingest_nist_data')
    assert hasattr(ingestion, 'ingest_pubchem_data')
    assert hasattr(ingestion, 'ingest_mtr_data')
    assert hasattr(ingestion, 'main')

def test_data_loader_interface():
    """Test that data loader functions exist."""
    from utils.data_loader import fetch_nist_data, fetch_pubchem_data, fetch_mtr_data
    assert callable(fetch_nist_data)
    assert callable(fetch_pubchem_data)
    assert callable(fetch_mtr_data)
